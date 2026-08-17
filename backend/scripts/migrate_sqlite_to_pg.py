"""One-off data migration: copies all rows from the old SQLite `grades.db`
into the Postgres database configured via `DATABASE_URL`.

This only moves *data* - the target schema must already exist, i.e. run
`flask db upgrade` against the target Postgres database first.

Usage:
    DATABASE_URL=postgresql+psycopg://user:pass@host:5432/dbname \\
        python scripts/migrate_sqlite_to_pg.py path/to/grades.db [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import sys

from sqlalchemy import MetaData, create_engine, select, text

# Insertion order respects foreign-key dependencies (parents before children).
TABLE_ORDER = [
    "user",
    "studiengang",
    "modul",
    "modul_studiengang",
    "grade_attempt",
    "submission_series",
    "submission",
    "kombi_modul",
    "kombimodul_module",
]

# Tables with a Postgres SERIAL "id" primary key - their sequence must be
# advanced past the copied rows' ids, or the next INSERT from the app would
# collide with a migrated row.
SEQUENCE_TABLES = [
    "user",
    "studiengang",
    "modul",
    "grade_attempt",
    "submission_series",
    "submission",
    "kombi_modul",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sqlite_path", help="Path to the old grades.db")
    parser.add_argument("--dry-run", action="store_true", help="Only print row counts, write nothing")
    args = parser.parse_args()

    if not os.path.exists(args.sqlite_path):
        sys.exit(f"No such file: {args.sqlite_path}")

    pg_url = os.environ.get("DATABASE_URL")
    if not pg_url:
        sys.exit("DATABASE_URL must point at the target Postgres database")

    sqlite_engine = create_engine(f"sqlite:///{args.sqlite_path}")
    pg_engine = create_engine(pg_url)

    sqlite_meta = MetaData()
    sqlite_meta.reflect(bind=sqlite_engine)
    pg_meta = MetaData()
    pg_meta.reflect(bind=pg_engine)

    missing = [t for t in TABLE_ORDER if t not in pg_meta.tables]
    if missing:
        sys.exit(f"Target schema is missing table(s) {missing} - run 'flask db upgrade' first")

    with sqlite_engine.connect() as sconn, pg_engine.begin() as pconn:
        for table_name in TABLE_ORDER:
            if table_name not in sqlite_meta.tables:
                continue
            src = sqlite_meta.tables[table_name]
            dst = pg_meta.tables[table_name]

            rows = [dict(r._mapping) for r in sconn.execute(select(src))]
            print(f"{table_name}: {len(rows)} row(s)")
            if args.dry_run or not rows:
                continue
            pconn.execute(dst.insert(), rows)

        if args.dry_run:
            print("Dry run - nothing written.")
            return

        for table_name in SEQUENCE_TABLES:
            pconn.execute(
                text(
                    f"SELECT setval(pg_get_serial_sequence('\"{table_name}\"', 'id'), "
                    f'COALESCE((SELECT MAX(id) FROM "{table_name}"), 1))'
                )
            )

    print("Done.")


if __name__ == "__main__":
    main()
