import httpx

from app.core.config import settings

from app.services.llm_gateway.base import (
    BaseLLMProvider,
    LLMResult
)

class CloudProvider(BaseLLMProvider):

    async def generate(
        self,
        messages: list[dict],
        temperature: float = 0.2,
        response_format: str | None = None
    ) -> LLMResult:

        if not getattr(settings, "CLOUD_LLM_ENABLED", False):
            raise RuntimeError(
                "Cloud LLM provider is disabled"
            )

        api_key = getattr(settings, "CLOUD_LLM_API_KEY", None)
        if not api_key:
            raise RuntimeError(
                "Cloud API key is missing"
            )

        base_url = getattr(settings, "CLOUD_LLM_BASE_URL", None)
        if not base_url:
            raise RuntimeError(
                "Cloud API URL is missing"
            )

        model = getattr(settings, "CLOUD_LLM_MODEL", None)
        if not model:
            raise RuntimeError(
                "Cloud model is missing"
            )

        url = (
            f"{base_url.rstrip('/')}"
            "/chat/completions"
        )

        headers = {
            "Authorization": (
                f"Bearer {api_key}"
            ),
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }

        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(
            timeout=60
        ) as client:

            response = await client.post(
                url,
                headers=headers,
                json=payload
            )

            response.raise_for_status()

            data = response.json()

        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        if not content or not content.strip():
            raise ValueError(
                "Cloud provider returned an empty response"
            )

        return LLMResult(
            content=content,
            provider="cloud",
            model=model
        )