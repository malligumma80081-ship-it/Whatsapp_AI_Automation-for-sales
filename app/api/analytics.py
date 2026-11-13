from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.services.analytics_service import (
    get_sales_summary,
    get_customer_summary,
    get_product_sales,
)


router = APIRouter()


@router.get("/sales")
def sales_report(
    db: Session = Depends(get_db),
):

    return get_sales_summary(db)


@router.get("/customers")
def customer_report(
    db: Session = Depends(get_db),
):

    return get_customer_summary(db)


@router.get("/top-products")
def top_products(
    db: Session = Depends(get_db),
):

    return get_product_sales(db)