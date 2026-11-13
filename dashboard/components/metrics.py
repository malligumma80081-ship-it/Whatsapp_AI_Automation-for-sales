import streamlit as st

def show_metrics(
    total_orders,
    total_customers,
    total_sales,
    total_products,
):
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Orders",
        total_orders,
    )

    col2.metric(
        "Customers",
        total_customers,
    )

    col3.metric(
        "Order Value",
        f"₹{total_sales:,.2f}",
    )

    col4.metric(
        "Products",
        total_products,
    )