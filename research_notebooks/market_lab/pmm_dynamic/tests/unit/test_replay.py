"""Tests for trial replay harness."""

import os
import json
import logging

import numpy as np
import pytest

from pmm_lab.utils.replay import (
    TrialRecord,
    save_trial_records,
    load_trial_records,
    replay_and_verify,
)


def _run_and_record(candles, pair_rules, bar_interval_seconds=300):
    """Helper: run a known config and return (TrialRecord, actual_objective)."""
    from pmm_lab.sim.executor_model import SimConfig
    from pmm_lab.sim.runner import CandleSimRunner
    from pmm_lab.metrics.metrics import compute_metrics
    from pmm_lab.objective.objective import objective_v1
    from pmm_lab.data.hashing import hash_candles

    config = SimConfig(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5],
        sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
    )

    runner = CandleSimRunner(config, pair_rules)
    result = runner.run(candles)
    metrics = compute_metrics(result, 100.0, candles, bar_interval_seconds)
    obj = objective_v1(metrics)

    # Build params dict that canonicalizer would accept
    params = {
        "macd_fast": config.macd_fast,
        "macd_slow": config.macd_slow,
        "macd_signal": config.macd_signal,
        "natr_length": config.natr_length,
        "buy_n_levels": 2,
        "sell_n_levels": 2,
        "buy_spread_base": 1.0,
        "buy_spread_ratio": 2.0,
        "sell_spread_base": 1.0,
        "sell_spread_ratio": 2.0,
        "buy_side_weight": 0.5,
        "amount_skew": 1.0,
        "total_amount_quote": 100.0,
        "executor_refresh_time": config.executor_refresh_time,
        "cooldown_time": config.cooldown_time,
        "stop_loss": config.stop_loss,
        "take_profit": config.take_profit,
        "time_limit": config.time_limit,
        "trailing_stop_activation": 0.0,
        "trailing_stop_delta": 0.001,
    }

    record = TrialRecord(
        trial_number=0,
        params=params,
        objective_value=obj.raw_score,
        dataset_hash=hash_candles(candles),
    )

    return record, obj.raw_score


# ── TrialRecord serialization tests ─────────────────────────────


class TestTrialRecordRoundtrip:
    def test_trial_record_to_json_roundtrip(self, tmp_path):
        record = TrialRecord(
            trial_number=5,
            params={"buy_spread_base": 1.5, "sell_spread_base": 2.0},
            objective_value=0.123456,
            reject_reason=None,
            dataset_hash="abc123",
            fold_scores=[0.1, 0.2, 0.3],
            user_attrs={"key": "value"},
        )
        path = str(tmp_path / "test.jsonl")
        save_trial_records([record], path)
        loaded = load_trial_records(path)
        assert len(loaded) == 1
        assert loaded[0].trial_number == 5
        assert loaded[0].params == record.params
        assert abs(loaded[0].objective_value - 0.123456) < 1e-10
        assert loaded[0].dataset_hash == "abc123"
        assert loaded[0].fold_scores == [0.1, 0.2, 0.3]
        assert loaded[0].user_attrs == {"key": "value"}


class TestSaveLoadMultiple:
    def test_save_load_multiple_records(self, tmp_path):
        records = [
            TrialRecord(trial_number=i, params={"x": i}, objective_value=float(i))
            for i in range(5)
        ]
        path = str(tmp_path / "multi.jsonl")
        save_trial_records(records, path)
        loaded = load_trial_records(path)
        assert len(loaded) == 5
        for i, r in enumerate(loaded):
            assert r.trial_number == i
            assert r.objective_value == float(i)


class TestLoadEmptyFile:
    def test_load_empty_file(self, tmp_path):
        path = str(tmp_path / "empty.jsonl")
        with open(path, "w") as f:
            pass
        loaded = load_trial_records(path)
        assert loaded == []


class TestTrialRecordNoneFields:
    def test_trial_record_with_none_fields(self, tmp_path):
        record = TrialRecord(
            trial_number=0,
            params={"a": 1},
            objective_value=-999.0,
            reject_reason="bad params",
            fold_scores=None,
            user_attrs=None,
        )
        path = str(tmp_path / "none.jsonl")
        save_trial_records([record], path)
        loaded = load_trial_records(path)
        assert len(loaded) == 1
        assert loaded[0].fold_scores is None
        assert loaded[0].user_attrs is None
        assert loaded[0].reject_reason == "bad params"


# ── Replay verification tests ───────────────────────────────────


