from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth_dependencies import require_admin
from app.database.connection import get_db
from app.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
)
from app.services.customer_service import (
    delete_customer,
    create_customer,
    get_customer_by_id,
    get_customer_by_phone,
    get_all_customers,
    update_customer,
)

router = APIRouter()


@router.post(
    "/",
    response_model=CustomerResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def register_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
):

    try:
        return create_customer(db, data)

    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/", response_model=list[CustomerResponse])
def list_customers(db: Session = Depends(get_db)):

    return get_all_customers(db)


@router.get("/{customer_id}", response_model=CustomerResponse)
def customer_details(
    customer_id: int,
    db: Session = Depends(get_db),
):

    customer = get_customer_by_id(db, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return customer


@router.get("/phone/{phone}", response_model=CustomerResponse)
def find_customer(
    phone: str,
    db: Session = Depends(get_db),
):

    customer = get_customer_by_phone(db, phone)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return customer


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
    dependencies=[Depends(require_admin)],
)
def edit_customer(
    customer_id: int,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
):
    try:
        return update_customer(db, customer_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete(
    "/{customer_id}",
    status_code=204,
    dependencies=[Depends(require_admin)],
)
def remove_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    try:
        delete_customer(db, customer_id)
    except ValueError as exc:
        status_code = 404 if str(exc) == "Customer not found" else 409
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc