from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
)

from app.services.product_service import (
    create_product as create_product_service,
    get_product,
    search_products,
    update_product,
    deactivate_product,
)
from fastapi import Depends
from app.core.auth_dependencies import require_admin

router = APIRouter()

@router.post(
    "/",
    response_model=ProductResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def add_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
):

    try:
        return await create_product_service(db, data)

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )


@router.get("/")
def list_products(
    search: str | None = None,
    available: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):

    products, total = search_products(
        db=db,
        search=search,
        available=available,
        skip=(page - 1) * page_size,
        limit=page_size,
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "products": products,
    }


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def product_details(
    product_id: str,
    db: Session = Depends(get_db),
):

    product = get_product(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(require_admin)],
)
async def edit_product(
    product_id: str,
    data: ProductUpdate,
    db: Session = Depends(get_db),
):

    try:
        return await update_product(
            db,
            product_id,
            data,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.delete(
    "/{product_id}",
    dependencies=[Depends(require_admin)],
)
async def remove_product(
    product_id: str,
    db: Session = Depends(get_db),
):

    try:

        product = await deactivate_product(
            db,
            product_id,
        )

        return {
            "message": "Product deactivated",
            "product_id": product.product_id,
            "available": product.available,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )