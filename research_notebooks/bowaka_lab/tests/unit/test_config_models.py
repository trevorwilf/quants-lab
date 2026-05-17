"""Phase 1: Pydantic model validation tests."""

from __future__ import annotations

from datetime import date

import pytest

from bowaka_lab.config.models import (
    BowakaBacktestConfig,
    DataConfig,
    ExitConfig,
    PrefilterConfig,
    SignalFadeConfig,
)


def test_data_config_rejects_bad_date_range():
    with pytest.raises(Exception):
        DataConfig(start_date=date(2026, 1, 1), end_date=date(2025, 1, 1))


def test_exit_config_rejects_negative_stop_pct():
    with pytest.raises(Exception):
        ExitConfig(stop_pct=-0.01)


def test_exit_config_rejects_zero_max_hold_days():
    with pytest.raises(Exception):
        ExitConfig(max_hold_days=0)


def test_prefilter_config_rejects_inverted_price_range():
    with pytest.raises(Exception):
        PrefilterConfig(price_min=10.0, price_max=5.0)


def test_signal_fade_config_rejects_bad_hhmm():
    with pytest.raises(Exception):
        SignalFadeConfig(rth_eval_time="25:00")
    with pytest.raises(Exception):
        SignalFadeConfig(rth_eval_time="bogus")


def test_bowaka_backtest_config_min_fields():
    cfg = BowakaBacktestConfig.model_validate(
        {
            "data": {
                "vendor": "alpaca",
                "feed": "iex",
                "start_date": "2026-01-01",
                "end_date": "2026-05-15",
            }
        }
    )
    assert cfg.data.start_date == date(2026, 1, 1)
    assert cfg.exits.stop_pct == 0.08


def test_bowaka_backtest_config_rejects_extra_top_level_key():
    with pytest.raises(Exception):
        BowakaBacktestConfig.model_validate(
            {
                "data": {
                    "vendor": "alpaca",
                    "feed": "iex",
                    "start_date": "2026-01-01",
                    "end_date": "2026-05-15",
                },
                "bogus": 1,
            }
        )


def test_bowaka_backtest_config_canonical_dict_is_json_safe():
    cfg = BowakaBacktestConfig.model_validate(
        {
            "data": {
                "vendor": "alpaca",
                "feed": "iex",
                "start_date": "2026-01-01",
                "end_date": "2026-05-15",
            }
        }
    )
    cd = cfg.canonical_dict()
    import json

    s = json.dumps(cd, sort_keys=True)
    cd2 = json.loads(s)
    assert cd == cd2


def test_signal_fade_config_thresholds_default_present():
    sf = SignalFadeConfig()
    assert sf.shadow_thresholds == [4, 5, 6, 7, 8, 9]


def test_exit_config_ambiguous_bar_policy_rejects_invalid():
    with pytest.raises(Exception):
        ExitConfig(ambiguous_bar_policy="bogus_choice")
