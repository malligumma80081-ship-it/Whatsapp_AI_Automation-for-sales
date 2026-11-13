import hmac

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limiter import rate_limit
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.database.connection import SessionLocal, ensure_database_ready
from app.database.models import User
from app.schemas.auth import (
    AdminSignupRequest,
    LoginRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "/signup",
    status_code=201,
    dependencies=[Depends(rate_limit(3, 60))],
)
def signup(
    request: AdminSignupRequest,
    db: Session = Depends(get_db),
):
    configured_key = settings.ADMIN_SIGNUP_KEY.strip()
    if not configured_key or not hmac.compare_digest(
        request.signup_key,
        configured_key,
    ):
        raise HTTPException(
            status_code=403,
            detail="Admin signup is disabled or the invite key is invalid.",
        )

    ensure_database_ready()
    existing_user = db.scalar(
        select(User).where(User.email == request.email)
    )
    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    user = User(
        email=str(request.email),
        hashed_password=hash_password(request.password),
        role="admin",
        is_active=True,
    )
    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        ) from exc

    return {"message": "Admin account created. You can now log in."}
@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[
        Depends(rate_limit(5, 60))
    ],
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    try:
        ensure_database_ready()
        user = db.scalar(
            select(User).where(
                User.email == request.email
            )
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Authentication service is temporarily unavailable.",
        ) from exc

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    hashed_password = str(getattr(user, "hashed_password", ""))
    if not verify_password(request.password, hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    if not bool(user.is_active):
        raise HTTPException(
            status_code=403,
            detail="Account is inactive.",
        )

    user_id = int(getattr(user, "id"))
    token, expires_in = create_access_token(
        user_id=user_id,
        role=str(user.role),
    )

    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
    )