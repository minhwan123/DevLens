from unittest.mock import MagicMock, patch

import numpy as np

from devlens.infrastructure.vector_store.embedding_model import SentenceTransformerEmbedder


def test_embed_converts_numpy_vectors_to_lists() -> None:
    fake_model = MagicMock()
    fake_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])

    with patch(
        "devlens.infrastructure.vector_store.embedding_model.SentenceTransformer",
        return_value=fake_model,
    ):
        embedder = SentenceTransformerEmbedder()
        vectors = embedder.embed(["a", "b"])

    assert vectors == [[0.1, 0.2], [0.3, 0.4]]
    fake_model.encode.assert_called_once_with(["a", "b"], normalize_embeddings=True)


def test_embedder_prefers_the_local_cache_first() -> None:
    with patch(
        "devlens.infrastructure.vector_store.embedding_model.SentenceTransformer"
    ) as mock_cls:
        SentenceTransformerEmbedder(model_name="custom-model")

    mock_cls.assert_called_once_with("custom-model", local_files_only=True)


def test_embedder_falls_back_to_a_real_download_when_not_cached() -> None:
    """Regression guard: if the model isn't cached yet, the offline-first attempt raises and
    must not be left uncaught — it should retry once for real, allowing the download."""
    fake_model = MagicMock()

    with patch(
        "devlens.infrastructure.vector_store.embedding_model.SentenceTransformer",
        side_effect=[OSError("not cached locally"), fake_model],
    ) as mock_cls:
        embedder = SentenceTransformerEmbedder(model_name="custom-model")

    assert embedder._model is fake_model
    assert mock_cls.call_args_list == [
        (("custom-model",), {"local_files_only": True}),
        (("custom-model",), {}),
    ]
