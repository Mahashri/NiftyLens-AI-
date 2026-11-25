"""LangGraph-based, optional Gemini research workflow."""
import os
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class ResearchState(TypedDict, total=False):
    symbol: str
    company_data: dict
    draft: str
    result: str

def build_research_graph():
    def draft_research(state: ResearchState):
        import google.generativeai as genai
        key=os.getenv("GEMINI_API_KEY","").strip()
        if not key: raise RuntimeError("GEMINI_API_KEY is not configured")
        genai.configure(api_key=key)
        model=genai.GenerativeModel(os.getenv("GEMINI_MODEL","gemini-2.0-flash"))
        prompt=(
            "You are an equity research assistant. Review the supplied company fundamentals. "
            "Write a balanced educational research note with: business/fundamental highlights, "
            "valuation observations, financial-quality questions, key risks, missing data and "
            "next due-diligence steps. Do not provide buy/sell instructions, price targets, "
            "or guaranteed returns. Distinguish source facts from interpretation.\n\n"
            + str(state.get("company_data", {}))
        )
        response=model.generate_content(prompt)
        return {"draft": response.text or "The model returned an empty response."}
    def safety_review(state: ResearchState):
        draft=state.get("draft","")
        return {"result": draft + "\n\n---\nEducational research only. Not investment advice. Verify current filings, valuation and market data independently."}
    graph=StateGraph(ResearchState)
    graph.add_node("draft_research",draft_research)
    graph.add_node("safety_review",safety_review)
    graph.add_edge(START,"draft_research")
    graph.add_edge("draft_research","safety_review")
    graph.add_edge("safety_review",END)
    return graph.compile()

async def run_research(symbol: str, company_data: dict):
    import asyncio
    graph=build_research_graph()
    state=await asyncio.to_thread(graph.invoke,{"symbol":symbol,"company_data":company_data})
    return state.get("result","No research summary produced.")
