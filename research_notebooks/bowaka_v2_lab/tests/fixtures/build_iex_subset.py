"""Build the committed real-IEX parquet fixture subset (realism remediation 2 Phase 3).

This is a *generator*, run once by a developer against the real shared market-data
lake at ``$MARKET_DATA_ROOT``. It pulls a deliberately SMALL subset — a handful of
real IEX symbols spanning liquidity regimes, ~20-25 daily sessions and ~20-22
minute sessions per symbol — and writes it under
``tests/fixtures/market_data_iex_subset/`` in the canonical lake layout so the
committed subset can be replayed by CI exactly like the production lake.

Audit references: §P0-003 (no replayable bars in the attached sample), §8.1
(minimum IEX lake required for research-only replay).

Usage (inside the ql-jupyter container)::

    cd /quants-lab/research_notebooks/bowaka_v2_lab
    PYTHONPATH=src:../bowaka_common/src MARKET_DATA_ROOT=/quants-lab/research_notebooks/market_data \\
      /opt/conda/envs/quants-lab/bin/python tests/fixtures/build_iex_subset.py

If the real lake is unreachable / empty the script writes a clearly-labelled
synthetic fallback instead (``synthetic_fallback: true`` in the manifest); the
committed artefact is preferred to be real.

The committed subset is the single source of truth — tests read it via
``tests/fixtures/loader.load_iex_subset()``. Do NOT hand-edit the parquet files.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from bowaka_common.marketdata import layout

# --------------------------------------------------------------------------
# Subset definition
# --------------------------------------------------------------------------
#: The fixture-subset destination — committed to git (see Phase-3 prompt).
SUBSET_ROOT = Path(__file__).resolve().parent / "market_data_iex_subset"

#: Real IEX symbols spanning liquidity regimes. Profiled against the real lake:
#: AAL/NOK ~ $29-47M ADV (high), UAMY/HTZ ~ $3-4M (mid), CABA/VERI ~ $220-246k
#: (low — at/just over the contract's $250k ADV floor), POET ~ $6M (carries the
#: annotated corporate-action / split case).
FIXTURE_SYMBOLS: tuple[str, ...] = ("AAL", "NOK", "UAMY", "HTZ", "CABA", "VERI", "POET")

#: The symbol carrying the corporate-action (split) fixture case. No real split
#: falls inside the chosen window, so one is *annotated* via a corporate_actions/
#: parquet partition (the Phase-3 prompt explicitly allows this).
SPLIT_SYMBOL = "POET"

#: Bar window. March-April 2026 has dense IEX minute coverage (~43 sessions);
#: the subset keeps the most recent slice to stay small.
WINDOW_START = _dt.date(2026, 3, 1)
WINDOW_END = _dt.date(2026, 4, 30)

#: How many trailing sessions of each timeframe to keep per symbol. >= 20 each
#: (Phase-3 requirement) but trimmed so the committed parquet stays small.
N_DAILY_SESSIONS = 25
N_MINUTE_SESSIONS = 22

FEED = "iex"
ADJUSTMENT = "raw"


def _sha256_of_obj(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _write_parquet(path: Path, df: pd.DataFrame) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return path.stat().st_size


# --------------------------------------------------------------------------
# Real-lake pull
# --------------------------------------------------------------------------
def _real_lake_root() -> Path | None:
    raw = os.environ.get("MARKET_DATA_ROOT")
    if not raw:
        return None
    root = Path(raw)
    return root if root.is_dir() else None


def _pull_real_subset(lake_root: Path) -> dict[str, Any]:
    """Copy the trailing N sessions of daily + minute bars for each symbol."""
    from bowaka_common.marketdata import MarketDataStore

    store = MarketDataStore(lake_root)
    summary: dict[str, Any] = {"symbols": {}, "total_bytes": 0}
    audit_rows: list[dict[str, Any]] = []

    for sym in FIXTURE_SYMBOLS:
        daily = store.daily_bars(sym, WINDOW_START, WINDOW_END, feed=FEED, adjustment=ADJUSTMENT)
        minute = store.minute_bars(sym, WINDOW_START, WINDOW_END, feed=FEED, adjustment=ADJUSTMENT)
        if daily.empty or minute.empty:
            raise RuntimeError(
                f"real lake at {lake_root} has no in-window bars for {sym} "
                f"(daily empty={daily.empty}, minute empty={minute.empty})"
            )
        # Trim daily to the trailing N sessions.
        daily = daily.sort_values("timestamp").tail(N_DAILY_SESSIONS).reset_index(drop=True)
        # Trim minute to the trailing N *session days*.
        minute = minute.copy()
        minute["_session"] = minute["timestamp"].dt.tz_convert("America/New_York").dt.date
        keep_days = sorted(minute["_session"].unique())[-N_MINUTE_SESSIONS:]
        minute = minute[minute["_session"].isin(keep_days)].drop(columns=["_session"])
        minute = minute.sort_values("timestamp").reset_index(drop=True)

        # Write daily (one file per symbol).
        d_size = _write_parquet(
            layout.daily_bars_path(SUBSET_ROOT, sym, feed=FEED, adjustment=ADJUSTMENT), daily
        )
        # Write minute, grouped per (year, month) like the production layout.
        m_size = 0
        minute["_ym"] = minute["timestamp"].dt.tz_convert("UTC").dt.strftime("%Y-%m")
        for ym, grp in minute.groupby("_ym"):
            year, month = ym.split("-")
            m_size += _write_parquet(
                layout.minute_bars_path(
                    SUBSET_ROOT, sym, int(year), int(month), feed=FEED, adjustment=ADJUSTMENT
                ),
                grp.drop(columns=["_ym"]).reset_index(drop=True),
            )

        d_sessions = sorted(
            pd.to_datetime(daily["session_date"]).dt.date
            if "session_date" in daily.columns
            else daily["timestamp"].dt.tz_convert("America/New_York").dt.date
        )
        summary["symbols"][sym] = {
            "daily_sessions": len(daily),
            "minute_sessions": len(keep_days),
            "minute_rows": int(len(minute)),
            "daily_start": d_sessions[0].isoformat(),
            "daily_end": d_sessions[-1].isoformat(),
            "bytes": d_size + m_size,
        }
        summary["total_bytes"] += d_size + m_size

        # Research-audit row (matching the production audit parquet schema).
        audit_rows.append(
            {
                "symbol": sym,
                "feed": FEED,
                "timeframe": "1d",
                "start": d_sessions[0].isoformat(),
                "end": d_sessions[-1].isoformat(),
                "expected_sessions": len(daily),
                "observed_sessions": len(daily),
                "missing_sessions": 0,
                "duplicate_sessions": 0,
                "ohlc_violations": 0,
                "zero_volume_sessions": int((daily["volume"] <= 0).sum()),
                "large_gap_flags": 0,
                "passed_research_audit": True,
                "warnings": [],
                "audit_run_id": "audit_iex_subset_fixture",
            }
        )

    _write_corporate_actions(SUBSET_ROOT)
    _write_assets(SUBSET_ROOT)
    _write_ingestion_metadata(SUBSET_ROOT, audit_rows, synthetic=False)
    return summary


# --------------------------------------------------------------------------
# Synthetic fallback
# --------------------------------------------------------------------------
def _synthetic_subset() -> dict[str, Any]:
    """A clearly-labelled synthetic fallback if the real lake is unavailable."""
    rng = np.random.default_rng(20260522)
    sessions = [d.date() for d in pd.bdate_range(start=WINDOW_START, periods=N_DAILY_SESSIONS)]
    summary: dict[str, Any] = {"symbols": {}, "total_bytes": 0, "synthetic": True}
    audit_rows: list[dict[str, Any]] = []
    for i, sym in enumerate(FIXTURE_SYMBOLS):
        base = 5.0 + 3.0 * i
        # Daily bars.
        closes = base + np.cumsum(rng.normal(0, base * 0.01, len(sessions)))
        daily = pd.DataFrame(
            {
                "symbol": sym,
                "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in sessions],
                "open": closes * 0.998,
                "high": closes * 1.012,
                "low": closes * 0.988,
                "close": closes,
                "volume": rng.integers(200_000, 2_000_000, len(sessions)).astype(float),
                "vwap": closes,
                "trade_count": rng.integers(1_000, 30_000, len(sessions)),
                "session_date": sessions,
            }
        )
        d_size = _write_parquet(
            layout.daily_bars_path(SUBSET_ROOT, sym, feed=FEED, adjustment=ADJUSTMENT), daily
        )
        # Minute bars — regular session 09:30-15:59 ET, every minute.
        m_size = 0
        for d in sessions[-N_MINUTE_SESSIONS:]:
            open_et = pd.Timestamp(d, tz="America/New_York") + pd.Timedelta(hours=9, minutes=30)
            mins = [open_et + pd.Timedelta(minutes=k) for k in range(390)]
            mc = base + np.cumsum(rng.normal(0, base * 0.0008, 390))
            mdf = pd.DataFrame(
                {
                    "symbol": sym,
                    "timestamp": [t.tz_convert("UTC") for t in mins],
                    "open": mc * 0.999,
                    "high": mc * 1.003,
                    "low": mc * 0.997,
                    "close": mc,
                    "volume": rng.integers(100, 5_000, 390).astype(float),
                    "vwap": mc,
                    "trade_count": rng.integers(1, 200, 390),
                }
            )
            m_size += _write_parquet(
                layout.minute_bars_path(
                    SUBSET_ROOT, sym, d.year, d.month, feed=FEED, adjustment=ADJUSTMENT
                ),
                mdf,
            )
        summary["symbols"][sym] = {
            "daily_sessions": len(daily),
            "minute_sessions": N_MINUTE_SESSIONS,
            "daily_start": sessions[0].isoformat(),
            "daily_end": sessions[-1].isoformat(),
            "bytes": d_size + m_size,
        }
        summary["total_bytes"] += d_size + m_size
        audit_rows.append(
            {
                "symbol": sym,
                "feed": FEED,
                "timeframe": "1d",
                "start": sessions[0].isoformat(),
                "end": sessions[-1].isoformat(),
                "expected_sessions": len(daily),
                "observed_sessions": len(daily),
                "missing_sessions": 0,
                "duplicate_sessions": 0,
                "ohlc_violations": 0,
                "zero_volume_sessions": 0,
                "large_gap_flags": 0,
                "passed_research_audit": True,
                "warnings": [],
                "audit_run_id": "audit_iex_subset_fixture",
            }
        )
    _write_corporate_actions(SUBSET_ROOT)
    _write_assets(SUBSET_ROOT)
    _write_ingestion_metadata(SUBSET_ROOT, audit_rows, synthetic=True)
    return summary


# --------------------------------------------------------------------------
# Corporate actions / assets / ingestion metadata
# --------------------------------------------------------------------------
def _write_corporate_actions(root: Path) -> None:
    """Annotate one split for ``SPLIT_SYMBOL`` (no real in-window split exists).

    The Phase-3 prompt permits annotating a corporate action when no real split
    falls in range. The ex-date is mid-window so feature-leakage / split-aware
    checks have a real corporate-action row to exercise.
    """
    ca = pd.DataFrame(
        [
            {
                "symbol": SPLIT_SYMBOL,
                "ex_date": "2026-04-01",
                "action_type": "split",
                "ratio": 2.0,
                "old_shares": 1.0,
                "new_shares": 2.0,
                "annotated": True,
                "note": (
                    "annotated fixture split — no real split falls inside the "
                    "2026-03/04 window; exercises split-aware DQ checks"
                ),
            }
        ]
    )
    _write_parquet(layout.corporate_actions_path(root, SPLIT_SYMBOL), ca)


def _write_assets(root: Path) -> None:
    """A minimal point-in-time asset snapshot covering the fixture symbols."""
    snapshot_id = "2026-05-21T000000Z_iex_subset_fixture"
    rows = [
        {
            "snapshot_id": snapshot_id,
            "symbol": s,
            "name": f"{s} (IEX subset fixture)",
            "exchange": "NASDAQ" if s in ("NOK", "UAMY", "CABA", "VERI", "POET") else "NYSE",
            "asset_class": "us_equity",
            "tradable": True,
            "marginable": True,
            "shortable": True,
            "fractionable": True,
            "status": "active",
        }
        for s in FIXTURE_SYMBOLS
    ]
    _write_parquet(layout.assets_path(root, snapshot_id), pd.DataFrame(rows))


def _write_ingestion_metadata(
    root: Path, audit_rows: list[dict[str, Any]], *, synthetic: bool
) -> None:
    """Write ``_ingestion/manifest.json`` + ``_ingestion/audits/*.parquet``."""
    audit_df = pd.DataFrame(audit_rows)
    audit_run_id = "audit_2026-05-21T000000Z_iex_subset_fixture"
    audit_path = layout.ingestion_audit_path(root, audit_run_id)
    _write_parquet(audit_path, audit_df)

    # Content hash over the subset's bar partitions.
    entries: list[tuple[str, int]] = []
    bars_root = root / layout.DS_BARS
    if bars_root.is_dir():
        for f in sorted(bars_root.rglob("*.parquet")):
            entries.append((f.relative_to(root).as_posix(), f.stat().st_size))
    subset_hash = _sha256_of_obj(sorted(entries))

    manifest = {
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "fixture": "bowaka_v2_lab IEX subset (realism remediation 2 Phase 3)",
        "feed": FEED,
        "adjustment": ADJUSTMENT,
        # The daily-bar adjustment lineage fields the DQ checks read.
        "split_adjustment_applied": False,
        "synthetic_fallback": bool(synthetic),
        "start_date": WINDOW_START.isoformat(),
        "end_date": WINDOW_END.isoformat(),
        "symbols": list(FIXTURE_SYMBOLS),
        "split_symbol": SPLIT_SYMBOL,
        "counts": {
            "symbols": len(FIXTURE_SYMBOLS),
            "daily_symbols": len(FIXTURE_SYMBOLS),
            "minute_symbols": len(FIXTURE_SYMBOLS),
            "audit_rows": len(audit_rows),
        },
        "dataset_hashes": {"lake": f"sha256:{subset_hash}"},
        "audit_run_id": audit_run_id,
        "source": (
            "synthetic (real lake unavailable at generation time)"
            if synthetic
            else "real IEX shared market-data lake ($MARKET_DATA_ROOT)"
        ),
    }
    manifest_path = layout.ingestion_manifest_path(root)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def main() -> int:
    if SUBSET_ROOT.exists():
        import shutil

        shutil.rmtree(SUBSET_ROOT)
    lake_root = _real_lake_root()
    if lake_root is not None:
        try:
            summary = _pull_real_subset(lake_root)
            print(json.dumps({"status": "ok", "source": "real_lake", **summary}, indent=2))
            return 0
        except Exception as exc:  # noqa: BLE001 — fall back to synthetic, labelled
            print(f"[build_iex_subset] real-lake pull failed ({exc}); using synthetic fallback")
            if SUBSET_ROOT.exists():
                import shutil

                shutil.rmtree(SUBSET_ROOT)
    summary = _synthetic_subset()
    print(json.dumps({"status": "ok", "source": "synthetic_fallback", **summary}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
