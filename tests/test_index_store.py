import json
from pathlib import Path

import pytest

from northstar_qa.errors import IndexError
from northstar_qa.index_store import load_index


def test_rejects_invalid_json(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    index_path.write_text("not json", encoding="utf-8")

    with pytest.raises(IndexError, match="Could not read index"):
        load_index(index_path)


def test_rejects_unknown_index_version(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    index_path.write_text(json.dumps({"version": 99, "chunks": []}), encoding="utf-8")

    with pytest.raises(IndexError, match="Unsupported index version"):
        load_index(index_path)


def test_rejects_non_object_index(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    index_path.write_text("[]", encoding="utf-8")

    with pytest.raises(IndexError, match="incomplete or invalid"):
        load_index(index_path)


def test_rejects_index_without_chunks(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    index_path.write_text(
        json.dumps({"version": 1, "chunks": []}), encoding="utf-8"
    )

    with pytest.raises(IndexError, match="no searchable chunks"):
        load_index(index_path)

