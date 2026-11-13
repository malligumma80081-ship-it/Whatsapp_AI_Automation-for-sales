
import re
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.database.models import (
    Customer,
    Product,
    ConversationSession,
    ConversationMessage,
)
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.message_service import generate_reply
from app.services.order_service import create_order


# --------------------------------------------------
# 1. Conversation Session
# --------------------------------------------------

def get_or_create_session(
    db: Session,
    customer_id: int,
    channel: str,
):
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if not customer:
        raise ValueError("Customer not found.")

    session = (
        db.query(ConversationSession)
        .filter(
            ConversationSession.customer_id == customer_id,
            ConversationSession.channel == channel,
            ConversationSession.is_active.is_(True),
        )
        .order_by(ConversationSession.id.desc())
        .with_for_update()
        .first()
    )

    if session:
        return session

    session = ConversationSession(
        customer_id=customer_id,
        channel=channel,
        state="idle",
        context={},
        is_active=True,
    )

    db.add(session)
    db.flush()

    return session


# --------------------------------------------------
# 2. Save Conversation Message
# --------------------------------------------------

def save_message(
    db: Session,
    session_id: int,
    role: str,
    content: str,
):
    message = ConversationMessage(
        session_id=session_id,
        role=role,
        content=content,
    )

    db.add(message)


# --------------------------------------------------
# 3. Parse Quantity
# --------------------------------------------------

def parse_quantity(message: str) -> int | None:
    match = re.search(r"\b(\d+)\b", message)

    if not match:
        return None

    quantity = int(match.group(1))

    if 1 <= quantity <= 100:
        return quantity

    return None


# --------------------------------------------------
# 4. Parse Product Size
# --------------------------------------------------

def parse_size(message: str) -> str | None:
    text = message.lower().strip()
    text = text.replace(" ", "")

    if "500ml" in text:
        return "500 ml"

    if any(
        value in text
        for value in ("1l", "1litre", "1liter")
    ):
        return "1 litre"

    return None


# --------------------------------------------------
# 5. Find Available Product
# --------------------------------------------------

def find_product_by_size(
    db: Session,
    size: str,
):
    products = (
        db.query(Product)
        .filter(Product.available.is_(True))
        .all()
    )

    def normalize(value: str) -> str:
        value = (
            value.lower()
            .replace(" ", "")
            .replace("liter", "litre")
        )

        if value == "1l":
            return "1litre"

        return value

    requested_size = normalize(size)

    for product in products:
        if normalize(product.size) == requested_size:
            return product

    return None


# --------------------------------------------------
# 6. Create Order From Conversation Context
# --------------------------------------------------

def create_order_from_context(
    db: Session,
    customer_id: int,
    context: dict[str, Any],
):
    product_id = context.get("product_id")
    quantity = context.get("quantity")
    delivery_mode = context.get("delivery_mode")
    payment_method = context.get("payment_method")
    address = context.get("delivery_address")

    if not product_id:
        raise ValueError("Product is missing.")

    if not quantity or not 1 <= int(quantity) <= 100:
        raise ValueError("Invalid quantity.")

    if delivery_mode not in {"home_delivery", "pickup"}:
        raise ValueError("Invalid delivery mode.")

    if payment_method not in {"upi", "cash_on_delivery"}:
        raise ValueError("Invalid payment method.")

    if delivery_mode == "home_delivery" and not address:
        raise ValueError("Delivery address is missing.")

    product = (
        db.query(Product)
        .filter(
            Product.id == int(product_id),
            Product.available.is_(True),
        )
        .first()
    )

    if not product:
        raise ValueError("Product is unavailable.")

    order_data = OrderCreate(
        customer_id=customer_id,
        items=[
            OrderItemCreate(
                product_id=int(product_id),
                quantity=int(quantity),
            )
        ],
        delivery_mode=delivery_mode,
        address=address,
        payment_method=payment_method,
    )

    order = create_order(
        db=db,
        customer_id=customer_id,
        order_data=order_data,
    )

    return order


# --------------------------------------------------
# 7. Order Tool
# --------------------------------------------------

