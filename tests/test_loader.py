from pathlib import Path

import pytest

from northstar_qa.errors import DocumentLoadError
from northstar_qa.loader import load_documents


def test_loads_markdown_and_text_files(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_text("# Setup\n\nTurn on Bluetooth.", encoding="utf-8")
    (tmp_path / "faq.txt").write_text("Common questions", encoding="utf-8")
    (tmp_path / "photo.png").write_bytes(b"not really a photo")

    documents = load_documents(tmp_path)

    assert [document.source for document in documents] == ["faq.txt", "guide.md"]
    assert all("photo.png" not in document.path for document in documents)


def test_missing_directory_has_a_helpful_error(tmp_path: Path) -> None:
    with pytest.raises(DocumentLoadError, match="does not exist"):
        load_documents(tmp_path / "missing")


def test_rejects_directory_without_supported_documents(tmp_path: Path) -> None:
    (tmp_path / "data.csv").write_text("name,value", encoding="utf-8")

    with pytest.raises(DocumentLoadError, match="No supported documents"):
        load_documents(tmp_path)


def test_normalizes_a_common_broken_apostrophe(tmp_path: Path) -> None:
    (tmp_path / "policy.md").write_text(
        "The customer\u00e2\u20ac\u2122s request is reviewed.", encoding="utf-8"
    )

    document = load_documents(tmp_path)[0]

    assert document.content == "The customer's request is reviewed."
