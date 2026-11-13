from decimal import Decimal
from typing import cast
from sqlalchemy import update
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session, selectinload

from app.database.models import (
    Customer,
    Product,
    Inventory,
    Order,
    OrderItem,
    Payment,
    StockMovement,
)
from app.schemas import order


def create_order(db: Session, order_data):

    try:

        # 1. Validate customer

        customer = db.get(
            Customer,
            order_data.customer_id,
        )

        if customer is None:
            raise ValueError("Customer not found")

        # 2. Validate delivery address

        if (
            order_data.delivery_mode == "home_delivery"
            and not order_data.delivery_address
        ):
            raise ValueError("Delivery address required")

        total_amount = Decimal("0.00")

        order_items = []
        movement_records = []

        # 3. Start order processing

        for item in order_data.items:

            product = db.get(
                Product,
                item.product_id,
            )

            if product is None:
                raise ValueError(
                    f"Product {item.product_id} not found"
                )

            if not product.available:
                raise ValueError(
                    f"{product.product_name} is unavailable"
                )

            # 4. Calculate using database price

            quantity = item.quantity

            unit_price = product.price

            subtotal = unit_price * quantity

            total_amount += subtotal

            # 5. Atomically reserve inventory

            stock_update = cast(
                CursorResult,
                db.execute(
                    update(Inventory)
                    .where(
                        Inventory.product_id == product.product_id,
                        Inventory.stock_quantity >= quantity,
                    )
                    .values(
                        stock_quantity=(
                            Inventory.stock_quantity - quantity
                        )
                    )
                ),
            )

            if stock_update.rowcount != 1:
                raise ValueError(
                    f"Insufficient stock for {product.size}"
                )

            order_items.append(
                OrderItem(
                    product_id=product.product_id,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=subtotal,
                )
            )

            movement = StockMovement(
                product_id=product.product_id,
                change_quantity=-quantity,
                reason="Customer order",
            )
            db.add(movement)
            movement_records.append(movement)

        # 6. Create order

        order = Order(
            customer_id=customer.id,
            total_amount=total_amount,
            delivery_mode=order_data.delivery_mode,
            delivery_address=order_data.delivery_address,
            delivery_latitude=order_data.delivery_latitude,
            delivery_longitude=order_data.delivery_longitude,
            status="confirmed",
            items=order_items,
        )
        db.add(order)
        db.flush()

        for movement in movement_records:
            movement.reference = f"Order #{order.id}"

        # 7. Create payment record

        payment = Payment(
            order_id=order.id,
            payment_method=order_data.payment_method,
            payment_status="pending",
        )

        db.add(payment)

        # 8. Commit all changes together

        db.commit()

        # 9. Reload order with items

        saved_order = (
            db.query(Order)
            .options(selectinload(Order.items))
            .filter(Order.id == order.id)
            .one()
        )

        return saved_order

    except Exception:

        db.rollback()

        raise


def get_order_by_id(db: Session, order_id: int):

    return (
        db.query(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.payment),
        )
        .filter(Order.id == order_id)
        .first()
    )


def get_all_orders(db: Session):

    return (
        db.query(Order)
        .options(selectinload(Order.items))
        .order_by(Order.id.desc())
        .all()
    )


def get_customer_orders(
    db: Session,
    customer_id: int,
):

    return (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.customer_id == customer_id)
        .order_by(Order.id.desc())
        .all()
    )


def update_order_status(
    db: Session,
    order_id: int,
    new_status: str,
):

    try:

        order = (
            db.query(Order)
            .options(selectinload(Order.items))
            .filter(Order.id == order_id)
            .with_for_update()
            .first()
        )

        if order is None:
            raise ValueError("Order not found")

        if order.status in ["cancelled", "delivered"]:
            raise ValueError(
                "This order cannot be modified"
            )

        if new_status == "cancelled":

            # Restore stock when an order is cancelled.

            for item in order.items:

                inventory = (
                    db.query(Inventory)
                    .filter(
                        Inventory.product_id == item.product_id
                    )
                    .with_for_update()
                    .first()
                )

                if inventory is None:
                    raise ValueError(
                        "Inventory record not found"
                    )

                inventory.stock_quantity += item.quantity
                db.add(
                    StockMovement(
                        product_id=item.product_id,
                        change_quantity=item.quantity,
                        reason="Order cancelled",
                        reference=f"Order #{order.id}",
                    )
                )

        order.status = new_status

        db.commit()

        db.refresh(order)

        return order

    except Exception:

        db.rollback()

        raise


def update_payment_status(
    db: Session,
    order_id: int,
    new_status: str,
):

    payment = (
        db.query(Payment)
        .filter(Payment.order_id == order_id)
        .first()
    )

    if payment is None:
        raise ValueError("Payment record not found")

    if payment.payment_status in ["paid", "refunded"]:
        raise ValueError(
            "Payment status cannot be changed from this state"
        )

    if new_status == "refunded":
        raise ValueError(
            "Refund processing requires a verified payment "
            "and refund workflow"
        )

    if new_status == "paid" and payment.payment_method == "upi":
        raise ValueError(
            "UPI payment must be verified through a payment "
            "provider before marking it paid"
        )

    payment.payment_status = new_status

    db.commit()

    db.refresh(payment)

    return payment