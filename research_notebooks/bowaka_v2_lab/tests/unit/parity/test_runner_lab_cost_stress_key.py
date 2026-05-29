"""Regression: cost_stress override goes to ``backtest.cost_stress``.

Pre-fix, the runner overrode ``cost_model.stress_label`` — a field that
doesn't exist in :class:`BowakaV2Config`. The BowakaV2Config schema rejects
extra keys, so the override blew up validation:

    pydantic_core._pydantic_core.ValidationError: 1 validation error for
    BowakaV2Config
    cost_model
      Extra inputs are not permitted [type=extra_forbidden, input_value=
      {'stress_label': 'conservative'}, ...]

The correct field is ``backtest.cost_stress`` — a ``Literal["base",
"conservative", "severe"]`` that mirrors the production CLI's
``--cost-stress`` choices.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pytest
import yaml

from bowaka_v2_lab.parity.runner import run_lab_backtester


def test_cost_stress_override_targets_backtest_field(tmp_path: Path) -> None:
    """A bare smoke config + cost_stress="conservative" must not raise on
    validation. Pre-fix it raised ``extra_forbidden`` for ``cost_model``."""
    cfg = {
        "strategy_id": "smoke_parity_override",
        "version_label": "smoke",
        "simulation": {"mode": "smoke_fixture"},
        "universe": {"symbols": ["A", "B"]},
        "backtest": {"start_date": "2026-05-19", "end_date": "2026-05-19"},
        "market_data": {"minute_bar_source": "fixture"},
    }
    cfg_path = tmp_path / "smoke.yml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    # Just confirm the cost_stress override doesn't blow validation. The full
    # backtest may still raise downstream (smoke fixture isn't fully wired
    # here), but the validation step must succeed.
    try:
        run_lab_backtester(
            start_date=_dt.date(2026, 5, 19),
            end_date=_dt.date(2026, 5, 19),
            symbols=["A", "B"],
            lab_config_path=cfg_path,
            cost_stress="conservative",
            run_dir=tmp_path / "run",
        )
    except Exception as exc:  # noqa: BLE001 — we accept downstream failures
        msg = str(exc)
        # The specific regression: must NOT be the ``extra_forbidden`` /
        # ``cost_model`` ValidationError.
        assert "cost_model" not in msg, (
            "cost_stress override leaked into the cost_model namespace: "
            f"{exc!r}"
        )
        assert "Extra inputs are not permitted" not in msg, (
            f"strict-schema rejection on cost_stress path: {exc!r}"
        )


def test_invalid_cost_stress_value_is_rejected_by_schema(tmp_path: Path) -> None:
    """``backtest.cost_stress`` has a Literal type; an unknown value is rejected
    by validation. This guards the runner against silently accepting bad input."""
    cfg = {
        "strategy_id": "smoke_parity_override",
        "version_label": "smoke",
        "simulation": {"mode": "smoke_fixture"},
        "universe": {"symbols": ["A", "B"]},
        "backtest": {"start_date": "2026-05-19", "end_date": "2026-05-19"},
        "market_data": {"minute_bar_source": "fixture"},
    }
    cfg_path = tmp_path / "smoke.yml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    with pytest.raises(Exception) as exc_info:
        run_lab_backtester(
            start_date=_dt.date(2026, 5, 19),
            end_date=_dt.date(2026, 5, 19),
            symbols=["A", "B"],
            lab_config_path=cfg_path,
            cost_stress="aggressive",  # not in Literal["base","conservative","severe"]
            run_dir=tmp_path / "run",
        )
    msg = str(exc_info.value)
    # Pydantic Literal violation surfaces as a value error.
    assert "cost_stress" in msg or "Input should be" in msg or "Literal" in msg.lower()
