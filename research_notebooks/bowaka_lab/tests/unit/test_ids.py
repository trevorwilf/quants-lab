"""Phase 1: deterministic ID generators."""

from __future__ import annotations

from datetime import date, datetime

from bowaka_lab.utils.ids import (
    asset_snapshot_id,
    counterfactual_id,
    ingestion_run_id,
    prefilter_run_id,
    run_id,
    trade_id,
)


def test_run_id_deterministic():
    started = datetime(2026, 5, 16, 22, 30)
    a = run_id(strategy="bowaka", config_hash="sha256:a13f0d", started_at=started, feed="iex")
    b = run_id(strategy="bowaka", config_hash="sha256:a13f0d", started_at=started, feed="iex")
    assert a == b


def test_run_id_changes_on_different_inputs():
    started = datetime(2026, 5, 16, 22, 30)
    a = run_id(strategy="bowaka", config_hash="sha256:a13f0d", started_at=started, feed="iex")
    b = run_id(strategy="bowaka", config_hash="sha256:other", started_at=started, feed="iex")
    assert a != b


def test_prefilter_run_id_format():
    pid = prefilter_run_id(signal_date=date(2026, 5, 11), feed="iex", config_hash="sha256:a13f0d")
    assert pid.startswith("prefilter_2026-05-11_iex_cfg_")


def test_trade_id_distinct_per_symbol():
    a = trade_id(symbol="RILY", trade_date=date(2026, 5, 12), entry_rule="fixed_time_0945", config_hash="sha256:x")
    b = trade_id(symbol="QS", trade_date=date(2026, 5, 12), entry_rule="fixed_time_0945", config_hash="sha256:x")
    assert a != b


def test_counterfactual_id_grid_no_collision():
    seen = set()
    for stop_pct in [0.05, 0.08, 0.10]:
        for target_pct in [0.08, 0.12, 0.20]:
            for fade in [None, 6, 8, 9]:
                cfid = counterfactual_id(
                    symbol="RILY",
                    trade_date=date(2026, 5, 12),
                    variant={"stop_pct": stop_pct, "target_pct": target_pct, "fade": fade},
                )
                assert cfid not in seen
                seen.add(cfid)


def test_ingestion_run_id_format():
    iid = ingestion_run_id(feed="iex", timeframe="1d", adjustment="raw", started_at=datetime(2026, 5, 16, 22, 10))
    assert iid.startswith("ingest_2026-05-16T221000Z_iex_1d_raw")


def test_asset_snapshot_id_format():
    sid = asset_snapshot_id(vendor="alpaca", captured_at=datetime(2026, 5, 16, 22, 0))
    assert sid.endswith("_alpaca_assets")
