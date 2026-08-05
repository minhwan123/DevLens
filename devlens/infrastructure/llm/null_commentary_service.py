class NullCommentaryService:
    """Fallback used when GEMINI_API_KEY isn't configured.

    Keeps the report pipeline working end-to-end without credentials — graceful
    degradation, the same idea as InMemoryCacheRepository standing in for PostgreSQL.
    """

    async def generate_commentary(self, prompt: str) -> str:
        return (
            "AI 분석 의견을 생성할 수 없습니다: GEMINI_API_KEY가 설정되지 않았습니다. "
            "이 섹션을 제외한 나머지 리포트는 정상적으로 제공됩니다."
        )
