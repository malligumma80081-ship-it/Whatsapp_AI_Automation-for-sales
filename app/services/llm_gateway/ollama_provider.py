import httpx

from app.core.config import settings

from app.services.llm_gateway.base import (
    BaseLLMProvider,
    LLMResult
)

class OllamaProvider(BaseLLMProvider):

    async def generate(
        self,
        messages: list[dict],
        temperature: float = 0.2,
        response_format: str | None = None,
    ) -> LLMResult:

        url = (
            f"{settings.OLLAMA_BASE_URL.rstrip('/')}"
            "/api/chat"
        )

        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }

        if response_format == "json":
            payload["format"] = "json"

        async with httpx.AsyncClient(
            timeout=settings.OLLAMA_TIMEOUT
        ) as client:

            response = await client.post(
                url,
                json=payload
            )

            response.raise_for_status()

            data = response.json()

        content = (
            data.get("message", {})
            .get("content", "")
        )

        if not content.strip():
            raise ValueError(
                "Ollama returned an empty response"
            )

        return LLMResult(
            content=content,
            provider="ollama",
            model=settings.OLLAMA_MODEL
        )