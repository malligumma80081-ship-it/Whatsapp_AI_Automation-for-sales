import json

from app.services.llm_gateway.gateway import LLMGateway
from app.services.tool_registry import execute_tool

llm_gateway = LLMGateway()

async def process_tool_request(message: str, db):
    prompt = f"""
You are an AI assistant for Millet Milk Sales.

Available tools:
1. get_products: arguments {{}}
2. check_inventory: arguments {{"product_id": "RAGI500"}}
3. calculate_order: arguments
   {{"product_id": "RAGI500", "quantity": 2}}
4. get_order_status: arguments {{"order_id": 1}}

Rules:
- Select only one tool.
- Never invent product IDs or order IDs.
- Do not select create_order.
- Do not invent prices or stock.
- If information is missing, return tool_name as "none".
- Return JSON only.

Customer message: {message}

JSON format:
{{
  "tool_name": "check_inventory",
  "arguments": {{"product_id": "RAGI500"}}
}}
"""

    result = await llm_gateway.generate(
        messages=[{"role": "user", "content": prompt}],
        task="general",
        temperature=0,
        response_format="json",
    )

    plan = json.loads(result.content)
    tool_name = plan.get("tool_name")
    arguments = plan.get("arguments", {})

    allowed_tools = {
        "get_products",
        "check_inventory",
        "calculate_order",
        "get_order_status",
    }

    if tool_name not in allowed_tools:
        return {
            "reply": "Please provide more details so I can help.",
            "tool_result": None,
        }

    tool_result = execute_tool(
        db=db,
        tool_name=tool_name,
        arguments=arguments,
    )

    answer_result = await llm_gateway.generate(
        messages=[
            {
                "role": "user",
                "content": (
                    "Answer the customer using only this tool result. "
                    "Do not invent facts or prices.\n"
                    f"Customer message: {message}\n"
                    f"Tool result: {json.dumps(tool_result)}"
                ),
            }
        ],
        task="general",
        temperature=0.2,
    )

    return {
        "reply": answer_result.content,
        "tool_name": tool_name,
        "tool_result": tool_result,
        "provider": answer_result.provider,
    }