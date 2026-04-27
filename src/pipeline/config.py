from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    project_root: Path
    raw_dir: Path
    clean_dir: Path
    reports_dir: Path
    db_path: Path
    top_n: int


def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[2]
    raw_dir = project_root / os.getenv("RAW_DIR", "data/raw")
    clean_dir = project_root / os.getenv("CLEAN_DIR", "data/clean")
    reports_dir = project_root / os.getenv("REPORTS_DIR", "reports")
    db_path = project_root / os.getenv("DB_PATH", "data/patents.db")
    top_n = int(os.getenv("TOP_N", "10"))

    return Settings(
        project_root=project_root,
        raw_dir=raw_dir,
        clean_dir=clean_dir,
        reports_dir=reports_dir,
        db_path=db_path,
        top_n=top_n,
    )


RAW_FILE_CANDIDATES = {
    "patents": ["patents", "g_patent"],
    "abstracts": ["abstracts", "g_patent_abstract"],
    "inventors": ["inventors", "g_inventor_disambiguated"],
    "companies": ["companies", "g_assignee_disambiguated"],
    "locations": ["locations", "g_location_disambiguated"],
}



def resolve_raw_file(
    raw_dir: Path,
    stems: list[str],
    *,
    required: bool,
) -> Path | None:
    for stem in stems:
        csv_path = raw_dir / f"{stem}.csv"
        tsv_path = raw_dir / f"{stem}.tsv"

        if csv_path.exists():
            return csv_path
        if tsv_path.exists():
            return tsv_path

    if required:
        expected = ", ".join(f"{stem}.csv/.tsv" for stem in stems)
        raise FileNotFoundError(f"Missing raw file. Tried: {expected} in {raw_dir}.")

    return None
