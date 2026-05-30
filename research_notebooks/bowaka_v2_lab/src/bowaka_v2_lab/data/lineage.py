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


def resolve_lake_root_with_dataset_lineage_fallback(
    cfg: Mapping[str, Any],
    dataset_lineage: Mapping[str, Any] | None,
) -> Path:
    """Resolve the lake root honouring a dataset_lineage fallback.

    Replay paths (paper-vs-sim reconciliation; cached fold artifacts) carry a
    ``dataset_lineage`` dict that may stamp a ``lake_root`` distinct from the
    cfg's — usually because the replay was recorded against a different lake
    mount. We honour that fallback (``cfg.market_data.shared_root`` > the
    lineage's ``lake_root`` > the resolver chain), then coerce the result so
    a buggy value (None or ``Path('None')``) raises loudly instead of
    silently producing empty suppliers downstream.

    The dataset-lineage callsites must not duplicate the
    ``cfg['market_data'].get('shared_root')`` pattern in their own code (the
    AST regression test refuses it outside ``data/lineage.py``).
    """
    md = cfg.get("market_data", {}) or {}
    explicit = md.get("shared_root")
    if explicit:
        return _coerce_lake_root(explicit)
    if dataset_lineage:
        lineage_root = dataset_lineage.get("lake_root") if isinstance(dataset_lineage, Mapping) else None
        if lineage_root:
            return _coerce_lake_root(lineage_root)
    return _coerce_lake_root(resolve_lake_root(cfg))


def _coerce_lake_root(value: Any) -> Path:
    """Defensive helper: reject obviously-bad lake-root values at the boundary.

    Returns the value as a normalised, absolute :class:`Path` if it represents
    a real path. Raises :class:`RuntimeError` if the value is ``None``,
    ``Path("None")``, an empty string, or otherwise non-resolvable.

    Use this anywhere a ``lake_root`` crosses an API boundary into code that
    reads parquet — particularly subprocess worker entry points, where a
    silently-empty supplier produces zero candidates and looks like a regime
    issue rather than a bug.

    The 2026-05-29 diagnostic traced "constant -1.5 objective" / "0 candidates"
    / "100% quote coverage" walkforward studies to ``md.get("shared_root")``
    returning ``None`` for shipping configs and being passed downstream as
    ``Path("None")``. This helper is the boundary guard so any future
    bypass of :func:`resolve_lake_root` fails loudly instead of silently.
    """
    if value is None:
        raise RuntimeError(
            "lake_root resolved to None. Use "
            "bowaka_v2_lab.data.lineage.resolve_lake_root(cfg) "
            "instead of cfg['market_data'].get('shared_root')."
        )
    coerced = Path(str(value)).resolve()
    sep = "\\" if "\\" in str(coerced) else "/"
    if coerced.name == "None" or str(coerced).endswith(f"{sep}None"):
        raise RuntimeError(
            f"lake_root coerced to {coerced!r}, which is the "
            "Path-stringification of None. Use "
            "bowaka_v2_lab.data.lineage.resolve_lake_root(cfg) "
            "instead of cfg['market_data'].get('shared_root')."
        )
    if str(coerced) == "" or str(value) == "":
        raise RuntimeError("lake_root coerced to empty Path.")
    return coerced


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


# Speedup hotfix 2026-05-26 — process-local cache for the per-partition
# rglob hashes. ``build_dataset_lineage`` is called per fold per trial
# inside ``run_backtest``; with ~30k parquet files in the bars tree the
# rglob alone dominates trial wall-clock (proven via py-spy dump on
# workers stuck in ``_bars_partitions_hash``). The lake is immutable for
# the duration of a study, so memoising by ``(lake_root, timeframe,
# manifest_generated_at)`` is safe — a re-ingestion auto-busts the cache
# because the manifest's ``generated_at`` timestamp changes.
_BARS_PARTITION_HASH_CACHE: dict[tuple[str, str, str], str] = {}


