"""Create the PostgreSQL database named in .env, if it does not exist yet.

Connects to the built-in `postgres` maintenance database, because you cannot
create a database from inside the one you are creating.

    python scripts/create_database.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def main() -> int:
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "dent_detection")

    if not password:
        print("DB_PASSWORD is empty in .env - set the postgres user's password first.")
        return 1

    try:
        # autocommit is required: CREATE DATABASE cannot run inside a transaction.
        with psycopg.connect(
            host=host, port=port, user=user, password=password, dbname="postgres", autocommit=True
        ) as conn:
            exists = conn.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (db_name,)
            ).fetchone()

            if exists:
                print(f"Database '{db_name}' already exists - nothing to do.")
                return 0

            # The name cannot be a bound parameter in DDL, so quote it instead.
            conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"Created database '{db_name}'.")
            return 0

    except psycopg.OperationalError as exc:
        print(f"Could not connect to PostgreSQL at {host}:{port} as '{user}'.")
        print(f"  {exc}")
        print("\nCheck that the service is running and DB_PASSWORD in .env is correct.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
