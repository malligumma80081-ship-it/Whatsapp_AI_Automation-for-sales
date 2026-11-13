import os
import httpx

from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000/api/v1",
)

class APIClient:

    def __init__(self, token=None):
        self.token = token

    def headers(self):
        if not self.token:
            return {}

        return {
            "Authorization": f"Bearer {self.token}"
        }

    def get(self, endpoint, params=None):
        return self._request(
            "GET", endpoint, params=params
        )

    def post(self, endpoint, data=None):
        return self._request(
            "POST", endpoint, json=data
        )

    def put(self, endpoint, data=None):
        return self._request(
            "PUT", endpoint, json=data
        )

    def patch(self, endpoint, data=None):
        return self._request(
            "PATCH", endpoint, json=data
        )

    def delete(self, endpoint):
        return self._request("DELETE", endpoint)

    def _request(self, method, endpoint, **kwargs):
        url = f"{API_BASE_URL}{endpoint}"

        try:
            response = httpx.request(
                method,
                url,
                headers=self.headers(),
                timeout=15,
                **kwargs,
            )

            response.raise_for_status()

            if response.status_code == 204:
                return None

            if not response.content:
                return None

            return response.json()

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                detail = exc.response.text[:300]
                if not self.token:
                    raise RuntimeError(
                        f"Login failed: {detail}"
                    ) from exc

                import streamlit as st

                st.session_state.clear()
                st.session_state["auth_message"] = (
                    "Your session expired. Please log in again."
                )
                st.switch_page("dashboard/main.py")

                raise RuntimeError(
                    "Your session expired. Please log in again."
                ) from exc

            if exc.response.status_code == 403:
                try:
                    detail = exc.response.json().get("detail")
                except (ValueError, AttributeError):
                    detail = None

                raise RuntimeError(
                    str(detail)
                    if detail
                    else "You do not have permission for this action."
                ) from exc

            raise RuntimeError(
                f"API error: {exc.response.status_code} "
                f"{exc.response.text[:300]}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                "Cannot connect to FastAPI. Check backend status."
            ) from exc