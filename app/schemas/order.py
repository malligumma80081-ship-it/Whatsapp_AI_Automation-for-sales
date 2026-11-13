from decimal import Decimal
from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
    model_validator,
)
from pydantic import BaseModel


class OrderItemCreate(BaseModel):

    product_id: str

    quantity: int = Field(gt=0, le=100)


class OrderCreate(BaseModel):

    customer_id: int

    items: list[OrderItemCreate] = Field(
        min_length=1,
        max_length=20,
    )

    delivery_mode: Literal[
        "home_delivery",
        "pickup",
    ]

    delivery_address: str | None = None

    delivery_latitude: float | None = Field(default=None, ge=-90, le=90)

    delivery_longitude: float | None = Field(default=None, ge=-180, le=180)

    payment_method: Literal[
        "cash_on_delivery",
        "upi",
    ]

    @model_validator(mode="after")
    def validate_order(self):

        product_ids = [
            item.product_id for item in self.items
        ]

        if len(product_ids) != len(set(product_ids)):
            raise ValueError(
                "Duplicate products are not allowed. "
                "Combine quantities into one item."
            )

        if (
            self.delivery_mode == "home_delivery"
            and not self.delivery_address
        ):
            raise ValueError(
                "Delivery address is required "
                "for home delivery."
            )

        if (self.delivery_latitude is None) != (
            self.delivery_longitude is None
        ):
            raise ValueError(
                "Delivery latitude and longitude must be provided together."
            )

        return self


class OrderItemResponse(BaseModel):

    product_id: str

    quantity: int

    unit_price: Decimal

    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):

    id: int

    customer_id: int

    total_amount: Decimal

    delivery_mode: str

    delivery_address: str | None

    delivery_latitude: Decimal | None = None

    delivery_longitude: Decimal | None = None

    rider_latitude: Decimal | None = None

    rider_longitude: Decimal | None = None

    location_updated_at: datetime | None = None

    delivered_at: datetime | None = None

    status: str

    items: list[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):

    status: Literal[
        "confirmed",
        "preparing",
        "out_for_delivery",
        "delivered",
        "cancelled",
    ]


class PaymentStatusUpdate(BaseModel):

    payment_status: Literal[
        "pending",
        "paid",
        "failed",
        "refunded",
    ]


class TrackingWebhookRequest(BaseModel):
    event: Literal["location", "out_for_delivery", "delivered"]
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    recorded_at: datetime

    @field_validator("recorded_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("recorded_at must include a timezone")
        return value


class InventoryUpdate(BaseModel):

    stock_quantity: int = Field(ge=0)

class OrderConfirmationResponse(BaseModel):
    order_id: int
    total_amount: str
    order_status: str
    payment_status: str
    message: str    