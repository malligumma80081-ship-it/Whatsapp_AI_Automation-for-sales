# Delivery Tracking Integration

## Setup

1. Set a unique `TRACKING_WEBHOOK_SECRET` in `.env` and restart FastAPI.
2. Apply the database migration with `alembic upgrade head`.
3. Configure the delivery provider to send HTTPS POST requests to:

   `https://<your-api-host>/api/v1/orders/{order_id}/tracking`

   Send the secret in the `X-Tracking-Token` header. Do not put it in the URL or provider payload.

## Payload

```json
{
  "event": "location",
  "latitude": 17.385044,
  "longitude": 78.486671,
  "recorded_at": "2026-11-13T10:15:00Z"
}
```

Supported events are `location`, `out_for_delivery`, and `delivered`. `recorded_at` must be an ISO 8601 timestamp. The provider should send updates in UTC and use the order ID assigned by this API.

The `delivered` event is accepted only when the order has a confirmed destination pin and the provider's coordinates are within 150 meters of that pin. The latest rider location is stored even when a delivery confirmation is outside the radius; that request receives HTTP 409 and the order is not marked delivered. Cancelled orders reject updates, and older timestamps are rejected.

## Destination Pins

For dashboard-created home-delivery orders, enter the house/flat number, street, locality, city, and six-digit PIN code. Resolve the address, inspect the OpenStreetMap candidates, and select the result that actually matches the home before placing the order. The public OpenStreetMap geocoder is best-effort; do not assume an ambiguous result is correct. OpenStreetMap attribution is shown in the dashboard.

The Orders page polls the latest provider location every five seconds while the live tracking panel is open. Existing orders without destination coordinates can show rider locations but cannot be automatically confirmed as delivered.
