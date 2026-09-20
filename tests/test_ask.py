from pathlib import Path

from northstar_qa.cli import main
from northstar_qa.service import ingest_documents


def build_test_index(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "refund-policy.md").write_text(
        "# Refund policy\n\nCustomers may request a refund for a new subscription "
        "within 30 days of the original charge date.",
        encoding="utf-8",
    )
    (docs / "shipping.txt").write_text(
        "Standard shipping usually takes 5 to 7 business days after dispatch.",
        encoding="utf-8",
    )
    index_path = tmp_path / "index.json"
    ingest_documents(docs, index_path)
    return index_path


def test_cli_asks_a_supported_question(tmp_path: Path, capsys) -> None:
    index_path = build_test_index(tmp_path)

    exit_code = main(
        ["ask", "What is the refund policy?", "--index", str(index_path)]
    )
    output = capsys.readouterr()

    assert exit_code == 0
    assert "within 30 days" in output.out
    assert "refund-policy.md" in output.out


def test_cli_declines_an_unsupported_question(tmp_path: Path, capsys) -> None:
    index_path = build_test_index(tmp_path)

    exit_code = main(
        ["ask", "Who won the football championship?", "--index", str(index_path)]
    )
    output = capsys.readouterr()

    assert exit_code == 0
    assert "could not find enough support" in output.out
    assert "- None" in output.out


def test_cli_explains_how_to_fix_a_missing_index(tmp_path: Path, capsys) -> None:
    exit_code = main(
        ["ask", "What is the refund policy?", "--index", str(tmp_path / "none.json")]
    )
    output = capsys.readouterr()

    assert exit_code == 1
    assert "Run the ingest command first" in output.err


def test_cli_rejects_empty_question(tmp_path: Path, capsys) -> None:
    index_path = build_test_index(tmp_path)

    exit_code = main(["ask", "   ", "--index", str(index_path)])
    output = capsys.readouterr()

    assert exit_code == 1
    assert "Question cannot be empty" in output.err


def test_cli_rejects_invalid_top_k(tmp_path: Path, capsys) -> None:
    index_path = build_test_index(tmp_path)

    exit_code = main(
        ["ask", "What is the refund policy?", "--index", str(index_path), "--top-k", "0"]
    )
    output = capsys.readouterr()

    assert exit_code == 1
    assert "--top-k must be at least 1" in output.err
