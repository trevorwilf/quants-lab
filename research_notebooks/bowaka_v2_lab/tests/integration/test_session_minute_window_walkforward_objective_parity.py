"""Walk-forward objective is unchanged by the session minute-window cache.

Speedup report v2 §4 P3 / §5.7 / Phase 4 task 6. Strongest objective
parity test: a 2-trial walk-forward study with the flag off vs on must
produce identical ``best_value`` / ``best_params``.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
import yaml

from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake, write_walkforward_test_config
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study


_LAB_ROOT = Path(__file__).resolve().parents[2]


def _write_cfg(out_path: Path, *, lake: Path, symbols, enable: bool) -> Path:
    raw_cfg = _LAB_ROOT / "configs" / "bowaka_v2_actual_iex_current_code_optuna.yml"
    cfg_path = write_walkforward_test_config(
        raw_cfg, out_path,
        lake=lake, symbols=symbols,
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=2,
    )
    doc = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    doc.setdefault("optuna", {})["cached_suppliers"] = True
    doc["optuna"].setdefault("acceleration", {})[
        "session_minute_window_cache"
    ] = {"enabled": bool(enable)}
    cfg_path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return cfg_path


@pytest.mark.slow
def test_walkforward_objective_parity_session_window_off_vs_on(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    symbols = ["AAA"]
    build_tiny_lake(lake, symbols, start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))

    cfg_off = _write_cfg(tmp_path / "wf_off.yml", lake=lake, symbols=symbols, enable=False)
    cfg_on = _write_cfg(tmp_path / "wf_on.yml", lake=lake, symbols=symbols, enable=True)

    res_off = run_walkforward_study(cfg_off, n_trials=2, allow_smoke=True)
    res_on = run_walkforward_study(cfg_on, n_trials=2, allow_smoke=True)

    assert res_off["status"] == "ok"
    assert res_on["status"] == "ok"
    assert abs(float(res_off["best_value"]) - float(res_on["best_value"])) <= 1e-9
    for k, v in res_off["best_params"].items():
        assert k in res_on["best_params"]
        vb = res_on["best_params"][k]
        if isinstance(v, float):
            assert abs(float(v) - float(vb)) <= 1e-9
        else:
            assert v == vb
