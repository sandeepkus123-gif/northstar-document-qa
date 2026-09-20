from northstar_qa.models import Chunk
from northstar_qa.retrieval import has_enough_support, retrieve


CHUNKS = [
    Chunk(
        "refunds:0",
        "refund-policy.md",
        "New subscription purchases may be refunded within 30 days.",
        0,
    ),
    Chunk(
        "shipping:0",
        "shipping.md",
        "Standard shipping usually takes 5 to 7 business days.",
        0,
    ),
    Chunk(
        "setup:0",
        "setup.md",
        "Enable Bluetooth and keep the band close to the phone.",
        0,
    ),
]


def test_retrieval_ranks_the_relevant_chunk_first() -> None:
    results = retrieve("Can I get a subscription refund?", CHUNKS)

    assert results[0].chunk.source == "refund-policy.md"
    assert "refund" in results[0].matched_terms


def test_normalizes_common_word_forms() -> None:
    results = retrieve("Are subscriptions refundable?", CHUNKS)

    assert results[0].chunk.source == "refund-policy.md"
    assert has_enough_support(results, "Are subscriptions refundable?")


def test_unrelated_question_has_no_support() -> None:
    question = "What is the capital of France?"
    results = retrieve(question, CHUNKS)

    assert results == []
    assert not has_enough_support(results, question)


def test_company_name_alone_does_not_make_an_answer_supported() -> None:
    question = "Who is the CEO of Northstar Fitness?"
    results = retrieve(question, CHUNKS)

    assert results == []
    assert not has_enough_support(results, question)
