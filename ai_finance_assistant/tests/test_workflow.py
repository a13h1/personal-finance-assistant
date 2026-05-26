from src.workflow.router import create_workflow
from langchain_core.messages import HumanMessage


def test_create_workflow_routing_and_synthesis():
    # Create simple mock agents that return a predictable response
    class MockAgent:
        def __init__(self, name):
            self.name = name

        def process(self, query, context, trace_metadata=None):
            return f"response-{self.name}"

    agent_names = ["finance_qa", "portfolio", "market", "goal_planning", "news", "tax"]
    agents = {name: MockAgent(name) for name in agent_names}

    compiled = create_workflow(agents)

    # Provide a tax-related human message so the router selects the `tax` agent
    state = {
        "messages": [HumanMessage(content="How does capital gains tax work?")],
        "session_id": "s-test",
        "profile": {},
        "portfolio": None,
    }

    out = compiled.invoke(state)

    # Ensure intents include 'tax' and that the final synthesized message contains the tax agent response
    assert "intents" in out and "tax" in out["intents"]
    msgs = out.get("messages", [])
    # messages are langchain message objects; check their `.content` where available
    contents = [getattr(m, "content", m) for m in msgs]
    assert any("response-tax" in str(c) for c in contents)
