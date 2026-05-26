from abc import ABC, abstractmethod
from typing import Optional
from src.core.llm_interface import LLMInterface
from src.utils.error_handler import with_fallback


class BaseAgent(ABC):
    def __init__(self, llm: LLMInterface, system_prompt: str, name: str):
        self.llm = llm
        self.system_prompt = system_prompt
        self.name = name

    @abstractmethod
    def process(self, query: str, context: dict, trace_metadata: Optional[dict] = None) -> str:
        pass

    def _build_prompt(self, query: str, additional_context: str = "") -> str:
        if additional_context:
            return f"{additional_context}\n\nUser Question: {query}"
        return query
