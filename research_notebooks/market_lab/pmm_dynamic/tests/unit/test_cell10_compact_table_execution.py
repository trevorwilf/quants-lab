"""Runtime-execution test for cell 10 against mock sweep_results.
ML-DIR-011 regression guard: ranking must actually produce expected output."""
import json
from pathlib import Path

import pytest

NB_DIR = Path(__file__).resolve().parents[2] / "notebooks" / "direction-custom"

ALL_NOTEBOOKS = [
    "mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb",
    "mean_reversion_bb_rsi_retest_sweep.ipynb",
    "ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb",
    "ema_regime_hold_retest_sweep.ipynb",
]


def _cell10_source(nb_name: str) -> str:
    with open(NB_DIR / nb_name, encoding="utf-8") as f:
        nb = json.load(f)
    src = nb["cells"][10]["source"]
    if isinstance(src, list):
        src = "".join(src)
    return src


def _mock_results():
    return [
        {"status": "validated_pass", "validation_status": "validated_pass",
         "connector": "nonkyc", "pair": "XMR-USDT",
         "robust_score": 0.85, "dataset_days": 90,
         "yaml_path": "/tmp/valid.yml",
         "holdout_report": None, "recent_window_result": None, "checks": {"a": True}},
        {"status": "validated_fail", "validation_status": "validated_fail",
         "connector": "mexc", "pair": "KAS-USDT",
         "robust_score": 1.2, "dataset_days": 90,
         "yaml_path": "/tmp/rejected/bad.yml",
         "mandatory_gates_failed": ["walkforward_robust"],
         "holdout_report": None, "recent_window_result": None, "checks": {}},
        {"status": "optimized_only", "validation_status": "optimized_only",
         "connector": "mexc", "pair": "SHIB-USDT",
         "robust_score": 3.0, "dataset_days": 10,
         "yaml_path": None,
         "holdout_report": None, "recent_window_result": None, "checks": {}},
        {"status": "load_error", "validation_status": "load_error",
         "connector": "mexc", "pair": "BAD-USDT",
         "error": "mongo unreachable",
         "holdout_report": None, "recent_window_result": None},
    ]


@pytest.mark.parametrize("nb_name", ALL_NOTEBOOKS)
def test_cell10_executes_without_error(nb_name, capsys):
    import os
    src = _cell10_source(nb_name)
    exec_ns = {"sweep_results": _mock_results(), "os": os, "Path": Path, "print": print}
    exec(src, exec_ns)
    out = capsys.readouterr().out
    assert "COMPACT RESULTS TABLE" in out
    assert "XMR-USDT" in out


@pytest.mark.parametrize("nb_name", ALL_NOTEBOOKS)
def test_cell10_does_not_rank_rejected_in_primary_table(nb_name, capsys):
    """A validated_fail row with robust_score=1.2 must NOT outrank XMR-USDT (0.85) in
    the primary table."""
    import os
    src = _cell10_source(nb_name)
    exec_ns = {"sweep_results": _mock_results(), "os": os, "Path": Path, "print": print}
    exec(src, exec_ns)
    out = capsys.readouterr().out

    primary_start = out.find("COMPACT RESULTS TABLE")
    rejected_start = out.find("REJECTED CANDIDATES")
    assert primary_start >= 0
    # Primary section goes from primary_start up to rejected section (or end)
    end = rejected_start if rejected_start > primary_start else len(out)
    primary_section = out[primary_start:end]

    xmr_idx = primary_section.find("XMR-USDT")
    kas_idx = primary_section.find("KAS-USDT")
    assert xmr_idx >= 0, "XMR-USDT must appear in primary (validated_pass)"
    assert kas_idx == -1, (
        f"KAS-USDT is validated_fail and must NOT appear in the primary table. "
        f"Output:\n{primary_section[:500]}"
    )


@pytest.mark.parametrize("nb_name", ALL_NOTEBOOKS)
def test_cell10_rejected_section_shows_kas(nb_name, capsys):
    import os
    src = _cell10_source(nb_name)
    exec_ns = {"sweep_results": _mock_results(), "os": os, "Path": Path, "print": print}
    exec(src, exec_ns)
    out = capsys.readouterr().out
    assert "REJECTED CANDIDATES" in out
    assert "KAS-USDT" in out
    assert "walkforward_robust" in out
