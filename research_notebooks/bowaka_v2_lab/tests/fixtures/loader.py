"""Test-side IEX fixture-subset loader (realism remediation 2 Phase 3).

Tests that need a *real, replayable* lake call :func:`load_iex_subset`. It
resolves a lake root from one of three sources, governed by the
``--lake-source`` pytest CLI option (default ``auto``):

- ``committed`` — the parquet subset committed under
  ``tests/fixtures/market_data_iex_subset/`` (audit §P0-003: a small, real,
  in-repo, deterministic replay set). This is the default for CI.
- ``lake`` — a freshly-pulled subset generated from the full shared lake at
  ``$MARKET_DATA_ROOT`` (preferred when a developer has the real lake mounted
  and wants to refresh).
- ``auto`` — committed if present, else ``lake``, else a labelled synthetic
  fallback.

The returned :class:`IexSubset` carries the lake ``root``, the symbol list, the
trading sessions covered, and whether the data is real or a synthetic fallback
(``synthetic_fallback``). Tests that depend on the *synthetic* path must mark
themselves ``@pytest.mark.synthetic_fallback`` and skip when the resolved subset
is real-only-required.
"""
from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from bowaka_common.marketdata import layout

#: The committed real-IEX subset (written by ``build_iex_subset.py``).
COMMITTED_SUBSET_ROOT = Path(__file__).resolve().parent / "market_data_iex_subset"


@dataclass(frozen=True)
class IexSubset:
    """A resolved IEX fixture lake the tests can replay against."""

    root: Path
    symbols: tuple[str, ...]
    sessions: tuple[_dt.date, ...]
    feed: str
    adjustment: str
    synthetic_fallback: bool
    source: str  # "committed" | "lake" | "synthetic"
    split_symbol: Optional[str]
    manifest: dict

    @property
    def daily_sessions(self) -> tuple[_dt.date, ...]:
        return self.sessions


def _load_manifest(root: Path) -> dict:
    path = layout.ingestion_manifest_path(root)
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _sessions_from_lake(root: Path, symbols: tuple[str, ...], feed: str, adjustment: str) -> tuple[_dt.date, ...]:
    """The union of daily-bar session dates across the subset symbols."""
    sessions: set[_dt.date] = set()
    for sym in symbols:
        path = layout.daily_bars_path(root, sym, feed=feed, adjustment=adjustment)
        if not path.is_file():
            continue
        df = pd.read_parquet(path)
        if df.empty:
            continue
        if "session_date" in df.columns:
            sessions |= set(pd.to_datetime(df["session_date"]).dt.date)
        elif "timestamp" in df.columns:
            sessions |= set(pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/New_York").dt.date)
    return tuple(sorted(sessions))


def _subset_from_root(root: Path, *, source: str) -> IexSubset:
    """Build an :class:`IexSubset` from a lake root that is already a subset."""
    manifest = _load_manifest(root)
    symbols = tuple(manifest.get("symbols") or [])
    if not symbols:
        # Discover from the bars/ tree if the manifest is silent.
        daily_root = layout.bars_timeframe_root(root, "1d", feed="iex", adjustment="raw")
        symbols = tuple(sorted(p.name.split("=", 1)[1] for p in daily_root.glob("symbol=*"))) if daily_root.is_dir() else ()
    feed = str(manifest.get("feed", "iex"))
    adjustment = str(manifest.get("adjustment", "raw"))
    sessions = _sessions_from_lake(root, symbols, feed, adjustment)
    return IexSubset(
        root=root,
        symbols=symbols,
        sessions=sessions,
        feed=feed,
        adjustment=adjustment,
        synthetic_fallback=bool(manifest.get("synthetic_fallback", False)),
        source=source,
        split_symbol=manifest.get("split_symbol"),
        manifest=manifest,
    )


def committed_subset_available() -> bool:
    """True when the committed real-IEX subset exists and has bar parquet."""
    if not COMMITTED_SUBSET_ROOT.is_dir():
        return False
    bars = COMMITTED_SUBSET_ROOT / layout.DS_BARS
    return bars.is_dir() and any(bars.rglob("*.parquet"))


def _generate_from_full_lake(dest: Path) -> Optional[Path]:
    """Pull a fresh subset from the full shared lake into ``dest``.

    Returns the subset root, or ``None`` when the full lake is unavailable.
    """
    import os

    raw = os.environ.get("MARKET_DATA_ROOT")
    if not raw or not Path(raw).is_dir():
        return None
    # Reuse the generator's real-lake puller, redirected at ``dest``.
    from tests.fixtures import build_iex_subset as _gen

    orig_root = _gen.SUBSET_ROOT
    try:
        _gen.SUBSET_ROOT = dest
        _gen._pull_real_subset(Path(raw))
    except Exception:  # noqa: BLE001 — a partial lake means "no fresh subset"
        return None
    finally:
        _gen.SUBSET_ROOT = orig_root
    return dest


def load_iex_subset(
    *,
    lake_source: str = "auto",
    tmp_path: Optional[Path] = None,
) -> IexSubset:
    """Resolve an IEX fixture lake for a test.

    Parameters
    ----------
    lake_source:
        ``committed`` | ``lake`` | ``auto`` — see the module docstring. The
        pytest ``--lake-source`` option supplies this via the ``lake_source``
        fixture in ``tests/conftest.py``.
    tmp_path:
        When ``lake_source`` resolves to ``lake`` a fresh subset is written
        here. Required for ``lake``; ignored otherwise.
    """
    source = str(lake_source or "auto").lower()
    if source not in ("committed", "lake", "auto"):
        raise ValueError(f"unknown lake-source {lake_source!r}; expected committed|lake|auto")

    if source == "committed":
        if not committed_subset_available():
            raise FileNotFoundError(
                f"--lake-source committed but no committed subset at {COMMITTED_SUBSET_ROOT}; "
                "run tests/fixtures/build_iex_subset.py"
            )
        return _subset_from_root(COMMITTED_SUBSET_ROOT, source="committed")

    if source == "lake":
        if tmp_path is None:
            raise ValueError("--lake-source lake requires a tmp_path to write the fresh subset")
        dest = _generate_from_full_lake(tmp_path / "iex_subset_from_lake")
        if dest is None:
            raise FileNotFoundError(
                "--lake-source lake but $MARKET_DATA_ROOT is unset or the full lake is unavailable"
            )
        return _subset_from_root(dest, source="lake")

    # auto: committed -> fresh lake pull -> synthetic.
    if committed_subset_available():
        return _subset_from_root(COMMITTED_SUBSET_ROOT, source="committed")
    if tmp_path is not None:
        dest = _generate_from_full_lake(tmp_path / "iex_subset_from_lake")
        if dest is not None:
            return _subset_from_root(dest, source="lake")
    # Last resort — a labelled synthetic subset.
    dest = (tmp_path / "iex_subset_synthetic") if tmp_path is not None else COMMITTED_SUBSET_ROOT
    from tests.fixtures import build_iex_subset as _gen

    orig_root = _gen.SUBSET_ROOT
    try:
        _gen.SUBSET_ROOT = dest
        _gen._synthetic_subset()
    finally:
        _gen.SUBSET_ROOT = orig_root
    return _subset_from_root(dest, source="synthetic")


__all__ = ["IexSubset", "load_iex_subset", "committed_subset_available", "COMMITTED_SUBSET_ROOT"]
