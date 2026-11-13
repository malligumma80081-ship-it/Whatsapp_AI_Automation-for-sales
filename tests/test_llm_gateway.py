import asyncio
import unittest

from unittest.mock import AsyncMock, patch

import httpx

from app.services.llm_gateway.base import LLMResult

from app.services.llm_gateway.gateway import LLMGateway

class TestLLMGateway(unittest.IsolatedAsyncioTestCase):

    async def test_successful_generation(self):

        gateway = LLMGateway()

        fake_result = LLMResult(
            content="Hello from AI",
            provider="ollama",
            model="llama3.2:3b"
        )

        with patch.object(
            gateway.router,
            "select_provider"
        ) as mock_router:

            provider = AsyncMock()

            provider.generate.return_value = fake_result

            mock_router.return_value = provider

            with patch(
                "app.services.llm_gateway.gateway.record_request"
            ):

                result = await gateway.generate(
                    messages=[
                        {
                            "role": "user",
                            "content": "Hello"
                        }
                    ]
                )

        self.assertEqual(
            result.content,
            "Hello from AI"
        )

    async def test_retry_after_connection_error(self):

        gateway = LLMGateway()

        fake_result = LLMResult(
            content="Recovered",
            provider="ollama",
            model="llama3.2:3b"
        )

        provider = AsyncMock()

        provider.generate.side_effect = [
            httpx.ConnectError("Connection failed"),
            fake_result
        ]

        with patch.object(
            gateway.router,
            "select_provider",
            return_value=provider
        ):

            with patch(
                "app.services.llm_gateway.gateway.record_request"
            ):

                with patch(
                    "app.services.llm_gateway.gateway.asyncio.sleep",
                    new_callable=AsyncMock
                ):

                    result = await gateway.generate(
                        messages=[
                            {
                                "role": "user",
                                "content": "Hello"
                            }
                        ]
                    )

        self.assertEqual(
            result.content,
            "Recovered"
        )

        self.assertEqual(
            provider.generate.await_count,
            2
        )

if __name__ == "__main__":
    unittest.main()