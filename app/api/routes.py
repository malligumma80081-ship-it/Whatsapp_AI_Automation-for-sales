from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.database.models import Product, Customer

from app.schemas.product import ProductResponse


router = APIRouter()


@router.get("/business")
def get_business_details():

    return {
        "business_name": "Millet Milk Sales",
        "business_type": "Millet Milk Sales",
        "main_product": "Ragi Milk",
        "delivery_modes": [
            "home_delivery",
            "pickup",
        ],
        "payment_modes": [
            "cash_on_delivery",
            "upi",
        ],
    }


@router.get(
    "/products",
    response_model=list[ProductResponse],
)
def get_products(db: Session = Depends(get_db)):

    products = db.query(Product).all()

    return products


@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
):

    product = db.get(Product, product_id)

    if product is None:

        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product


@router.post("/customers")
def create_customer(
    customer_data: dict,
    db: Session = Depends(get_db),
):

    name = customer_data.get("name")
    phone = customer_data.get("phone")

    if not name or not phone:

        raise HTTPException(
            status_code=400,
            detail="Name and phone are required",
        )

    existing = db.query(Customer).filter(
        Customer.phone == phone
    ).first()

    if existing:

        raise HTTPException(
            status_code=409,
            detail="Customer already exists",
        )

    customer = Customer(
        name=name,
        phone=phone,
        address=customer_data.get("address"),
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return {
        "message": "Customer created successfully",
        "customer_id": customer.id,
        "name": customer.name,
    }