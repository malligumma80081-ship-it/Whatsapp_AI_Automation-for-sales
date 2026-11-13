from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class LLMResult:
    content: str
    provider: str
    model: str

class BaseLLMProvider(ABC):

    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
        temperature: float = 0.2,
        response_format: str | None = None,
    ) -> LLMResult:
        pass