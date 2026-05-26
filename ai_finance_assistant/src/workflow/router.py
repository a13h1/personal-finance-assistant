from typing import TypedDict, Literal, List, Dict, Any, Optional, Annotated
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage, HumanMessage


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    intents: List[str]
    portfolio: Optional[Dict]
    profile: Dict
    error: Optional[str]
    session_id: str


def classify_intent(state: AgentState, classifier_llm: Any = None) -> AgentState:
    # Support two input shapes:
    # - tests and simple callers: state contains a `query` string and expects a single `intent` value
    # - langgraph-style callers: state contains `messages` and we return an `intents` list

    # If a simple `query` string is provided (used by unit tests), classify and
    # return a single `intent` string in the result to keep the API simple.
    if "query" in state:
        query = str(state.get("query", "")).lower()
    else:
        # Get the latest user query from messages (langgraph integration)
        query = ""
        for m in reversed(state.get("messages", [])):
            if isinstance(m, HumanMessage):
                query = str(m.content)
                break
        query = query.lower()

    intents: list[str] = []

    # Simple keyword-based multi-routing
    if any(w in query for w in ["tax", "capital gains", "ira", "roth", "401k", "deduction", "write off"]):
        intents.append("tax")
    if any(w in query for w in ["portfolio", "holding", "stock i own", "my investment", "analyze my", "diversif"]):
        intents.append("portfolio")
    if any(w in query for w in ["price", "market", "trading", "quote", "stock price", "how is", "perform"]):
        intents.append("market")
    if any(w in query for w in ["news", "headline", "announced", "report", "earnings", "merger"]):
        intents.append("news")
    if any(w in query for w in ["goal", "retire", "save for", "plan", "how much do i need", "afford", "financial plan"]):
        intents.append("goal_planning")

    if not intents:
        if classifier_llm:
            prompt = f"Given the user query: '{query}', classify it into one or more of these categories: tax, portfolio, market, news, goal_planning, finance_qa. Return only a comma-separated list of categories."
            try:
                llm_response = classifier_llm.generate(prompt)
                predicted = [p.strip().lower() for p in llm_response.split(',')]
                valid_intents = {"tax", "portfolio", "market", "news", "goal_planning", "finance_qa"}
                intents = [p for p in predicted if p in valid_intents]
            except Exception:
                pass

        if not intents:
            intents.append("finance_qa")

    # If caller provided a `query` string, tests expect a single `intent` value
    if "query" in state:
        return {"intent": intents[0]}  # type: ignore

    # Otherwise return the langgraph-compatible list of intents
    return {"intents": intents}  # type: ignore


def route_by_intent(state: AgentState) -> List[str]:
    return state["intents"]


def create_workflow(agents: Dict, synthesis_llm: Any = None, classifier_llm: Any = None) -> Any:
    workflow = StateGraph(AgentState)

    def classify_node(state: AgentState) -> AgentState:
        return classify_intent(state, classifier_llm)

    workflow.add_node("classify", classify_node)

    agent_names = ["finance_qa", "portfolio", "market", "goal_planning", "news", "tax"]

    def make_agent_node(agent_name: str):
        def agent_node(state: AgentState) -> AgentState:
            agent = agents[agent_name]

            # Find the query
            query = ""
            for m in reversed(state["messages"]):
                if isinstance(m, HumanMessage):
                    query = str(m.content)
                    break

            context = {
                "messages": state.get("messages", []),
                "portfolio": state.get("portfolio"),
                "profile": state.get("profile", {}),
            }
            trace_metadata = {
                "session_id": state.get("session_id"),
                "agent_name": agent_name,
                "intents": state.get("intents"),
            }
            try:
                response_content = agent.process(query, context, trace_metadata=trace_metadata)
            except Exception as e:
                response_content = f"I encountered an error processing your request in {agent_name}. Please try again. (Error: {str(e)[:100]})"

            # Return an AIMessage specifically identifying the agent
            return {"messages": [AIMessage(content=response_content, name=agent_name)]} # type: ignore
        return agent_node

    for agent_name in agent_names:
        workflow.add_node(agent_name, make_agent_node(agent_name))

    def synthesize_responses(state: AgentState) -> AgentState:
        # Get the latest messages added by agents (they will be at the end, added after the last human message)
        agent_messages = []
        for m in reversed(state["messages"]):
            if isinstance(m, HumanMessage):
                break
            if isinstance(m, AIMessage) and m.name in agent_names:
                agent_messages.append(m)

        agent_messages.reverse()

        if not agent_messages:
            return {"messages": [AIMessage(content="I'm sorry, I couldn't process your request.", name="synthesizer")]} # type: ignore

        if len(agent_messages) == 1:
            # Only one agent responded, we can just use its response as the final one
            final_content = agent_messages[0].content
        else:
            # Combine them
            if synthesis_llm:
                prompt = "You are a financial assistant. Combine the following insights into a cohesive response for the user.\n\n"
                for msg in agent_messages:
                    prompt += f"--- Insight from {msg.name} expert ---\n{msg.content}\n\n"
                prompt += "Provide a single, well-structured, and helpful response."
                
                try:
                    final_content = synthesis_llm.generate(prompt)
                except Exception as e:
                    # Fallback
                    final_content = "Here are the insights I gathered:\n\n" + "\n\n".join([f"**From {m.name} expert:**\n{m.content}" for m in agent_messages])
            else:
                final_content = "Here are the insights I gathered:\n\n" + "\n\n".join([f"**From {m.name} expert:**\n{m.content}" for m in agent_messages])

        return {"messages": [AIMessage(content=final_content, name="synthesizer")]} # type: ignore

    workflow.add_node("synthesize", synthesize_responses)

    workflow.add_edge(START, "classify")
    workflow.add_conditional_edges("classify", route_by_intent, agent_names)

    for agent_name in agent_names:
        workflow.add_edge(agent_name, "synthesize")

    workflow.add_edge("synthesize", END)

    return workflow.compile()
