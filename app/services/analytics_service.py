from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.models import (
    Order,
    OrderItem,
    Customer,
    Product,
)


def get_sales_summary(db: Session):

    total_orders = (
        db.query(func.count(Order.id))
        .filter(Order.status != "cancelled")
        .scalar()
    ) or 0

    total_revenue = (
        db.query(func.sum(Order.total_amount))
        .filter(Order.status != "cancelled")
        .scalar()
    ) or 0

    delivered_orders = (
        db.query(func.count(Order.id))
        .filter(Order.status == "delivered")
        .scalar()
    ) or 0

    pending_orders = (
        db.query(func.count(Order.id))
        .filter(
            Order.status.in_([
                "pending",
                "confirmed",
                "preparing",
            ])
        )
        .scalar()
    ) or 0

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "delivered_orders": delivered_orders,
        "pending_orders": pending_orders,
        "currency": "INR",
    }


def get_customer_summary(db: Session):

    total_customers = (
        db.query(func.count(Customer.id))
        .scalar()
    ) or 0

    purchasing_customers = (
        db.query(
            func.count(
                func.distinct(Order.customer_id)
            )
        )
        .filter(Order.status != "cancelled")
        .scalar()
    ) or 0

    repeat_customers = (
        db.query(Order.customer_id)
        .filter(Order.status != "cancelled")
        .group_by(Order.customer_id)
        .having(func.count(Order.id) >= 2)
        .count()
    )

    return {
        "total_customers": total_customers,
        "purchasing_customers": purchasing_customers,
        "repeat_customers": repeat_customers,
    }


def get_product_sales(db: Session):

    results = (
        db.query(
            Product.product_id,
            Product.product_name,
            Product.size,
            func.sum(OrderItem.quantity).label(
                "units_sold"
            ),
            func.sum(OrderItem.subtotal).label(
                "revenue"
            ),
        )
        .join(
            OrderItem,
            Product.product_id == OrderItem.product_id,
        )
        .join(
            Order,
            OrderItem.order_id == Order.id,
        )
        .filter(Order.status != "cancelled")
        .group_by(
            Product.product_id,
            Product.product_name,
            Product.size,
        )
        .order_by(
            func.sum(OrderItem.quantity).desc()
        )
        .all()
    )

    return [
        {
            "product_id": row.product_id,
            "product_name": row.product_name,
            "size": row.size,
            "units_sold": row.units_sold,
            "revenue": row.revenue,
        }
        for row in results
    ]