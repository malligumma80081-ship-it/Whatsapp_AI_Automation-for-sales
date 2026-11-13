from pydantic import BaseModel, Field
from pydantic import Field

class RAGRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=1000
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=10
    )


class RAGSource(BaseModel):
    chunk_id: str
    source: str
    chunk_index: int
    distance: float


class RAGResponse(BaseModel):
    question: str
    answer: str
    sources: list[RAGSource] = Field(default_factory=list)
    requires_human: bool = False
    provider: str = "ollama-rag"