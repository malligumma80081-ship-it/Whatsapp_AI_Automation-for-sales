import pytest

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)

def test_password_hashing():
    password = "StrongPassword123!"

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)

def test_wrong_password():
    hashed = hash_password("StrongPassword123!")

    assert not verify_password(
        "WrongPassword123!",
        hashed,
    )

def test_jwt_creation():
    token, expires_in = create_access_token(
        user_id=1,
        role="admin",
    )

    assert isinstance(token, str)
    assert expires_in > 0