from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Document:
    source: str
    path: str
    content: str


@dataclass(frozen=True)
class Chunk:
    id: str
    source: str
    text: str
    position: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict) -> "Chunk":
        try:
            return cls(
                id=str(value["id"]),
                source=str(value["source"]),
                text=str(value["text"]),
                position=int(value["position"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Invalid chunk data") from exc


@dataclass(frozen=True)
class SearchResult:
    chunk: Chunk
    score: float
    matched_terms: tuple[str, ...]
    query_coverage: float
