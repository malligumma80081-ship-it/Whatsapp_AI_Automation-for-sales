from pydantic import BaseModel, Field


class ConversationRequest(BaseModel):
    customer_id: int
    message: str = Field(min_length=1, max_length=1000)
    channel: str = "internal"


class ConversationResponse(BaseModel):
    session_id: int
    state: str
    reply: str