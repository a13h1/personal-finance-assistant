from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import os
import glob
from typing import List


class FinancialVectorStore:
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2",
                 chunk_size: int = 500, chunk_overlap: int = 50):
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        self.vectorstore = None

    def build_from_directory(self, docs_dir: str) -> None:
        documents = []
        for filepath in glob.glob(os.path.join(docs_dir, "*.md")):
            with open(filepath, "r") as f:
                content = f.read()
            filename = os.path.basename(filepath).replace(".md", "").replace("_", " ").title()
            doc = Document(page_content=content, metadata={"source": filename, "file": filepath})
            documents.append(doc)

        if not documents:
            raise ValueError(f"No documents found in {docs_dir}")

        chunks = self.text_splitter.split_documents(documents)
        self.vectorstore = FAISS.from_documents(chunks, self.embeddings)

    def save(self, path: str) -> None:
        if self.vectorstore:
            os.makedirs(path, exist_ok=True)
            self.vectorstore.save_local(path)

    def load(self, path: str) -> None:
        self.vectorstore = FAISS.load_local(path, self.embeddings, allow_dangerous_deserialization=True)

    def search(self, query: str, k: int = 3) -> List[Document]:
        if not self.vectorstore:
            return []
        return self.vectorstore.similarity_search(query, k=k)
