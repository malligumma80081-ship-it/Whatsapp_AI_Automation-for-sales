from datetime import datetime, timezone
from math import asin, cos, radians, sin, sqrt
import threading
import time

import httpx
from sqlalchemy.orm import Session

from app.database.models import Order


_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_GEOCODER_LOCK = threading.Lock()
_LAST_GEOCODER_REQUEST = 0.0
DELIVERY_RADIUS_METERS = 150


def find_delivery_candidates(address: str) -> list[dict]:
    global _LAST_GEOCODER_REQUEST

    query = address.strip()
    if len(query) < 10:
        raise ValueError("Enter the full house, street, locality, city, and pincode.")

    with _GEOCODER_LOCK:
        wait_seconds = 1.0 - (time.monotonic() - _LAST_GEOCODER_REQUEST)
        if wait_seconds > 0:
            time.sleep(wait_seconds)

        try:
            response = httpx.get(
                _NOMINATIM_URL,
                params={
                    "q": query,
                    "format": "jsonv2",
                    "addressdetails": 1,
                    "limit": 5,
                    "countrycodes": "in",
                },
                headers={"User-Agent": "MilletMilkSalesAI/1.0"},
                timeout=10,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError("OpenStreetMap address lookup failed.") from exc
        finally:
            _LAST_GEOCODER_REQUEST = time.monotonic()

    candidates = []
    for result in response.json():
        try:
            candidates.append(
                {
                    "display_name": result["display_name"],
                    "latitude": float(result["lat"]),
                    "longitude": float(result["lon"]),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    return candidates


def _utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _distance_meters(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    earth_radius_meters = 6_371_000
    delta_latitude = radians(latitude_b - latitude_a)
    delta_longitude = radians(longitude_b - longitude_a)
    haversine = (
        sin(delta_latitude / 2) ** 2
        + cos(radians(latitude_a))
        * cos(radians(latitude_b))
        * sin(delta_longitude / 2) ** 2
    )
    return earth_radius_meters * 2 * asin(sqrt(haversine))


def record_tracking_update(
    db: Session,
    order_id: int,
    event: str,
    latitude: float,
    longitude: float,
    recorded_at: datetime,
) -> dict:
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .with_for_update()
        .first()
    )
    if order is None:
        raise ValueError("Order not found")
    if order.status == "cancelled":
        raise ValueError("Cancelled orders cannot receive tracking updates")
    if order.status == "delivered" and event != "delivered":
        raise ValueError("Delivered orders cannot receive new location events")

    update_time = _utc_naive(recorded_at)
    previous_time = order.location_updated_at
    if previous_time is not None and update_time < _utc_naive(previous_time):
        raise ValueError("Tracking update is older than the last recorded location")

    distance_meters = None
    if event == "delivered":
        if order.delivery_latitude is None or order.delivery_longitude is None:
            raise ValueError("Order has no verified delivery destination pin")
        distance_meters = _distance_meters(
            float(latitude),
            float(longitude),
            float(order.delivery_latitude),
            float(order.delivery_longitude),
        )

    order.rider_latitude = latitude
    order.rider_longitude = longitude
    order.location_updated_at = update_time

    if event == "out_for_delivery":
        if order.status not in {"delivered", "cancelled"}:
            order.status = "out_for_delivery"
    elif event == "delivered":
        if distance_meters is not None and distance_meters > DELIVERY_RADIUS_METERS:
            db.commit()
            raise ValueError(
                "Rider is outside the 150-meter delivery confirmation radius"
            )
        order.status = "delivered"
        order.delivered_at = update_time

    db.commit()
    db.refresh(order)
    return {
        "order_id": order.id,
        "status": order.status,
        "rider_latitude": float(order.rider_latitude),
        "rider_longitude": float(order.rider_longitude),
        "location_updated_at": order.location_updated_at,
        "distance_to_destination_meters": distance_meters,
    }