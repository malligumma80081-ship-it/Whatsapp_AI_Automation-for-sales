import hashlib
import hmac

from app.core.config import settings


def verify_webhook_signature(
    body: bytes,
    signature: str | None,
) -> bool:

    if not settings.WHATSAPP_APP_SECRET:
        return False

    if not signature:
        return False

    expected_signature = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    expected_header = f"sha256={expected_signature}"

    return hmac.compare_digest(
        expected_header,
        signature,
    )


def verify_webhook_token(
    provided_token: str | None,
) -> bool:

    configured_token = settings.WHATSAPP_VERIFY_TOKEN

    if not configured_token or not provided_token:
        return False

    return hmac.compare_digest(
        configured_token,
        provided_token,
    )