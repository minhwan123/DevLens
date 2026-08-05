import pytest

from devlens.infrastructure.vector_store.faiss_similarity_index import FaissSimilarityIndex

_ITEM_IDS = ["a", "b", "c"]
_VECTORS = [
    [1.0, 0.0],
    [0.0, 1.0],
    [0.70710678, 0.70710678],
]


def test_search_returns_cosine_similarity_for_every_item() -> None:
    index = FaissSimilarityIndex(_ITEM_IDS, _VECTORS)

    scores = index.search([1.0, 0.0], top_k=3)

    assert scores["a"] == pytest.approx(1.0, abs=1e-4)
    assert scores["b"] == pytest.approx(0.0, abs=1e-4)
    assert scores["c"] == pytest.approx(0.70710678, abs=1e-4)


def test_top_k_limits_the_number_of_results() -> None:
    index = FaissSimilarityIndex(_ITEM_IDS, _VECTORS)

    scores = index.search([1.0, 0.0], top_k=1)

    assert set(scores.keys()) == {"a"}


def test_top_k_larger_than_catalog_returns_everything() -> None:
    index = FaissSimilarityIndex(_ITEM_IDS, _VECTORS)

    scores = index.search([1.0, 0.0], top_k=100)

    assert set(scores.keys()) == {"a", "b", "c"}
