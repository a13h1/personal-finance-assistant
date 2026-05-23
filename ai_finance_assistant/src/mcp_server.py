import os
import uuid
import logging
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.workflow.orchestrator import FinanceOrchestrator

logger = logging.getLogger(__name__)
app = FastAPI(
    title="AI Finance Assistant MCP Server",
    description="Expose finance agent tools over HTTP for Claude Desktop integration.",
    version="0.1.0",
)


def get_orchestrator() -> FinanceOrchestrator:
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    return FinanceOrchestrator(config_path=config_path)

orchestrator = get_orchestrator()


class MCPRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    response: str
    agent: str
    status: str = "ok"
    error: Optional[str] = None
    session_id: Optional[str] = None


def _resolve_session_id(request: MCPRequest) -> str:
    if request.session_id:
        return request.session_id
    if request.user_id:
        return request.user_id
    return str(uuid.uuid4())


def _invoke_agent(agent_name: str, request: MCPRequest) -> MCPResponse:
    if not request.query:
        raise HTTPException(status_code=422, detail="query is required")

    session_id = _resolve_session_id(request)
    orchestrator.session_manager.get_or_create_session(session_id, user_id=request.user_id)
    profile = orchestrator.session_manager.get_profile(session_id, user_id=request.user_id)
    portfolio = orchestrator.session_manager.get_portfolio(session_id, user_id=request.user_id)
    history = orchestrator.session_manager.get_history(session_id, last_n=10)

    context = {
        "history": history,
        "portfolio": portfolio,
        "profile": {
            "risk_tolerance": profile.risk_tolerance,
            "investment_horizon": profile.investment_horizon,
            "experience_level": profile.experience_level,
        },
    }

    agent = orchestrator.agents.get(agent_name)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_name}")

    try:
        response = agent.process(request.query, context)
    except Exception as exc:
        logger.exception("MCP agent execution failed")
        raise HTTPException(status_code=500, detail=str(exc))

    orchestrator.session_manager.add_message(session_id, "user", request.query, agent=agent_name, user_id=request.user_id)
    orchestrator.session_manager.add_message(session_id, "assistant", response, agent=agent_name, user_id=request.user_id)

    return MCPResponse(response=response, agent=agent_name, status="ok", session_id=session_id)


@app.get("/mcp/tools")
def list_tools() -> Dict[str, Any]:
    return {
        "tools": [
            {"name": "finance_qa", "description": "General financial education and Q&A."},
            {"name": "portfolio", "description": "Portfolio analysis and recommendations."},
            {"name": "market", "description": "Market data and stock price inquiries."},
            {"name": "goal_planning", "description": "Financial goal setting and planning."},
            {"name": "news", "description": "Financial news summarization."},
            {"name": "tax", "description": "Tax education and high-level guidance."},
        ]
    }


@app.post("/mcp/finance_qa", response_model=MCPResponse)
def ask_finance_qa(request: MCPRequest) -> MCPResponse:
    return _invoke_agent("finance_qa", request)


@app.post("/mcp/portfolio", response_model=MCPResponse)
def ask_portfolio(request: MCPRequest) -> MCPResponse:
    return _invoke_agent("portfolio", request)


@app.post("/mcp/market", response_model=MCPResponse)
def ask_market(request: MCPRequest) -> MCPResponse:
    return _invoke_agent("market", request)


@app.post("/mcp/goal_planning", response_model=MCPResponse)
def ask_goal_planning(request: MCPRequest) -> MCPResponse:
    return _invoke_agent("goal_planning", request)


@app.post("/mcp/news", response_model=MCPResponse)
def ask_news(request: MCPRequest) -> MCPResponse:
    return _invoke_agent("news", request)


@app.post("/mcp/tax", response_model=MCPResponse)
def ask_tax(request: MCPRequest) -> MCPResponse:
    return _invoke_agent("tax", request)
