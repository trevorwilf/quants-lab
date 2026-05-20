"""Atomic file I/O helpers (write-then-rename, JSONL appender, Parquet writer)."""
from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator

from .serialization import to_json


def atomic_write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """Write ``content`` to ``path`` atomically (tmp → rename)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(tmp_fd, "w", encoding=encoding) as fh:
            fh.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        finally:
            raise


def atomic_write_json(path: Path, obj: Any, *, indent: int | None = 2) -> None:
    atomic_write_text(Path(path), to_json(obj, indent=indent))


def append_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    """Append ``records`` to a JSONL file, returning count appended."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("a", encoding="utf-8") as fh:
        for rec in records:
            fh.write(to_json(rec))
            fh.write("\n")
            n += 1
    return n


def write_parquet(path: Path, df: "object", *, compression: str = "snappy") -> None:
    """Write a DataFrame to Parquet atomically (tmp → rename)."""
    import pandas as pd  # local import to keep utils import-light

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        assert isinstance(df, pd.DataFrame), f"expected DataFrame, got {type(df).__name__}"
        df.to_parquet(tmp_path, compression=compression, index=False)
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass
        raise


@contextmanager
def atomic_replace(path: Path) -> Iterator[Path]:
    """Yield a temp path; on success, rename it to ``path``."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        yield tmp
        os.replace(tmp, path)
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except Exception:
                pass
        raise
