from pathlib import Path

import pytest

from northstar_qa.service import ask_question, ingest_documents


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIRECTORY = PROJECT_ROOT / "docs"


@pytest.fixture(scope="module")
def real_index(tmp_path_factory: pytest.TempPathFactory) -> Path:
    index_path = tmp_path_factory.mktemp("real-index") / "index.json"
    result = ingest_documents(DOCS_DIRECTORY, index_path)

    assert result.document_count == 9
    assert result.chunk_count > result.document_count
    return index_path


@pytest.mark.parametrize(
    ("question", "expected_text", "expected_source"),
    [
        ("What is the refund policy?", "30 days", "refund-policy.md"),
        ("How long does standard shipping take?", "5 to 7", "faq.md"),
        ("How much does the monthly plan cost?", "$12", "subscription-plans.md"),
        ("What should I do if the NS Band will not sync?", "Bluetooth", "troubleshooting.txt"),
        ("Does Northstar sell health data to advertisers?", "does not sell", "faq.md"),
    ],
)
def test_answers_across_the_real_collection(
    real_index: Path,
    question: str,
    expected_text: str,
    expected_source: str,
) -> None:
    answer = ask_question(question, real_index)

    assert answer.supported
    assert expected_text.casefold() in answer.text.casefold()
    assert any(expected_source in source for source in answer.sources)


@pytest.mark.parametrize(
    "question",
    [
        "Who is the CEO of Northstar Fitness?",
        "What is the weather in Mumbai?",
    ],
)
def test_declines_questions_not_answered_by_the_collection(
    real_index: Path, question: str
) -> None:
    answer = ask_question(question, real_index)

    assert not answer.supported
    assert answer.sources == ()
