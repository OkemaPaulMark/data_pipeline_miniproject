from __future__ import annotations

from pathlib import Path

import pandas as pd

from .analyze import run_analysis
from .config import RAW_FILE_CANDIDATES, get_settings, resolve_raw_file
from .extract import read_chunks, CHUNK_SIZE
from .load import initialize_database, load_to_sqlite
from .transform import (
    clean_companies_chunk,
    clean_comp_rel_chunk,
    clean_inv_rel_chunk,
    clean_inventors_chunk,
    clean_locations_chunk,
    clean_patents_chunk,
)

ABSTRACT_ROW_LIMIT = 2_000_000


def run_pipeline() -> None:
    settings = get_settings()
    settings.clean_dir.mkdir(parents=True, exist_ok=True)

    # Resolve raw file paths
    raw_files = {}
    for table_name, candidates in RAW_FILE_CANDIDATES.items():
        file_path = resolve_raw_file(
            settings.raw_dir, candidates, required=(table_name == "patents")
        )
        if file_path:
            raw_files[table_name] = file_path
        else:
            print(f"[WARN] Optional raw file missing for '{table_name}'.")

    # ------------------------------------------------------------------
    # Step 1: Locations (small file — load fully to build country lookup)
    # ------------------------------------------------------------------
    print("[1/6] Processing locations...")
    loc_map = {}
    if "locations" in raw_files:
        loc_chunks = []
        for chunk in read_chunks(raw_files["locations"]):
            loc_chunks.append(clean_locations_chunk(chunk))
        locations_df = pd.concat(loc_chunks, ignore_index=True).drop_duplicates(subset=["location_id"])
        locations_df.to_csv(settings.clean_dir / "clean_locations.csv", index=False)
        loc_map = dict(zip(locations_df["location_id"], locations_df["country"]))
        print(f"   → {len(locations_df):,} locations")
        del locations_df, loc_chunks
    else:
        print("   → Skipped (no file)")

    # ------------------------------------------------------------------
    # Step 2: Abstracts — read first 2M rows, save as lookup dict
    # ------------------------------------------------------------------
    print(f"[2/6] Processing abstracts (first {ABSTRACT_ROW_LIMIT:,} rows)...")
    abstract_map = {}
    if "abstracts" in raw_files:
        rows_read = 0
        for chunk in read_chunks(raw_files["abstracts"]):
            remaining = ABSTRACT_ROW_LIMIT - rows_read
            if remaining <= 0:
                break
            chunk = chunk.head(remaining)
            # Column is patent_abstract in PatentsView
            col = "patent_abstract" if "patent_abstract" in chunk.columns else "abstract"
            chunk = chunk[["patent_id", col]].rename(columns={col: "abstract"})
            chunk["patent_id"] = chunk["patent_id"].astype(str).str.strip()
            chunk["abstract"] = chunk["abstract"].fillna("").astype(str).str.strip()
            abstract_map.update(dict(zip(chunk["patent_id"], chunk["abstract"])))
            rows_read += len(chunk)
        print(f"   → {len(abstract_map):,} abstracts loaded")
    else:
        print("   → Skipped (no file)")

    # ------------------------------------------------------------------
    # Step 3: Patents — chunk by chunk, merge abstract from lookup
    # ------------------------------------------------------------------
    print("[3/6] Processing patents...")
    patents_path = settings.clean_dir / "clean_patents.csv"
    first = True
    total_patents = 0
    for chunk in read_chunks(raw_files["patents"]):
        clean = clean_patents_chunk(chunk)
        # Merge abstract in — map from dict, empty string if not found
        clean["abstract"] = clean["patent_id"].map(abstract_map).fillna("")
        # Reorder columns to match schema
        clean = clean[["patent_id", "title", "abstract", "filing_date", "year"]]
        clean.to_csv(patents_path, mode="w" if first else "a", header=first, index=False)
        first = False
        total_patents += len(clean)
    print(f"   → {total_patents:,} patents")
    del abstract_map

    # ------------------------------------------------------------------
    # Step 4: Inventors — chunk by chunk
    # ------------------------------------------------------------------
    print("[4/6] Processing inventors...")
    inventors_path = settings.clean_dir / "clean_inventors.csv"
    first = True
    total_inventors = 0
    for chunk in read_chunks(raw_files["inventors"]):
        clean = clean_inventors_chunk(chunk, loc_map)
        clean.to_csv(inventors_path, mode="w" if first else "a", header=first, index=False)
        first = False
        total_inventors += len(clean)
    print(f"   → {total_inventors:,} inventors")

    # ------------------------------------------------------------------
    # Step 5: Companies — chunk by chunk
    # ------------------------------------------------------------------
    print("[5/6] Processing companies...")
    companies_path = settings.clean_dir / "clean_companies.csv"
    first = True
    total_companies = 0
    for chunk in read_chunks(raw_files["companies"]):
        clean = clean_companies_chunk(chunk)
        clean.to_csv(companies_path, mode="w" if first else "a", header=first, index=False)
        first = False
        total_companies += len(clean)
    print(f"   → {total_companies:,} companies")

    # ------------------------------------------------------------------
    # Step 6: Relationships — extract pairs from inventors + companies,
    #          join on patent_id, write to CSV
    # ------------------------------------------------------------------
    print("[6/7] Building relationships...")
    inv_rel_path = settings.clean_dir / "_inv_rel_temp.csv"
    comp_rel_path = settings.clean_dir / "_comp_rel_temp.csv"

    first = True
    for chunk in read_chunks(raw_files["inventors"]):
        pairs = clean_inv_rel_chunk(chunk)
        pairs.to_csv(inv_rel_path, mode="w" if first else "a", header=first, index=False)
        first = False

    first = True
    for chunk in read_chunks(raw_files["companies"]):
        pairs = clean_comp_rel_chunk(chunk)
        pairs.to_csv(comp_rel_path, mode="w" if first else "a", header=first, index=False)
        first = False

    print("   → Joining inventor + company pairs on patent_id...")
    inv_rel = pd.read_csv(inv_rel_path)
    comp_rel = pd.read_csv(comp_rel_path)
    relationships = (
        inv_rel.merge(comp_rel, on="patent_id", how="inner")
        [["patent_id", "inventor_id", "company_id"]]
        .drop_duplicates()
    )
    relationships.to_csv(settings.clean_dir / "clean_relationships.csv", index=False)
    print(f"   → {len(relationships):,} relationships")

    inv_rel_path.unlink(missing_ok=True)
    comp_rel_path.unlink(missing_ok=True)
    del inv_rel, comp_rel, relationships

    # ------------------------------------------------------------------
    # Step 7: Load into SQLite and run analysis
    # ------------------------------------------------------------------
    print("[7/7] Loading into database and running analysis...")
    schema_path = Path(__file__).resolve().parents[2] / "sql" / "schema.sql"
    initialize_database(settings.db_path, schema_path)

    clean_tables = {
        "patents":       pd.read_csv(settings.clean_dir / "clean_patents.csv"),
        "inventors":     pd.read_csv(settings.clean_dir / "clean_inventors.csv"),
        "companies":     pd.read_csv(settings.clean_dir / "clean_companies.csv"),
        "relationships": pd.read_csv(settings.clean_dir / "clean_relationships.csv"),
    }
    load_to_sqlite(clean_tables, settings.db_path)
    run_analysis(settings.db_path, settings.reports_dir, settings.top_n)

    print("\n✅ Pipeline complete!")


if __name__ == "__main__":
    run_pipeline()
