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

st.set_page_config(page_title="Customers", layout="wide")

if not st.session_state.get("logged_in"):
    st.error("Please log in from the main dashboard.")
    st.stop()

client = APIClient(st.session_state["token"])

st.title("Customer Management")

try:
    customers = client.get("/customers/")

    if customers:
        df = pd.DataFrame(customers)

        # Avoid showing unnecessary personal information.
        display_columns = [
            col for col in
            ["id", "name", "phone"]
            if col in df.columns
        ]

        st.dataframe(
            df[display_columns],
            use_container_width=True,
        )
    else:
        st.info("No customers found.")

except Exception as exc:
    st.error(str(exc))
    customers = []

st.divider()
st.subheader("Register Customer")

with st.form("register_customer"):
    name = st.text_input("Customer Name")
    phone = st.text_input(
        "Phone Number",
        placeholder="10-20 characters",
    )
    address = st.text_area("Address (optional)")
    submitted = st.form_submit_button("Register Customer")

    if submitted:
        name = name.strip()
        phone = phone.strip()

        if len(name) < 2:
            st.error("Enter a customer name with at least 2 characters.")
        elif not 10 <= len(phone) <= 20:
            st.error("Phone number must be 10 to 20 characters.")
        else:
            try:
                client.post(
                    "/customers/",
                    {
                        "name": name,
                        "phone": phone,
                        "address": address.strip() or None,
                    },
                )
                st.success(f"Registered {name} successfully.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

if customers:
    st.divider()
    st.subheader("Edit or Delete Customer")
    customer_by_id = {customer["id"]: customer for customer in customers}

    selected_customer_id = st.selectbox(
        "Customer Record",
        list(customer_by_id),
        format_func=lambda value: (
            f"{customer_by_id[value]['name']} · "
            f"{customer_by_id[value]['phone']}"
        ),
    )
    selected_customer = customer_by_id[selected_customer_id]

    with st.form("edit_customer"):
        updated_name = st.text_input(
            "Customer Name",
            value=selected_customer["name"],
        )
        updated_phone = st.text_input(
            "Phone Number",
            value=selected_customer["phone"],
        )
        updated_address = st.text_area(
            "Address (optional)",
            value=selected_customer.get("address") or "",
        )
        update_submitted = st.form_submit_button("Save Customer Changes")

    if update_submitted:
        updated_name = (updated_name or "").strip()
        updated_phone = (updated_phone or "").strip()
        if len(updated_name) < 2:
            st.error("Enter a customer name with at least 2 characters.")
        elif not 10 <= len(updated_phone) <= 20:
            st.error("Phone number must be 10 to 20 characters.")
        else:
            try:
                client.patch(
                    f"/customers/{selected_customer_id}",
                    {
                        "name": updated_name,
                        "phone": updated_phone,
                        "address": updated_address.strip() or None,
                    },
                )
                st.success("Customer updated.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    with st.form("delete_customer"):
        confirm_delete = st.checkbox(
            f"Confirm deletion of {selected_customer['name']}"
        )
        delete_submitted = st.form_submit_button("Delete Customer")

    if delete_submitted:
        if not confirm_delete:
            st.error("Confirm deletion before continuing.")
        else:
            try:
                client.delete(f"/customers/{selected_customer_id}")
                st.success("Customer deleted.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))