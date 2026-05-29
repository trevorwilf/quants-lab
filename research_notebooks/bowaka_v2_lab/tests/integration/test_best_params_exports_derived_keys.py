"""Phase 2 (audit 2026-05-29 §6.8) — best_params exports internal + derived keys.

The study artifact's ``best_params`` carries BOTH the internal gap/ratio
search keys AND the derived actual-strategy fields (hard / critical /
target_pct), and ``derived_keys`` lists the derived names. The derived
``target_pct`` equals ``clamp(stop_pct * reward_risk_ratio)`` within 1e-12.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake, write_walkforward_test_config
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study

_SF = "exits.signal_fade.score_thresholds."


def _read_ok_artifact(tmp_path: Path) -> dict:
    for p in sorted(tmp_path.rglob("optuna/*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("status") == "ok":
            return d
    raise AssertionError("no status=ok study artifact found")


def test_best_params_has_internal_and_derived(tmp_path: Path, lab_root: Path) -> None:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=3,
    )
    run_walkforward_study(cfg_path, allow_smoke=True)
    art = _read_ok_artifact(tmp_path)
    bp = art["best_params"]

    # internal (gap/ratio) keys
    assert _SF + "soft" in bp
    assert _SF + "hard_gap" in bp
    assert _SF + "critical_gap" in bp
    assert "exits.reward_risk_ratio" in bp
    # derived (actual-strategy) keys
    assert _SF + "hard" in bp
    assert _SF + "critical" in bp
    assert "exits.target_pct" in bp

    expected_target = min(0.40, bp["exits.stop_pct"] * bp["exits.reward_risk_ratio"])
    assert abs(bp["exits.target_pct"] - expected_target) < 1e-12
    expected_hard = min(0.70, bp[_SF + "soft"] + bp[_SF + "hard_gap"])
    assert abs(bp[_SF + "hard"] - expected_hard) < 1e-12

    assert set(art["derived_keys"]) == {
        _SF + "hard", _SF + "critical", "exits.target_pct",
    }
