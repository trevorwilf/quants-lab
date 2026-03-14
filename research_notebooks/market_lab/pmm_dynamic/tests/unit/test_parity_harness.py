"""Tests for parity framework (works without Hummingbot installed)."""

import os
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


class TestNativeParityRaisesWithoutHummingbot:
    def test_native_parity_raises_without_hummingbot(self, sample_candles_5m):
        with pytest.raises(ImportError, match="Hummingbot is not installed"):
            check_feature_parity_native(sample_candles_5m, _TEST_PARAMS)


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
