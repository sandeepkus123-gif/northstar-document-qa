import re

from .models import Chunk, Document


PARAGRAPH_BREAK = re.compile(r"\n\s*\n")


def chunk_documents(
    documents: list[Document], max_chars: int = 900, overlap_paragraphs: int = 2
) -> list[Chunk]:
    if max_chars < 100:
        raise ValueError("max_chars must be at least 100")
    if overlap_paragraphs < 0:
        raise ValueError("overlap_paragraphs cannot be negative")

    chunks: list[Chunk] = []
    for document in documents:
        paragraphs = _paragraphs(document.content, max_chars)
        groups = _group_paragraphs(paragraphs, max_chars, overlap_paragraphs)

        for position, group in enumerate(groups):
            chunks.append(
                Chunk(
                    id=f"{document.path}:{position}",
                    source=document.path,
                    text="\n\n".join(group),
                    position=position,
                )
            )

    return chunks


def _paragraphs(content: str, max_chars: int) -> list[str]:
    paragraphs: list[str] = []
    for paragraph in PARAGRAPH_BREAK.split(content.strip()):
        paragraph = " ".join(line.strip() for line in paragraph.splitlines()).strip()
        if not paragraph:
            continue
        paragraphs.extend(_split_long_paragraph(paragraph, max_chars))
    return paragraphs


def _split_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    if len(paragraph) <= max_chars:
        return [paragraph]

    pieces: list[str] = []
    current: list[str] = []
    current_length = 0

    for word in paragraph.split():
        added_length = len(word) + (1 if current else 0)
        if current and current_length + added_length > max_chars:
            pieces.append(" ".join(current))
            current = []
            current_length = 0

        current.append(word)
        current_length += len(word) + (1 if current_length else 0)

    if current:
        pieces.append(" ".join(current))
    return pieces


def _group_paragraphs(
    paragraphs: list[str], max_chars: int, overlap_paragraphs: int
) -> list[list[str]]:
    groups: list[list[str]] = []
    current: list[str] = []

    for paragraph in paragraphs:
        candidate_length = sum(len(item) for item in current) + len(paragraph)
        candidate_length += 2 * len(current)

        if current and candidate_length > max_chars:
            groups.append(current)
            current = current[-overlap_paragraphs:] if overlap_paragraphs else []

            # Do not let an overlap consume the whole next chunk.
            while current and len("\n\n".join(current + [paragraph])) > max_chars:
                current.pop(0)

        current.append(paragraph)

    if current and (not groups or current != groups[-1]):
        groups.append(current)
    return groups
