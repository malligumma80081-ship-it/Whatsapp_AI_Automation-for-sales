from sqlalchemy.orm import Session

from app.database.models import (
    Product,
    Inventory,
)
from app.services.cache_service import delete_cache

PRODUCT_CACHE_KEY = "millet:products:catalog"


async def create_product(db: Session, data):

    existing = db.get(
        Product,
        data.product_id,
    )

    if existing:
        raise ValueError("Product already exists")

    product = Product(
        product_id=data.product_id,
        product_name=data.product_name,
        millet_name=data.millet_name,
        size=data.size,
        price=data.price,
        currency="INR",
        available=True,
    )

    try:

        db.add(product)
        db.flush()

        inventory = Inventory(
            product_id=product.product_id,
            stock_quantity=data.initial_stock,
        )

        db.add(inventory)

        if data.initial_stock > 0:
            from app.database.models import StockMovement

            db.add(
                StockMovement(
                    product_id=product.product_id,
                    change_quantity=data.initial_stock,
                    reason="Initial stock",
                )
            )

        db.commit()
        db.refresh(product)
        await delete_cache(PRODUCT_CACHE_KEY)

        return product

    except Exception:
        db.rollback()
        raise


def get_product(db: Session, product_id: str):

    return db.get(Product, product_id)


def search_products(
    db: Session,
    search: str | None = None,
    available: bool | None = None,
    skip: int = 0,
    limit: int = 10,
):

    query = db.query(Product)

    if search:

        query = query.filter(
            Product.product_name.ilike(
                f"%{search}%"
            )
        )

    if available is not None:

        query = query.filter(
            Product.available == available
        )

    total = query.count()

    products = (
        query
        .order_by(Product.product_name)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return products, total


async def update_product(
    db: Session,
    product_id: str,
    data,
):

    product = db.get(Product, product_id)

    if product is None:
        raise ValueError("Product not found")

    changes = data.model_dump(
        exclude_unset=True
    )

    if "product_name" in changes and changes["product_name"] is None:
        raise ValueError("Product name cannot be null")

    if "price" in changes and changes["price"] is None:
        raise ValueError("Price cannot be null")

    for key, value in changes.items():

        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    await delete_cache(PRODUCT_CACHE_KEY)

    return product


async def deactivate_product(
    db: Session,
    product_id: str,
):

    product = db.get(Product, product_id)

    if product is None:
        raise ValueError("Product not found")

    product.available = False

    db.commit()
    db.refresh(product)
    await delete_cache(PRODUCT_CACHE_KEY)

    return product