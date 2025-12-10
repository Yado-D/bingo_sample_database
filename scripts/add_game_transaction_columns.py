"""
Migration helper: add missing columns to `game_transactions` table if they don't exist.
This script uses the project's config (`app.core.config.settings`) and SQLAlchemy engine.
Run with the same Python environment used by the app so `DATABASE_URL` and dependencies are available.
"""
from sqlalchemy import text
from app.core.database import engine

ALTERS = [
    "ALTER TABLE game_transactions ADD COLUMN IF NOT EXISTS dedacted_amount DOUBLE PRECISION",
    "ALTER TABLE game_transactions ADD COLUMN IF NOT EXISTS owner_id INTEGER",
    "ALTER TABLE game_transactions ADD COLUMN IF NOT EXISTS owner_name TEXT",
    "ALTER TABLE game_transactions ADD COLUMN IF NOT EXISTS jester_id INTEGER",
    "ALTER TABLE game_transactions ADD COLUMN IF NOT EXISTS jester_name TEXT",
    "ALTER TABLE game_transactions ADD COLUMN IF NOT EXISTS jester_remaining_balance DOUBLE PRECISION",
    "ALTER TABLE game_transactions ADD COLUMN IF NOT EXISTS total_balance DOUBLE PRECISION",
]


def main():
    print("Connecting to DB via app.core.database.engine")
    with engine.begin() as conn:
        for stmt in ALTERS:
            try:
                print("Executing:", stmt)
                conn.execute(text(stmt))
                print("OK")
            except Exception as e:
                print("FAILED:", e)

    print("Migration finished.")


if __name__ == "__main__":
    main()
