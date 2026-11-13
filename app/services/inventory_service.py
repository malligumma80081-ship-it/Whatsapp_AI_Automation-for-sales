import logging
from typing import Any

from sqlalchemy.orm import Session

from app.database.models import Inventory, Product, StockMovement
from app.services.cache_service import delete_cache, delete_cache_pattern

logger = logging.getLogger(__name__)

PRODUCT_CACHE_KEY = "millet:products:catalog"
INVENTORY_CACHE_PATTERN = "millet:inventory:*"


async def save_inventory_change(
    db: Session,
    inventory_record: Any,
) -> Any:
    """Commit a prepared inventory record change and invalidate related caches."""
    try:
        db.add(inventory_record)
        db.commit()
        db.refresh(inventory_record)
    except Exception:
        db.rollback()
        raise

    # The database commit succeeded; cache failures should not undo the change.
    try:
        await delete_cache(PRODUCT_CACHE_KEY)
        await delete_cache_pattern(INVENTORY_CACHE_PATTERN)
    except Exception:
        logger.exception("Inventory saved, but cache invalidation failed")

    return inventory_record


async def update_stock(
    db: Session,
    product_id: str,
    new_quantity: int,
    reason: str,
) -> Inventory:
    if new_quantity < 0:
        raise ValueError("Stock cannot be negative")

    try:
        product = db.get(Product, product_id)
        if product is None:
            raise ValueError("Product not found")

        inventory = (
            db.query(Inventory)
            .filter(Inventory.product_id == product_id)
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

        difference = new_quantity - inventory.stock_quantity
        inventory.stock_quantity = new_quantity

        if difference:
            db.add(
                StockMovement(
                    product_id=product_id,
                    change_quantity=difference,
                    reason=reason,
                )
            )

        db.commit()
        db.refresh(inventory)

    except Exception:
        db.rollback()
        raise

    try:
        await delete_cache(PRODUCT_CACHE_KEY)
        await delete_cache_pattern(INVENTORY_CACHE_PATTERN)
    except Exception:
        logger.exception("Stock updated, but cache invalidation failed")

    return inventory