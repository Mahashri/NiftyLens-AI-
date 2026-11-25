import asyncio, json, os
from contextlib import AsyncExitStack
from typing import Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class ScreenerMCP:
    def __init__(self):
        self.stack = None; self.session = None; self.tools = set(); self.lock = asyncio.Lock()
    async def connect(self):
        async with self.lock:
            if self.session: return
            stack = AsyncExitStack()
            package = os.getenv("SCREENER_MCP_PACKAGE", "screener-mcp")
            version = os.getenv("SCREENER_MCP_VERSION", "0.2.0")
            params = StdioServerParameters(command="npx", args=["-y", f"{package}@{version}"], env=os.environ.copy())
            try:
                read, write = await stack.enter_async_context(stdio_client(params))
                session = await stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                listed = await session.list_tools()
                self.tools = {t.name for t in listed.tools}; self.stack, self.session = stack, session
            except Exception:
                await stack.aclose(); raise
    async def call(self, name: str, args: dict[str, Any]):
        await self.connect()
        if name not in self.tools: raise ValueError(f"MCP tool not available: {name}")
        async with self.lock: result = await self.session.call_tool(name, args)
        values=[]
        for item in result.content:
            if getattr(item, "text", None):
                try: values.append(json.loads(item.text))
                except json.JSONDecodeError: values.append(item.text)
        if result.isError: raise RuntimeError(str(values))
        return values[0] if len(values)==1 else values
    async def status(self):
        try:
            await self.connect(); return {"connected":True,"tools":sorted(self.tools)}
        except Exception as e: return {"connected":False,"error":str(e),"tools":[]}
    async def close(self):
        if self.stack: await self.stack.aclose()
        self.stack=None; self.session=None; self.tools=set()
