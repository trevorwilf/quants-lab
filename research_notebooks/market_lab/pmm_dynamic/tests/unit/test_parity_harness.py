"""Tests for parity framework (works without Hummingbot installed)."""

import os
from pathlib import Path
import numpy as np
import pytest

from pmm_lab.parity.fixtures import generate_frozen_fixture, load_frozen_fixture, FrozenFixture
from pmm_lab.parity.feature_parity import check_feature_parity_frozen, check_feature_parity_native, ParityResult
from pmm_lab.parity.export_parity import validate_export_comprehensive

_TEST_PARAMS = {
    "macd_fast": 21, "macd_slow": 42, "macd_signal": 9, "natr_length": 14,
    "buy_n_levels": 2, "sell_n_levels": 2,
    "buy_spread_base": 1.0, "buy_spread_ratio": 2.0,
    "sell_spread_base": 1.0, "sell_spread_ratio": 2.0,
    "buy_side_weight": 0.5, "amount_skew": 1.0,
    "total_amount_quote": 100.0,
    "executor_refresh_time": 3120.0, "cooldown_time": 3120.0,
    "stop_loss": 0.03, "take_profit": 0.015, "time_limit": 43200,
    "trailing_stop_activation": 0.0, "trailing_stop_delta": 0.001,
}


class TestGenerateFrozenFixture:
    def test_generate_frozen_fixture(self, tmp_path, sample_candles_5m):
        fixture_dir = generate_frozen_fixture(
            sample_candles_5m, _TEST_PARAMS, name="test", output_dir=str(tmp_path),
        )
        assert os.path.isdir(fixture_dir)
        assert os.path.isfile(os.path.join(fixture_dir, "candles.npy"))
        assert os.path.isfile(os.path.join(fixture_dir, "fixture.json"))


class TestLoadFrozenFixture:
    def test_load_frozen_fixture(self, tmp_path, sample_candles_5m):
        fixture_dir = generate_frozen_fixture(
            sample_candles_5m, _TEST_PARAMS, name="test", output_dir=str(tmp_path),
        )
        fixture = load_frozen_fixture(fixture_dir)
        assert isinstance(fixture, FrozenFixture)
        assert fixture.name == "test"
        assert isinstance(fixture.candles, np.ndarray)
        assert isinstance(fixture.config_params, dict)
        assert isinstance(fixture.expected_features, dict)
        assert isinstance(fixture.expected_yaml_fields, dict)
        assert isinstance(fixture.metadata, dict)


class TestFrozenFixtureCandlesMatch:
    def test_frozen_fixture_candles_match(self, tmp_path, sample_candles_5m):
        fixture_dir = generate_frozen_fixture(
            sample_candles_5m, _TEST_PARAMS, name="test", output_dir=str(tmp_path),
        )
        fixture = load_frozen_fixture(fixture_dir)
        assert np.array_equal(fixture.candles, sample_candles_5m)


class TestFrozenFeatureParityPasses:
    def test_frozen_feature_parity_passes(self, tmp_path, sample_candles_5m):
        fixture_dir = generate_frozen_fixture(
            sample_candles_5m, _TEST_PARAMS, name="test", output_dir=str(tmp_path),
        )
        fixture = load_frozen_fixture(fixture_dir)
        result = check_feature_parity_frozen(
            fixture.candles, fixture.expected_features, fixture.config_params,
        )
        assert result.passed
        assert len(result.mismatches) == 0


class TestFrozenFeatureParityDetectsDrift:
    def test_frozen_feature_parity_detects_drift(self, tmp_path, sample_candles_5m):
        fixture_dir = generate_frozen_fixture(
            sample_candles_5m, _TEST_PARAMS, name="test", output_dir=str(tmp_path),
        )
        fixture = load_frozen_fixture(fixture_dir)
        # Modify an expected value to simulate drift
        modified_features = dict(fixture.expected_features)
        first_bar = list(modified_features.keys())[0]
        modified_features[first_bar] = dict(modified_features[first_bar])
        modified_features[first_bar]["reference_price"] = 99999.0  # wrong value
        result = check_feature_parity_frozen(
            fixture.candles, modified_features, fixture.config_params,
        )
        assert not result.passed
        assert len(result.mismatches) > 0


class TestParityResultHasFields:
    def test_parity_result_has_fields(self, tmp_path, sample_candles_5m):
        fixture_dir = generate_frozen_fixture(
            sample_candles_5m, _TEST_PARAMS, name="test", output_dir=str(tmp_path),
        )
        fixture = load_frozen_fixture(fixture_dir)
        result = check_feature_parity_frozen(
            fixture.candles, fixture.expected_features, fixture.config_params,
        )
        assert isinstance(result, ParityResult)
        assert isinstance(result.passed, bool)
        assert isinstance(result.mode, str)
        assert isinstance(result.mismatches, list)
        assert isinstance(result.max_abs_diff, float)
        assert isinstance(result.max_rel_diff, float)


