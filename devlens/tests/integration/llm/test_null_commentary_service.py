from devlens.infrastructure.llm.null_commentary_service import NullCommentaryService


async def test_null_commentary_service_returns_a_placeholder_message() -> None:
    service = NullCommentaryService()

    commentary = await service.generate_commentary("any prompt")

    assert "GEMINI_API_KEY" in commentary
