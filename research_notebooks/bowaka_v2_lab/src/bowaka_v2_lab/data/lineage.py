"""Content-derived dataset lineage for v2 backtests (realism Phase 2).

Replaces the placeholder ``dataset_hash = run_hash[:16]`` with a hash that is a
deterministic function of the actual market-data the run consumed. Two runs over
the same lake selection + config produce the same ``dataset_hash``; mutating one
minute parquet's size/mtime, the lake manifest, or the symbol universe changes it.

The hash is structured (a JSON object hashed with ``sort_keys=True``) so the
component hashes can also be surfaced in the run manifest for forensics.

Two regimes:

- **Lake-backed** — ``market_data.minute_bar_source`` / ``daily_bar_source`` is
  ``alpaca`` / ``shared``. The lake's ``_ingestion/manifest.json`` supplies the
  ``lake_manifest_hash``, ``adjustment`` and provider; ``bars/`` / ``quotes/`` /
  ``corporate_actions/`` are walked for per-partition (path, size) lists.
- **Synthetic** — no lake (smoke / fixture configs, or direct ``run_backtest``
  calls with synthetic suppliers). A deterministic hash is derived from
  ``{feed, date_range, symbol_universe_hash, lab_config_hash, synthetic: True}``.
  This must be stable and must never raise.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from bowaka_common.marketdata import layout as _layout
from bowaka_common.marketdata.store import resolve_market_data_root


# Bar timeframes the lineage hash walks, mapped to their layout roots.
_BARS_TIMEFRAMES = ("1d", "1m")


def _sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_of_obj(obj: Any) -> str:
    """SHA-256 hex of a JSON-canonicalised object (sorted keys, compact)."""
    return _sha256_hex(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    )


def symbol_universe_hash(symbols: Iterable[str]) -> str:
    """SHA-256 of the sorted, de-duplicated symbol list."""
    syms = sorted({str(s) for s in symbols if s})
    return _sha256_of_obj(syms)


def uses_lake(cfg: Mapping[str, Any]) -> bool:
    """True when the config points either bar feed at the shared market-data lake."""
    md = cfg.get("market_data", {}) or {}
    lake_sources = {"alpaca", "shared"}
    return (
        str(md.get("minute_bar_source", "fixture")) in lake_sources
        or str(md.get("daily_bar_source", "fixture")) in lake_sources
    )


def resolve_lake_root(cfg: Mapping[str, Any]) -> Path:
    """Resolve the lake root: ``market_data.shared_root`` > ``$MARKET_DATA_ROOT`` > in-repo default."""
    md = cfg.get("market_data", {}) or {}
    return resolve_market_data_root(md.get("shared_root"), create=False)


def load_lake_manifest(lake_root: Path) -> Optional[dict[str, Any]]:
    """Load the lake's ``_ingestion/manifest.json``; ``None`` if absent or unreadable."""
    path = _layout.ingestion_manifest_path(lake_root)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — a corrupt manifest must not crash a run
        return None


def _partition_files_hash(root: Path) -> str:
    """SHA-256 of the sorted ``(relative_path, size_bytes)`` list under ``root``.

    Walks every ``*.parquet`` recursively. An absent directory hashes to the
    hash of the empty list — stable, never raises. The relative path keeps the
    hash independent of where the lake is mounted.
    """
    entries: list[tuple[str, int]] = []
    if root.is_dir():
        for f in sorted(root.rglob("*.parquet")):
            try:
                size = f.stat().st_size
            except OSError:
                size = -1
            entries.append((f.relative_to(root).as_posix(), size))
    entries.sort()
    return _sha256_of_obj(entries)


def _bars_partitions_hash(lake_root: Path, timeframe: str) -> str:
    """Per-partition hash of every symbol's bars for one timeframe (all feeds/adjustments)."""
    # Walk the whole bars/<timeframe-aware> tree: layout nests
    # bars/vendor=*/feed=*/timeframe=<tf>/adjustment=*/symbol=*/...
    bars_root = lake_root / _layout.DS_BARS
    if not bars_root.is_dir():
        return _sha256_of_obj([])
    entries: list[tuple[str, int]] = []
    for tf_dir in sorted(bars_root.glob(f"vendor=*/feed=*/timeframe={timeframe}/adjustment=*")):
        for f in sorted(tf_dir.rglob("*.parquet")):
            try:
                size = f.stat().st_size
            except OSError:
                size = -1
            entries.append((f.relative_to(bars_root).as_posix(), size))
    entries.sort()
    return _sha256_of_obj(entries)


def _quotes_partitions_hash(lake_root: Path) -> str:
    """Per-partition hash of the ``quotes/`` tree (empty-list hash when absent)."""
    return _partition_files_hash(lake_root / _layout.DS_QUOTES)


def _corp_actions_hash(lake_root: Path) -> str:
    """Per-partition hash of ``corporate_actions/``; ``"none"`` when the tree is absent."""
    ca_root = lake_root / _layout.DS_CORPORATE_ACTIONS
    if not ca_root.is_dir():
        return "none"
    return _partition_files_hash(ca_root)


def quotes_partitions_available(lake_root: Path) -> bool:
    """True when a non-empty ``quotes/`` directory exists in the lake."""
    quotes_root = lake_root / _layout.DS_QUOTES
    if not quotes_root.is_dir():
        return False
    return any(quotes_root.rglob("*.parquet"))


def lake_provider(lake_manifest: Optional[Mapping[str, Any]]) -> str:
    """Provider string for a lake-backed run.

    The current lake manifest has no explicit ``provider`` key; the layout's
    canonical vendor is ``alpaca``, so that is the fallback.
    """
    if lake_manifest:
        for key in ("provider", "vendor", "source"):
            v = lake_manifest.get(key)
            if v:
                return str(v)
    return _layout.DEFAULT_VENDOR  # "alpaca"


