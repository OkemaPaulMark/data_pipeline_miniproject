from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict

import pandas as pd


QUERIES: Dict[str, str] = {
    # Q1: Top Inventors
    "q1_top_inventors": """
        SELECT i.name AS inventor_name, COUNT(DISTINCT r.patent_id) AS patent_count
        FROM relationships r
        JOIN inventors i ON i.inventor_id = r.inventor_id
        GROUP BY i.inventor_id, inventor_name
        ORDER BY patent_count DESC, inventor_name ASC
        LIMIT ?;
    """,
    # Q2: Top Companies
    "q2_top_companies": """
        SELECT c.name AS company_name, COUNT(DISTINCT r.patent_id) AS patent_count
        FROM relationships r
        JOIN companies c ON c.company_id = r.company_id
        GROUP BY c.company_id, company_name
        ORDER BY patent_count DESC, company_name ASC
        LIMIT ?;
    """,
    # Q3: Countries
    "q3_top_countries": """
        SELECT i.country AS country, COUNT(DISTINCT r.patent_id) AS patent_count
        FROM relationships r
        JOIN inventors i ON i.inventor_id = r.inventor_id
        GROUP BY i.country
        ORDER BY patent_count DESC, country ASC;
    """,
    # Q4: Trends Over Time
    "q4_trends_over_time": """
        SELECT year, COUNT(*) AS patent_count
        FROM patents
        WHERE year IS NOT NULL
        GROUP BY year
        ORDER BY year ASC;
    """,
    # Q5: JOIN Query (patents, inventors, companies)
    "q5_join_details": """
        SELECT p.patent_id, p.title, p.year,
               i.name AS inventor_name,
               c.name AS company_name
        FROM relationships r
        JOIN patents p ON p.patent_id = r.patent_id
        JOIN inventors i ON i.inventor_id = r.inventor_id
        JOIN companies c ON c.company_id = r.company_id
        ORDER BY p.year DESC, p.patent_id ASC
        LIMIT 100;
    """,
    # Q6: CTE Query (inventors with >=2 patents)
    "q6_cte": """
        WITH inventor_counts AS (
            SELECT i.inventor_id, i.name AS inventor_name, COUNT(DISTINCT r.patent_id) AS patents
            FROM inventors i
            JOIN relationships r ON r.inventor_id = i.inventor_id
            GROUP BY i.inventor_id, inventor_name
        )
        SELECT inventor_name, patents
        FROM inventor_counts
        WHERE patents >= 2
        ORDER BY patents DESC, inventor_name ASC
        LIMIT ?;
    """,
    # Q7: Ranking Query (window function)
    "q7_ranking": """
        SELECT inventor_name, patent_count, patent_rank
        FROM (
            SELECT
                i.name AS inventor_name,
                COUNT(DISTINCT r.patent_id) AS patent_count,
                RANK() OVER (ORDER BY COUNT(DISTINCT r.patent_id) DESC) AS patent_rank
            FROM relationships r
            JOIN inventors i ON i.inventor_id = r.inventor_id
            GROUP BY i.inventor_id, inventor_name
        ) ranked
        ORDER BY patent_rank ASC, inventor_name ASC
        LIMIT ?;
    """,
}


def run_analysis(db_path: Path, reports_dir: Path, top_n: int) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        total_patents = pd.read_sql_query(
            "SELECT COUNT(*) AS total_patents FROM patents", conn
        )
        top_inventors = pd.read_sql_query(
            QUERIES["q1_top_inventors"], conn, params=[top_n]
        )
        top_companies = pd.read_sql_query(
            QUERIES["q2_top_companies"], conn, params=[top_n]
        )
        top_countries = pd.read_sql_query(QUERIES["q3_top_countries"], conn)
        trends = pd.read_sql_query(QUERIES["q4_trends_over_time"], conn)

        # Export required CSV reports.
        top_inventors.to_csv(reports_dir / "top_inventors.csv", index=False)
        top_companies.to_csv(reports_dir / "top_companies.csv", index=False)
        top_countries.to_csv(reports_dir / "country_trends.csv", index=False)
        trends.to_csv(reports_dir / "trends_over_time.csv", index=False)

        json_report = {
            "total_patents": int(total_patents.loc[0, "total_patents"]),
            "top_inventors": [
                {"name": row["inventor_name"], "patents": int(row["patent_count"])}
                for _, row in top_inventors.iterrows()
            ],
            "top_companies": [
                {"name": row["company_name"], "patents": int(row["patent_count"])}
                for _, row in top_companies.iterrows()
            ],
            "top_countries": [
                {"country": row["country"], "share": round(int(row["patent_count"]) / int(total_patents.loc[0, "total_patents"]), 4)}
                for _, row in top_countries.head(top_n).iterrows()
            ],
        }

        (reports_dir / "patent_report.json").write_text(
            json.dumps(json_report, indent=2), encoding="utf-8"
        )

        _print_console_report(
            total_patents=int(total_patents.loc[0, "total_patents"]),
            top_inventors=top_inventors,
            top_companies=top_companies,
            top_countries=top_countries.head(top_n),
        )


def _print_console_report(
    total_patents: int,
    top_inventors: pd.DataFrame,
    top_companies: pd.DataFrame,
    top_countries: pd.DataFrame,
) -> None:
    print("================== PATENT REPORT ==================")
    print(f"Total Patents: {total_patents:,}")

    print("Top Inventors:")
    for idx, row in top_inventors.iterrows():
        print(f"  {idx + 1}. {row['inventor_name']} - {int(row['patent_count']):,}")

    print("Top Companies:")
    for idx, row in top_companies.iterrows():
        print(f"  {idx + 1}. {row['company_name']} - {int(row['patent_count']):,}")

    print("Top Countries:")
    for idx, row in top_countries.iterrows():
        print(f"  {idx + 1}. {row['country']} - {int(row['patent_count']):,}")
