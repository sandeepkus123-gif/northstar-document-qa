import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .errors import IndexError
from .models import Chunk, Document


INDEX_VERSION = 1


def save_index(
    path: Path,
    source_directory: Path,
    documents: list[Document],
    chunks: list[Chunk],
) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "version": INDEX_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_directory": str(source_directory.expanduser().resolve()),
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "documents": [document.path for document in documents],
        "chunks": [chunk.to_dict() for chunk in chunks],
    }

    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_name = temporary_file.name
            json.dump(payload, temporary_file, ensure_ascii=False, indent=2)
            temporary_file.write("\n")

        os.replace(temporary_name, path)
    except OSError as exc:
        raise IndexError(f"Could not save index to {path}: {exc}") from exc
    finally:
        if temporary_name and Path(temporary_name).exists():
            Path(temporary_name).unlink()


def load_index(path: Path) -> list[Chunk]:
    path = path.expanduser().resolve()
    if not path.exists():
        raise IndexError(
            f"No local index found at {path}. Run the ingest command first."
        )

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IndexError(f"Could not read index at {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise IndexError(f"Index at {path} is incomplete or invalid.")
    if payload.get("version") != INDEX_VERSION:
        raise IndexError(
            f"Unsupported index version. Rebuild it with the ingest command."
        )

    try:
        chunks = [Chunk.from_dict(value) for value in payload["chunks"]]
    except (KeyError, TypeError, ValueError) as exc:
        raise IndexError(f"Index at {path} is incomplete or invalid.") from exc

    if not chunks:
        raise IndexError(f"Index at {path} contains no searchable chunks.")
    return chunks
