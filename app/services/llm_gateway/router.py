from app.core.config import settings

from app.services.llm_gateway.ollama_provider import (
    OllamaProvider
)

from app.services.llm_gateway.cloud_provider import (
    CloudProvider
)

class ModelRouter:

    def __init__(self):
        self.providers = {
            "ollama": OllamaProvider(),
            "cloud": CloudProvider()
        }

    def select_provider(self, task: str = "general"):

        # Keep RAG on the configured local provider
        # unless a future routing policy changes it.
        if task == "rag":
            provider_name = "ollama"

        else:
            provider_name = str(
                getattr(settings, "LLM_DEFAULT_PROVIDER", "ollama")
            ).lower()

        if provider_name not in self.providers:
            raise ValueError(
                f"Unsupported provider: {provider_name}"
            )

        return self.providers[provider_name]

    def get_fallback_provider(self, primary_name: str):

        if not getattr(settings, "CLOUD_LLM_ENABLED", False):
            return None

        if primary_name == "ollama":
            return self.providers["cloud"]

        return self.providers["ollama"]