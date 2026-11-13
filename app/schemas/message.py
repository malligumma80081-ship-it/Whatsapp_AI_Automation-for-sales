from typing import Optional

from pydantic import BaseModel, Field


class MessageRequest(BaseModel):
    customer_id: Optional[int] = None
    message: str = Field(
        min_length=1,
        max_length=1000
    )


class MessageResponse(BaseModel):
    intent: str
    reply: str
    channel: str = "internal"
    requires_human: bool = False