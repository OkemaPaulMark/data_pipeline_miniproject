"""
Builds clean_relationships.csv from the two temp files in chunks.
Run from the project root: python build_relationships.py
"""
import pandas as pd
from pathlib import Path

CLEAN_DIR = Path("data/clean")
CHUNK_SIZE = 100_000

inv_rel_path = CLEAN_DIR / "_inv_rel_temp.csv"
comp_rel_path = CLEAN_DIR / "_comp_rel_temp.csv"
out_path = CLEAN_DIR / "clean_relationships.csv"


def main():
    # Load comp_rel fully — it's the smaller file (378MB)
    print("Loading company-patent pairs...")
    comp_rel = pd.read_csv(comp_rel_path)
    comp_rel["patent_id"] = comp_rel["patent_id"].astype(str).str.strip()
    comp_rel["company_id"] = comp_rel["company_id"].astype(str).str.strip()
    print(f"  {len(comp_rel):,} company-patent pairs")

    # Stream inv_rel in chunks and join against comp_rel
    print("Joining inventor pairs chunk by chunk...")
    first = True
    total = 0
    for i, chunk in enumerate(pd.read_csv(inv_rel_path, chunksize=CHUNK_SIZE)):
        chunk["patent_id"] = chunk["patent_id"].astype(str).str.strip()
        chunk["inventor_id"] = chunk["inventor_id"].astype(str).str.strip()

        merged = (
            chunk.merge(comp_rel, on="patent_id", how="inner")
            [["patent_id", "inventor_id", "company_id"]]
            .drop_duplicates()
        )

        merged.to_csv(out_path, mode="w" if first else "a", header=first, index=False)
        first = False
        total += len(merged)

        if (i + 1) % 10 == 0:
            print(f"  processed {(i + 1) * CHUNK_SIZE:,} inventor rows → {total:,} relationships so far")

    print(f"\nDone — {total:,} relationships saved to {out_path}")

    inv_rel_path.unlink()
    comp_rel_path.unlink()
    print("Temp files deleted")


if __name__ == "__main__":
    main()
