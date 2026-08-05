from devlens.config.settings import Settings
from devlens.infrastructure.llm.cached_commentary_service import CachedCommentaryService
from devlens.infrastructure.llm.gemini_client import GeminiCommentaryService
from devlens.infrastructure.llm.null_commentary_service import NullCommentaryService
from devlens.infrastructure.persistence.cache_repository import CacheRepository


def build_commentary_service(
    settings: Settings, cache: CacheRepository
) -> CachedCommentaryService | NullCommentaryService:
    if not settings.gemini_api_key:
        return NullCommentaryService()
    gemini_service = GeminiCommentaryService(
        api_key=settings.gemini_api_key, model_name=settings.gemini_model_name
    )
    return CachedCommentaryService(
        inner=gemini_service, cache=cache, ttl_seconds=settings.gemini_cache_ttl_seconds
    )
