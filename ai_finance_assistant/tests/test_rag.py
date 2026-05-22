import pytest
import tempfile
import os
from src.rag.vector_store import FinancialVectorStore
from src.rag.retriever import RAGRetriever


@pytest.fixture
def temp_docs_dir(tmp_path):
    doc1 = tmp_path / "test_doc.md"
    doc1.write_text("# Investing Basics\nInvesting is putting money to work to generate returns over time. "
                    "It is a fundamental concept in personal finance that allows individuals to grow wealth.")
    doc2 = tmp_path / "bonds_basics.md"
    doc2.write_text("# Bonds Basics\nBonds are fixed-income securities that represent loans made to governments "
                    "or corporations. They pay regular interest and return principal at maturity.")
    return str(tmp_path)


def test_vector_store_build(temp_docs_dir):
    vs = FinancialVectorStore(embedding_model="all-MiniLM-L6-v2")
    vs.build_from_directory(temp_docs_dir)
    assert vs.vectorstore is not None


def test_vector_store_build_no_docs():
    vs = FinancialVectorStore(embedding_model="all-MiniLM-L6-v2")
    with pytest.raises(ValueError, match="No documents found"):
        vs.build_from_directory("/tmp/nonexistent_dir_12345")


def test_vector_store_save_load(tmp_path, temp_docs_dir):
    vs = FinancialVectorStore(embedding_model="all-MiniLM-L6-v2")
    vs.build_from_directory(temp_docs_dir)

    index_path = str(tmp_path / "test_index")
    vs.save(index_path)
    assert os.path.exists(index_path)

    vs2 = FinancialVectorStore(embedding_model="all-MiniLM-L6-v2")
    vs2.load(index_path)
    assert vs2.vectorstore is not None


def test_retriever_search(temp_docs_dir):
    vs = FinancialVectorStore(embedding_model="all-MiniLM-L6-v2")
    vs.build_from_directory(temp_docs_dir)
    retriever = RAGRetriever(vs)
    context = retriever.retrieve("what is investing", k=1)
    assert len(context) > 0


def test_retriever_search_with_sources(temp_docs_dir):
    vs = FinancialVectorStore(embedding_model="all-MiniLM-L6-v2")
    vs.build_from_directory(temp_docs_dir)
    retriever = RAGRetriever(vs)
    context, sources = retriever.retrieve_with_sources("bonds and fixed income", k=2)
    assert len(context) > 0
    assert len(sources) > 0


def test_retriever_empty_vectorstore():
    vs = FinancialVectorStore(embedding_model="all-MiniLM-L6-v2")
    # No documents loaded
    retriever = RAGRetriever(vs)
    context = retriever.retrieve("investing", k=3)
    assert context == ""

    context2, sources2 = retriever.retrieve_with_sources("investing", k=3)
    assert context2 == ""
    assert sources2 == []
