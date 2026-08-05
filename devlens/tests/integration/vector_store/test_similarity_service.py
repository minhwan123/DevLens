import pytest

from devlens.infrastructure.vector_store.similarity_service import EmbeddingSimilarityService


class _FakeEmbedder:
    """Deterministic stand-in for SentenceTransformerEmbedder — no real model is loaded."""

    def __init__(self, vectors: dict[str, list[float]]) -> None:
        self._vectors = vectors

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vectors[text] for text in texts]


def test_rank_returns_similarity_scores_keyed_by_item_id() -> None:
    embedder = _FakeEmbedder(
        {
            "query": [1.0, 0.0],
            "item-a text": [1.0, 0.0],
            "item-b text": [0.0, 1.0],
        }
    )
    service = EmbeddingSimilarityService(embedder=embedder)  # type: ignore[arg-type]

    scores = service.rank("query", {"item-a": "item-a text", "item-b": "item-b text"})

    assert scores["item-a"] == pytest.approx(1.0, abs=1e-4)
    assert scores["item-b"] == pytest.approx(0.0, abs=1e-4)


def test_rank_returns_empty_dict_for_an_empty_catalog() -> None:
    service = EmbeddingSimilarityService(embedder=_FakeEmbedder({}))  # type: ignore[arg-type]

    scores = service.rank("query", {})

    assert scores == {}