def create_order_tool(
    db: Session,
    customer_id: int,
    product_id: int,
    quantity: int,
    delivery_mode: str,
    payment_method: str,
    address: str | None,
    confirmed: bool,
):
    if confirmed is not True:
        raise PermissionError("Order confirmation required.")

    context = {
        "product_id": product_id,
        "quantity": quantity,
        "delivery_mode": delivery_mode,
        "payment_method": payment_method,
        "delivery_address": address,
    }

    order = create_order_from_context(
        db=db,
        customer_id=customer_id,
        context=context,
    )

    return {
        "order_id": order.id,
        "total_amount": order.total_amount,
    }


# --------------------------------------------------
# 8. Generate Conversation Reply
# --------------------------------------------------

def generate_conversation_reply(
    db: Session,
    customer_id: int,
    channel: str,
    message: str,
):
    text = message.strip()

    if not text:
        raise ValueError("Message cannot be empty.")

    try:
        session = get_or_create_session(
            db=db,
            customer_id=customer_id,
            channel=channel,
        )

        session_id = session.id
        context = dict(session.context or {})
        state = session.state
        lower_text = text.lower()

        save_message(
            db=db,
            session_id=session_id,
            role="user",
            content=text,
        )

        # ------------------------------------------
        # CANCEL ORDER CONVERSATION
        # ------------------------------------------

        if re.search(r"\b(cancel|stop order)\b", lower_text):

            session.state = "idle"
            session.context = {}

            reply = (
                "Your current order conversation has been cancelled."
            )

        # ------------------------------------------
        # START ORDER
        # ------------------------------------------

        elif state == "idle" and re.search(
            r"\b(order|buy|need|want)\b",
            lower_text,
        ):

            quantity = parse_quantity(text)

            if quantity:
                context["quantity"] = quantity

                session.state = "awaiting_size"

                reply = (
                    f"You need {quantity} bottle(s). "
                    "Which size would you prefer: "
                    "500 ml or 1 litre?"
                )

            else:
                session.state = "awaiting_quantity"

                reply = (
                    "How many bottles of Ragi Milk would you like?"
                )

            session.context = context

        # ------------------------------------------
        # GET QUANTITY
        # ------------------------------------------

        elif state == "awaiting_quantity":

            quantity = parse_quantity(text)

            if quantity is None:

                reply = (
                    "Please enter a valid quantity "
                    "between 1 and 100."
                )

            else:
                context["quantity"] = quantity

                session.context = context
                session.state = "awaiting_size"

                reply = (
                    f"Great! {quantity} bottle(s). "
                    "Which size: 500 ml or 1 litre?"
                )

        # ------------------------------------------
        # GET PRODUCT SIZE
        # ------------------------------------------

        elif state == "awaiting_size":

            size = parse_size(text)

            if not size:

                reply = (
                    "Please select either 500 ml or 1 litre."
                )

            else:
                product = find_product_by_size(db, size)

                if not product:

                    reply = (
                        f"Sorry, the {size} product "
                        "is currently unavailable."
                    )

                else:
                    quantity = int(context["quantity"])

                    price = Decimal(str(product.price))
                    total = price * quantity

                    context.update({
                        "product_id": int(product.id),
                        "product_name": product.name,
                        "size": size,
                        "unit_price": str(price),
                        "total_amount": str(total),
                    })

                    session.context = context
                    session.state = "awaiting_delivery"

                    reply = (
                        f"{quantity} × {size} = ₹{total:.2f}.\n"
                        "Would you prefer home delivery or pickup?"
                    )

        # ------------------------------------------
        # GET DELIVERY OPTION
        # ------------------------------------------

        elif state == "awaiting_delivery":

            if lower_text in {
                "home",
                "home delivery",
                "delivery",
            }:

                context["delivery_mode"] = "home_delivery"

                session.state = "awaiting_address"
                session.context = context

                reply = (
                    "Please share your complete delivery address."
                )

            elif lower_text in {
                "pickup",
                "pick up",
                "customer pickup",
            }:

                context["delivery_mode"] = "pickup"

                session.state = "awaiting_payment"
                session.context = context

                reply = (
                    "Customer pickup selected. "
                    "Would you like to pay using UPI "
                    "or Cash on Delivery?"
                )

            else:

                reply = (
                    "Please choose home delivery or pickup."
                )

        # ------------------------------------------
        # GET DELIVERY ADDRESS
        # ------------------------------------------

        elif state == "awaiting_address":

            if len(text) < 8:

                reply = (
                    "Please provide a more complete delivery address."
                )

            else:
                context["delivery_address"] = text

                session.context = context
                session.state = "awaiting_payment"

                reply = (
                    "Address received. "
                    "Would you like to pay using UPI "
                    "or Cash on Delivery?"
                )

        # ------------------------------------------
        # GET PAYMENT METHOD
        # ------------------------------------------

        elif state == "awaiting_payment":

            if lower_text in {"upi", "pay using upi"}:

                selected_method = "upi"

            elif lower_text in {
                "cash",
                "cod",
                "cash on delivery",
            }:

                selected_method = "cash_on_delivery"

            else:

                selected_method = None

            if selected_method is None:

                reply = (
                    "Please select UPI or Cash on Delivery."
                )

            else:
                context["payment_method"] = selected_method

                session.context = context
                session.state = "awaiting_confirmation"

                address = context.get(
                    "delivery_address",
                    "Customer pickup",
                )

                reply = (
                    "Please review your order:\n\n"
                    f"Product: {context['product_name']}\n"
                    f"Size: {context['size']}\n"
                    f"Quantity: {context['quantity']}\n"
                    f"Total: ₹{context['total_amount']}\n"
                    f"Delivery: {context['delivery_mode']}\n"
                    f"Address: {address}\n"
                    f"Payment: {selected_method}\n\n"
                    "Would you like to confirm this order? "
                    "Reply YES or NO."
                )

        # ------------------------------------------
        # CONFIRM ORDER
        # ------------------------------------------

        elif state == "awaiting_confirmation":

            if lower_text in {"yes", "yes confirm", "confirm"}:

                if context.get("order_id"):

                    reply = (
                        f"Your order #{context['order_id']} "
                        "has already been created."
                    )

                else:
                    required_fields = {
                        "product_id",
                        "quantity",
                        "delivery_mode",
                        "payment_method",
                    }

                    if not required_fields.issubset(context):
                        raise ValueError(
                            "Order details are incomplete."
                        )

                    result = create_order_tool(
                        db=db,
                        customer_id=customer_id,
                        product_id=int(context["product_id"]),
                        quantity=int(context["quantity"]),
                        delivery_mode=context["delivery_mode"],
                        payment_method=context["payment_method"],
                        address=context.get("delivery_address"),
                        confirmed=True,
                    )

                    context["order_id"] = result["order_id"]

                    session.context = context
                    session.state = "completed"

                    reply = (
                        f"Order #{result['order_id']} "
                        "placed successfully.\n"
                        f"Total: ₹{result['total_amount']}"
                    )

            elif lower_text in {"no", "no cancel"}:

                session.state = "idle"
                session.context = {}

                reply = (
                    "Your order was not placed. "
                    "You can start again anytime."
                )

            else:

                reply = (
                    "Please reply YES to confirm or NO to cancel."
                )

        # ------------------------------------------
        # COMPLETED ORDER
        # ------------------------------------------

        elif state == "completed":

            if re.search(
                r"\b(order|buy|need|want)\b",
                lower_text,
            ):

                session.state = "awaiting_quantity"
                session.context = {}

                reply = (
                    "Let's start a new order. "
                    "How many bottles would you like?"
                )

            else:

                reply = (
                    "Your previous order conversation is complete. "
                    "Would you like to start a new order?"
                )

        # ------------------------------------------
        # GENERAL AI RESPONSE
        # ------------------------------------------

        else:

            result = generate_reply(text, db)

            reply = result.get(
                "reply",
                "Sorry, I could not understand your message.",
            )

        # ------------------------------------------
        # SAVE ASSISTANT MESSAGE
        # ------------------------------------------

        save_message(
            db=db,
            session_id=session_id,
            role="assistant",
            content=reply,
        )

        db.commit()
        db.refresh(session)

        return {
            "session_id": session.id,
            "state": session.state,
            "reply": reply,
        }

    except Exception:
        db.rollback()
        raise
