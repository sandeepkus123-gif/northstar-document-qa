# Engineering Notes

## Architecture

The application has a thin CLI over a service layer. Ingestion loads local
documents, creates paragraph-aware chunks, and stores those chunks with source
metadata in JSON. Asking a question loads that JSON, constructs a BM25 index in
memory, retrieves relevant chunks, and selects supporting sentences for the
answer.

The modules are deliberately small: loading, chunking, persistence, retrieval,
and answer composition can be tested independently. JSON was chosen over
`pickle` because it is portable, inspectable, and safer to load.

## Retrieval strategy

The retriever uses BM25 Okapi (`k1=1.5`, `b=0.75`). Text is lowercased,
tokenized, and stripped of common query words. A small normalization map handles
forms such as `refundable`/`refund` and `cancellation`/`cancel`.

Filename matches receive a modest boost. This helps a focused source such as
`refund-policy.md` outrank a general FAQ when both contain similar words.

The answer layer is extractive rather than generative. It ranks sentences from
the retrieved chunks, removes near-duplicates, and returns their source files.
A coverage check rejects questions that do not match enough meaningful query
terms. Troubleshooting issue blocks are kept together so their steps remain
useful.

## Trade-offs and limitations

- BM25 is lexical. It may miss a valid answer phrased with an unknown synonym.
- The small normalization map is intentionally limited and English-specific.
- Extractive answers can sound less natural than LLM-generated prose.
- Confidence is based on query-term coverage rather than a trained relevance
  model, so ambiguous questions may still need rephrasing.
- The BM25 structure is rebuilt when a question is asked. That is negligible
  for this collection but would not be ideal for a very large corpus.
- Markdown is treated as readable text rather than parsed into a full syntax
  tree.

For a larger production system, the next step would be hybrid retrieval using
local embeddings plus BM25, followed by a locally hosted model constrained to
the retrieved context. Index versioning and evaluation data would also become
more formal.
