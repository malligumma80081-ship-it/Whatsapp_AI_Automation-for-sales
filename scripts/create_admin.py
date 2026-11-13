import getpass

from sqlalchemy import select

from app.database.connection import SessionLocal
from app.database.models import User
from app.core.security import hash_password

def main():
    email = input("Admin email: ").strip().lower()
    password = getpass.getpass("Admin password: ")

    if len(password) < 12:
        raise ValueError(
            "Admin password must contain at least 12 characters."
        )

    db = SessionLocal()

    try:
        existing = db.scalar(
            select(User).where(User.email == email)
        )

        if existing:
            raise ValueError("User already exists.")

        admin = User(
            email=email,
            hashed_password=hash_password(password),
            role="admin",
            is_active=True,
        )

        db.add(admin)
        db.commit()

        print("Admin account created.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    main()