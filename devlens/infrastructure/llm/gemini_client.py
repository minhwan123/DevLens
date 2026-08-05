import asyncio

from google import genai


class GeminiCommentaryService:
    """Generates free-form commentary text via the Gemini API.

    Never makes ranking/scoring decisions — see PriorityScorePolicy and friends for the
    actual (non-LLM, rule-based) recommendation logic this only explains in prose.
    """

    def __init__(self, api_key: str, model_name: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    async def generate_commentary(self, prompt: str) -> str:
        response = await asyncio.to_thread(
            self._client.models.generate_content, model=self._model_name, contents=prompt
        )
        return response.text or ""
