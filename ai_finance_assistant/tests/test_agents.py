import pytest
from unittest.mock import MagicMock, patch
from src.agents.finance_qa_agent import FinanceQAAgent
from src.agents.market_agent import MarketAgent
from src.workflow.router import classify_intent, AgentState
from langchain_core.messages import HumanMessage


def make_state(query: str) -> AgentState:
    return {
        "query": query,
        "intent": "",
        "response": "",
        "history": [],
        "portfolio": None,
        "profile": {},
        "error": None,
    }


class TestIntentClassification:
    def test_tax_intent(self):
        state = classify_intent(make_state("How does capital gains tax work?"))
        assert state["intent"] == "tax"

    def test_portfolio_intent(self):
        state = classify_intent(make_state("Can you analyze my portfolio?"))
        assert state["intent"] == "portfolio"

    def test_market_intent(self):
        state = classify_intent(make_state("What is the current price of AAPL?"))
        assert state["intent"] == "market"

    def test_news_intent(self):
        state = classify_intent(make_state("What are the latest earnings reports?"))
        assert state["intent"] == "news"

    def test_goal_intent(self):
        state = classify_intent(make_state("How much do I need to save for retirement?"))
        assert state["intent"] == "goal_planning"

    def test_default_finance_qa(self):
        state = classify_intent(make_state("What is an ETF?"))
        assert state["intent"] == "finance_qa"

    def test_ira_tax_intent(self):
        state = classify_intent(make_state("What is a Roth IRA?"))
        assert state["intent"] == "tax"

    def test_diversify_portfolio_intent(self):
        state = classify_intent(make_state("How should I diversify my holdings?"))
        assert state["intent"] == "portfolio"

    def test_news_merger_intent(self):
        state = classify_intent(make_state("Did Tesla announce any merger recently?"))
        assert state["intent"] == "news"

    def test_goal_afford_intent(self):
        state = classify_intent(make_state("Can I afford to retire at 60?"))
        assert state["intent"] == "goal_planning"


class TestMarketAgent:
    def test_extract_symbols(self):
        mock_llm = MagicMock()
        mock_market = MagicMock()
        agent = MarketAgent(mock_llm, mock_market, "system prompt")
        symbols = agent._extract_symbols("What about AAPL and MSFT today?")
        assert "AAPL" in symbols
        assert "MSFT" in symbols

    def test_extract_symbols_empty(self):
        mock_llm = MagicMock()
        mock_market = MagicMock()
        agent = MarketAgent(mock_llm, mock_market, "system prompt")
        symbols = agent._extract_symbols("how are markets doing today")
        assert symbols == []

    def test_process_calls_llm(self):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Market analysis response"
        mock_market = MagicMock()
        mock_market.get_market_indices.return_value = {}
        mock_market.get_quote.return_value = None
        agent = MarketAgent(mock_llm, mock_market, "system prompt")
        result = agent.process("How is the market doing?", {})
        assert result == "Market analysis response"
        mock_llm.generate.assert_called_once()


class TestFinanceQAAgent:
    def test_process_with_rag_context(self):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Answer about investing"
        mock_retriever = MagicMock()
        mock_retriever.retrieve_with_sources.return_value = ("Some financial context", ["Investing Basics"])
        agent = FinanceQAAgent(mock_llm, mock_retriever, "system prompt")
        result = agent.process("What is investing?", {})
        assert "Investing Basics" in result
        mock_retriever.retrieve_with_sources.assert_called_once_with("What is investing?", k=3)

    def test_process_no_rag_context(self):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Generic finance answer"
        mock_retriever = MagicMock()
        mock_retriever.retrieve_with_sources.return_value = ("", [])
        agent = FinanceQAAgent(mock_llm, mock_retriever, "system prompt")
        result = agent.process("Explain bonds", {})
        assert result == "Generic finance answer"
        # When no rag context and no history, generate should be called with just the query
        mock_llm.generate.assert_called_once()

    def test_process_with_history(self):
        mock_llm = MagicMock()
        mock_llm.generate_with_history.return_value = "Contextual answer"
        mock_retriever = MagicMock()
        mock_retriever.retrieve_with_sources.return_value = ("", [])
        agent = FinanceQAAgent(mock_llm, mock_retriever, "system prompt")
        history = [{"role": "user", "content": "What is a stock?"}, {"role": "assistant", "content": "A stock is..."}]
        result = agent.process("What about bonds?", {"history": history})
        mock_llm.generate_with_history.assert_called_once()


def test_classify_intent_with_messages():
    from src.workflow.router import classify_intent
    state = {
        "messages": [HumanMessage(content="How does capital gains tax work?")],
    }
    out = classify_intent(state)
    assert "intents" in out
    assert "tax" in out["intents"]


def test_financeqa_agent_with_messages_calls_generate_with_history():
    mock_llm = MagicMock()
    mock_llm.generate_with_history.return_value = "Contextual answer"
    mock_retriever = MagicMock()
    mock_retriever.retrieve_with_sources.return_value = ("", [])
    agent = FinanceQAAgent(mock_llm, mock_retriever, "system prompt")
    from langchain_core.messages import HumanMessage
    messages = [HumanMessage(content="What is a stock?")]
    result = agent.process("What about bonds?", {"messages": messages})
    mock_llm.generate_with_history.assert_called_once()


