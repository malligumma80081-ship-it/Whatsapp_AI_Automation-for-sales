import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from dotenv import dotenv_values
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()
ALLOWED_JWT_ALGORITHMS = {"HS256", "HS384", "HS512"}


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def _get_jwt_secret() -> str:
    env_file = Path(__file__).resolve().parents[2] / ".env"
    secret = (
        getattr(settings, "JWT_SECRET_KEY", None)
        or os.getenv("JWT_SECRET_KEY")
        or dotenv_values(env_file).get("JWT_SECRET_KEY")
    )

    if not isinstance(secret, str):
        raise RuntimeError("JWT_SECRET_KEY is not configured")

    secret = secret.strip()
    placeholders = {
        "",
        "your-secret-key",
        "change-me",
        "paste-generated-secret-here",
    }
    if secret.casefold() in placeholders or len(secret.encode("utf-8")) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must be a non-placeholder secret of at least 32 bytes"
        )

    return secret


def create_access_token(user_id: int, role: str) -> tuple[str, int]:
    expires_minutes = getattr(settings, "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    if not isinstance(expires_minutes, int) or expires_minutes <= 0:
        raise RuntimeError("JWT token expiration must be a positive integer")

    algorithm = getattr(settings, "JWT_ALGORITHM", "HS256")
    if algorithm not in ALLOWED_JWT_ALGORITHMS:
        raise RuntimeError("JWT_ALGORITHM must be HS256, HS384, or HS512")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=expires_minutes)

    token = jwt.encode(
        {
            "sub": str(user_id),
            "role": role,
            "iat": now,
            "exp": expires_at,
        },
        _get_jwt_secret(),
        algorithm=algorithm,
    )
    return token, expires_minutes * 60

# DATABASE_URL = "sqlite:///./millet_milk.db"
# JWT_SECRET_KEY = "PASTE_A_GENERATED_SECRET_HERE"
# WHATSAPP_VERIFY_TOKEN = "PASTE_A_DIFFERENT_GENERATED_SECRET_HERE"