# Local Document Q&A

A small command-line application that answers questions from local Markdown and
text documents. It uses BM25 retrieval and extractive answer composition, so it
does not need an API key, hosted model, or paid service.

## Requirements

- Python 3.10 or newer (tested with Python 3.12)
- Windows PowerShell examples are shown below

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, the environment can be used directly without
changing the execution policy:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Ingest documents

Build a local index from the supplied document collection:

```powershell
python app.py ingest .\docs
```

The loader searches the directory recursively for `.md` and `.txt` files. It
splits their contents into overlapping chunks and writes `knowledge_index.json`
in the current directory.

To use a different index location:

```powershell
python app.py ingest .\docs --index .\data\northstar-index.json
```

## Ask questions

```powershell
python app.py ask "What is the refund policy?"
python app.py ask "How long does standard shipping take?"
python app.py ask "What should I do if my NS Band will not sync?"
```

Each supported answer includes the document files used. If the collection does
not contain enough evidence, the application says so and reports no sources.

An index at a custom location can be queried with:

```powershell
python app.py ask "How much is the annual plan?" --index .\data\northstar-index.json
```

`--top-k` controls how many retrieved chunks are considered. The default is 4:

```powershell
python app.py ask "Can I return the band?" --top-k 5
```

## Run tests

```powershell
python -m pytest -q
```

The tests cover document loading, chunking, index persistence, retrieval,
answer composition, CLI errors, and questions against the supplied `docs`
collection.

## Common errors

- **No local index found**: run `python app.py ingest .\docs` first.
- **No supported documents found**: confirm the directory contains `.md` or
  `.txt` files.
- **Unsupported index version**: rebuild the index with the current code.
- **Question cannot be empty**: pass a non-empty quoted question.

## Project layout

```text
app.py                  CLI entry point
northstar_qa/           loading, chunking, indexing, retrieval and answering
tests/                  unit and end-to-end tests
docs/                   supplied local knowledge base
requirements.txt        runtime and test dependencies
NOTES.md                architecture and trade-offs
```
