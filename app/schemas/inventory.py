from sqlalchemy.orm import Session

from app.database.models import (
    Inventory,
    Product,
    StockMovement,
)

def get_inventory(db: Session):

    return (
        db.query(Inventory)
        .join(Product)
        .order_by(Product.product_name)
        .all()
    )

def update_stock(
    db: Session,
    product_id: str,
    new_quantity: int,
    reason: str,
):

    if new_quantity < 0:
        raise ValueError("Stock cannot be negative")

    try:

        product = db.get(Product, product_id)

        if product is None:
            raise ValueError("Product not found")

        inventory = (
            db.query(Inventory)
            .filter(
                Inventory.product_id == product_id
            )
            .with_for_update()
            .first()
        )

        if inventory is None:

            inventory = Inventory(
                product_id=product_id,
                stock_quantity=0,
            )

            db.add(inventory)
            db.flush()

        old_quantity = inventory.stock_quantity

        difference = new_quantity - old_quantity

        inventory.stock_quantity = new_quantity

        if difference != 0:

            movement = StockMovement(
                product_id=product_id,
                change_quantity=difference,
                reason=reason,
            )

            db.add(movement)

        db.commit()
        db.refresh(inventory)

        return inventory

    except Exception:
        db.rollback()
        raise

from pydantic import BaseModel, Field

class InventoryUpdate(BaseModel):

    stock_quantity: int = Field(ge=0)

    reason: str = Field(
        min_length=3,
        max_length=100,
    )    