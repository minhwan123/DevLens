from sentence_transformers import SentenceTransformer

_DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"


class SentenceTransformerEmbedder:
    """Wraps a Sentence Transformers model, downloading/caching weights on first use."""

    def __init__(self, model_name: str = _DEFAULT_MODEL_NAME) -> None:
        try:
            # This model's weights are pinned and never change, so once cached there is no
            # reason to pay for (or hang on) a Hugging Face Hub network round-trip just to
            # check for updates. Prefer whatever is already on disk.
            self._model = SentenceTransformer(model_name, local_files_only=True)
        except Exception:
            # Not cached yet on this machine (first run) -- fetch it for real.
            self._model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]