class TestNativeParityWorksWithoutHummingbot:
    def test_native_parity_works_without_hummingbot(self, sample_candles_5m):
        """Native parity now replicates controller logic directly."""
        result = check_feature_parity_native(sample_candles_5m, _TEST_PARAMS)
        assert isinstance(result, ParityResult)
        assert result.mode == "native"
        # Should pass since both use the same underlying logic
        assert result.passed


class TestComprehensiveValidationPasses:
    def test_comprehensive_validation_passes(self, tmp_path, sample_candles_5m, default_pair_rules):
        from pmm_lab.sim.executor_model import SimConfig
        from pmm_lab.export.hb_yaml import export_yaml

        config = SimConfig(
            buy_spreads=[1.0, 2.0], sell_spreads=[1.0, 2.0],
            buy_amounts_pct=[0.5, 0.5], sell_amounts_pct=[0.5, 0.5],
            total_amount_quote=100.0,
        )
        path = str(tmp_path / "test.yaml")
        export_yaml(config, path)
        result = validate_export_comprehensive(path)
        assert result.valid, f"Errors: {result.errors}"


class TestCommittedShortFixtureParity:
    def test_committed_short_fixture_parity(self):
        """Load committed fixtures/short_100bar_compat, run parity check -> 0 mismatches."""
        fixture_dir = str(Path(__file__).resolve().parent.parent.parent / "fixtures" / "short_100bar_compat")
        if not os.path.isdir(fixture_dir):
            pytest.skip("Committed short fixture not found")
        fixture = load_frozen_fixture(fixture_dir)
        result = check_feature_parity_frozen(
            fixture.candles, fixture.expected_features, fixture.config_params,
        )
        assert result.passed, f"Mismatches: {result.mismatches}"
        assert len(result.mismatches) == 0


class TestCommittedLongFixtureParity:
    def test_committed_long_fixture_parity(self):
        """Load committed fixtures/long_500bar_compat, run parity check -> 0 mismatches."""
        fixture_dir = str(Path(__file__).resolve().parent.parent.parent / "fixtures" / "long_500bar_compat")
        if not os.path.isdir(fixture_dir):
            pytest.skip("Committed long fixture not found")
        fixture = load_frozen_fixture(fixture_dir)
        result = check_feature_parity_frozen(
            fixture.candles, fixture.expected_features, fixture.config_params,
        )
        assert result.passed, f"Mismatches: {result.mismatches}"
        assert len(result.mismatches) == 0


class TestLongFixtureExceedsMaxRecords:
    def test_long_fixture_exceeds_max_records(self):
        """Verify the long fixture's check_bars include bars > 142 (beyond sliding window boundary)."""
        fixture_dir = str(Path(__file__).resolve().parent.parent.parent / "fixtures" / "long_500bar_compat")
        if not os.path.isdir(fixture_dir):
            pytest.skip("Committed long fixture not found")
        fixture = load_frozen_fixture(fixture_dir)
        check_bar_indices = [int(k) for k in fixture.expected_features.keys()]
        max_records = 42 + 100  # macd_slow + 100
        beyond_max = [b for b in check_bar_indices if b > max_records]
        assert len(beyond_max) > 0, (
            f"No check bars beyond max_records={max_records}. "
            f"Check bars: {check_bar_indices}"
        )


class TestComprehensiveValidationChecksExpectedFields:
    def test_comprehensive_validation_checks_expected_fields(self, tmp_path, sample_candles_5m, default_pair_rules):
        from pmm_lab.sim.executor_model import SimConfig
        from pmm_lab.export.hb_yaml import export_yaml

        config = SimConfig(
            buy_spreads=[1.0, 2.0], sell_spreads=[1.0, 2.0],
            buy_amounts_pct=[0.5, 0.5], sell_amounts_pct=[0.5, 0.5],
            total_amount_quote=100.0,
        )
        path = str(tmp_path / "test.yaml")
        export_yaml(config, path)
        # Correct field
        result = validate_export_comprehensive(
            path, expected_fields={"controller_name": "pmm_dynamic"},
        )
        assert result.valid
        # Wrong field
        result = validate_export_comprehensive(
            path, expected_fields={"controller_name": "wrong_name"},
        )
        assert not result.valid
        assert any("controller_name" in e for e in result.errors)
