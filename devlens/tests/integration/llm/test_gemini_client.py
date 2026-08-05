from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from devlens.infrastructure.llm.gemini_client import GeminiCommentaryService


async def test_generate_commentary_returns_the_response_text() -> None:
    fake_response = SimpleNamespace(text="generated text")
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with patch("devlens.infrastructure.llm.gemini_client.genai.Client", return_value=fake_client):
        service = GeminiCommentaryService(api_key="fake-key", model_name="gemini-flash-latest")
        commentary = await service.generate_commentary("test prompt")

    assert commentary == "generated text"
    fake_client.models.generate_content.assert_called_once_with(
        model="gemini-flash-latest", contents="test prompt"
    )


async def test_generate_commentary_returns_empty_string_when_response_text_is_none() -> None:
    fake_response = SimpleNamespace(text=None)
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with patch("devlens.infrastructure.llm.gemini_client.genai.Client", return_value=fake_client):
        service = GeminiCommentaryService(api_key="fake-key", model_name="gemini-flash-latest")
        commentary = await service.generate_commentary("test prompt")

    assert commentary == ""
