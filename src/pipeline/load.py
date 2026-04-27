from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict

import pandas as pd


def initialize_database(db_path: Path, schema_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = schema_path.read_text(encoding="utf-8")

    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()


def write_clean_csvs(clean_tables: Dict[str, pd.DataFrame], clean_dir: Path) -> None:
    clean_dir.mkdir(parents=True, exist_ok=True)

    clean_tables["patents"].to_csv(clean_dir / "clean_patents.csv", index=False)
    clean_tables["inventors"].to_csv(clean_dir / "clean_inventors.csv", index=False)
    clean_tables["companies"].to_csv(clean_dir / "clean_companies.csv", index=False)
    clean_tables["relationships"].to_csv(clean_dir / "clean_relationships.csv", index=False)


def load_to_sqlite(clean_tables: Dict[str, pd.DataFrame], db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        clean_tables["patents"].to_sql(
            "patents", conn, if_exists="replace", index=False
        )
        clean_tables["inventors"].to_sql(
            "inventors", conn, if_exists="replace", index=False
        )
        clean_tables["companies"].to_sql(
            "companies", conn, if_exists="replace", index=False
        )
        clean_tables["relationships"].to_sql(
            "relationships", conn, if_exists="replace", index=False
        )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_rel_patent ON relationships(patent_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_rel_inventor ON relationships(inventor_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_rel_company ON relationships(company_id)"
        )
        conn.commit()
