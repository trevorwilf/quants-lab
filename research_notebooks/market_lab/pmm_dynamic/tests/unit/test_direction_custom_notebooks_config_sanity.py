"""Config-cell (cell 3) sanity checks for the four direction-custom notebooks."""

import json
import re
from pathlib import Path

import pytest


NB_DIR = Path(__file__).resolve().parents[2] / "notebooks" / "direction-custom"


def _load_cell3(name: str) -> str:
    with open(NB_DIR / name, encoding="utf-8") as f:
        nb = json.load(f)
    src = nb["cells"][3].get("source", "")
    if isinstance(src, list):
        return "".join(src)
    return src


def _assert_assignment(cell: str, var: str, value_re: str, name: str) -> None:
    """Check a `VAR = <regex>` assignment appears in the cell."""
    pat = rf"^\s*{re.escape(var)}\s*=\s*({value_re})\s*(?:#|$)"
    assert re.search(pat, cell, flags=re.MULTILINE), (
        f"{name}: expected `{var} = {value_re}` in cell 3, not found"
    )


MR_MULTI = "mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb"
MR_RETEST = "mean_reversion_bb_rsi_retest_sweep.ipynb"
EMA_MULTI = "ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb"
EMA_RETEST = "ema_regime_hold_retest_sweep.ipynb"


class TestCommonValues:
    @pytest.mark.parametrize("name", [MR_MULTI, MR_RETEST, EMA_MULTI, EMA_RETEST])
    def test_n_trials_is_500(self, name):
        cell = _load_cell3(name)
        _assert_assignment(cell, "N_TRIALS", r"500", name)


class TestMRConfig:
    @pytest.mark.parametrize("name", [MR_MULTI, MR_RETEST])
    def test_min_data_days_56(self, name):
        cell = _load_cell3(name)
        _assert_assignment(cell, "MIN_DATA_DAYS", r"56", name)

    @pytest.mark.parametrize("name", [MR_MULTI, MR_RETEST])
    def test_max_training_days_180(self, name):
        cell = _load_cell3(name)
        _assert_assignment(cell, "MAX_TRAINING_DAYS", r"180", name)

    def test_mr_multi_top_n_100(self):
        cell = _load_cell3(MR_MULTI)
        _assert_assignment(cell, "TOP_N", r"100", MR_MULTI)

    def test_mr_retest_top_n_75(self):
        cell = _load_cell3(MR_RETEST)
        _assert_assignment(cell, "TOP_N", r"75", MR_RETEST)


class TestEMAConfig:
    @pytest.mark.parametrize("name", [EMA_MULTI, EMA_RETEST])
    def test_min_data_days_120(self, name):
        cell = _load_cell3(name)
        _assert_assignment(cell, "MIN_DATA_DAYS", r"120", name)

    @pytest.mark.parametrize("name", [EMA_MULTI, EMA_RETEST])
    def test_max_training_days_none(self, name):
        cell = _load_cell3(name)
        _assert_assignment(cell, "MAX_TRAINING_DAYS", r"None", name)

    @pytest.mark.parametrize("name", [EMA_MULTI, EMA_RETEST])
    def test_signal_and_regime_intervals_defined(self, name):
        cell = _load_cell3(name)
        assert "SIGNAL_CONNECTOR_INTERVALS" in cell, f"{name}: missing SIGNAL_CONNECTOR_INTERVALS"
        assert "REGIME_CONNECTOR_INTERVALS" in cell, f"{name}: missing REGIME_CONNECTOR_INTERVALS"

    def test_ema_multi_top_n_100(self):
        cell = _load_cell3(EMA_MULTI)
        _assert_assignment(cell, "TOP_N", r"100", EMA_MULTI)

    def test_ema_retest_top_n_75(self):
        cell = _load_cell3(EMA_RETEST)
        _assert_assignment(cell, "TOP_N", r"75", EMA_RETEST)


class TestRetestPairsPresent:
    @pytest.mark.parametrize("name", [MR_RETEST, EMA_RETEST])
    def test_retest_pairs_defined(self, name):
        cell = _load_cell3(name)
        assert "RETEST_PAIRS" in cell, f"{name}: missing RETEST_PAIRS definition"
