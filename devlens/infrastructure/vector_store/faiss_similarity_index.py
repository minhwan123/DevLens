import faiss
import numpy as np


class FaissSimilarityIndex:
    """Cosine-similarity search over a small in-memory catalog via a FAISS inner-product index.

    Vectors must already be L2-normalized (SentenceTransformerEmbedder does this), so inner
    product is equivalent to cosine similarity.
    """

    def __init__(self, item_ids: list[str], vectors: list[list[float]]) -> None:
        self._item_ids = item_ids
        matrix = np.array(vectors, dtype="float32")
        self._index = faiss.IndexFlatIP(matrix.shape[1])
        self._index.add(matrix)

    def search(self, query_vector: list[float], top_k: int) -> dict[str, float]:
        query = np.array([query_vector], dtype="float32")
        scores, indices = self._index.search(query, min(top_k, len(self._item_ids)))
        return {
            self._item_ids[item_index]: float(score)
            for item_index, score in zip(indices[0], scores[0], strict=True)
            if item_index != -1
        }
