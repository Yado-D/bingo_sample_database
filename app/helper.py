import secrets
import string
from app import models

CHARSET = string.digits + string.ascii_lowercase


def generate_code(length=6):
    six_digit_random_number = "".join(secrets.choice(CHARSET) for _ in range(length))
    return six_digit_random_number


def generate_unique_code(db):
    while True:
        code = generate_code()
        new = db.query(models.BingoCard).filter(models.BingoCard.id == code).first()
        if not new:
            return code
