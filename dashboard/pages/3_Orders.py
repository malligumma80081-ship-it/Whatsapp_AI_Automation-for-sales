from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve()
for candidate in (PROJECT_ROOT.parent, *PROJECT_ROOT.parents):
    if (candidate / "requirements.txt").exists():
        PROJECT_ROOT = candidate
        break
else:
    PROJECT_ROOT = PROJECT_ROOT.parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

from dashboard.api_client import APIClient

st.set_page_config(page_title="Orders", layout="wide")

if not st.session_state.get("logged_in"):
    st.error("Please log in from the main dashboard.")
    st.stop()

client = APIClient(st.session_state["token"])

st.title("Order Management")

try:
    orders = client.get("/orders/") or []
    if orders:
        order_rows = []
        for order in orders:
            row = {key: value for key, value in order.items() if key != "items"}
            row["items"] = ", ".join(
                f"{item['product_id']} × {item['quantity']}"
                for item in order.get("items", [])
            )
            order_rows.append(row)
        st.dataframe(pd.DataFrame(order_rows), use_container_width=True)
    else:
        st.info("No orders available.")

except Exception as exc:
    st.error(str(exc))
    orders = []

st.divider()
st.subheader("Create Order")

try:
    customers = client.get("/customers/") or []
    product_response = client.get(
        "/products/",
        params={"page_size": 100},
    ) or {}
    products = (
        product_response.get("products", [])
        if isinstance(product_response, dict)
        else product_response
    )
except Exception as exc:
    st.error(str(exc))
    customers = []
    products = []

