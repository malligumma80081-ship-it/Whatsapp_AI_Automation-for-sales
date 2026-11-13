from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    Product,
    Inventory,
    Order,
    OrderItem,
)

def get_products(db: Session):
    products = db.scalars(
        select(Product).where(Product.available.is_(True))
    ).all()

    return [
        {
            "product_id": str(getattr(product, "id")),
            "name": getattr(product, "name"),
            "size": product.size,
            "price": str(product.price),
        }
        for product in products
    ]

def check_inventory(db: Session, product_id: str):
    product = db.get(Product, product_id)

    if not product or not product.available:
        return {"available": False, "stock": 0}

    inventory = db.scalar(
        select(Inventory).where(
            Inventory.product_id == product_id
        )
    )

    stock = inventory.stock_quantity if inventory else 0

    return {
        "product_id": str(getattr(product, "id")),
        "product_name": getattr(product, "name"),
        "available": stock > 0,
        "stock": stock,
    }

def calculate_order(
    db: Session,
    product_id: str,
    quantity: int,
):
    if quantity < 1 or quantity > 100:
        raise ValueError("Quantity must be between 1 and 100.")

    product = db.get(Product, product_id)

    if not product or not product.available:
        raise ValueError("Product is not available.")

    inventory_result = check_inventory(db, product_id)

    if inventory_result["stock"] < quantity:
        raise ValueError("Insufficient stock.")

    unit_price = Decimal(str(product.price))
    total = unit_price * quantity

    return {
        "product_id": str(getattr(product, "id")),
        "product_name": getattr(product, "name"),
        "quantity": quantity,
        "unit_price": str(unit_price),
        "total": str(total),
        "currency": "INR",
    }

def get_order_status(db: Session, order_id: int):
    order = db.get(Order, order_id)

    if not order:
        raise ValueError("Order not found.")

    return {
        "order_id": order.id,
        "status": order.status,
        "total_amount": str(order.total_amount),
    }
def execute_tool(
    db: Session,
    tool_name: str,
    arguments: dict,
    confirmed: bool = False,
):
    if tool_name == "get_products":
        return get_products(db)

    if tool_name == "check_inventory":
        product_id = arguments.get("product_id")

        if not product_id:
            raise ValueError("product_id is required.")

        return check_inventory(db, str(product_id))

    if tool_name == "calculate_order":
        return calculate_order(
            db=db,
            product_id=str(arguments["product_id"]),
            quantity=int(arguments["quantity"]),
        )

    if tool_name == "get_order_status":
        return get_order_status(
            db=db,
            order_id=int(arguments["order_id"]),
        )

    if tool_name == "create_order":
        if not confirmed:
            raise PermissionError(
                "Customer confirmation is required before creating an order."
            )

        raise NotImplementedError(
            "Connect this tool to the existing Day 3 order service "
            "using the confirmation adapter below."
        )

    raise ValueError("Unsupported tool.")