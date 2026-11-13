from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.services.product_cache_service import (
    get_cached_products,
)
from app.services.cache_service import delete_cache
from app.core.redis_client import check_redis

router = APIRouter(prefix="/cache", tags=["Redis Cache"])

def get_db(): 
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/products")
async def cached_products(db: Session = Depends(get_db)):
    return await get_cached_products(db)

@router.delete("/products")
async def clear_product_cache():
    deleted = await delete_cache("millet:products:catalog")

    return {
        "success": True,
        "cache_deleted": deleted,
    }

@router.get("/health")
async def redis_health():
    try:
        await check_redis()
        return {"redis": "connected"}
    except Exception:
        return {"redis": "unavailable"}
