from sqlalchemy.orm import Session

from app.database.models import Customer, Order, User


def create_customer(db: Session, customer_data):

    existing_customer = (
        db.query(Customer)
        .filter(
            Customer.phone == customer_data.phone
        )
        .first()
    )

    if existing_customer:
        raise ValueError("Customer already exists")

    customer = Customer(
        name=customer_data.name,
        phone=customer_data.phone,
        address=customer_data.address,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def get_customer_by_id(db: Session, customer_id: int):

    return db.get(Customer, customer_id)


def get_customer_by_phone(db: Session, phone: str):

    return (
        db.query(Customer)
        .filter(Customer.phone == phone)
        .first()
    )


def get_all_customers(db: Session):

    return db.query(Customer).order_by(
        Customer.id.desc()
    ).all()


def update_customer(db: Session, customer_id: int, data):
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise ValueError("Customer not found")

    changes = data.model_dump(exclude_unset=True)
    for field in ("name", "phone"):
        if field in changes and changes[field] is None:
            raise ValueError(f"{field.title()} cannot be null")

    if "phone" in changes:
        duplicate = (
            db.query(Customer)
            .filter(
                Customer.phone == changes["phone"],
                Customer.id != customer_id,
            )
            .first()
        )
        if duplicate:
            raise ValueError("Phone number is already registered")

    for field, value in changes.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)
    return customer


def delete_customer(db: Session, customer_id: int):
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise ValueError("Customer not found")

    has_orders = (
        db.query(Order.id)
        .filter(Order.customer_id == customer_id)
        .first()
        is not None
    )
    has_user = (
        db.query(User.id)
        .filter(User.customer_id == customer_id)
        .first()
        is not None
    )
    if has_orders or has_user:
        raise ValueError(
            "Customer has linked orders or an account and cannot be deleted"
        )

    db.delete(customer)
    db.commit()