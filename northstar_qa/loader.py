from pathlib import Path

from .errors import DocumentLoadError
from .models import Document


SUPPORTED_EXTENSIONS = {".md", ".txt"}


def load_documents(directory: Path) -> list[Document]:
    directory = directory.expanduser().resolve()

    if not directory.exists():
        raise DocumentLoadError(f"Documents directory does not exist: {directory}")
    if not directory.is_dir():
        raise DocumentLoadError(f"Documents path is not a directory: {directory}")

    paths = sorted(
        path
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if not paths:
        raise DocumentLoadError(
            f"No supported documents found in {directory}. Expected .md or .txt files."
        )

    documents: list[Document] = []
    for path in paths:
        try:
            content = path.read_text(encoding="utf-8").strip()
            content = content.replace("\u00e2\u20ac\u2122", "'")
        except (OSError, UnicodeError) as exc:
            raise DocumentLoadError(f"Could not read {path}: {exc}") from exc

        # Empty notes are harmless, but there is nothing useful to index.
        if not content:
            continue

        documents.append(
            Document(
                source=path.name,
                path=path.relative_to(directory).as_posix(),
                content=content,
            )
        )

    if not documents:
        raise DocumentLoadError("The supported documents were empty.")

    return documents
