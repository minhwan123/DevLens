from devlens.config.settings import Settings
from devlens.infrastructure.llm.cached_commentary_service import CachedCommentaryService
from devlens.infrastructure.llm.factory import build_commentary_service
from devlens.infrastructure.llm.null_commentary_service import NullCommentaryService
from devlens.infrastructure.persistence.in_memory_cache_repository import InMemoryCacheRepository


def test_no_api_key_falls_back_to_null_service() -> None:
    settings = Settings(gemini_api_key=None)

    service = build_commentary_service(settings, InMemoryCacheRepository())

    assert isinstance(service, NullCommentaryService)


def test_api_key_configured_wraps_the_real_gemini_service_with_caching() -> None:
    settings = Settings(
        gemini_api_key="fake-key-not-called", gemini_model_name="gemini-flash-latest"
    )

    service = build_commentary_service(settings, InMemoryCacheRepository())

    assert isinstance(service, CachedCommentaryService)
