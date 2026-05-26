from typing import Optional
from src.agents.base_agent import BaseAgent
from src.core.llm_interface import LLMInterface
from src.rag.retriever import RAGRetriever


class FinanceQAAgent(BaseAgent):
    """Agent for finance question answering with retrieval-augmented generation.

    FinanceQAAgent uses a retriever to fetch related financial knowledge and
    constructs a prompt for the underlying LLM. The agent supports optional
    conversation history and appends source citations when available.
    """

    def __init__(self, llm: LLMInterface, retriever: RAGRetriever, system_prompt: str):
        """Initialize the finance QA agent.

        Args:
            llm: The LLM interface used to generate responses.
            retriever: The RAG retriever used to fetch context and sources.
            system_prompt: The system prompt guiding the LLM behavior.
        """
        super().__init__(llm, system_prompt, "Finance Q&A")
        self.retriever = retriever

    def process(self, query: str, context: dict, trace_metadata: Optional[dict] = None) -> str:
        """Process a finance query and return an answer.

        The method retrieves relevant context, constructs a prompt, and uses the
        LLM to generate a response. If conversation history exists, it is included
        in the request. Retrieved sources are appended to the final answer.

        Args:
            query: The user question to answer.
            context: The conversational context, including optional history.
            trace_metadata: Optional metadata for tracing the request.

        Returns:
            A generated answer string with optional source citations.
        """
        rag_context, sources = self.retriever.retrieve_with_sources(query, k=3)

        prompt = query
        if rag_context:
            prompt = f"Based on the following financial knowledge:\n\n{rag_context}\n\nAnswer this question: {query}"

        # Support both `messages` (langchain style) and `history` (tests/legacy callers)
        messages = context.get("messages") or context.get("history") or []
        if messages:
            from langchain_core.messages import HumanMessage
            response = self.llm.generate_with_history(
                messages + [HumanMessage(content=prompt)],
                self.system_prompt,
                trace_metadata=trace_metadata,
            )
        else:
            response = self.llm.generate(prompt, self.system_prompt, trace_metadata=trace_metadata)

        if sources:
            response += f"\n\n*Sources: {', '.join(sources)}*"

        return response