def lake_adjustment(lake_manifest: Optional[Mapping[str, Any]]) -> str:
    """Adjustment policy declared by the lake manifest (default ``"raw"``)."""
    if lake_manifest:
        v = lake_manifest.get("adjustment")
        if v:
            return str(v)
    return _layout.DEFAULT_ADJUSTMENT  # "raw"


def lake_split_adjustment_applied(
    lake_manifest: Optional[Mapping[str, Any]],
) -> Optional[bool]:
    """Whether the lake applied split adjustments, per its manifest.

    Realism remediation 2 Phase 1 — reads the optional manifest
    ``split_adjustment_applied`` flag (extends the dataset-manifest schema).
    Returns ``None`` when the manifest omits the flag, so the caller can fall
    back to inferring it from the adjustment policy.
    """
    if lake_manifest:
        v = lake_manifest.get("split_adjustment_applied")
        if v is not None:
            return bool(v)
    return None


def _lake_manifest_hash(lake_manifest: Optional[Mapping[str, Any]]) -> str:
    """The lake's own content hash from ``dataset_hashes.lake``; ``"none"`` if absent."""
    if not lake_manifest:
        return "none"
    hashes = lake_manifest.get("dataset_hashes") or {}
    lake = hashes.get("lake")
    return str(lake) if lake else "none"


def _date_range(start: Any, end: Any) -> list[str]:
    """Normalise a ``[start, end]`` pair to ISO date strings."""

    def _iso(x: Any) -> str:
        if x is None:
            return "1970-01-01"
        if isinstance(x, _dt.datetime):
            return x.date().isoformat()
        if isinstance(x, _dt.date):
            return x.isoformat()
        return str(x)

    return [_iso(start), _iso(end)]


def build_dataset_lineage(
    *,
    cfg: Mapping[str, Any],
    symbols: Iterable[str],
    start: Any,
    end: Any,
    lab_config_hash: str,
) -> dict[str, Any]:
    """Build the structured dataset-lineage record for a run.

    Returns a dict with the full content-derived ``dataset_hash``, the component
    hashes (for forensics), the resolved ``provider`` and ``adjustment``, and the
    regime (``lake`` vs ``synthetic``). Never raises — a missing/corrupt lake
    degrades to the synthetic regime so direct ``run_backtest`` calls with
    synthetic suppliers keep working.
    """
    feed = str((cfg.get("market_data", {}) or {}).get("feed", "iex"))
    sym_hash = symbol_universe_hash(symbols)
    date_range = _date_range(start, end)

    lake_backed = uses_lake(cfg)
    lake_manifest: Optional[dict[str, Any]] = None
    lake_root: Optional[Path] = None
    if lake_backed:
        try:
            lake_root = resolve_lake_root(cfg)
            lake_manifest = load_lake_manifest(lake_root)
        except Exception:  # noqa: BLE001 — lake resolution must never crash a run
            lake_root = None
            lake_manifest = None
        # A lake-sourced config whose lake is unreadable still has no real
        # partitions to hash; fall back to the synthetic regime so the hash is
        # stable, but the DQ layer (see data_quality.py) records the defect.
        if lake_root is None or not lake_root.is_dir():
            lake_backed = False

    if lake_backed and lake_root is not None:
        components: dict[str, Any] = {
            "lake_manifest_hash": _lake_manifest_hash(lake_manifest),
            "feed": feed,
            "adjustment": lake_adjustment(lake_manifest),
            "date_range": date_range,
            "symbol_universe_hash": sym_hash,
            "daily_partitions_hash": _bars_partitions_hash(lake_root, "1d"),
            "minute_partitions_hash": _bars_partitions_hash(lake_root, "1m"),
            "quote_partitions_hash": _quotes_partitions_hash(lake_root),
            "assets_snapshot_id": _assets_snapshot_id(lake_root),
            "corp_actions_hash": _corp_actions_hash(lake_root),
            "lab_config_hash": lab_config_hash,
        }
        provider = lake_provider(lake_manifest)
        regime = "lake"
    else:
        # Synthetic regime: a deterministic hash that depends only on logical
        # inputs (no filesystem). Stable across hosts; never raises.
        components = {
            "feed": feed,
            "date_range": date_range,
            "symbol_universe_hash": sym_hash,
            "lab_config_hash": lab_config_hash,
            "synthetic": True,
        }
        provider = "fixture"
        regime = "synthetic"

    dataset_hash = _sha256_of_obj(components)
    return {
        "dataset_hash": dataset_hash,
        "regime": regime,
        "provider": provider,
        "adjustment": components.get("adjustment", "synthetic"),
        "components": components,
        "lake_root": str(lake_root) if lake_root is not None else None,
        "lake_manifest": lake_manifest,
    }


def _assets_snapshot_id(lake_root: Path) -> str:
    """Most-recent asset snapshot id under the lake, or ``"none"``."""
    assets_root = _layout.assets_root(lake_root)
    if not assets_root.is_dir():
        return "none"
    snaps = sorted(assets_root.glob("snapshot_id=*"))
    if not snaps:
        return "none"
    return snaps[-1].name.split("=", 1)[1]


__all__ = [
    "build_dataset_lineage",
    "load_lake_manifest",
    "resolve_lake_root",
    "uses_lake",
    "symbol_universe_hash",
    "lake_provider",
    "lake_adjustment",
    "lake_split_adjustment_applied",
    "quotes_partitions_available",
]
