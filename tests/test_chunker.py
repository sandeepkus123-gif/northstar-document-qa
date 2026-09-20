from northstar_qa.chunker import chunk_documents
from northstar_qa.models import Document


def test_small_document_stays_in_one_chunk() -> None:
    document = Document("faq.md", "faq.md", "# FAQ\n\nRefunds take five days.")

    chunks = chunk_documents([document], max_chars=200)

    assert len(chunks) == 1
    assert chunks[0].id == "faq.md:0"
    assert "Refunds take five days" in chunks[0].text


def test_chunks_keep_source_and_overlap() -> None:
    document = Document(
        "guide.md",
        "guides/guide.md",
        "First paragraph has useful setup details.\n\n"
        "Second paragraph explains Bluetooth pairing.\n\n"
        "Third paragraph covers firmware updates.",
    )

    chunks = chunk_documents([document], max_chars=100, overlap_paragraphs=1)

    assert len(chunks) >= 2
    assert all(chunk.source == "guides/guide.md" for chunk in chunks)
    assert "Second paragraph" in chunks[0].text
    assert "Second paragraph" in chunks[1].text


def test_rejects_unreasonably_small_chunk_size() -> None:
    document = Document("faq.md", "faq.md", "Some content")

    try:
        chunk_documents([document], max_chars=20)
    except ValueError as exc:
        assert "at least 100" in str(exc)
    else:
        raise AssertionError("Expected a ValueError")

