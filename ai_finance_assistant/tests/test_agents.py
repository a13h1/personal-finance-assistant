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
