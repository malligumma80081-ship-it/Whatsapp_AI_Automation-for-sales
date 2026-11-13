from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
import sys

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import Boolean, Date, DateTime, Float, Integer, Numeric, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app
from app.database.models import Customer


def _get_route_dependencies(dependant):
    """Yield dependencies recursively for a FastAPI route."""
    for dependency in getattr(dependant, "dependencies", []):
        yield dependency
        yield from _get_route_dependencies(dependency)


@pytest.fixture
def db_session():
    # Reuse model metadata, but never connect tests to the configured production DB.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Customer.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Customer.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    previous_overrides = app.dependency_overrides.copy()

    # Override route-local get_db functions as well as shared dependencies.
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        for dependency in _get_route_dependencies(route.dependant):
            call = getattr(dependency, "call", None)
            if callable(call) and getattr(call, "__name__", "") == "get_db":
                app.dependency_overrides[call] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


@pytest.fixture
def customer_id(db_session):
    # Populate required scalar columns when the model has no defaults.
    values = {}
    for column in Customer.__table__.columns:
        if (
            column.primary_key
            or column.nullable
            or column.default is not None
            or column.server_default is not None
            or column.autoincrement is True
        ):
            continue

        name = column.name
        kind = column.type

        if isinstance(kind, String):
            value = f"test_{name}"
            values[name] = value[:kind.length] if kind.length else value
        elif isinstance(kind, Boolean):
            values[name] = False
        elif isinstance(kind, Integer):
            values[name] = 1
        elif isinstance(kind, Numeric):
            values[name] = Decimal("1")
        elif isinstance(kind, Float):
            values[name] = 1.0
        elif isinstance(kind, DateTime):
            values[name] = datetime.now(timezone.utc)
        elif isinstance(kind, Date):
            values[name] = date.today()

    customer = Customer(**values)
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    primary_key = next(iter(Customer.__table__.primary_key))
    return getattr(customer, primary_key.key)