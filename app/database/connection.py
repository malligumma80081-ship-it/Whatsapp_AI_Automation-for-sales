import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.database.base import Base
from app.database.models import User  # noqa: F401 ensures User model is registered


DATABASE_URL = settings.DATABASE_URL

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False
    }


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def ensure_database_ready():
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        existing_user = db.query(User).first()
        if existing_user is not None:
            return

        admin_email = os.getenv("ADMIN_EMAIL", "admin@milletmilk.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "AdminPassword123!")

        admin = User(
            email=admin_email,
            hashed_password=hash_password(admin_password),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()