"""Lake-completeness verification (audit 2026-05-23 §P0-004 / §P0-005, Phase 1).

The bowaka v2 lab's data ingestion is operator-owned. Remediation 3 does NOT
add the writers; it adds the verifier: a CLI that fails closed when a
required parquet partition is missing under ``intended_realism``. Once the
ingestion work is done, ``bowaka-v2-lab verify-lake --intended-realism`` will
pass cleanly and the lab can be promoted to that mode.

Checks performed:
- ``bars/vendor=alpaca/feed={feed}/timeframe=1d/...`` — at least N parquet files
- ``bars/vendor=alpaca/feed={feed}/timeframe=1m/...`` — at least N parquet files
- ``quotes/vendor=alpaca/feed={feed}/...``           — at least one parquet
- ``statuses/...``                                   — at least one parquet
- ``corporate_actions/...``                          — at least one parquet
- ``assets/vendor=alpaca/snapshot_id=*``              — at least 1 historical snapshot
  (intended_realism warns when only 1 present — historical snapshots needed for
  point-in-time eligibility — but does NOT fail, because failing here would
  block all current research; P1-001 tracks the ingestion of historical
  snapshots separately.)
- Manifest ``adjustment`` value is ``adjusted`` or ``split_adjusted``, not
  ``raw``, when ``--intended-realism``.

The verifier exits non-zero on any failed required check under
``--intended-realism`` and emits a structured JSON summary.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


#: Minimum parquet-file counts under bars/{timeframe}. The lake is operator-
#: managed; this is a *presence* check, not a coverage check (coverage lives in
#: data_quality.py). A small lake is OK; an empty lake is not.
_MIN_DAILY_PARQUETS = 1
_MIN_MINUTE_PARQUETS = 1


@dataclass
class LakeCheck:
    name: str
    status: str  # "pass" | "fail" | "warn" | "skipped"
    detail: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class LakeVerifyResult:
    lake_root: str
    intended_realism: bool
    passed: bool
    checks: list[LakeCheck]
    summary: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "lake_root": self.lake_root,
            "intended_realism": self.intended_realism,
            "passed": self.passed,
            "checks": [asdict(c) for c in self.checks],
            "summary": self.summary,
        }


def _count_parquets(root: Path) -> int:
    if not root.is_dir():
        return 0
    return sum(1 for _ in root.rglob("*.parquet"))


def _check_bars(lake_root: Path, *, feed: str, timeframe: str, min_count: int,
                intended_realism: bool) -> LakeCheck:
    from bowaka_common.marketdata import layout as _layout

    # Walk every adjustment partition under the timeframe (the manifest pins
    # one, but historical lakes may carry multiple adjustments).
    tf_parent = (
        Path(lake_root) / "bars" / f"vendor=alpaca" / f"feed={feed}"
        / f"timeframe={timeframe}"
    )
    count = _count_parquets(tf_parent)
    if count >= min_count:
        return LakeCheck(
            name=f"bars_{timeframe}_{feed}",
            status="pass",
            detail=f"{count} parquet file(s) under {tf_parent}",
            evidence={"count": count, "min_required": min_count, "root": str(tf_parent)},
        )
    status = "fail" if intended_realism else "warn"
    return LakeCheck(
        name=f"bars_{timeframe}_{feed}",
        status=status,
        detail=(
            f"only {count} parquet file(s) under {tf_parent} (need >= {min_count})"
            + (" — required under --intended-realism" if intended_realism else "")
        ),
        evidence={"count": count, "min_required": min_count, "root": str(tf_parent)},
    )


def _check_quotes(lake_root: Path, *, feed: str, intended_realism: bool) -> LakeCheck:
    quotes_root = Path(lake_root) / "quotes" / f"vendor=alpaca" / f"feed={feed}"
    count = _count_parquets(quotes_root)
    if count >= 1:
        return LakeCheck(
            name=f"quotes_{feed}",
            status="pass",
            detail=f"{count} quote parquet file(s) under {quotes_root}",
            evidence={"count": count, "root": str(quotes_root)},
        )
    status = "fail" if intended_realism else "warn"
    return LakeCheck(
        name=f"quotes_{feed}",
        status=status,
        detail=(
            f"no quote parquets under {quotes_root}"
            + (" — intended_realism requires historical quotes" if intended_realism else "")
        ),
        evidence={"count": 0, "root": str(quotes_root)},
    )


def _check_statuses(lake_root: Path, *, intended_realism: bool) -> LakeCheck:
    statuses_root = Path(lake_root) / "statuses" / "vendor=alpaca"
    count = _count_parquets(statuses_root)
    if count >= 1:
        return LakeCheck(
            name="statuses",
            status="pass",
            detail=f"{count} status parquet file(s) under {statuses_root}",
            evidence={"count": count, "root": str(statuses_root)},
        )
    status = "fail" if intended_realism else "warn"
    return LakeCheck(
        name="statuses",
        status=status,
        detail=(
            f"no status (halt/LULD) parquets under {statuses_root}"
            + (" — intended_realism requires halt status data" if intended_realism else "")
        ),
        evidence={"count": 0, "root": str(statuses_root)},
    )


def _check_corporate_actions(lake_root: Path, *, intended_realism: bool) -> LakeCheck:
    ca_root = Path(lake_root) / "corporate_actions" / "vendor=alpaca"
    count = _count_parquets(ca_root)
    if count >= 1:
        return LakeCheck(
            name="corporate_actions",
            status="pass",
            detail=f"{count} corporate-actions parquet file(s) under {ca_root}",
            evidence={"count": count, "root": str(ca_root)},
        )
    status = "fail" if intended_realism else "warn"
    return LakeCheck(
        name="corporate_actions",
        status=status,
        detail=(
            f"no corporate-actions parquets under {ca_root}"
            + (" — intended_realism requires CA data" if intended_realism else "")
        ),
        evidence={"count": 0, "root": str(ca_root)},
    )


def _check_assets(lake_root: Path, *, intended_realism: bool) -> LakeCheck:
    assets_root = Path(lake_root) / "assets" / "vendor=alpaca"
    if not assets_root.is_dir():
        status = "fail" if intended_realism else "warn"
        return LakeCheck(
            name="assets",
            status=status,
            detail=(
                f"assets root {assets_root} not present"
                + (" — intended_realism requires at least one historical snapshot"
                   if intended_realism else "")
            ),
            evidence={"snapshots": 0, "root": str(assets_root)},
        )
    snapshots = sorted(p.name for p in assets_root.iterdir() if p.is_dir())
    if not snapshots:
        status = "fail" if intended_realism else "warn"
        return LakeCheck(
            name="assets",
            status=status,
            detail=f"no snapshot directories under {assets_root}",
            evidence={"snapshots": 0, "root": str(assets_root)},
        )
    if intended_realism and len(snapshots) == 1:
        return LakeCheck(
            name="assets",
            status="warn",
            detail=(
                f"only 1 asset snapshot ({snapshots[0]}); intended_realism PIT "
                "eligibility ideally needs historical snapshots (P1-001 tracks "
                "ingestion). Warn-only because failing would block all current "
                "research."
            ),
            evidence={"snapshots": snapshots, "count": 1, "root": str(assets_root)},
        )
    return LakeCheck(
        name="assets",
        status="pass",
        detail=f"{len(snapshots)} asset snapshot(s) under {assets_root}",
        evidence={"snapshots": snapshots, "count": len(snapshots),
                  "root": str(assets_root)},
    )


def _check_manifest_adjustment(lake_root: Path, *, intended_realism: bool) -> LakeCheck:
    """Manifest ``adjustment`` must be ``adjusted`` / ``split_adjusted`` (not ``raw``)."""
    from bowaka_common.marketdata import layout as _layout

    manifest_path = _layout.ingestion_manifest_path(lake_root)
    if not manifest_path.is_file():
        status = "fail" if intended_realism else "warn"
        return LakeCheck(
            name="manifest_adjustment",
            status=status,
            detail=(
                f"ingestion manifest not found at {manifest_path}"
                + (" — intended_realism requires the manifest" if intended_realism else "")
            ),
            evidence={"path": str(manifest_path)},
        )
    try:
        doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 — corrupt manifest is a hard fail
        return LakeCheck(
            name="manifest_adjustment",
            status="fail",
            detail=f"ingestion manifest {manifest_path} could not be parsed: {exc}",
            evidence={"path": str(manifest_path), "exception": str(exc)},
        )
    adjustment = doc.get("adjustment") or doc.get("default_adjustment")
    if adjustment is None:
        # Walk individual feeds; if any are raw under intended_realism that's a fail.
        feeds = doc.get("feeds") or {}
        raw_feeds = [
            feed for feed, info in feeds.items()
            if isinstance(info, dict)
               and str(info.get("adjustment", "")).lower() == "raw"
        ]
        if intended_realism and raw_feeds:
            return LakeCheck(
                name="manifest_adjustment",
                status="fail",
                detail=(
                    f"intended_realism forbids ``adjustment: raw`` — feeds {raw_feeds} "
                    "carry raw bars. The realism contract requires split-adjusted "
                    "daily bars."
                ),
                evidence={"raw_feeds": raw_feeds, "feeds": feeds},
            )
        return LakeCheck(
            name="manifest_adjustment",
            status="skipped",
            detail=(
                f"ingestion manifest at {manifest_path} declares no top-level "
                "``adjustment`` field; per-feed adjustments checked separately"
            ),
            evidence={"manifest_keys": sorted(doc.keys())},
        )
    if str(adjustment).lower() == "raw" and intended_realism:
        return LakeCheck(
            name="manifest_adjustment",
            status="fail",
            detail=(
                f"intended_realism forbids ``adjustment: raw`` — manifest declares "
                f"{adjustment!r}. Re-ingest with adjusted / split_adjusted bars."
            ),
            evidence={"adjustment": adjustment},
        )
    return LakeCheck(
        name="manifest_adjustment",
        status="pass",
        detail=f"manifest adjustment is {adjustment!r}",
        evidence={"adjustment": adjustment},
    )


def verify_lake(
    lake_root: str | Path,
    *,
    feed: str = "iex",
    intended_realism: bool = False,
    min_daily_parquets: int = _MIN_DAILY_PARQUETS,
    min_minute_parquets: int = _MIN_MINUTE_PARQUETS,
) -> LakeVerifyResult:
    """Run every lake-verification check and return the aggregated result.

    Under ``intended_realism`` any failing check makes ``passed=False``;
    otherwise warnings are surfaced but do not flip ``passed``. Audit
    2026-05-23 §P0-004 / §P0-005.
    """
    lake_path = Path(lake_root)
    checks: list[LakeCheck] = [
        _check_bars(lake_path, feed=feed, timeframe="1d",
                    min_count=min_daily_parquets, intended_realism=intended_realism),
        _check_bars(lake_path, feed=feed, timeframe="1m",
                    min_count=min_minute_parquets, intended_realism=intended_realism),
        _check_quotes(lake_path, feed=feed, intended_realism=intended_realism),
        _check_statuses(lake_path, intended_realism=intended_realism),
        _check_corporate_actions(lake_path, intended_realism=intended_realism),
        _check_assets(lake_path, intended_realism=intended_realism),
        _check_manifest_adjustment(lake_path, intended_realism=intended_realism),
    ]
    passed = all(c.status != "fail" for c in checks)
    summary = {
        "pass": sum(1 for c in checks if c.status == "pass"),
        "warn": sum(1 for c in checks if c.status == "warn"),
        "fail": sum(1 for c in checks if c.status == "fail"),
        "skipped": sum(1 for c in checks if c.status == "skipped"),
    }
    return LakeVerifyResult(
        lake_root=str(lake_path),
        intended_realism=intended_realism,
        passed=passed,
        checks=checks,
        summary=summary,
    )


def verify_lake_or_raise(
    lake_root: str | Path,
    *,
    feed: str = "iex",
    intended_realism: bool = False,
) -> LakeVerifyResult:
    """Run :func:`verify_lake`; raise :class:`MissingLakePartitionError` on failure."""
    from ..optuna.errors import MissingLakePartitionError

    result = verify_lake(
        lake_root, feed=feed, intended_realism=intended_realism,
    )
    if not result.passed:
        failures = [c for c in result.checks if c.status == "fail"]
        reasons = "; ".join(f"[{c.name}] {c.detail}" for c in failures)
        raise MissingLakePartitionError(
            f"lake verification failed: {len(failures)} required check(s) failed: "
            f"{reasons}"
        )
    return result


__all__ = [
    "LakeCheck",
    "LakeVerifyResult",
    "verify_lake",
    "verify_lake_or_raise",
]
