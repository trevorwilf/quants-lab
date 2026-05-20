"""Partitioned Parquet read/write helpers.

The layout follows ``[Report §8.3]``:

  parquet/bars/vendor=alpaca/feed=iex/timeframe=1d/adjustment=raw/symbol=RILY/part.parquet
  parquet/quotes/vendor=alpaca/feed=iex/session_date=2026-05-12/symbol=RILY.parquet
  parquet/candidates/strategy=bowaka/feed=iex/signal_date=2026-05-11/candidates.parquet
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


@dataclass(frozen=True)
class PathParts:
    """Hive-style partition tags for a Parquet artifact."""

    parts: dict[str, str]

    def __post_init__(self):
        for k, v in self.parts.items():
            if not isinstance(k, str) or not k:
                raise ValueError(f"PathParts key must be non-empty str, got {k!r}")
            if "=" in k or "/" in k or "\\" in k:
                raise ValueError(f"PathParts key {k!r} contains illegal char")
            if v is None:
                raise ValueError(f"PathParts value for {k!r} is None")
            if "/" in str(v) or "\\" in str(v):
                raise ValueError(f"PathParts value for {k!r} contains path separator: {v!r}")

    def as_path(self) -> Path:
        return Path(*(f"{k}={v}" for k, v in self.parts.items()))


class ParquetStore:
    """Wraps a root directory and writes Hive-partitioned files."""

    def __init__(self, root: Path | str):
        self.root = Path(root)

    def path_for(self, dataset: str, parts: PathParts, filename: str = "part.parquet") -> Path:
        return self.root / dataset / parts.as_path() / filename

    def write(
        self,
        df: pd.DataFrame,
        *,
        dataset: str,
        parts: PathParts,
        filename: str = "part.parquet",
        overwrite: bool = True,
    ) -> Path:
        target = self.path_for(dataset, parts, filename)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not overwrite:
            raise FileExistsError(f"{target} already exists and overwrite=False")
        table = pa.Table.from_pandas(df, preserve_index=False)
        pq.write_table(table, target)
        return target

    def read(self, dataset: str, parts: PathParts, filename: str = "part.parquet") -> pd.DataFrame:
        target = self.path_for(dataset, parts, filename)
        if not target.exists():
            raise FileNotFoundError(target)
        # pq.read_table() infers Hive partition columns from the on-disk path, which
        # would inject vendor=alpaca, etc. into the DataFrame. Read the file content
        # directly so the round-trip only contains the columns the caller wrote.
        return pq.ParquetFile(str(target)).read().to_pandas()

    def scan_dataset(self, dataset: str, *, filters: list[Any] | None = None) -> pd.DataFrame:
        root = self.root / dataset
        if not root.exists():
            return pd.DataFrame()
        dataset_obj = pq.ParquetDataset(root, filters=filters)
        return dataset_obj.read().to_pandas()
