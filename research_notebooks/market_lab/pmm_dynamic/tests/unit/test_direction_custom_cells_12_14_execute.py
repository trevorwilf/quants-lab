"""Runtime-execution tests for cells 12 and 14. ML-DIR-003 regression guard.

These tests load each committed notebook, synthesize realistic sweep_results,
and exec() the cells. The old cells raise KeyError on r["trading_pair"]; the
new cells must run cleanly.
"""
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
RETEST_NOTEBOOKS = [nb for nb in ALL_NOTEBOOKS if "retest" in nb]


def _cell_source(nb_name: str, cell_idx: int) -> str:
    with open(NB_DIR / nb_name, encoding="utf-8") as f:
        nb = json.load(f)
    src = nb["cells"][cell_idx]["source"]
    if isinstance(src, list):
        src = "".join(src)
    return src


def _mock_sweep_results():
    return [
        {"status": "validated_pass", "validation_status": "validated_pass",
         "connector": "nonkyc", "pair": "XMR-USDT",
         "robust_score": 0.85, "best_score": None,
         "yaml_path": "/tmp/mr/nonkyc_xmr_usdt_5m_screening_best.yml",
         "total_reject_fraction": 0.10,
         "checks": {"walkforward_robust": True}},
        {"status": "validated_fail", "validation_status": "validated_fail",
         "connector": "mexc", "pair": "KAS-USDT",
         "robust_score": 0.4, "mandatory_gates_failed": ["walkforward_robust"],
         "yaml_path": "/tmp/mr/rejected/mexc_kas_usdt_5m_screening_best.yml",
         "total_reject_fraction": 0.45,
         "checks": {"walkforward_robust": False}},
        {"status": "complete", "validation_status": "complete",
         "connector": "mexc", "pair": "DOGE-USDT",
         "robust_score": 0.55,
         "yaml_path": "/tmp/mr/mexc_doge_usdt_5m_screening_best.yml",
         "checks": {"walkforward_robust": True}},
        {"status": "optimized_only", "validation_status": "optimized_only",
         "connector": "nonkyc", "pair": "SHIB-USDT",
         "robust_score": 2.0,
         "yaml_path": None,
         "checks": {}},
        {"status": "load_error", "validation_status": "load_error",
         "connector": "mexc", "pair": "BAD-USDT",
         "error": "mongo down",
         "robust_score": None},
    ]


@pytest.mark.parametrize("nb_name", ALL_NOTEBOOKS)
def test_cell_12_executes_without_error(nb_name):
    src = _cell_source(nb_name, 12)
    assert 'r["trading_pair"]' not in src, f"{nb_name}: cell 12 still has bracket trading_pair"
    # Allow `r.get("best_score", ...)` (compat) but no raw bracket best_score
    assert 'r["best_score"]' not in src, (
        f"{nb_name}: cell 12 still raw-references r['best_score']"
    )
    exec_ns = {"sweep_results": _mock_sweep_results(), "print": print}
    exec(src, exec_ns)  # must not raise


@pytest.mark.parametrize("nb_name", RETEST_NOTEBOOKS)
def test_cell_14_executes_without_error(nb_name):
    src = _cell_source(nb_name, 14)
    assert 'r["trading_pair"]' not in src, f"{nb_name}: cell 14 still has bracket trading_pair"
    assert "robust_score" in src, f"{nb_name}: cell 14 must reference robust_score"
    exec_ns = {"sweep_results": _mock_sweep_results(), "print": print}
    exec(src, exec_ns)  # must not raise


@pytest.mark.parametrize("nb_name", RETEST_NOTEBOOKS)
def test_cell_14_ranks_validated_pass_first(nb_name, capsys):
    src = _cell_source(nb_name, 14)
    exec_ns = {"sweep_results": _mock_sweep_results(), "print": print}
    exec(src, exec_ns)
    out = capsys.readouterr().out
    # validated_pass XMR=0.85 vs "complete" DOGE=0.55 → XMR first
    lines = [l for l in out.splitlines() if "XMR-USDT" in l or "DOGE-USDT" in l]
    assert lines, f"{nb_name}: expected XMR/DOGE rows in output"
    xmr_idx = next((i for i, l in enumerate(lines) if "XMR-USDT" in l), -1)
    doge_idx = next((i for i, l in enumerate(lines) if "DOGE-USDT" in l), -1)
    assert xmr_idx != -1 and doge_idx != -1
    assert xmr_idx < doge_idx, (
        f"{nb_name}: ranking wrong — XMR (0.85) should come before DOGE (0.55). Output:\n{out}"
    )


@pytest.mark.parametrize("nb_name", RETEST_NOTEBOOKS)
def test_cell_14_shows_rejected_section(nb_name, capsys):
    src = _cell_source(nb_name, 14)
    exec_ns = {"sweep_results": _mock_sweep_results(), "print": print}
    exec(src, exec_ns)
    out = capsys.readouterr().out
    # The validated_fail KAS-USDT candidate must appear in the rejected section.
    assert "KAS-USDT" in out, f"{nb_name}: rejected KAS-USDT must appear in output"
    assert "Rejected candidates" in out, f"{nb_name}: rejected section header missing"
    assert "walkforward_robust" in out, f"{nb_name}: failed gate name should be printed"
