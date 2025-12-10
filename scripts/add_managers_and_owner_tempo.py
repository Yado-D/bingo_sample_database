"""Tempo script to add an Owner and a Manager user to the database.

Owner: phone=0932528482
Manager: phone=0932528483
Password for both: 112233

Usage:
    python -m scripts.add_managers_and_owner_tempo

The script uses the project's `SessionLocal`, `models` and `utils` so it will
respect the same DB settings and password hashing as the app.

Note: Ensure your `DATABASE_URL` environment variable is set (same as the app).
"""
from sqlalchemy.exc import IntegrityError

from app import models, utils
from app.database import SessionLocal


USERS = [
    {
        "first_name": "Abebe",
        "last_name": "Tadesse",
        "phone": "0911111111",
        "password": "112233",
        "role": models.Role.OWNER,
    },
    {
        "first_name": "Kebede",
        "last_name": "Bekele",
        "phone": "0922222222",
        "password": "112233",
        "role": models.Role.MANAGER,
    },
]


def create_user(db, first_name, last_name, phone, password, role, superior_id=None, created_by=None):
    existing = db.query(models.User).filter(models.User.phone == phone).first()
    if existing:
        print(f"SKIP: user with phone {phone} already exists (id={existing.id}, role={existing.role}).")
        return existing

    hashed = utils.hash_password(password)
    user = models.User(
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        phone_number=phone,
        password=hashed,
        role=role,
        wallet_balance=0.0,
        superior_id=superior_id,
        created_by=created_by,
    )

    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        print(f"CREATED: id={user.id} phone={user.phone} role={user.role}")
        return user
    except IntegrityError as e:
        db.rollback()
        print(f"IntegrityError creating user {phone}: {e}")
    except Exception as e:
        db.rollback()
        print(f"Error creating user {phone}: {e}")


def main():
    db = SessionLocal()
    try:
        # Create owner first
        owner_spec = USERS[0]
        owner = create_user(
            db,
            owner_spec["first_name"],
            owner_spec["last_name"],
            owner_spec["phone"],
            owner_spec["password"],
            owner_spec["role"],
            superior_id=None,
            created_by=None,
        )

        # Create manager and attach to owner
        manager_spec = USERS[1]
        create_user(
            db,
            manager_spec["first_name"],
            manager_spec["last_name"],
            manager_spec["phone"],
            manager_spec["password"],
            manager_spec["role"],
            superior_id=owner.id if owner else None,
            created_by=owner.id if owner else None,
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()