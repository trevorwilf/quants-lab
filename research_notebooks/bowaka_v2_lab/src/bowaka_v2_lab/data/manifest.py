"""v2-tagged wrapper over bowaka_common.artifacts.dataset_manifest."""
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
    extras: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    base_extras = {"strategy_id": "bowaka_v2"}
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
