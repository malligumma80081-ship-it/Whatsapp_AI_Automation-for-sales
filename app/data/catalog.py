from decimal import Decimal
from dataclasses import dataclass


@dataclass
class Product:
    product_id: str
    product_name: str
    millet_name: str
    size: str
    price: Decimal
    currency: str
    available: bool


PRODUCTS = [
    Product(
        product_id="RAGI500",
        product_name="Ragi Milk",
        millet_name="Ragi",
        size="500 ml",
        price=Decimal("45.00"),
        currency="INR",
        available=True,
    ),

    Product(
        product_id="RAGI1000",
        product_name="Ragi Milk",
        millet_name="Ragi",
        size="1 litre",
        price=Decimal("72.00"),
        currency="INR",
        available=True,
    ),
]


def get_all_products():
    return PRODUCTS


def get_product_by_id(product_id: str):

    for product in PRODUCTS:

        if product.product_id == product_id:
            return product

    return None