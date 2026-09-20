import json
from pathlib import Path

from northstar_qa.cli import main
from northstar_qa.service import ingest_documents


def test_ingest_writes_a_readable_json_index(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "refunds.md").write_text(
        "# Refunds\n\nNew subscriptions can be refunded within 30 days.",
        encoding="utf-8",
    )
    index_path = tmp_path / "index.json"

    result = ingest_documents(docs, index_path)
    saved = json.loads(index_path.read_text(encoding="utf-8"))

    assert result.document_count == 1
    assert result.chunk_count == 1
    assert saved["version"] == 1
    assert saved["documents"] == ["refunds.md"]
    assert saved["chunks"][0]["source"] == "refunds.md"


def test_cli_ingest_reports_success(tmp_path: Path, capsys) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "faq.txt").write_text("A short FAQ.", encoding="utf-8")
    index_path = tmp_path / "index.json"

    exit_code = main(["ingest", str(docs), "--index", str(index_path)])
    output = capsys.readouterr()

    assert exit_code == 0
    assert "Indexed 1 documents" in output.out
    assert index_path.exists()


def test_cli_ingest_reports_missing_directory(tmp_path: Path, capsys) -> None:
    exit_code = main(["ingest", str(tmp_path / "missing")])
    output = capsys.readouterr()

    assert exit_code == 1
    assert "does not exist" in output.err
