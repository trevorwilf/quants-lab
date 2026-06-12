"""PB.6 — mode-lattice / suitability / derive_validation integration for the
tape-replay fill model.

The tape-replay model is an OPT-IN knob (not a new mode, not default-on in IR).
Until PB.5 validates its fidelity against the real tape, any run that consumed
the tape must cap at ``research_only`` regardless of mode/feed. These tests lock
that gate plus the opt-in ``derive_validation_config`` promotion hook.
"""
from __future__ import annotations

import json
from pathlib import Path

from bowaka_v2_lab.optuna.autoconfig import derive_validation_config
from bowaka_v2_lab.promotion.suitability import decide_suitability


def _write_run_dir(tmp_path: Path, *, consumes_tape: bool) -> Path:
    """A SIP + intended_realism run with FULL evidence (walk-forward + recon).

    Without the tape, this would resolve to ``backtesting_only``; the only thing
    that pushes it down to ``research_only`` is the tape-consumption cap.
    """
    rd = tmp_path / ("tape" if consumes_tape else "legacy")
    rd.mkdir(parents=True)
    (rd / "summary.json").write_text(json.dumps({"feed": "sip"}), encoding="utf-8")
    (rd / "run_manifest.json").write_text(
        json.dumps({
            "feed": "sip",
            "simulation": {"mode": "intended_realism"},
            "simulation_contract": "intended_realism",
            "fill_model": {
                "execution": "tape_replay" if consumes_tape else "legacy",
                "exits": "tape_replay" if consumes_tape else "legacy",
                "consumes_trade_tape": consumes_tape,
            },
        }),
        encoding="utf-8",
    )
    # Full evidence — would otherwise allow backtesting_only.
    (rd / "walkforward_holdout.json").write_text("{}", encoding="utf-8")
    (rd / "reconciliation_report.md").write_text("# recon", encoding="utf-8")
    return rd


def test_tape_replay_run_caps_at_research_only(tmp_path):
    rd = _write_run_dir(tmp_path, consumes_tape=True)
    assert decide_suitability(rd) == "research_only"


def test_legacy_run_with_same_evidence_reaches_backtesting_only(tmp_path):
    # Control: identical run WITHOUT the tape resolves a tier higher, proving the
    # cap above is the tape consumption — not the feed/evidence/mode.
    rd = _write_run_dir(tmp_path, consumes_tape=False)
    assert decide_suitability(rd) == "backtesting_only"


def test_derive_validation_default_does_not_enable_tape_replay():
    search = {
        "simulation": {"mode": "fast_realism"},
        "execution": {"order_style": "market"},
        "exits": {"time_stop": {"enabled": True}},
    }
    out = derive_validation_config(search)
    assert out["simulation"]["mode"] == "intended_realism"
    # Opt-in default off → fill_model untouched (absent → legacy downstream).
    assert "fill_model" not in (out.get("execution") or {})
    assert "fill_model" not in (out.get("exits") or {})


def test_derive_validation_enable_tape_replay_sets_both_blocks():
    search = {
        "simulation": {"mode": "fast_realism"},
        "execution": {"order_style": "market"},
        "exits": {"time_stop": {"enabled": True}},
    }
    out = derive_validation_config(search, enable_tape_replay=True)
    assert out["execution"]["fill_model"] == "tape_replay"
    assert out["exits"]["fill_model"] == "tape_replay"
    # The rest of each block is preserved.
    assert out["execution"]["order_style"] == "market"
    assert out["exits"]["time_stop"]["enabled"] is True
