import os
import pytest
from unittest.mock import MagicMock, patch
from src.core.llm_interface import LangfuseAdapter, LLMInterface
from langchain_core.messages import HumanMessage, AIMessage

def test_langfuse_adapter_legacy_keys():
    # Test mapping legacy LANGFUSE_API_KEY to public/secret keys
    adapter = LangfuseAdapter(api_key="legacy-key")
    assert adapter.api_key == "legacy-key"
    assert adapter.public_key == "legacy-key"
    assert adapter.secret_key == "legacy-key"

@patch("src.core.llm_interface.ChatOpenAI")
def test_llm_interface_generate(mock_chat_openai):
    # Setup mock LLM response
    mock_llm_instance = MagicMock()
    mock_result = MagicMock()
    mock_result.generations = [[MagicMock(message=MagicMock(content="Mock response"))]]
    mock_llm_instance.generate.return_value = mock_result
    mock_chat_openai.return_value = mock_llm_instance
    
    with patch("src.core.llm_interface.LangfuseAdapter") as mock_langfuse_adapter:
        # Simulate Langfuse being enabled
        mock_adapter_instance = MagicMock()
        mock_adapter_instance.start_generation.return_value = MagicMock()
        mock_langfuse_adapter.return_value = mock_adapter_instance
        
        # We need to temporarily set an env var so LLMInterface initializes LangfuseAdapter
        with patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "test"}):
            llm = LLMInterface(model="test-model", temperature=0.0, max_tokens=100)
            
            result = llm.generate("Test query", system_prompt="System rules", trace_metadata={"session_id": "123"})
            
            assert result == "Mock response"
            mock_llm_instance.generate.assert_called_once()
            
            # Assert Langfuse start_generation was called
            mock_adapter_instance.start_generation.assert_called_once()
            call_kwargs = mock_adapter_instance.start_generation.call_args.kwargs
            assert call_kwargs["name"] == "llm.generate"
            assert call_kwargs["prompt"] == "Test query"
            assert call_kwargs["metadata"]["session_id"] == "123"
            
            # Assert Langfuse update_generation was called
            mock_adapter_instance.update_generation.assert_called_once()
            update_kwargs = mock_adapter_instance.update_generation.call_args.kwargs
            assert update_kwargs["output"] == "Mock response"


@patch("src.core.llm_interface.ChatOpenAI")
def test_llm_interface_generate_with_history(mock_chat_openai):
    # Setup mock LLM response
    mock_llm_instance = MagicMock()
    mock_result = MagicMock()
    mock_result.generations = [[MagicMock(message=MagicMock(content="History response"))]]
    mock_llm_instance.generate.return_value = mock_result
    mock_chat_openai.return_value = mock_llm_instance
    
    with patch("src.core.llm_interface.LangfuseAdapter") as mock_langfuse_adapter:
        mock_adapter_instance = MagicMock()
        mock_adapter_instance.start_generation.return_value = MagicMock()
        mock_langfuse_adapter.return_value = mock_adapter_instance
        
        with patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "test"}):
            llm = LLMInterface(model="test-model", temperature=0.0, max_tokens=100)
            
            messages = [HumanMessage(content="Hello")]
            result = llm.generate_with_history(messages, system_prompt="System rules", trace_metadata={"session_id": "456"})
            
            assert result == "History response"
            mock_llm_instance.generate.assert_called_once()
            
            # Assert Langfuse start_generation was called
            mock_adapter_instance.start_generation.assert_called_once()
            call_kwargs = mock_adapter_instance.start_generation.call_args.kwargs
            assert call_kwargs["name"] == "llm.generate_with_history"
            assert "Hello" in call_kwargs["prompt"]
            assert call_kwargs["metadata"]["session_id"] == "456"
            assert call_kwargs["metadata"]["history_len"] == 1
