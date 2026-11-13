import jwt

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.database.models import User
from app.core.security import _get_jwt_secret
from app.core.config import settings

bearer_scheme = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    try:
        jwt_secret_key = _get_jwt_secret()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    jwt_algorithm = settings.JWT_ALGORITHM

    try:
        payload = jwt.decode(
            token,
            jwt_secret_key,
            algorithms=[jwt_algorithm],
        )

        user_id = int(payload["sub"])
        token_role = payload["role"]

    except (
        jwt.InvalidTokenError,
        KeyError,
        ValueError,
        TypeError,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)

    if user is None or user.is_active is not True:
        raise HTTPException(
            status_code=401,
            detail="User not found or inactive.",
        )

    # Do not trust an old role claim after a role change.
    if token_role != user.role:
        raise HTTPException(
            status_code=401,
            detail="User permissions have changed. Log in again.",
        )

    return user

def require_admin(
    current_user: User = Depends(get_current_user),
):
    role = getattr(current_user, "role", None)

    if role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required.",
        )

    return current_user