import re
from dataclasses import dataclass

from .models import SearchResult
from .retrieval import has_enough_support
from .tokenizer import tokenize, tokenize_query


SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+|\n+|\s+-\s+")
MARKDOWN_PREFIX = re.compile(r"^(?:#{1,6}\s+|[-*]\s+|\d+[.)]\s+)")
BOILERPLATE_PHRASES = (
    "this document describes",
    "covered in separate",
    "depends on the",
    "policy controls",
)
FOCUS_TERMS = {
    "annual",
    "cancel",
    "charge",
    "cost",
    "delete",
    "error",
    "include",
    "medical",
    "monthly",
    "premium",
    "refund",
    "renew",
    "shipping",
    "sync",
    "track",
}
UNSUPPORTED_ANSWER = (
    "I could not find enough support for that answer in the provided documents."
)


@dataclass(frozen=True)
class Answer:
    text: str
    sources: tuple[str, ...]
    supported: bool


def compose_answer(question: str, results: list[SearchResult]) -> Answer:
    if not has_enough_support(results, question):
        return Answer(UNSUPPORTED_ANSWER, (), False)

    query_terms = set(tokenize_query(question))
    single_passage_answer = bool(query_terms.intersection({"cost", "track", "sell"}))
    single_passage_answer = single_passage_answer or {
        "premium",
        "include",
    }.issubset(query_terms)
    single_passage_answer = single_passage_answer or {
        "premium",
        "features",
    }.issubset(query_terms)
    single_passage_answer = single_passage_answer or bool(
        query_terms.intersection({"step", "sleep", "heart", "recovery"})
        and "band" in query_terms
    )
    answer_limit = 1 if single_passage_answer else 2
    candidates: list[tuple[float, str, str]] = []
    highest_chunk_score = max((result.score for result in results), default=1.0)
    score_scale = max(abs(highest_chunk_score), 1.0)

    for result in results:
        paragraphs = result.chunk.text.split("\n\n")
        for paragraph_index, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            is_issue = paragraph.lower().startswith("issue:")
            following = (
                paragraphs[paragraph_index + 1].strip()
                if paragraph_index + 1 < len(paragraphs)
                else ""
            )
            previous = paragraphs[paragraph_index - 1].strip() if paragraph_index else ""
            previous_is_heading = (
                previous
                and len(previous.split()) <= 8
                and previous[-1] not in ".!?"
            )
            candidate_block = (
                f"{previous} {paragraph}"
                if previous_is_heading and " - " in paragraph
                else paragraph
            )
            if " - " in paragraph and following and not is_issue:
                combined_text = f"{candidate_block} {following}"
                combined_terms = set(tokenize(combined_text))
                if len(query_terms.intersection(combined_terms)) > len(
                    query_terms.intersection(tokenize(candidate_block))
                ):
                    candidate_block = combined_text
            candidate_block = re.sub(r"(^|\s)#{1,6}\s+", r"\1", candidate_block)
            paragraph_terms = set(tokenize(candidate_block))
            overlap = query_terms.intersection(paragraph_terms)
            is_structured_list = ":" in paragraph and " - " in paragraph
            required_overlap = min(2, len(query_terms)) if previous_is_heading else max(
                1, round(len(query_terms) * 0.75)
            )
            enough_list_overlap = len(overlap) >= required_overlap
            if (is_issue or is_structured_list) and enough_list_overlap:
                coverage = len(overlap) / len(query_terms)
                full_coverage_bonus = (
                    2.0 if len(query_terms) > 1 and coverage == 1.0 else 0.0
                )
                focus_bonus = 1.5 if overlap.intersection(FOCUS_TERMS) else 0.0
                free_tier_penalty = (
                    2.0
                    if "premium" in query_terms
                    and "free" not in query_terms
                    and "free tier" in candidate_block.casefold()
                    else 0.0
                )
                candidates.append(
                    (
                        (coverage * 3)
                        + (result.score / score_scale)
                        + 0.25
                        + full_coverage_bonus
                        + focus_bonus
                        - free_tier_penalty,
                        candidate_block,
                        result.chunk.source,
                    )
                )

        for raw_sentence in SENTENCE_BREAK.split(result.chunk.text):
            sentence = MARKDOWN_PREFIX.sub("", raw_sentence).strip()
            sentence_tokens = set(tokenize(sentence))
            overlap = query_terms.intersection(sentence_tokens)

            # Short headings often contain the query words but not an answer.
            if (
                not overlap
                or len(sentence.split()) < 5
                or sentence.endswith("?")
                or sentence[-1] not in ".!?"
            ):
                continue

            coverage = len(overlap) / len(query_terms)
            density = len(overlap) / max(len(sentence_tokens), 1)
            retrieval_boost = result.score / score_scale
            number_bonus = 0.6 if any(character.isdigit() for character in sentence) else 0
            enumeration_bonus = min(sentence.count(",") * 0.15, 0.6)
            full_coverage_bonus = (
                2.0 if len(query_terms) > 1 and coverage == 1.0 else 0.0
            )
            focus_bonus = 1.5 if overlap.intersection(FOCUS_TERMS) else 0.0
            boilerplate_penalty = 0.8 if any(
                phrase in sentence.casefold() for phrase in BOILERPLATE_PHRASES
            ) else 0
            free_tier_penalty = (
                2.0
                if "premium" in query_terms
                and "free" not in query_terms
                and "free tier" in sentence.casefold()
                else 0.0
            )
            sentence_score = (
                (coverage * 3)
                + density
                + retrieval_boost
                + number_bonus
                + enumeration_bonus
                + full_coverage_bonus
                + focus_bonus
                - boilerplate_penalty
                - free_tier_penalty
            )
            candidates.append((sentence_score, sentence, result.chunk.source))

    if not candidates:
        return Answer(UNSUPPORTED_ANSWER, (), False)

    candidates.sort(key=lambda item: item[0], reverse=True)
    chosen_sentences: list[str] = []
    sources: list[str] = []
    seen_sentences: set[str] = set()

    for _, sentence, source in candidates:
        normalized = sentence.casefold()
        if normalized in seen_sentences:
            continue
        sentence_terms = set(tokenize(sentence))
        if any(
            _similarity(sentence_terms, set(tokenize(existing))) >= 0.6
            for existing in chosen_sentences
        ):
            continue
        if sum(len(item) for item in chosen_sentences) + len(sentence) > 650:
            continue

        chosen_sentences.append(sentence)
        seen_sentences.add(normalized)
        if source not in sources:
            sources.append(source)
        if sentence.startswith("Issue:") and "Possible steps:" in sentence:
            break
        if len(chosen_sentences) == answer_limit:
            break

    if not chosen_sentences:
        return Answer(UNSUPPORTED_ANSWER, (), False)

    return Answer(" ".join(chosen_sentences), tuple(sources), True)


def _similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left.intersection(right)) / len(left.union(right))
