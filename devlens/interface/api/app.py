import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from devlens.config.settings import get_settings
from devlens.interface.api.dependencies import get_similarity_service
from devlens.interface.api.routers.analyze import router as analyze_router

logger = logging.getLogger(__name__)

_STARTUP_PRELOAD_TIMEOUT_SECONDS = 20.0


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Loading the Sentence Transformers model takes a few seconds and can involve a network
    # call to Hugging Face Hub even when the model is already cached locally (a freshness
    # check). Preloading it here means a real request doesn't pay that cost later — but a
    # network hiccup here must not block the whole server from starting. Running it off the
    # event loop keeps startup responsive to Ctrl+C, and a timeout + fallback means the model
    # just loads lazily on the first request instead, exactly like before this optimization.
    try:
        await asyncio.wait_for(
            asyncio.to_thread(get_similarity_service), timeout=_STARTUP_PRELOAD_TIMEOUT_SECONDS
        )
    except Exception:
        logger.warning(
            "Could not preload the embedding model at startup (network issue reaching "
            "Hugging Face Hub?). It will load lazily on the first request instead.",
            exc_info=True,
        )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="DevLens API",
        description="Analyze your GitHub. Understand your career.",
        lifespan=_lifespan,
    )
    allowed_origins = [
        origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(analyze_router)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