class TestReplaySingleTrial:
    def test_replay_single_trial_matches(self, tmp_path, sample_candles_5m, default_pair_rules):
        record, expected_score = _run_and_record(sample_candles_5m, default_pair_rules)
        ref_price = float(np.median(sample_candles_5m["close"]))

        path = str(tmp_path / "trials.jsonl")
        save_trial_records([record], path)

        mismatches = replay_and_verify(
            path, sample_candles_5m, default_pair_rules,
            bar_interval_seconds=300,
            reference_price=ref_price,
            tolerance=1e-6,
        )
        assert len(mismatches) == 0


class TestReplayRejectedTrial:
    def test_replay_rejected_trial_matches(self, tmp_path, sample_candles_5m, default_pair_rules):
        from pmm_lab.objective.objective import REJECT_SCORE

        # Params that will be rejected: both sides zero levels
        params = {
            "macd_fast": 21, "macd_slow": 42, "macd_signal": 9, "natr_length": 14,
            "buy_n_levels": 0, "sell_n_levels": 0,
            "buy_spread_base": 1.0, "buy_spread_ratio": 2.0,
            "sell_spread_base": 1.0, "sell_spread_ratio": 2.0,
            "buy_side_weight": 0.5, "amount_skew": 1.0,
            "total_amount_quote": 100.0,
            "executor_refresh_time": 3120.0, "cooldown_time": 3120.0,
            "stop_loss": 0.03, "take_profit": 0.015,
            "time_limit": 43200,
            "trailing_stop_activation": 0.0, "trailing_stop_delta": 0.001,
        }

        record = TrialRecord(
            trial_number=0,
            params=params,
            objective_value=REJECT_SCORE,
            reject_reason="both sides zero",
        )

        ref_price = float(np.median(sample_candles_5m["close"]))
        path = str(tmp_path / "rejected.jsonl")
        save_trial_records([record], path)

        mismatches = replay_and_verify(
            path, sample_candles_5m, default_pair_rules,
            bar_interval_seconds=300,
            reference_price=ref_price,
        )
        assert len(mismatches) == 0


class TestReplayDetectsMismatch:
    def test_replay_detects_mismatch(self, tmp_path, sample_candles_5m, default_pair_rules):
        record, actual_score = _run_and_record(sample_candles_5m, default_pair_rules)
        # Tamper with objective value
        record.objective_value = actual_score + 999.0

        ref_price = float(np.median(sample_candles_5m["close"]))
        path = str(tmp_path / "bad.jsonl")
        save_trial_records([record], path)

        mismatches = replay_and_verify(
            path, sample_candles_5m, default_pair_rules,
            bar_interval_seconds=300,
            reference_price=ref_price,
        )
        assert len(mismatches) == 1
        assert mismatches[0]["trial_number"] == 0


class TestReplayMaxReplays:
    def test_replay_max_replays_limits_count(self, tmp_path, sample_candles_5m, default_pair_rules):
        record, _ = _run_and_record(sample_candles_5m, default_pair_rules)
        records = []
        for i in range(5):
            r = TrialRecord(
                trial_number=i,
                params=record.params,
                objective_value=record.objective_value,
                dataset_hash=record.dataset_hash,
            )
            records.append(r)

        ref_price = float(np.median(sample_candles_5m["close"]))
        path = str(tmp_path / "many.jsonl")
        save_trial_records(records, path)

        mismatches = replay_and_verify(
            path, sample_candles_5m, default_pair_rules,
            bar_interval_seconds=300,
            reference_price=ref_price,
            max_replays=2,
        )
        # max_replays=2, all should match
        assert len(mismatches) == 0


class TestReplayWarnsOnHashMismatch:
    def test_replay_warns_on_hash_mismatch(self, tmp_path, sample_candles_5m, default_pair_rules, caplog):
        record, _ = _run_and_record(sample_candles_5m, default_pair_rules)
        record.dataset_hash = "wrong_hash_value"

        ref_price = float(np.median(sample_candles_5m["close"]))
        path = str(tmp_path / "hash_warn.jsonl")
        save_trial_records([record], path)

        with caplog.at_level(logging.WARNING):
            mismatches = replay_and_verify(
                path, sample_candles_5m, default_pair_rules,
                bar_interval_seconds=300,
                reference_price=ref_price,
            )

        assert any("hash mismatch" in r.message.lower() for r in caplog.records), \
            f"Expected hash mismatch warning, got: {[r.message for r in caplog.records]}"
        # Objective should still match
        assert len(mismatches) == 0
