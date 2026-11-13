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

from dashboard.api_client import APIClient

def login():
    st.title("Millet Milk Sales")

    auth_message = st.session_state.pop("auth_message", None)
    if auth_message:
        st.warning(auth_message)

    account_action = st.radio(
        "Account",
        ["Log in", "Sign up"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if account_action == "Log in":
        st.subheader("Admin Login")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(
                "Login",
                use_container_width=True,
            )

        if submitted:
            try:
                result = APIClient().post(
                    "/auth/login",
                    {"email": email, "password": password},
                )
                if not result:
                    raise ValueError("Login failed: no response received")

                st.session_state["token"] = result["access_token"]
                st.session_state["logged_in"] = True
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    else:
        st.subheader("Create Admin Account")
        st.info(
            "Admin signup requires an invite key configured by the administrator. "
            "Set ADMIN_SIGNUP_KEY in .env to enable it."
        )
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input(
                "Password (12+ characters)",
                type="password",
                key="signup_password",
            )
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
            )
            signup_key = st.text_input(
                "Admin Invite Key",
                type="password",
            )
            submitted = st.form_submit_button(
                "Create Account",
                use_container_width=True,
            )

        if submitted:
            if password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 12:
                st.error("Use a password with at least 12 characters.")
            else:
                try:
                    APIClient().post(
                        "/auth/signup",
                        {
                            "email": email,
                            "password": password,
                            "signup_key": signup_key,
                        },
                    )
                    st.success("Admin account created. Log in to continue.")
                except Exception as exc:
                    st.error(str(exc))

def logout():
    st.session_state.clear()
    st.rerun()