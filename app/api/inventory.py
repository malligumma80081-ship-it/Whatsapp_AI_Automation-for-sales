from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth_dependencies import require_admin
from app.database.connection import get_db
from app.schemas.inventory import InventoryUpdate
from app.services.inventory_service import update_stock
from app.database.models import Inventory, StockMovement

router = APIRouter()


@router.get("/")
def list_inventory(db: Session = Depends(get_db)):

    records = db.query(Inventory).all()

    return [
        {
            "product_id": item.product_id,
            "product_name": item.product.product_name,
            "size": item.product.size,
            "stock_quantity": item.stock_quantity,
        }
        for item in records
    ]


@router.put("/{product_id}")
async def set_inventory(
    product_id: str,
    data: InventoryUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):

    try:

        inventory = await update_stock(
            db=db,
            product_id=product_id,
            new_quantity=data.stock_quantity,
            reason=str(getattr(data, "reason", "") or ""),
        )

        return {
            "message": "Inventory updated",
            "product_id": inventory.product_id,
            "stock_quantity": inventory.stock_quantity,
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.get("/movements")
def stock_movement_history(
    db: Session = Depends(get_db),
):

    movements = (
        db.query(StockMovement)
        .order_by(StockMovement.id.desc())
        .limit(100)
        .all()
    )

    return movements