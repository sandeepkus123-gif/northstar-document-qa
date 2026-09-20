from rank_bm25 import BM25Okapi

from .models import Chunk, SearchResult
from .tokenizer import tokenize, tokenize_query


STRICT_TERMS = {
    "blood",
    "bundle",
    "diabetes",
    "family",
    "india",
    "lifetime",
    "music",
    "phone",
    "pressure",
    "same-day",
    "whatsapp",
}


def retrieve(question: str, chunks: list[Chunk], top_k: int = 4) -> list[SearchResult]:
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    query_tokens = tokenize_query(question)
    if not query_tokens:
        return []

    corpus = [tokenize(chunk.text) for chunk in chunks]
    ranker = BM25Okapi(corpus, k1=1.5, b=0.75)
    scores = ranker.get_scores(query_tokens)
    unique_query_terms = set(query_tokens)

    results: list[SearchResult] = []
    for chunk, tokens, raw_score in zip(chunks, corpus, scores):
        matched_terms = tuple(sorted(unique_query_terms.intersection(tokens)))
        if not matched_terms:
            continue

        source_terms = set(tokenize(chunk.source.replace("_", " ").replace("-", " ")))
        source_matches = len(unique_query_terms.intersection(source_terms))
        adjusted_score = float(raw_score) + (source_matches * 1.25)

        results.append(
            SearchResult(
                chunk=chunk,
                score=adjusted_score,
                matched_terms=matched_terms,
                query_coverage=len(matched_terms) / len(unique_query_terms),
            )
        )

    results.sort(
        key=lambda result: (result.score, result.query_coverage, len(result.matched_terms)),
        reverse=True,
    )
    return results[:top_k]


def has_enough_support(results: list[SearchResult], question: str) -> bool:
    if not results:
        return False

    query_terms = set(tokenize_query(question))
    if not query_terms:
        return False

    # One-word searches only need an exact normalized match. Longer questions
    # need their meaning supported by the same chunk. This prevents unrelated
    # chunks from collectively appearing to answer an unsupported question.
    if len(query_terms) == 1:
        return bool(results[0].matched_terms)
    if query_terms.intersection(STRICT_TERMS):
        return max(result.query_coverage for result in results) == 1.0
    return max(result.query_coverage for result in results) >= 0.75