def _bars_partitions_hash(lake_root: Path, timeframe: str) -> str:
    """Per-partition hash of every symbol's bars for one timeframe (all feeds/adjustments).

    Cached by ``(str(lake_root), timeframe, manifest_generated_at)`` so a
    walk-forward study with ~30k bar parquets pays the rglob cost once
    per study, not once per (trial × fold).
    """
    # Walk the whole bars/<timeframe-aware> tree: layout nests
    # bars/vendor=*/feed=*/timeframe=<tf>/adjustment=*/symbol=*/...
    bars_root = lake_root / _layout.DS_BARS
    if not bars_root.is_dir():
        return _sha256_of_obj([])
    # Cache key derives from the lake manifest's ``generated_at`` — a
    # re-ingest re-stamps it and the cache misses, producing a fresh hash.
    manifest_gen_at = ""
    try:
        manifest_gen_at = str(
            (load_lake_manifest(lake_root) or {}).get("generated_at", "")
        )
    except Exception:  # noqa: BLE001 — best-effort cache key; fall back to no key
        pass
    key = (str(lake_root), timeframe, manifest_gen_at)
    cached = _BARS_PARTITION_HASH_CACHE.get(key)
    if cached is not None:
        return cached
    entries: list[tuple[str, int]] = []
    for tf_dir in sorted(bars_root.glob(f"vendor=*/feed=*/timeframe={timeframe}/adjustment=*")):
        for f in sorted(tf_dir.rglob("*.parquet")):
            try:
                size = f.stat().st_size
            except OSError:
                size = -1
            entries.append((f.relative_to(bars_root).as_posix(), size))
    entries.sort()
    out = _sha256_of_obj(entries)
    _BARS_PARTITION_HASH_CACHE[key] = out
    return out


def _bars_partitions_hash_cache_clear() -> None:
    """Test hook: clear the per-partition hash cache."""
    _BARS_PARTITION_HASH_CACHE.clear()


# Same memoisation pattern as ``_bars_partitions_hash`` — see the speedup
# hotfix comment above. Keyed by ``(str(lake_root), kind, manifest_generated_at)``.
_PARTITION_HASH_CACHE: dict[tuple[str, str, str], str] = {}


def _cached_partition_hash(
    lake_root: Path, kind: str, builder,
) -> str:
    manifest_gen_at = ""
    try:
        manifest_gen_at = str(
            (load_lake_manifest(lake_root) or {}).get("generated_at", "")
        )
    except Exception:  # noqa: BLE001
        pass
    key = (str(lake_root), kind, manifest_gen_at)
    cached = _PARTITION_HASH_CACHE.get(key)
    if cached is not None:
        return cached
    out = builder()
    _PARTITION_HASH_CACHE[key] = out
    return out


def _quotes_partitions_hash(lake_root: Path) -> str:
    """Per-partition hash of the ``quotes/`` tree (empty-list hash when absent).

    Cached — see :data:`_PARTITION_HASH_CACHE`. The lake is immutable within
    a study, so re-running this per-trial would waste filesystem-walk time.
    """
    return _cached_partition_hash(
        lake_root, "quotes",
        lambda: _partition_files_hash(lake_root / _layout.DS_QUOTES),
    )


def _corp_actions_hash(lake_root: Path) -> str:
    """Per-partition hash of ``corporate_actions/``; ``"none"`` when the tree is absent.

    Cached — see :data:`_PARTITION_HASH_CACHE`.
    """
    ca_root = lake_root / _layout.DS_CORPORATE_ACTIONS
    if not ca_root.is_dir():
        return "none"
    return _cached_partition_hash(
        lake_root, "corp_actions",
        lambda: _partition_files_hash(ca_root),
    )


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


# --------------------------------------------------------------------------
# Content-addressed dataset hash (realism remediation 2 Phase 3, audit §P1-005)
# --------------------------------------------------------------------------
#: Process-local cache: ``parquet path -> (mtime_ns, size, footer_hash_hex)``.
#: A parquet's footer hash is re-derived only when its mtime / size changes, so
#: a study that hashes the same lake many times pays the read cost once.
_FOOTER_HASH_CACHE: dict[str, tuple[int, int, str]] = {}


def _parquet_footer_hash(path: Path) -> str:
    """SHA-256 of a parquet file's footer (schema + per-row-group metadata).

    The footer captures the schema and every row group's statistics / byte
    offsets — it changes whenever the payload changes, but is far cheaper to
    hash than the whole file. Cached by ``(mtime_ns, size)``; an unreadable
    parquet hashes to a stable ``"unreadable:<size>"`` token rather than raising.
    """
    try:
        st = path.stat()
    except OSError:
        return "missing"
    key = str(path)
    cached = _FOOTER_HASH_CACHE.get(key)
    if cached is not None and cached[0] == st.st_mtime_ns and cached[1] == st.st_size:
        return cached[2]
    footer_hex: str
    try:
        import pyarrow.parquet as pq

        md = pq.read_metadata(path)
        # Build a deterministic footer fingerprint from schema field-name+
        # field-type pairs (avoid ``str(md.schema)`` — pyarrow's __repr__ leaks
        # the object's memory address) plus per-row-group byte sizes + per-
        # column compressed sizes. This is stable across processes and gives a
        # content-aware fingerprint without depending on private pyarrow APIs.
        try:
            arrow_schema = md.schema.to_arrow_schema()
            schema_fp = "|".join(f"{f.name}:{str(f.type)}" for f in arrow_schema)
        except Exception:  # noqa: BLE001 — schema introspection failure
            schema_fp = f"num_columns={md.num_columns}"
        parts: list[str] = [schema_fp, str(md.num_rows), str(md.num_row_groups)]
        for rg in range(md.num_row_groups):
            rgm = md.row_group(rg)
            parts.append(str(rgm.total_byte_size))
            for col in range(rgm.num_columns):
                cm = rgm.column(col)
                # Mix in column statistics (min/max/null_count) so a one-cell
                # payload edit changes the footer hash even when the compressed
                # column size is identical.
                stats = getattr(cm, "statistics", None)
                stats_fp = ""
                if stats is not None:
                    try:
                        stats_fp = (
                            f"min={stats.min!r}|max={stats.max!r}|"
                            f"nulls={stats.null_count}|distinct={stats.distinct_count}"
                        )
                    except Exception:  # noqa: BLE001 — stats may be partially populated
                        stats_fp = ""
                parts.append(
                    f"{cm.path_in_schema}:{cm.total_compressed_size}:{stats_fp}"
                )
        footer_bytes = "|".join(parts).encode("utf-8")
        footer_hex = _sha256_hex(footer_bytes)
    except Exception:  # noqa: BLE001 — pyarrow missing / corrupt parquet
        footer_hex = f"unreadable:{st.st_size}"
    _FOOTER_HASH_CACHE[key] = (st.st_mtime_ns, st.st_size, footer_hex)
    return footer_hex


