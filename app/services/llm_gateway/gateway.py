import asyncio
import logging
import time

import httpx

from app.core.config import settings

from app.services.llm_gateway.router import (
    ModelRouter
)

from app.services.llm_monitoring import (
    record_request
)

logger = logging.getLogger(__name__)

class LLMGateway:

    def __init__(self):
        self.router = ModelRouter()

    async def _generate_with_retry(
        self,
        provider,
        messages,
        temperature,
        response_format=None
    ):

        max_retries = getattr(settings, "LLM_MAX_RETRIES", 3)

        for attempt in range(max_retries + 1):

            try:
                return await provider.generate(
                    messages=messages,
                    temperature=temperature,
                    response_format=response_format
                )

            except httpx.HTTPStatusError as exc:

                status = exc.response.status_code

                # Retry only transient server/rate-limit errors.
                if status not in (429, 500, 502, 503, 504):
                    raise

                if attempt >= max_retries:
                    raise

                logger.warning(
                    "Temporary provider error %s; retry %s",
                    status,
                    attempt + 1
                )

            except (
                httpx.TimeoutException,
                httpx.ConnectError
            ):

                if attempt >= max_retries:
                    raise

                logger.warning(
                    "Provider connection failure; retry %s",
                    attempt + 1
                )

            delay = (
                getattr(settings, "LLM_RETRY_DELAY", 1.0)
                * (2 ** attempt)
            )

            await asyncio.sleep(delay)

    async def generate(
        self,
        messages: list[dict],
        task: str = "general",
        temperature: float = 0.2,
        response_format: str | None = None
    ):

        default_provider = getattr(
            settings,
            "LLM_DEFAULT_PROVIDER",
            "ollama"
        )
        primary = self.router.select_provider(task)

        start = time.perf_counter()

        try:
            result = await self._generate_with_retry(
                provider=primary,
                messages=messages,
                temperature=temperature,
                response_format=response_format
            )

            if result is None:
                raise RuntimeError("Primary LLM provider returned no result")

            latency = (
                time.perf_counter() - start
            ) * 1000

            record_request(
                provider=result.provider,
                success=True,
                latency_ms=latency
            )

            return result

        except Exception:
            logger.exception(
                "Primary LLM provider failed"
            )

            latency = (
                time.perf_counter() - start
            ) * 1000

            record_request(
                provider=(
                    default_provider
                ),
                success=False,
                latency_ms=latency
            )

            if not getattr(settings, "LLM_ENABLE_FALLBACK", False):
                raise

        # Attempt an alternative provider if configured.
        fallback = self.router.get_fallback_provider(
            default_provider
            if task != "rag"
            else "ollama"
        )

        if fallback is None:
            raise RuntimeError(
                "Primary LLM failed and no fallback is configured"
            )

        fallback_start = time.perf_counter()

        try:
            result = await self._generate_with_retry(
                provider=fallback,
                messages=messages,
                temperature=temperature,
                response_format=response_format
            )

            if result is None:
                raise RuntimeError("Fallback LLM provider returned no result")

            latency = (
                time.perf_counter() - fallback_start
            ) * 1000

            record_request(
                provider=result.provider,
                success=True,
                latency_ms=latency
            )

            return result

        except Exception:
            logger.exception(
                "Fallback LLM provider also failed"
            )

            latency = (
                time.perf_counter() - fallback_start
            ) * 1000

            record_request(
                provider=fallback.__class__.__name__,
                success=False,
                latency_ms=latency
            )

            raise RuntimeError(
                "All configured LLM providers failed"
            )