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

st.set_page_config(page_title="Products", layout="wide")

if not st.session_state.get("logged_in"):
    st.error("Please log in from the main dashboard.")
    st.stop()

client = APIClient(st.session_state["token"])

st.title("Product Management")

try:
    product_response = client.get(
        "/products/",
        params={"page_size": 100},
    )

    if isinstance(product_response, dict):
        product_list = product_response.get("products", [])
    else:
        product_list = product_response or []

    if product_list:
        st.dataframe(
            pd.DataFrame(product_list),
            use_container_width=True,
        )
    else:
        st.info("No products found.")

except Exception as exc:
    st.error(str(exc))
    product_list = []

if product_list:
    st.divider()
    st.subheader("Edit or Deactivate Product")
    product_ids = [product["product_id"] for product in product_list]
    selected_id = st.selectbox("Product", product_ids)
    selected_product = next(
        product
        for product in product_list
        if product["product_id"] == selected_id
    )

    with st.form("edit_product"):
        updated_name = st.text_input(
            "Product Name",
            value=selected_product["product_name"],
        )
        updated_millet = st.text_input(
            "Millet Name",
            value=selected_product["millet_name"],
        )
        updated_size = st.text_input(
            "Size",
            value=selected_product["size"],
        )
        updated_price = st.number_input(
            "Price (₹)",
            min_value=0.01,
            value=float(selected_product["price"]),
            step=1.0,
        )
        update_submitted = st.form_submit_button("Save Changes")

    if update_submitted:
        try:
            client.patch(
                f"/products/{selected_id}",
                {
                    "product_name": updated_name,
                    "millet_name": updated_millet,
                    "size": updated_size,
                    "price": updated_price,
                },
            )
            st.success("Product updated.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    with st.form("deactivate_product"):
        confirm_deactivation = st.checkbox(
            f"Confirm deactivation of {selected_id}"
        )
        deactivate_submitted = st.form_submit_button(
            "Deactivate Product",
            type="secondary",
        )

    if deactivate_submitted:
        if not confirm_deactivation:
            st.error("Confirm deactivation before continuing.")
        else:
            try:
                client.delete(f"/products/{selected_id}")
                st.success("Product deactivated.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

st.divider()
st.subheader("Add a New Product")

with st.form("add_product"):
    product_id = st.text_input("Product ID")
    product_name = st.text_input("Product Name")
    millet_name = st.text_input("Millet Name")
    size = st.text_input("Size", placeholder="500 ml")
    price = st.number_input(
        "Price (₹)",
        min_value=0.01,
        step=1.0,
    )
    initial_stock = st.number_input(
        "Initial Stock",
        min_value=0,
        step=1,
    )

    submitted = st.form_submit_button("Add Product")

    if submitted:
        payload = {
            "product_id": product_id,
            "product_name": product_name,
            "millet_name": millet_name,
            "size": size,
            "price": price,
            "initial_stock": int(initial_stock),
        }

        try:
            result = client.post(
                "/products/",
                payload,
            )
            st.success("Product added successfully.")
            st.json(result)
            st.rerun()

        except Exception as exc:
            st.error(str(exc))