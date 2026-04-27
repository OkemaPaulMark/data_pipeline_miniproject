import pandas as pd
from pathlib import Path

CLEAN_DIR = Path("data/clean")
NROWS = 500_000


def load_data():
    patents = pd.read_csv(
        CLEAN_DIR / "clean_patents.csv",
        usecols=["patent_id", "year", "abstract"],
        nrows=NROWS,
        low_memory=False,
    )
    inventors = pd.read_csv(
        CLEAN_DIR / "clean_inventors.csv",
        usecols=["inventor_id", "name", "country"],
        nrows=NROWS,
    )
    companies = pd.read_csv(
        CLEAN_DIR / "clean_companies.csv",
        usecols=["company_id", "name"],
        nrows=NROWS,
    )
    relationships = pd.read_csv(
        CLEAN_DIR / "clean_relationships.csv",
        usecols=["patent_id", "inventor_id", "company_id"],
        nrows=NROWS,
    )
    locations = pd.read_csv(
        CLEAN_DIR / "clean_locations.csv",
        usecols=["location_id", "country"],
    ) if (CLEAN_DIR / "clean_locations.csv").exists() else None

    # Load full year column from entire patents CSV for accurate year charts
    all_years = pd.read_csv(
        CLEAN_DIR / "clean_patents.csv",
        usecols=["year"],
        low_memory=False,
    )

    return patents, inventors, companies, relationships, locations, all_years


def get_summary_stats(patents, inventors, companies, relationships, locations):
    return {
        "Total Patents": len(patents),
        "Total Inventors": len(inventors),
        "Total Companies": len(companies),
        "Total Relationships": len(relationships),
    }
