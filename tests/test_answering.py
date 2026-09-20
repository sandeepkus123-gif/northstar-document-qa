from northstar_qa.answering import UNSUPPORTED_ANSWER, compose_answer
from northstar_qa.models import Chunk, SearchResult


def test_answer_uses_supporting_sentence_and_source() -> None:
    chunk = Chunk(
        "refund:0",
        "refund-policy.md",
        "# Refund Policy\n\nCustomers may request a refund within 30 days of purchase.",
        0,
    )
    results = [SearchResult(chunk, 2.5, ("refund",), 0.5)]

    answer = compose_answer("What is the refund policy?", results)

    assert answer.supported
    assert "within 30 days" in answer.text
    assert answer.sources == ("refund-policy.md",)


def test_unsupported_answer_does_not_invent_details() -> None:
    answer = compose_answer("Who is the company CEO?", [])

    assert not answer.supported
    assert answer.text == UNSUPPORTED_ANSWER
    assert answer.sources == ()
