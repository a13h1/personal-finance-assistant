from typing import TypedDict, Literal, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END


class AgentState(TypedDict):
    query: str
    intent: str
    response: str
    history: List[Dict]
    portfolio: Optional[Dict]
    profile: Dict
    error: Optional[str]


def classify_intent(state: AgentState) -> AgentState:
    query = state["query"].lower()

    # Simple keyword-based routing
    if any(w in query for w in ["tax", "capital gains", "ira", "roth", "401k", "deduction", "write off"]):
        intent = "tax"
    elif any(w in query for w in ["portfolio", "holding", "stock i own", "my investment", "analyze my", "diversif"]):
        intent = "portfolio"
    elif any(w in query for w in ["price", "market", "trading", "quote", "stock price", "how is", "perform"]):
        if any(w in query for w in ["news", "headline", "announced", "report"]):
            intent = "news"
        else:
            intent = "market"
    elif any(w in query for w in ["news", "headline", "announced", "report", "earnings", "merger"]):
        intent = "news"
    elif any(w in query for w in ["goal", "retire", "save for", "plan", "how much do i need", "afford", "financial plan"]):
        intent = "goal_planning"
    else:
        intent = "finance_qa"

    return {**state, "intent": intent}


def route_by_intent(state: AgentState) -> Literal["finance_qa", "portfolio", "market", "goal_planning", "news", "tax"]:
    return state["intent"]


def create_workflow(agents: Dict) -> Any:
    workflow = StateGraph(AgentState)

    workflow.add_node("classify", classify_intent)

    def make_agent_node(agent_name: str):
        def agent_node(state: AgentState) -> AgentState:
            agent = agents[agent_name]
            context = {
                "history": state.get("history", []),
                "portfolio": state.get("portfolio"),
                "profile": state.get("profile", {}),
            }
            try:
                response = agent.process(state["query"], context)
            except Exception as e:
                response = f"I encountered an error processing your request. Please try again. (Error: {str(e)[:100]})"
            return {**state, "response": response}
        return agent_node

    for agent_name in ["finance_qa", "portfolio", "market", "goal_planning", "news", "tax"]:
        workflow.add_node(agent_name, make_agent_node(agent_name))

    workflow.set_entry_point("classify")
    workflow.add_conditional_edges("classify", route_by_intent, {
        "finance_qa": "finance_qa",
        "portfolio": "portfolio",
        "market": "market",
        "goal_planning": "goal_planning",
        "news": "news",
        "tax": "tax",
    })

    for agent_name in ["finance_qa", "portfolio", "market", "goal_planning", "news", "tax"]:
        workflow.add_edge(agent_name, END)

    return workflow.compile()
