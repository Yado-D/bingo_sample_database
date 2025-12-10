"""Tempo script to add a superagent user to the database.

Usage:
    python -m scripts.add_superagent_tempo

This script uses the project's `SessionLocal`, `models` and `utils` so it will
respect the same DB settings and password hashing as the app.

Note: Ensure your `DATABASE_URL` environment variable is set (same as the app).
"""
from sqlalchemy.exc import IntegrityError

from app import models, utils
from app.database import SessionLocal


FIRST_NAME = "Deriba"
LAST_NAME = "Bekele"
PHONE = "0933333333"
PASSWORD = "112233"


def main():
    db = SessionLocal()
    try:
        # Check if a user with the same phone already exists
        existing = db.query(models.User).filter(models.User.phone == PHONE).first()
        if existing:
            print(f"User with phone {PHONE} already exists (id={existing.id}). No action taken.")
            return

        hashed = utils.hash_password(PASSWORD)

        user = models.User(
            first_name=FIRST_NAME,
            last_name=LAST_NAME,
            phone=PHONE,
            phone_number=PHONE,
            password=hashed,
            role=models.Role.SUPERAGENT,
            wallet_balance=0.0,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print("Created superagent:")
        print(f"  id: {user.id}")
        print(f"  first_name: {user.first_name}")
        print(f"  last_name: {user.last_name}")
        print(f"  phone: {user.phone}")
        print(f"  role: {user.role}")

    except IntegrityError as e:
        db.rollback()
        print("IntegrityError while creating user:", e)
    except Exception as e:
        db.rollback()
        print("Error while creating user:", e)
    finally:
        db.close()


if __name__ == "__main__":
    main()
