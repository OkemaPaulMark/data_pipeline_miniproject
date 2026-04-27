from __future__ import annotations

import pandas as pd


# ---------------------------------------------------------------------------
# Column aliases — maps target column name -> list of possible source names
# ---------------------------------------------------------------------------
COLUMN_ALIASES = {
    "patents": {
        "patent_id": ["patent_id", "id", "patent_number", "patent"],
        "title": ["title", "patent_title"],
        "abstract": ["abstract", "patent_abstract"],
        "filing_date": ["filing_date", "date", "application_date", "patent_date"],
    },
    "inventors": {
        "inventor_id": ["inventor_id", "id", "inventor"],
        "name_first": ["name_first", "inventor_name_first", "first_name",
                       "disambig_inventor_name_first"],
        "name_last": ["name_last", "inventor_name_last", "last_name",
                      "disambig_inventor_name_last"],
        "name": ["name", "inventor_name", "full_name"],
        "country": ["country", "country_code", "inventor_country"],
        "location_id": ["location_id"],
    },
    "companies": {
        "company_id": ["company_id", "id", "assignee_id"],
        "name": ["name", "company", "assignee_name", "organization",
                 "disambig_assignee_organization"],
    },
    "locations": {
        "location_id": ["location_id", "id"],
        "country": ["country", "country_code", "disambig_country"],
    },
}

REQUIRED_COLUMNS = {
    "patents": ["patent_id", "title", "abstract", "filing_date", "year"],
    "inventors": ["inventor_id", "name", "country"],
    "companies": ["company_id", "name"],
    "relationships": ["patent_id", "inventor_id", "company_id"],
    "locations": ["location_id", "country"],
}


def _standardize_columns(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    aliases = COLUMN_ALIASES[table_name]
    rename_map = {}
    normalized = {c.strip().lower(): c for c in df.columns}
    for target_col, candidates in aliases.items():
        for candidate in candidates:
            key = candidate.strip().lower()
            if key in normalized and normalized[key] not in rename_map.values():
                rename_map[normalized[key]] = target_col
                break
    return df.rename(columns=rename_map).copy()


def _ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df[columns]


# ---------------------------------------------------------------------------
# Per-chunk cleaners — each takes a raw chunk and returns a clean chunk
# ---------------------------------------------------------------------------

def clean_patents_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    df = _standardize_columns(chunk, "patents")
    if "year" not in df.columns:
        df["year"] = pd.to_datetime(df.get("filing_date"), errors="coerce").dt.year
    df = _ensure_columns(df, REQUIRED_COLUMNS["patents"])
    df["patent_id"] = df["patent_id"].astype(str).str.strip()
    df["title"] = df["title"].fillna("Unknown Title").astype(str).str.strip()
    df["abstract"] = df["abstract"].fillna("").astype(str).str.strip()
    df["filing_date"] = pd.to_datetime(df["filing_date"], errors="coerce").dt.date.astype("string")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df.dropna(subset=["patent_id"]).drop_duplicates(subset=["patent_id"])


def clean_inventors_chunk(chunk: pd.DataFrame, loc_map: dict) -> pd.DataFrame:
    df = _standardize_columns(chunk, "inventors")
    # Build full name
    if "name" not in df.columns:
        first = df.get("name_first", pd.Series("", index=df.index)).fillna("")
        last = df.get("name_last", pd.Series("", index=df.index)).fillna("")
        df["name"] = (first + " " + last).str.strip()
    # Resolve country from locations lookup
    if ("country" not in df.columns or df["country"].isna().all()) and loc_map:
        df["country"] = df.get("location_id", pd.Series(dtype=str)).map(loc_map)
    df = _ensure_columns(df, REQUIRED_COLUMNS["inventors"])
    df["inventor_id"] = df["inventor_id"].astype(str).str.strip()
    df["name"] = df["name"].replace("", "Unknown Inventor").fillna("Unknown Inventor").astype(str).str.strip()
    df["country"] = df["country"].fillna("UNK").astype(str).str.strip().str.upper()
    return df.dropna(subset=["inventor_id"]).drop_duplicates(subset=["inventor_id"])


def clean_companies_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    df = _standardize_columns(chunk, "companies")
    if "name" not in df.columns:
        org = df.get("disambig_assignee_organization", pd.Series("", index=df.index)).fillna("")
        first = df.get("disambig_assignee_individual_name_first", pd.Series("", index=df.index)).fillna("")
        last = df.get("disambig_assignee_individual_name_last", pd.Series("", index=df.index)).fillna("")
        individual = (first + " " + last).str.strip()
        df["name"] = org.where(org != "", individual)
    df = _ensure_columns(df, REQUIRED_COLUMNS["companies"])
    df["company_id"] = df["company_id"].astype(str).str.strip()
    df["name"] = df["name"].replace("", "Unknown Company").fillna("Unknown Company").astype(str).str.strip()
    return df.dropna(subset=["company_id"]).drop_duplicates(subset=["company_id"])


def clean_locations_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    df = _standardize_columns(chunk, "locations")
    df = _ensure_columns(df, REQUIRED_COLUMNS["locations"])
    df["location_id"] = df["location_id"].astype(str).str.strip()
    df["country"] = df["country"].fillna("UNK").astype(str).str.strip().str.upper()
    return df.dropna(subset=["location_id"]).drop_duplicates(subset=["location_id"])


def clean_inv_rel_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    """Extract (patent_id, inventor_id) pairs from an inventors chunk."""
    df = _standardize_columns(chunk, "inventors")
    if "patent_id" not in df.columns or "inventor_id" not in df.columns:
        return pd.DataFrame(columns=["patent_id", "inventor_id"])
    df = df[["patent_id", "inventor_id"]].dropna()
    df["patent_id"] = df["patent_id"].astype(str).str.strip()
    df["inventor_id"] = df["inventor_id"].astype(str).str.strip()
    return df.drop_duplicates()


def clean_comp_rel_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    """Extract (patent_id, company_id) pairs from an assignees chunk."""
    df = _standardize_columns(chunk, "companies")
    # After standardize, assignee_id becomes company_id
    if "patent_id" not in df.columns or "company_id" not in df.columns:
        return pd.DataFrame(columns=["patent_id", "company_id"])
    df = df[["patent_id", "company_id"]].dropna()
    df["patent_id"] = df["patent_id"].astype(str).str.strip()
    df["company_id"] = df["company_id"].astype(str).str.strip()
    return df.drop_duplicates()
