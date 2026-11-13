from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.database.base import Base
from app.database.connection import get_db
from app.database.models import User
from app.main import app


def _build_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    db.add(
        User(
            id=1,
            email="admin@example.com",
            hashed_password="hashed",
            role="admin",
            is_active=True,
        )
    )
    db.commit()
    db.close()

    token, _ = create_access_token(user_id=1, role="admin")

    with TestClient(app) as client:
        yield client, token

    app.dependency_overrides.clear()


def test_create_product_route_returns_201_for_admin():
    with _build_client() as (client, token):
        response = client.post(
            "/api/v1/products/",
            json={
                "product_id": "TESTP001",
                "product_name": "Test Product",
                "millet_name": "Ragi",
                "size": "500ml",
                "price": Decimal("120.00"),
                "initial_stock": 10,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201, response.text
    assert response.json()["product_id"] == "TESTP001"
