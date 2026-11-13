import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth_dependencies import require_admin
from app.core.config import settings
from app.core.rate_limiter import rate_limit
from app.database.connection import get_db

from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
    PaymentStatusUpdate,
    TrackingWebhookRequest,
)

from app.services.order_service import (
    create_order,
    get_order_by_id,
    get_all_orders,
    get_customer_orders,
    update_order_status,
    update_payment_status,
)
from app.services.delivery_tracking_service import (
    find_delivery_candidates,
    record_tracking_update,
)

router = APIRouter()


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def place_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
):

    try:

        return create_order(db, data)

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get("/", response_model=list[OrderResponse])
def list_orders(db: Session = Depends(get_db)):

    return get_all_orders(db)


@router.get(
    "/geocode",
    dependencies=[
        Depends(require_admin),
        Depends(rate_limit(1, 1)),
    ],
)
def geocode_delivery_address(
    address: str = Query(min_length=10, max_length=300),
):
    try:
        return find_delivery_candidates(address)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{order_id}", response_model=OrderResponse)
def order_details(
    order_id: int,
    db: Session = Depends(get_db),
):

    order = get_order_by_id(db, order_id)

    if order is None:

        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return order


@router.post("/{order_id}/tracking")
def receive_tracking_update(
    order_id: int,
    data: TrackingWebhookRequest,
    tracking_token: str | None = Header(
        default=None,
        alias="X-Tracking-Token",
    ),
    db: Session = Depends(get_db),
):
    configured_secret = settings.TRACKING_WEBHOOK_SECRET.strip()
    if not configured_secret:
        raise HTTPException(
            status_code=503,
            detail="Delivery tracking webhook is not configured.",
        )
    if tracking_token is None or not hmac.compare_digest(
        tracking_token,
        configured_secret,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid tracking provider credential.",
        )

    try:
        return record_tracking_update(
            db=db,
            order_id=order_id,
            event=data.event,
            latitude=data.latitude,
            longitude=data.longitude,
            recorded_at=data.recorded_at,
        )
    except ValueError as exc:
        status_code = 404 if str(exc) == "Order not found" else 409
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/customer/{customer_id}")
def customer_order_history(
    customer_id: int,
    db: Session = Depends(get_db),
):

    return get_customer_orders(db, customer_id)


@router.api_route(
    "/{order_id}/status",
    methods=["PUT", "PATCH"],
    dependencies=[Depends(require_admin)],
)
def change_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
):
    if data.status == "delivered":
        raise HTTPException(
            status_code=409,
            detail="Delivered status requires a verified provider GPS update.",
        )

    try:

        order = update_order_status(
            db,
            order_id,
            data.status,
        )

        return {
            "message": "Order status updated",
            "order_id": order.id,
            "status": order.status,
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.api_route(
    "/{order_id}/payment",
    methods=["PUT", "PATCH"],
    dependencies=[Depends(require_admin)],
)
def change_payment_status(
    order_id: int,
    data: PaymentStatusUpdate,
    db: Session = Depends(get_db),
):

    try:

        payment = update_payment_status(
            db,
            order_id,
            data.payment_status,
        )

        return {
            "message": "Payment status updated",
            "order_id": order_id,
            "payment_status": payment.payment_status,
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )