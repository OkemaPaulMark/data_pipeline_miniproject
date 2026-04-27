from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pandas as pd

CHUNK_SIZE = 100_000


def _detect_delimiter(file_path: Path) -> str:
    if file_path.suffix.lower() == ".tsv":
        return "\t"
    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
        sample = f.read(5000)
    if "\t" in sample and sample.count("\t") > sample.count(","):
        return "\t"
    return ","


def read_chunks(file_path: Path) -> Iterator[pd.DataFrame]:
    """Yield chunks of a CSV/TSV file one at a time."""
    delimiter = _detect_delimiter(file_path)
    for chunk in pd.read_csv(
        file_path,
        sep=delimiter,
        low_memory=False,
        chunksize=CHUNK_SIZE,
    ):
        yield chunk
