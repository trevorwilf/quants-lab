"""Atomic run-dir writer.

Writes a parquet file or JSONL file into a run directory atomically
(tmp → fsync → rename). Partial writes on failure leave no half-written file.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except OSError:
                pass
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        finally:
            raise


def write_json(path: Path, obj: Any, *, indent: int | None = 2) -> None:
    payload = json.dumps(obj, sort_keys=True, indent=indent, default=str)
    _atomic_write_bytes(Path(path), payload.encode("utf-8"))


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    n = 0
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec, sort_keys=True, default=str))
                fh.write("\n")
                n += 1
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except OSError:
                pass
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        finally:
            raise
    return n


def write_parquet(path: Path, df: "object", *, compression: str = "snappy") -> None:
    import pandas as pd

    assert isinstance(df, pd.DataFrame), f"expected DataFrame, got {type(df).__name__}"
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        df.to_parquet(tmp, compression=compression, index=False)
        os.replace(tmp, path)
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except Exception:
                pass
        raise


def write_run_dir(
    run_dir: Path,
    *,
    json_files: dict[str, Any] | None = None,
    jsonl_files: dict[str, Iterable[dict[str, Any]]] | None = None,
    parquet_files: dict[str, "object"] | None = None,
) -> dict[str, int]:
    """Bulk-write a set of artifacts into ``run_dir``, returning per-file counts."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    if json_files:
        for name, obj in json_files.items():
            write_json(run_dir / name, obj)
            counts[name] = 1
    if jsonl_files:
        for name, recs in jsonl_files.items():
            counts[name] = write_jsonl(run_dir / name, recs)
    if parquet_files:
        for name, df in parquet_files.items():
            write_parquet(run_dir / name, df)
            try:
                counts[name] = int(getattr(df, "shape", (0,))[0])
            except Exception:
                counts[name] = -1
    return counts
