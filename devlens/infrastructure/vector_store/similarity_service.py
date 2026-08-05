from devlens.infrastructure.vector_store.embedding_model import SentenceTransformerEmbedder
from devlens.infrastructure.vector_store.faiss_similarity_index import FaissSimilarityIndex


class EmbeddingSimilarityService:
    """Cosine similarity between a query text and a catalog of item texts.

    Embeds everything with Sentence Transformers, then searches a fresh in-memory FAISS index.
    Rebuilding the index per call is fine at this project's catalog size (tens of items); a
    persistent/incremental index would only be worth it at a much larger catalog scale.
    """

    def __init__(self, embedder: SentenceTransformerEmbedder | None = None) -> None:
        self._embedder = embedder or SentenceTransformerEmbedder()

    def rank(self, query_text: str, items: dict[str, str]) -> dict[str, float]:
        if not items:
            return {}
        item_ids = list(items.keys())
        vectors = self._embedder.embed([items[item_id] for item_id in item_ids])
        index = FaissSimilarityIndex(item_ids, vectors)
        query_vector = self._embedder.embed([query_text])[0]
        return index.search(query_vector, top_k=len(item_ids))
