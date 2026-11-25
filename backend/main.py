import os, re, asyncio
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from backend.screener_client import ScreenerMCP

mcp = ScreenerMCP()
@asynccontextmanager
async def lifespan(app):
    yield
    await mcp.close()
app=FastAPI(title="NiftyLens AI",version="0.1.0",lifespan=lifespan)
SYMBOL=re.compile(r"^[A-Z0-9&._-]{1,30}$")
def symbol_ok(s):
    s=s.strip().upper()
    if not SYMBOL.fullmatch(s): raise HTTPException(400,"Invalid NSE/BSE symbol")
    return s
async def call(tool,args):
    try: return await mcp.call(tool,args)
    except Exception as e: raise HTTPException(502,f"Screener MCP error: {e}") from e
@app.get("/api/health")
async def health(): return {"status":"ok","service":"NiftyLens AI","provider":"community Screener MCP"}
@app.get("/api/mcp/status")
async def status(): return await mcp.status()
@app.get("/api/stocks/{ticker}")
async def stock(ticker:str):
    s=symbol_ok(ticker)
    a,b=await asyncio.gather(call("get_fundamentals",{"symbol":s}),call("get_ratios",{"symbol":s}))
    return {"symbol":s,"fundamentals":a,"ratios":b}
@app.get("/api/stocks/{ticker}/financials")
async def financials(ticker:str): return await call("get_financials",{"symbol":symbol_ok(ticker)})
@app.get("/api/stocks/{ticker}/peers")
async def peers(ticker:str): return await call("get_peers",{"symbol":symbol_ok(ticker)})
@app.get("/api/stocks/{ticker}/quarters")
async def quarters(ticker:str): return await call("get_quarterly_results",{"symbol":symbol_ok(ticker)})
@app.get("/api/stocks/{ticker}/chart")
async def chart(ticker:str,metric:str="Price",days:int=365):
    if not re.fullmatch(r"[A-Za-z0-9 _-]{1,60}",metric) or not 1<=days<=3650: raise HTTPException(400,"Invalid chart parameters")
    return await call("get_chart",{"symbol":symbol_ok(ticker),"metric":metric,"days":days})
class Screen(BaseModel):
    query:str=Field(min_length=3,max_length=500); limit:int=Field(default=25,ge=1,le=100); sort:str|None=None; order:str=Field(default="desc",pattern="^(asc|desc)$")
@app.post("/api/screen")
async def screen(body:Screen):
    if re.search(r"\\bOR\\b|[()]",body.query,re.I): raise HTTPException(400,"Anonymous screening supports AND clauses only; remove OR and parentheses.")
    args={"query":body.query,"limit":body.limit,"order":body.order}
    if body.sort: args["sort"]=body.sort
    return await call("screen_stocks",args)
@app.post("/api/research/{ticker}")
async def research(ticker:str):
    key=os.getenv("GEMINI_API_KEY","").strip()
    if not key: raise HTTPException(503,"AI summaries disabled: configure GEMINI_API_KEY on the server.")
    data=await stock(ticker)
    try:
        import google.generativeai as genai
        genai.configure(api_key=key); model=genai.GenerativeModel(os.getenv("GEMINI_MODEL","gemini-2.0-flash"))
        prompt="Summarize strengths, risks, missing information and due-diligence questions from these company fundamentals. Educational research only; no buy/sell recommendation or price target.\n"+str(data)
        result=await asyncio.to_thread(model.generate_content,prompt)
        return {"symbol":data["symbol"],"summary":result.text}
    except Exception as e: raise HTTPException(502,f"Gemini request failed: {e}") from e
app.mount("/assets",StaticFiles(directory="frontend"),name="assets")
@app.get("/")
async def home(): return FileResponse("frontend/index.html")
