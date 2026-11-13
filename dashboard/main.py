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
import plotly.express as px

from dashboard.auth import login, logout
from dashboard.api_client import APIClient
from dashboard.components.metrics import show_metrics

st.set_page_config(
    page_title="Millet Milk Admin",
    page_icon="🥛",
    layout="wide",
)

if not st.session_state.get("logged_in"):
    login()
    st.stop()

client = APIClient(
    token=st.session_state.get("token")
)

with st.sidebar:
    st.title("🥛 Millet Milk Sales")
    st.caption("Admin Dashboard")

    st.write("Logged in as administrator")

    if st.button("Logout", use_container_width=True):
        logout()

st.title("Business Overview")
st.caption("Manage your Ragi Milk business.")

try:
    sales = client.get("/analytics/sales") or {}
    customers = client.get("/analytics/customers") or {}
    products = client.get("/products/") or {}

    # Adapt these fields to the actual analytics response.
    total_orders = sales.get("total_orders", 0)
    total_sales = float(
        sales.get("total_order_value", 0)
    )

    total_customers = (
        customers.get("total_customers", 0)
        if customers is not None
        else 0
    )

    total_products = (
        products.get("total", len(products))
        if isinstance(products, dict)
        else len(products) if products is not None else 0
    )

    show_metrics(
        total_orders=total_orders,
        total_customers=total_customers,
        total_sales=total_sales,
        total_products=total_products,
    )

    st.divider()

    st.subheader("Top Selling Products")

    top_products = client.get(
        "/analytics/top-products"
    ) or []

    if top_products:
        df = pd.DataFrame(top_products)

        st.dataframe(
            df,
            use_container_width=True,
        )

    else:
        st.info("No product sales available yet.")

except Exception as exc:
    st.error(str(exc))