import pytest
from unittest.mock import MagicMock, patch
from src.workflow.orchestrator import FinanceOrchestrator
from langchain_core.messages import AIMessage

@patch("src.workflow.orchestrator.create_workflow")
@patch("src.workflow.orchestrator.LLMInterface")
@patch("src.workflow.orchestrator.SessionManager")
@patch("src.workflow.orchestrator.MarketDataService")
@patch("src.workflow.orchestrator.FinancialVectorStore")
@patch("src.workflow.orchestrator.RAGRetriever")
def test_process_query(
    mock_retriever,
    mock_vector_store,
    mock_market_data,
    mock_session_manager,
    mock_llm,
    mock_create_workflow
):
    # Setup mock returns
    mock_session_instance = MagicMock()
    mock_session_instance.get_history.return_value = [{"role": "user", "content": "Hello"}]
    mock_profile = MagicMock()
    mock_profile.risk_tolerance = "moderate"
    mock_profile.investment_horizon = "long"
    mock_profile.experience_level = "beginner"
    mock_session_instance.get_profile.return_value = mock_profile
    mock_session_instance.get_portfolio.return_value = None
    mock_session_manager.return_value = mock_session_instance

    mock_workflow_instance = MagicMock()
    # Workflow invoke returns the state dict, we mock a synthesized response
    mock_workflow_instance.invoke.return_value = {
        "messages": [AIMessage(content="Final synthesized response")],
        "intents": ["tax", "portfolio"]
    }
    mock_create_workflow.return_value = mock_workflow_instance

    # Initialize orchestrator
    orchestrator = FinanceOrchestrator()
    
    # Process query
    result = orchestrator.process_query("What about taxes on my portfolio?", "session-123")
    
    # Assertions
    assert result["response"] == "Final synthesized response"
    assert result["agent"] == "tax,portfolio"
    
    # Verify session manager was updated correctly
    mock_session_instance.add_message.assert_any_call("session-123", "user", "What about taxes on my portfolio?")
    mock_session_instance.add_message.assert_any_call("session-123", "assistant", "Final synthesized response", agent="tax,portfolio")
    
    # Verify workflow was invoked with expected state shape (including mapped messages)
    mock_workflow_instance.invoke.assert_called_once()
    invoke_args = mock_workflow_instance.invoke.call_args[0][0]
    assert "messages" in invoke_args
    assert len(invoke_args["messages"]) == 1
    assert invoke_args["messages"][0].content == "Hello"
    assert invoke_args["intents"] == []
    assert invoke_args["session_id"] == "session-123"
