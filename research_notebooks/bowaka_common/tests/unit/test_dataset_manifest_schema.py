"""dataset_manifest builder: provider/feed/symbols/hash required."""
from __future__ import annotations

import pytest

from bowaka_common.artifacts.dataset_manifest import (
    DATASET_MANIFEST_SCHEMA_VERSION,
    build_dataset_manifest,
    validate_dataset_manifest,
)


def _ok(**overrides):
    base = dict(
        provider="alpaca",
        feed="iex",
        symbols=["AAPL", "MSFT"],
        start_date="2024-01-01",
        end_date="2024-12-31",
        dataset_hash="cafebabecafebabe",
        bar_count=12345,
    )
    base.update(overrides)
    return base


def test_basic_build() -> None:
    m = build_dataset_manifest(**_ok())
    assert m["schema_version"] == DATASET_MANIFEST_SCHEMA_VERSION
    assert m["symbols"] == ["AAPL", "MSFT"]
    validate_dataset_manifest(m)


def test_symbols_sorted_and_deduped() -> None:
    m = build_dataset_manifest(**_ok(symbols=["MSFT", "AAPL", "AAPL"]))
    assert m["symbols"] == ["AAPL", "MSFT"]


def test_empty_symbols_rejected() -> None:
    with pytest.raises(ValueError, match="symbols"):
        build_dataset_manifest(**_ok(symbols=[]))


def test_negative_bar_count_rejected() -> None:
    with pytest.raises(ValueError, match="bar_count"):
        build_dataset_manifest(**_ok(bar_count=-1))


def test_missing_provider_rejected() -> None:
    with pytest.raises(ValueError, match="provider"):
        build_dataset_manifest(**_ok(provider=""))


def test_missing_feed_rejected() -> None:
    with pytest.raises(ValueError, match="feed"):
        build_dataset_manifest(**_ok(feed=""))
