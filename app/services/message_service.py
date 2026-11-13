import re

from sqlalchemy.orm import Session

from app.database.models import Product


BUSINESS_NAME = "Millet Milk Sales"

DELIVERY_OPTIONS = (
    "We offer home delivery and customer pickup."
)

PAYMENT_OPTIONS = (
    "You can pay using Cash on Delivery or UPI."
)


def detect_intent(message: str) -> str:
    text = message.lower().strip()

    if re.search(
        r"\b(hi|hello|hey)\b|good morning|good evening",
        text
    ):
        return "greeting"

    if re.search(
        r"\b(price|cost|rate|how much)\b",
        text
    ):
        return "price"

    if re.search(
        r"\b(delivery|deliver|pickup)\b|pick up",
        text
    ):
        return "delivery"

    if re.search(
        r"\b(payment|upi|cash|pay)\b",
        text
    ):
        return "payment"

    if re.search(
        r"\b(product|menu|catalog|available)\b",
        text
    ):
        return "catalog"

    if re.search(
        r"\b(human|agent|support|person)\b|call me",
        text
    ):
        return "human_support"

    return "unknown"


def format_order_confirmation(
    order_id: int,
    customer_name: str,
    total_amount: float,
    delivery_mode: str,
    payment_method: str
) -> str:
    return (
        f"Hello {customer_name}!\n\n"
        f"Your Ragi Milk order is received.\n"
        f"Order ID: #{order_id}\n"
        f"Total: ₹{total_amount:.2f}\n"
        f"Delivery: {delivery_mode}\n"
        f"Payment: {payment_method}\n\n"
        "Thank you for choosing Millet Milk Sales!"
    )


def get_product_catalog(db: Session) -> list:
    products = (
        db.query(Product)
        .filter(Product.available.is_(True))
        .all()
    )

    return products


def format_catalog(products: list) -> str:
    if not products:
        return "Sorry, no products are currently available."

    lines = ["Our available Ragi Milk products:"]

    for product in products:
        lines.append(
            f"- {product.name}: "
            f"{product.size} - ₹{product.price}"
        )

    return "\n".join(lines)


def generate_reply(
    message: str,
    db: Session
) -> dict:
    intent = detect_intent(message)

    if intent == "greeting":
        return {
            "intent": intent,
            "reply": (
                f"Welcome to {BUSINESS_NAME}! "
                "We sell fresh Ragi Milk. "
                "How can I help you today?"
            ),
            "requires_human": False
        }

    if intent == "price":
        products = get_product_catalog(db)

        return {
            "intent": intent,
            "reply": format_catalog(products),
            "requires_human": False
        }

    if intent == "catalog":
        products = get_product_catalog(db)

        return {
            "intent": intent,
            "reply": format_catalog(products),
            "requires_human": False
        }

    if intent == "delivery":
        return {
            "intent": intent,
            "reply": DELIVERY_OPTIONS,
            "requires_human": False
        }

    if intent == "payment":
        return {
            "intent": intent,
            "reply": PAYMENT_OPTIONS,
            "requires_human": False
        }

    if intent == "human_support":
        return {
            "intent": intent,
            "reply": (
                "I'll forward your enquiry to our "
                "customer support team."
            ),
            "requires_human": True
        }

    return {
        "intent": "unknown",
        "reply": (
            "Sorry, I couldn't understand your question. "
            "Please ask about Ragi Milk prices, products, "
            "delivery or payment."
        ),
        "requires_human": False
    }
