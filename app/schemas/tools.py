from typing import Any, Literal
from pydantic import BaseModel, Field


ToolName = Literal[
    "get_products",
    "check_inventory",
    "calculate_order",
    "get_order_status",
    "create_order",
]


class ToolRequest(BaseModel):
    tool_name: ToolName
    arguments: dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False


class ToolResponse(BaseModel):
    tool_name: str
    success: bool
    result: dict[str, Any]
    message: str