def test_financeqa_agent_with_history_calls_generate_with_history():
    mock_llm = MagicMock()
    mock_llm.generate_with_history.return_value = "Contextual answer"
    mock_retriever = MagicMock()
    mock_retriever.retrieve_with_sources.return_value = ("", [])
    agent = FinanceQAAgent(mock_llm, mock_retriever, "system prompt")
    history = [{"role": "user", "content": "What is a stock?"}]
    result = agent.process("What about bonds?", {"history": history})
    mock_llm.generate_with_history.assert_called_once()

# --- Goal Planning Agent Tests ---
def test_goal_planning_agent_process():
    from src.agents.goal_planning_agent import GoalPlanningAgent
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "Goal plan"
    agent = GoalPlanningAgent(mock_llm, "system prompt")
    result = agent.process("I want to retire at 50", {})
    assert result == "Goal plan"
    mock_llm.generate.assert_called_once()

def test_goal_planning_agent_process_with_messages():
    from src.agents.goal_planning_agent import GoalPlanningAgent
    mock_llm = MagicMock()
    mock_llm.generate_with_history.return_value = "Contextual goal plan"
    agent = GoalPlanningAgent(mock_llm, "system prompt")
    messages = [HumanMessage(content="Hello")]
    result = agent.process("I want to retire at 50", {"messages": messages})
    assert result == "Contextual goal plan"
    mock_llm.generate_with_history.assert_called_once()

# --- News Agent Tests ---
def test_news_agent_process():
    from src.agents.news_agent import NewsAgent
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "News summary"
    mock_market = MagicMock()
    mock_market.get_news.return_value = [{"title": "Market up", "publisher": "Reuters"}]
    agent = NewsAgent(mock_llm, mock_market, "system prompt")
    result = agent.process("Any news on AAPL?", {})
    assert result == "News summary"
    mock_llm.generate.assert_called_once()
    mock_market.get_news.assert_called_once_with("AAPL")

def test_news_agent_process_with_messages():
    from src.agents.news_agent import NewsAgent
    mock_llm = MagicMock()
    mock_llm.generate_with_history.return_value = "Contextual news summary"
    mock_market = MagicMock()
    mock_market.get_news.return_value = []
    agent = NewsAgent(mock_llm, mock_market, "system prompt")
    messages = [HumanMessage(content="Hello")]
    result = agent.process("Market news?", {"messages": messages})
    assert result == "Contextual news summary"
    mock_llm.generate_with_history.assert_called_once()

# --- Portfolio Agent Tests ---
def test_portfolio_agent_process():
    from src.agents.portfolio_agent import PortfolioAgent
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "Portfolio analysis"
    mock_market = MagicMock()
    mock_market.analyze_portfolio.return_value = {"total_value": 1000}
    agent = PortfolioAgent(mock_llm, mock_market, "system prompt")
    context = {"portfolio": {"holdings": [{"symbol": "AAPL", "shares": 10}]}}
    result = agent.process("How is my portfolio?", context)
    assert result == "Portfolio analysis"
    mock_llm.generate.assert_called_once()

def test_portfolio_agent_process_with_messages():
    from src.agents.portfolio_agent import PortfolioAgent
    mock_llm = MagicMock()
    mock_llm.generate_with_history.return_value = "Contextual portfolio analysis"
    mock_market = MagicMock()
    mock_market.analyze_portfolio.return_value = {"total_value": 1000}
    agent = PortfolioAgent(mock_llm, mock_market, "system prompt")
    context = {
        "portfolio": {"holdings": [{"symbol": "AAPL", "shares": 10}]},
        "messages": [HumanMessage(content="Hello")]
    }
    result = agent.process("How is my portfolio?", context)
    assert result == "Contextual portfolio analysis"
    mock_llm.generate_with_history.assert_called_once()

# --- Tax Agent Tests ---
def test_tax_agent_process():
    from src.agents.tax_agent import TaxAgent
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "Tax advice"
    mock_retriever = MagicMock()
    mock_retriever.retrieve_with_sources.return_value = ("Tax context", ["Tax Code"])
    agent = TaxAgent(mock_llm, mock_retriever, "system prompt")
    result = agent.process("How do capital gains work?", {})
    assert "Tax Code" in result
    mock_llm.generate.assert_called_once()

def test_tax_agent_process_with_messages():
    from src.agents.tax_agent import TaxAgent
    mock_llm = MagicMock()
    mock_llm.generate_with_history.return_value = "Contextual tax advice"
    mock_retriever = MagicMock()
    mock_retriever.retrieve_with_sources.return_value = ("", [])
    agent = TaxAgent(mock_llm, mock_retriever, "system prompt")
    messages = [HumanMessage(content="Hello")]
    result = agent.process("What about Roth IRA?", {"messages": messages})
    assert result == "Contextual tax advice"
    mock_llm.generate_with_history.assert_called_once()

