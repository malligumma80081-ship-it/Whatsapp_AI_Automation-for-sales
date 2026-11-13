from decimal import Decimal

from app.database.connection import SessionLocal

from app.database.models import Product, Inventory


INITIAL_PRODUCTS = [
    {
        "product_id": "RAGI500",
        "product_name": "Ragi Milk",
        "millet_name": "Ragi",
        "size": "500 ml",
        "price": Decimal("45.00"),
    },
    {
        "product_id": "RAGI1000",
        "product_name": "Ragi Milk",
        "millet_name": "Ragi",
        "size": "1 litre",
        "price": Decimal("72.00"),
    },
]


def seed_products():

    db = SessionLocal()

    try:

        for item in INITIAL_PRODUCTS:

            product = db.get(
                Product,
                item["product_id"],
            )

            if product is None:

                product = Product(
                    **item,
                    currency="INR",
                    available=True,
                )

                db.add(product)

                db.flush()

                inventory = Inventory(
                    product_id=product.product_id,
                    stock_quantity=0,
                )

                db.add(inventory)

        db.commit()

        print("Products inserted successfully!")

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    seed_products()