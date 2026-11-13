from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models import Product
from app.services.cache_service import (
    get_cache,
    set_cache,
)

PRODUCT_CACHE_KEY = "millet:products:catalog"

async def get_cached_products(db: Session):
    cached_products = get_cache(PRODUCT_CACHE_KEY)

    if cached_products is not None:
        return {
            "source": "redis",
            "products": cached_products,
        }

    products = db.execute(select(Product)).scalars().all()

    result = [
        {
            "product_id": str(getattr(product, "id")),
            "name": getattr(product, "name"),
            "size": product.size,
            "price": str(product.price),
        }
        for product in products
    ]

    await set_cache(
        PRODUCT_CACHE_KEY,
        result,
        ttl=getattr(settings, "REDIS_CACHE_TTL", 300),
    )

    return {
        "source": "database",
        "products": result,
    }