from dataclasses import dataclass
from pathlib import Path

from .chunker import chunk_documents
from .answering import Answer, compose_answer
from .errors import QuestionError
from .index_store import load_index, save_index
from .loader import load_documents
from .retrieval import retrieve


@dataclass(frozen=True)
class IngestResult:
    document_count: int
    chunk_count: int
    index_path: Path


def ingest_documents(documents_directory: Path, index_path: Path) -> IngestResult:
    documents = load_documents(documents_directory)
    chunks = chunk_documents(documents)
    save_index(index_path, documents_directory, documents, chunks)

    return IngestResult(
        document_count=len(documents),
        chunk_count=len(chunks),
        index_path=index_path.resolve(),
    )


def ask_question(question: str, index_path: Path, top_k: int = 4) -> Answer:
    question = question.strip()
    if not question:
        raise QuestionError("Question cannot be empty.")

    chunks = load_index(index_path)
    results = retrieve(question, chunks, top_k=top_k)
    return compose_answer(question, results)
