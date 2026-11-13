import json
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models import Product
from app.schemas.ai import AIResponse
from app.services.llm_gateway.gateway import LLMGateway


logger = logging.getLogger(__name__)

llm_gateway = LLMGateway()


BUSINESS_CONTEXT = """
Business name: Millet Milk Sales

Product: Ragi Milk

Delivery options:
- Home delivery
- Customer pickup

Payment options:
- Cash on Delivery
- UPI

Important rules:
- Never claim an order has been placed unless
  the order service confirms it.
- Never claim a payment is successful without
  verified payment confirmation.
- Never invent discounts, delivery charges,
  availability, or business policies.
- For complex complaints or uncertain requests,
  recommend human support.
"""


def get_catalog_context(db: Session) -> str:
    products = (
        db.query(Product)
        .filter(Product.available.is_(True))
        .all()
    )

    if not products:
        return "No products are currently listed as available."

    lines = []

    for product in products:
        product_name = getattr(product, "name", None) or getattr(product, "product_name", None)
        product_size = getattr(product, "size", None)
        product_price = getattr(product, "price", None)

        lines.append(
            f"Product: {product_name}; "
            f"Size: {product_size}; "
            f"Price: Rs. {product_price}"
        )

    return "\n".join(lines)


def build_prompt(
    message: str,
    catalog_context: str
) -> str:

    return f"""
You are a helpful customer assistant for Millet Milk Sales.

Your task is to understand customer questions and
respond politely and accurately.

BUSINESS INFORMATION:
{BUSINESS_CONTEXT}

CURRENT PRODUCT CATALOGUE:
{catalog_context}

CUSTOMER MESSAGE:
{json.dumps(message, ensure_ascii=False)}

OUTPUT REQUIREMENTS:
Return only valid JSON with these fields:

{{
  "intent": "greeting",
  "reply": "Your customer-facing response",
  "requires_human": false
}}

Allowed intent values:
greeting, product_question, delivery, payment,
general, human_support, unknown

Rules:
- Use only the supplied business information.
- Do not invent product prices or product availability.
- Do not create orders or modify inventory.
- Do not claim a transaction has been completed.
- Keep the response concise and friendly.
- If the question is unclear, ask for clarification.
- If human support is required, set requires_human to true.
"""


async def generate_ai_reply(
    message: str,
    db: Session
) -> AIResponse:

    catalog_context = get_catalog_context(db)

    prompt = build_prompt(
        message=message,
        catalog_context=catalog_context
    )

    result = await llm_gateway.generate(
        messages=[{"role": "user", "content": prompt}],
        task="general",
        temperature=0.2,
        response_format="json",
    )
    if result is None or result.content is None:
        raise ValueError("The LLM gateway returned no response content.")

    parsed = json.loads(result.content)

    return AIResponse.model_validate(parsed)