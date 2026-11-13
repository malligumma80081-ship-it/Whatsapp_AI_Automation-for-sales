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

from dashboard.api_client import APIClient

st.set_page_config(page_title="Inventory", layout="wide")

if not st.session_state.get("logged_in"):
    st.error("Please log in from the main dashboard.")
    st.stop()

client = APIClient(st.session_state["token"])

st.title("Inventory Management")

try:
    inventory = client.get("/inventory/")
    if inventory:
        st.dataframe(pd.DataFrame(inventory), use_container_width=True)
    else:
        st.info("No inventory records yet.")

except Exception as exc:
    st.error(str(exc))
    inventory = []

try:
    product_response = client.get(
        "/products/",
        params={"page_size": 100},
    )
    if isinstance(product_response, dict):
        products = product_response.get("products", [])
    else:
        products = product_response or []
except Exception as exc:
    st.error(str(exc))
    products = []

st.divider()
st.subheader("Create or Update Stock")

if products:
    stock_by_product = {
        item["product_id"]: item["stock_quantity"]
        for item in inventory
    }
    product_ids = [product["product_id"] for product in products]
    with st.form("stock_update"):
        product_id = st.selectbox("Product", product_ids)
        stock = st.number_input(
            "Stock Quantity",
            min_value=0,
            value=int(stock_by_product.get(product_id, 0)),
            step=1,
            key=f"stock_quantity_{product_id}",
        )
        reason = st.text_input(
            "Adjustment Reason",
            value="Stock correction",
            max_chars=100,
        )
        submitted = st.form_submit_button("Save Stock")

    if submitted:
        if len(reason.strip()) < 3:
            st.error("Enter an adjustment reason with at least 3 characters.")
        else:
            try:
                result = client.put(
                    f"/inventory/{product_id}",
                    {
                        "stock_quantity": int(stock),
                        "reason": reason.strip(),
                    },
                )
                st.success("Inventory saved.")
                st.json(result)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
else:
    st.info("Add a product before creating inventory.")

if inventory:
    st.divider()
    st.subheader("Set Inventory to Zero")
    inventory_ids = [item["product_id"] for item in inventory]
    with st.form("zero_inventory"):
        remove_id = st.selectbox("Inventory Product", inventory_ids)
        confirm_zero = st.checkbox("Confirm setting this stock to zero")
        zero_submitted = st.form_submit_button("Set to Zero")

    if zero_submitted:
        if not confirm_zero:
            st.error("Confirm the stock adjustment before continuing.")
        else:
            try:
                client.put(
                    f"/inventory/{remove_id}",
                    {
                        "stock_quantity": 0,
                        "reason": "Inventory removed",
                    },
                )
                st.success("Stock set to zero; movement history is retained.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

with st.expander("Recent Stock Movements"):
    try:
        movements = client.get("/inventory/movements")
        if movements:
            st.dataframe(pd.DataFrame(movements), use_container_width=True)
        else:
            st.info("No stock movements recorded.")
    except Exception as exc:
        st.error(str(exc))