"""v2-tagged wrapper over bowaka_common.artifacts.dataset_manifest.

Realism remediation 2 Phase 1 (audit §P0-005): the v2 manifest carries two
adjustment-lineage fields beyond the shared schema —

- ``adjustment`` — the daily-bar adjustment policy (``raw`` / ``split_adjusted``
  / ``adjusted``); the data-quality ``adjustment_mismatch`` check reads it.
- ``split_adjustment_applied`` — an explicit boolean stating whether split
  adjustments were applied; the ``split_adjustment_mismatch`` check reads it,
  falling back to inferring from ``adjustment`` when it is absent.

Both are carried as ``extras`` (the shared dataset-manifest schema does not pin
them), so an absent flag never breaks validation.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from bowaka_common.artifacts.dataset_manifest import build_dataset_manifest


def build_v2_dataset_manifest(
    *,
    feed: str,
    symbols: Iterable[str],
    start_date: str,
    end_date: str,
    dataset_hash: str,
    bar_count: int,
    provider: str = "alpaca",
    adjustment: Optional[str] = None,
    split_adjustment_applied: Optional[bool] = None,
    extras: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    base_extras: dict[str, Any] = {"strategy_id": "bowaka_v2"}
    if adjustment is not None:
        base_extras["adjustment"] = str(adjustment)
    if split_adjustment_applied is not None:
        base_extras["split_adjustment_applied"] = bool(split_adjustment_applied)
    if extras:
        base_extras.update(extras)
    return build_dataset_manifest(
        provider=provider,
        feed=feed,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        dataset_hash=dataset_hash,
        bar_count=bar_count,
        extras=base_extras,
    )
