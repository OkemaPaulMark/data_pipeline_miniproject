"""
Loads clean CSVs into SQLite in chunks, then runs analysis.
Run from the project root: python load_and_analyze.py
"""
import sqlite3
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, ".")

from src.pipeline.config import get_settings
from src.pipeline.analyze import run_analysis

CHUNK_SIZE = 100_000
DB_ROW_LIMIT = 500_000   # rows per table loaded into SQLite


def load_csv_to_sqlite(csv_path: Path, table_name: str, conn: sqlite3.Connection) -> None:
    first = True
    total = 0
    for chunk in pd.read_csv(csv_path, chunksize=CHUNK_SIZE, low_memory=False):
        remaining = DB_ROW_LIMIT - total
        if remaining <= 0:
            break
        chunk = chunk.head(remaining)
        chunk.to_sql(table_name, conn, if_exists="replace" if first else "append", index=False)
        first = False
        total += len(chunk)
        print(f"  {table_name}: {total:,} rows loaded...", end="\r")
    print(f"  {table_name}: {total:,} rows ✓                ")


def main():
    settings = get_settings()

    # Initialise schema
    print("Initialising database...")
    schema_sql = Path("sql/schema.sql").read_text(encoding="utf-8")
    with sqlite3.connect(settings.db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()

    # Load each table in chunks
    with sqlite3.connect(settings.db_path) as conn:
        print("Loading patents...")
        load_csv_to_sqlite(settings.clean_dir / "clean_patents.csv", "patents", conn)

        print("Loading inventors...")
        load_csv_to_sqlite(settings.clean_dir / "clean_inventors.csv", "inventors", conn)

        print("Loading companies...")
        load_csv_to_sqlite(settings.clean_dir / "clean_companies.csv", "companies", conn)

        print("Loading relationships...")
        load_csv_to_sqlite(settings.clean_dir / "clean_relationships.csv", "relationships", conn)

        # Add indexes
        print("Creating indexes...")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rel_patent   ON relationships(patent_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rel_inventor ON relationships(inventor_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rel_company  ON relationships(company_id)")
        conn.commit()

    print("Running analysis and generating reports...")
    run_analysis(settings.db_path, settings.reports_dir, settings.top_n)
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
