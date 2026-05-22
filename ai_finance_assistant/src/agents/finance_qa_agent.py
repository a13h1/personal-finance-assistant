from src.agents.base_agent import BaseAgent
from src.core.llm_interface import LLMInterface
from src.rag.retriever import RAGRetriever


class FinanceQAAgent(BaseAgent):
    def __init__(self, llm: LLMInterface, retriever: RAGRetriever, system_prompt: str):
        super().__init__(llm, system_prompt, "Finance Q&A")
        self.retriever = retriever

    def process(self, query: str, context: dict) -> str:
        rag_context, sources = self.retriever.retrieve_with_sources(query, k=3)

        prompt = query
        if rag_context:
            prompt = f"Based on the following financial knowledge:\n\n{rag_context}\n\nAnswer this question: {query}"

        history = context.get("history", [])
        if history:
            response = self.llm.generate_with_history(
                history + [{"role": "user", "content": prompt}],
                self.system_prompt
            )
        else:
            response = self.llm.generate(prompt, self.system_prompt)

        if sources:
            response += f"\n\n*Sources: {', '.join(sources)}*"

        return response
