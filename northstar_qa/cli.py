import argparse
import sys
from pathlib import Path

from .errors import AppError
from .service import ask_question, ingest_documents


DEFAULT_INDEX_PATH = Path("knowledge_index.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Answer questions from a local document collection."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser(
        "ingest", help="Read documents and build a local search index."
    )
    ingest_parser.add_argument("directory", type=Path, help="Directory of .md/.txt files")
    ingest_parser.add_argument(
        "--index",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help="Index output path (default: knowledge_index.json)",
    )

    ask_parser = subparsers.add_parser(
        "ask", help="Answer a question using the local search index."
    )
    ask_parser.add_argument("question", help="Question to answer")
    ask_parser.add_argument(
        "--index",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help="Index input path (default: knowledge_index.json)",
    )
    ask_parser.add_argument(
        "--top-k",
        type=int,
        default=4,
        help="Number of relevant chunks to inspect (default: 4)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "ingest":
            result = ingest_documents(args.directory, args.index)
            print(
                f"Indexed {result.document_count} documents into "
                f"{result.chunk_count} chunks."
            )
            print(f"Index saved to: {result.index_path}")
            return 0
        if args.command == "ask":
            if args.top_k < 1:
                raise AppError("--top-k must be at least 1.")
            answer = ask_question(args.question, args.index, top_k=args.top_k)
            print("Answer:")
            print(answer.text)
            print("\nSources:")
            if answer.sources:
                for source in answer.sources:
                    print(f"- {source}")
            else:
                print("- None")
            return 0
    except AppError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    parser.error("Unknown command")
    return 2