available_products = [product for product in products if product.get("available")]
if customers and available_products:
    customer_by_id = {customer["id"]: customer for customer in customers}
    product_by_id = {product["product_id"]: product for product in available_products}

    delivery_mode = st.radio(
        "Delivery Mode",
        ["home_delivery", "pickup"],
        horizontal=True,
        format_func=lambda value: value.replace("_", " ").title(),
    ) or "pickup"
    delivery_address = None
    destination_pin = None

    if delivery_mode == "home_delivery":
        st.subheader("Delivery Address and Pin")
        with st.form("resolve_delivery_address"):
            address_col1, address_col2 = st.columns(2)
            with address_col1:
                house_number = st.text_input(
                    "House / Flat Number",
                    key="delivery_house_number",
                )
                street = st.text_input(
                    "Street / Road",
                    key="delivery_street",
                )
                locality = st.text_input(
                    "Area / Locality",
                    key="delivery_locality",
                )
            with address_col2:
                city = st.text_input("City", key="delivery_city")
                pincode = st.text_input(
                    "6-digit PIN code",
                    max_chars=6,
                    key="delivery_pincode",
                )
            resolve_submitted = st.form_submit_button("Find Address Pin")

        house_number = (house_number or "").strip()
        street = (street or "").strip()
        locality = (locality or "").strip()
        city = (city or "").strip()
        pincode = (pincode or "").strip()
        entered_address = ", ".join(
            value
            for value in (house_number, street, locality, city, pincode, "India")
            if value
        )
        if (
            st.session_state.get("resolved_delivery_address")
            != entered_address
        ):
            st.session_state.pop("resolved_delivery_address", None)
            st.session_state.pop("delivery_candidates", None)

        if resolve_submitted:
            if not all((house_number.strip(), street.strip(), locality.strip(), city.strip())):
                st.error("Enter the house number, street, area, and city.")
            elif len(pincode) != 6 or not pincode.isdigit():
                st.error("Enter a valid 6-digit PIN code.")
            else:
                try:
                    candidate_response = client.get(
                        "/orders/geocode",
                        params={"address": entered_address},
                    )
                    st.session_state["resolved_delivery_address"] = entered_address
                    st.session_state["delivery_candidates"] = candidate_response or []
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        candidate_response = st.session_state.get("delivery_candidates") or []
        candidates: list[dict[str, str | float]] = []
        for candidate in candidate_response:
            if not isinstance(candidate, dict):
                continue
            display_name = candidate.get("display_name")
            latitude = candidate.get("latitude")
            longitude = candidate.get("longitude")
            if (
                isinstance(display_name, str)
                and isinstance(latitude, (int, float))
                and isinstance(longitude, (int, float))
            ):
                candidates.append(
                    {
                        "display_name": display_name,
                        "latitude": float(latitude),
                        "longitude": float(longitude),
                    }
                )
        if candidates and st.session_state.get("resolved_delivery_address") == entered_address:
            destination_pin = st.selectbox(
                "Choose and confirm the matching map result",
                candidates,
                format_func=lambda candidate: str(candidate["display_name"])
                if candidate is not None
                else "Select a map result",
            )
            if destination_pin is not None:
                delivery_address = st.session_state["resolved_delivery_address"]
                st.caption(
                    f"Selected pin: {destination_pin['latitude']:.6f}, "
                    f"{destination_pin['longitude']:.6f}. Verify it matches the home."
                )
                latitude = float(destination_pin["latitude"])
                longitude = float(destination_pin["longitude"])
                map_url = (
                    "https://www.openstreetmap.org/export/embed.html?"
                    f"bbox={longitude - 0.003},{latitude - 0.003},"
                    f"{longitude + 0.003},{latitude + 0.003}"
                    f"&layer=mapnik&marker={latitude},{longitude}"
                )
                components.iframe(map_url, height=320, scrolling=False)
                st.caption("Map data and geocoding © OpenStreetMap contributors.")
        elif st.session_state.get("delivery_candidates") == [] and st.session_state.get(
            "resolved_delivery_address"
        ) == entered_address:
            st.warning("No map result was found. Check the address and PIN code.")

    with st.form("create_order"):
        customer_id = st.selectbox(
            "Customer",
            list(customer_by_id),
            format_func=lambda value: (
                f"{customer_by_id[value]['name']} · "
                f"{customer_by_id[value]['phone']}"
            ),
        )
        product_id = st.selectbox(
            "Product",
            list(product_by_id),
            format_func=lambda value: (
                f"{product_by_id[value]['product_name']} "
                f"({value})"
            ),
        )
        quantity = st.number_input("Quantity", min_value=1, max_value=100, step=1)
        payment_method = st.selectbox(
            "Payment Method",
            ["cash_on_delivery", "upi"],
            format_func=lambda value: value.replace("_", " ").title(),
        )
        create_submitted = st.form_submit_button("Place Order")

    if create_submitted:
        if customer_id is None:
            st.error("Select a customer before placing the order.")
        elif delivery_mode == "home_delivery" and not destination_pin:
            st.error("Find and confirm the delivery pin before placing this order.")
        else:
            resolved_latitude = (
                destination_pin["latitude"]
                if destination_pin is not None
                else None
            )
            resolved_longitude = (
                destination_pin["longitude"]
                if destination_pin is not None
                else None
            )
            try:
                result = client.post(
                    "/orders/",
                    {
                        "customer_id": int(customer_id),
                        "items": [
                            {
                                "product_id": product_id,
                                "quantity": int(quantity),
                            }
                        ],
                        "delivery_mode": delivery_mode,
                        "delivery_address": (
                            delivery_address
                            if destination_pin
                            else None
                        ),
                        "delivery_latitude": resolved_latitude,
                        "delivery_longitude": resolved_longitude,
                        "payment_method": payment_method,
                    },
                )
                if not result:
                    raise RuntimeError("The API returned no order details.")
                st.success(f"Order #{result['id']} created.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
else:
    st.info("Register a customer and add available stock before placing an order.")

if orders:
    order_ids = [order["id"] for order in orders]
    mutable_order_ids = [
        order["id"]
        for order in orders
        if order["status"] not in {"cancelled", "delivered"}
    ]
    st.divider()
    st.subheader("Update Order")

    if mutable_order_ids:
        with st.form("update_order_status"):
            status_order_id = st.selectbox(
                "Order",
                mutable_order_ids,
                key="status_order_id",
            )
            status = st.selectbox(
                "New Status",
                ["confirmed", "preparing", "out_for_delivery"],
            )
            status_submitted = st.form_submit_button("Update Status")

        if status_submitted:
            if status_order_id is None:
                st.error("Select an order to update.")
            else:
                try:
                    client.patch(
                        f"/orders/{int(status_order_id)}/status",
                        {"status": status},
                    )
                    st.success("Order status updated.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
    else:
        st.info("There are no active orders to update or cancel.")

    with st.form("update_payment_status"):
        payment_order_id = st.selectbox("Payment Order", order_ids)
        payment_status = st.selectbox(
            "Payment Status",
            ["pending", "paid", "failed"],
        )
        payment_submitted = st.form_submit_button("Update Payment")

    if payment_submitted:
        if payment_order_id is None:
            st.error("Select an order to update.")
        else:
            try:
                client.patch(
                    f"/orders/{int(payment_order_id)}/payment",
                    {"payment_status": payment_status},
                )
                st.success("Payment status updated.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    if mutable_order_ids:
        with st.form("cancel_order"):
            cancel_order_id = st.selectbox(
                "Order to Cancel",
                mutable_order_ids,
            )
            confirm_cancel = st.checkbox("Confirm order cancellation")
            cancel_submitted = st.form_submit_button("Cancel Order")

        if cancel_submitted:
            if not confirm_cancel:
                st.error("Confirm cancellation before continuing.")
            elif cancel_order_id is None:
                st.error("Select an order to cancel.")
            else:
                try:
                    client.patch(
                        f"/orders/{int(cancel_order_id)}/status",
                        {"status": "cancelled"},
                    )
                    st.success("Order cancelled and stock restored.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

trackable_order_ids = [
    order["id"]
    for order in orders
]

if trackable_order_ids:
    st.divider()
    st.subheader("Live Delivery Tracking")

    @st.fragment(run_every="5s")
    def show_live_tracking():
        tracked_order_id = st.selectbox(
            "Tracked Order",
            trackable_order_ids,
            key="tracked_order_id",
        )
        try:
            tracked_order = client.get(f"/orders/{tracked_order_id}") or {}
        except Exception as exc:
            st.error(str(exc))
            return
        if not tracked_order:
            st.info("Order tracking is not available yet.")
            return

        rider_lat = tracked_order.get("rider_latitude")
        rider_lon = tracked_order.get("rider_longitude")
        destination_lat = tracked_order.get("delivery_latitude")
        destination_lon = tracked_order.get("delivery_longitude")

        st.write(f"Status: **{tracked_order['status'].replace('_', ' ').title()}**")
        if tracked_order.get("location_updated_at"):
            st.caption(f"Last provider update: {tracked_order['location_updated_at']}")

        if rider_lat is None or rider_lon is None:
            st.info("Waiting for a location update from the delivery provider.")
            return

        rider_lat = float(rider_lat)
        rider_lon = float(rider_lon)
        st.caption(f"Rider: {rider_lat:.6f}, {rider_lon:.6f}")
        rider_map = (
            "https://www.openstreetmap.org/export/embed.html?"
            f"bbox={rider_lon - 0.005},{rider_lat - 0.005},"
            f"{rider_lon + 0.005},{rider_lat + 0.005}"
            f"&layer=mapnik&marker={rider_lat},{rider_lon}"
        )
        components.iframe(rider_map, height=360, scrolling=False)

        if destination_lat is not None and destination_lon is not None:
            destination_lat = float(destination_lat)
            destination_lon = float(destination_lon)
            st.caption(
                f"Delivery pin: {destination_lat:.6f}, {destination_lon:.6f}"
            )
            st.markdown(
                "[Open delivery pin in OpenStreetMap]"
                f"(https://www.openstreetmap.org/?mlat={destination_lat}"
                f"&mlon={destination_lon}#map=18/{destination_lat}/{destination_lon})"
            )

    show_live_tracking()