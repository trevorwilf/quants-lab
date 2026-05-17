"""Stable, content-addressed dataset hashes.

Two datasets with the same canonical rows (regardless of physical row order)
hash to the same value. We sort by deterministic key columns before hashing.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

PREFIX = "sha256:"


def hash_dataframe(df: pd.DataFrame, *, sort_by: Sequence[str] | None = None) -> str:
    """Return a deterministic SHA-256 hash of a DataFrame's content."""
    if df.empty:
        return PREFIX + hashlib.sha256(b"").hexdigest()
    sortable = sort_by or sorted(df.columns)
    keys = [c for c in sortable if c in df.columns]
    sorted_df = df.sort_values(by=keys, kind="mergesort").reset_index(drop=True) if keys else df
    table = pa.Table.from_pandas(sorted_df, preserve_index=False)
    digest = hashlib.sha256()
    for batch in table.to_batches():
        digest.update(batch.serialize().to_pybytes())
    return PREFIX + digest.hexdigest()


def hash_parquet_files(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(Path(p) for p in paths):
        table = pq.read_table(path)
        df = table.to_pandas()
        digest.update(hash_dataframe(df).encode("utf-8"))
    return PREFIX + digest.hexdigest()


def hash_documents(docs: Iterable[dict], *, sort_keys: Sequence[str]) -> str:
    """Hash a sequence of dicts; sort by ``sort_keys`` first for determinism."""
    import json

    docs_list = list(docs)
    docs_list.sort(key=lambda d: tuple(d.get(k) for k in sort_keys))
    payload = json.dumps(docs_list, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return PREFIX + hashlib.sha256(payload).hexdigest()