def _all_lake_parquet_paths(lake_root: Path) -> list[Path]:
    """Every ``*.parquet`` under ``bars/`` / ``quotes/`` / ``corporate_actions/``.

    Sorted by relative POSIX path so the list is mount-location independent.
    Ingestion-metadata parquet (``_ingestion/audits/*``) is included — the audit
    parquet is part of the dataset's content lineage.
    """
    out: list[Path] = []
    for sub in (_layout.DS_BARS, _layout.DS_QUOTES, _layout.DS_CORPORATE_ACTIONS):
        root = lake_root / sub
        if root.is_dir():
            out.extend(root.rglob("*.parquet"))
    audits = _layout.ingestion_dir(lake_root) / "audits"
    if audits.is_dir():
        out.extend(audits.rglob("*.parquet"))
    return sorted(out, key=lambda p: p.relative_to(lake_root).as_posix())


def content_addressed_dataset_hash(
    *,
    lake_root: Path,
    config_hash: str,
    code_manifest_hash: str,
    adjustment_policy: Optional[str] = None,
) -> dict[str, Any]:
    """Content-addressed dataset hash over a real lake (audit §P1-005).

    SHA-256 over a canonical JSON object combining:

    - the lake ``_ingestion/manifest.json`` in canonical form,
    - the sorted list of every ``bars`` / ``quotes`` / ``corporate_actions`` /
      audit parquet relative path,
    - each parquet file's *footer* hash (schema + row-group metadata),
    - the asset snapshot id,
    - the adjustment policy,
    - the config hash,
    - the code-manifest hash.

    Editing one parquet byte changes that file's footer hash and therefore the
    dataset hash; re-running with identical inputs reproduces it byte-for-byte
    (footer hashes are cached by ``mtime + size`` to avoid re-reading).

    Returns ``{dataset_hash, components}`` — ``components`` is the pre-hash
    object, surfaced for forensics.
    """
    manifest = load_lake_manifest(lake_root) or {}
    parquet_paths = _all_lake_parquet_paths(lake_root)
    rel_paths = [p.relative_to(lake_root).as_posix() for p in parquet_paths]
    footer_hashes = {
        p.relative_to(lake_root).as_posix(): _parquet_footer_hash(p) for p in parquet_paths
    }
    adjustment = (
        str(adjustment_policy)
        if adjustment_policy is not None
        else lake_adjustment(manifest)
    )
    components: dict[str, Any] = {
        "manifest_canonical": json.dumps(manifest, sort_keys=True, separators=(",", ":"), default=str),
        "parquet_partition_paths": rel_paths,
        "parquet_footer_hashes": footer_hashes,
        "asset_snapshot_id": _assets_snapshot_id(lake_root),
        "adjustment_policy": adjustment,
        "config_hash": str(config_hash),
        "code_manifest_hash": str(code_manifest_hash),
    }
    return {
        "dataset_hash": _sha256_of_obj(components),
        "components": components,
    }


__all__ = [
    "build_dataset_lineage",
    "content_addressed_dataset_hash",
    "load_lake_manifest",
    "_coerce_lake_root",
    "resolve_lake_root",
    "resolve_lake_root_with_dataset_lineage_fallback",
    "uses_lake",
    "symbol_universe_hash",
    "lake_provider",
    "lake_adjustment",
    "lake_split_adjustment_applied",
    "quotes_partitions_available",
]
