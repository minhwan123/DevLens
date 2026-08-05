import time
from unittest.mock import patch

from fastapi import FastAPI

from devlens.interface.api.app import _lifespan


async def test_lifespan_does_not_block_startup_when_preload_fails() -> None:
    """Regression test: a Hugging Face Hub hiccup during the startup preload must not hang
    the whole server — it should log a warning and let the app start, falling back to
    lazy-loading the embedding model on the first real request (the pre-optimization behavior).
    """

    def _raise() -> None:
        raise RuntimeError("simulated: HTTP Error 504 from huggingface.co")

    with patch("devlens.interface.api.app.get_similarity_service", side_effect=_raise):
        started_at = time.monotonic()
        async with _lifespan(FastAPI()):
            pass
        elapsed = time.monotonic() - started_at

    assert elapsed < 5.0
