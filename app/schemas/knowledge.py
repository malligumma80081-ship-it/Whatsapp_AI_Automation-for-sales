from pydantic import BaseModel, Field

class KnowledgeSearchRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=1000
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=10
    )

class KnowledgeResult(BaseModel):
    id: str
    content: str
    source: str
    chunk_index: int
    distance: float
    similarity: float

class KnowledgeSearchResponse(BaseModel):
    question: str
    results: list[KnowledgeResult]