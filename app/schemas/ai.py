from typing import Literal

from pydantic import BaseModel, Field


class AIRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=1000
    )


class AIResponse(BaseModel):
    intent: Literal[
        "greeting",
        "product_question",
        "delivery",
        "payment",
        "general",
        "human_support",
        "unknown"
    ]

    reply: str = Field(
        min_length=1,
        max_length=1500
    )

    requires_human: bool = False

    provider: str = "ollama"