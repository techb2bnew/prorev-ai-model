"""Bring an existing dent_detection database in line with the current models.

There is no Alembic in this project - the models in `app/models/` are the single
source of truth, and `flask init-db` creates whatever is missing. What it cannot
do is *change* a table that already exists, which is what this script is for.

Every step inspects the live schema first, so it only does what is still needed:
running it against an already-current database reports nothing to do, and
re-running it after a partial failure resumes safely.

Steps currently known:

  * fold the old `vehicles` table into columns on `inspections`
  * replace the vehicle detail columns with `customer_name` + `vehicle_type`
  * move the model backend onto `inspections`, drop `inference_runs`
  * rename the `rear` view angle to `back`
  * drop `alembic_version` and the columns nothing ever read

    python scripts/sync_schema.py           # show what would change
    python scripts/sync_schema.py --apply   # actually change it

Take a pg_dump backup first - the drops are irreversible.
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Columns folded in from the old `vehicles` table, since superseded by
# customer_name + vehicle_type but still needed as a copy source on old databases.
LEGACY_VEHICLE_COLUMNS = [
    ("vehicle_registration", "VARCHAR(30)"),
    ("vehicle_make", "VARCHAR(60)"),
    ("vehicle_model", "VARCHAR(60)"),
    ("vehicle_year", "INTEGER"),
    ("vehicle_colour", "VARCHAR(40)"),
]

NEW_COLUMNS = [
    ("inspections", "customer_name", "VARCHAR(150)"),
    ("inspections", "vehicle_type", "VARCHAR(40)"),
    ("inspections", "model_backend", "VARCHAR(40)"),
]

DEAD_COLUMNS = [
    ("damage_types", "default_severity_rules"),
    ("inspection_images", "annotated_url"),
    ("detections", "panel_hint"),
    # Written by the job but never read by anything.
    ("inspections", "processing_started_at"),
    # Replaced by a property: `images` is eager-loaded anyway, so a stored copy
    # of the count could only drift away from the rows themselves.
    ("inspections", "image_count"),
    # The customer name is the human handle now; the id is the machine one.
    ("inspections", "reference_code"),
]

INDEXES = [
    ("ix_inspections_customer_name", "inspections", "customer_name"),
    ("ix_inspections_vehicle_type", "inspections", "vehicle_type"),
]

DROPPED_TABLES = ["inference_runs", "vehicles", "alembic_version"]


def _table_exists(cur, table: str) -> bool:
    cur.execute(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = %s",
        (table,),
    )
    return cur.fetchone() is not None


def _column_exists(cur, table: str, column: str) -> bool:
    cur.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = %s AND column_name = %s",
        (table, column),
    )
    return cur.fetchone() is not None


def _has_rows(cur, sql: str) -> bool:
    """Whether a probe query matches anything - keeps data fixes idempotent."""
    cur.execute(sql)
    return cur.fetchone() is not None


def _index_exists(cur, name: str) -> bool:
    cur.execute("SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = %s", (name,))
    return cur.fetchone() is not None


def plan(cur) -> list[tuple[str, str]]:
    """The (description, SQL) steps still needed, in dependency order."""
    steps: list[tuple[str, str]] = []

    # --- 1. Columns that must exist before anything is copied into them ---
    for table, column, sql_type in NEW_COLUMNS:
        if not _column_exists(cur, table, column):
            steps.append(
                (
                    f"add {table}.{column}",
                    f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}",
                )
            )

    # A database still on the pre-consolidation shape needs the intermediate
    # vehicle columns to copy `vehicles` into before they are dropped again.
    folding_vehicles = _table_exists(cur, "vehicles") and _column_exists(
        cur, "inspections", "vehicle_id"
    )
    if folding_vehicles:
        for column, sql_type in LEGACY_VEHICLE_COLUMNS:
            if not _column_exists(cur, "inspections", column):
                steps.append(
                    (
                        f"add inspections.{column} (transitional)",
                        f"ALTER TABLE inspections ADD COLUMN {column} {sql_type}",
                    )
                )
        steps.append(
            (
                "copy vehicles into inspections",
                """
                UPDATE inspections i SET
                    vehicle_registration = v.registration_number,
                    vehicle_make         = v.make,
                    vehicle_model        = v.model,
                    vehicle_year         = v.year,
                    vehicle_colour       = v.colour
                FROM vehicles v
                WHERE i.vehicle_id = v.id
                """,
            )
        )

    # --- 2. Backfills, before their source is dropped ---
    if _table_exists(cur, "inference_runs"):
        steps.append(
            (
                "backfill model_backend from inference_runs",
                """
                UPDATE inspections i SET model_backend = r.model_backend
                FROM (
                    SELECT DISTINCT ON (inspection_id) inspection_id, model_backend
                    FROM inference_runs
                    WHERE model_backend IS NOT NULL
                    ORDER BY inspection_id, created_at DESC
                ) r
                WHERE r.inspection_id = i.id AND i.model_backend IS NULL
                """,
            )
        )

    # The old shape had no vehicle type, and every inspection in it was a car.
    if _column_exists(cur, "inspections", "vehicle_make") or folding_vehicles:
        steps.append(
            (
                "default vehicle_type to 'car' for pre-existing rows",
                "UPDATE inspections SET vehicle_type = 'car' WHERE vehicle_type IS NULL",
            )
        )

    # `vehicle_type` used to be the category and was backfilled to 'car'. It is
    # now the body style (sedan/suv/...), for which 'car' carries no information,
    # and there is no longer a make/model column to infer one from.
    if _column_exists(cur, "inspections", "vehicle_type") and _has_rows(
        cur, "SELECT 1 FROM inspections WHERE vehicle_type = 'car' LIMIT 1"
    ):
        steps.append(
            (
                "clear the placeholder vehicle_type 'car' (now a body style)",
                "UPDATE inspections SET vehicle_type = NULL WHERE vehicle_type = 'car'",
            )
        )

    if _column_exists(cur, "inspection_images", "view_angle") and _has_rows(
        cur, "SELECT 1 FROM inspection_images WHERE view_angle = 'rear' LIMIT 1"
    ):
        steps.append(
            (
                "rename view angle 'rear' to 'back'",
                "UPDATE inspection_images SET view_angle = 'back' WHERE view_angle = 'rear'",
            )
        )

    # --- 3. Drops ---
    if _column_exists(cur, "inspections", "vehicle_id"):
        steps.append(
            ("drop inspections.vehicle_id", "ALTER TABLE inspections DROP COLUMN vehicle_id")
        )

    for column, _ in LEGACY_VEHICLE_COLUMNS:
        if _column_exists(cur, "inspections", column) or folding_vehicles:
            steps.append(
                (
                    f"drop inspections.{column}",
                    f"ALTER TABLE inspections DROP COLUMN IF EXISTS {column}",
                )
            )

    for table, column in DEAD_COLUMNS:
        if _table_exists(cur, table) and _column_exists(cur, table, column):
            steps.append((f"drop {table}.{column}", f"ALTER TABLE {table} DROP COLUMN {column}"))

    for table in DROPPED_TABLES:
        if _table_exists(cur, table):
            steps.append((f"drop table {table}", f"DROP TABLE {table} CASCADE"))

    # --- 4. Indexes, once the columns they cover are settled ---
    for name, table, column in INDEXES:
        if not _index_exists(cur, name):
            steps.append(
                (
                    f"index {table}.{column}",
                    f"CREATE INDEX {name} ON {table} ({column})",
                )
            )

    return steps


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true", help="Execute the changes (default is a dry run)."
    )
    args = parser.parse_args()

    try:
        conn = psycopg.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            dbname=os.getenv("DB_NAME", "dent_detection"),
        )
    except psycopg.OperationalError as exc:
        print(f"Could not connect: {exc}")
        return 1

    with conn:
        with conn.cursor() as cur:
            steps = plan(cur)

            if not steps:
                print("Database already matches the models - nothing to do.")
                return 0

            print(f"{len(steps)} step(s) {'to apply' if args.apply else 'pending'}:\n")
            for description, _ in steps:
                print(f"  - {description}")

            if not args.apply:
                print("\nDry run. Re-run with --apply to execute.")
                return 0

            print()
            # One transaction: a failure half way through leaves nothing applied.
            for description, sql in steps:
                cur.execute(sql)
                print(f"  done: {description}")

    print("\nSchema synced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
