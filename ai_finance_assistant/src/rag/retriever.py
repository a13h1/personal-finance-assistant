from src.rag.vector_store import FinancialVectorStore
from typing import List, Optional
import os


class RAGRetriever:
    def __init__(self, vector_store: FinancialVectorStore):
        self.vector_store = vector_store

    def retrieve(self, query: str, k: int = 3) -> str:
        docs = self.vector_store.search(query, k=k)
        if not docs:
            return ""

        context_parts = []
        for doc in docs:
            source = doc.metadata.get("source", "Financial Knowledge Base")
            context_parts.append(f"**{source}**:\n{doc.page_content}")

        return "\n\n---\n\n".join(context_parts)

    def retrieve_with_sources(self, query: str, k: int = 3) -> tuple:
        docs = self.vector_store.search(query, k=k)
        if not docs:
            return "", []

        context_parts = []
        sources = []
        for doc in docs:
            source = doc.metadata.get("source", "Financial Knowledge Base")
            context_parts.append(f"**{source}**:\n{doc.page_content}")
            if source not in sources:
                sources.append(source)

        return "\n\n---\n\n".join(context_parts), sources
