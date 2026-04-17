"""Structural tests for the four committed direction-custom sweep notebooks.

Does NOT execute the notebooks — they require a live Mongo connection.
End-to-end semantics are covered by `tests/integration/test_directional_e2e.py`.
"""

import ast
import json
from pathlib import Path

import pytest


NB_DIR = Path(__file__).resolve().parents[2] / "notebooks" / "direction-custom"

NOTEBOOKS = {
    "mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb": 14,
    "mean_reversion_bb_rsi_retest_sweep.ipynb": 16,
    "ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb": 14,
    "ema_regime_hold_retest_sweep.ipynb": 16,
}


def _load_nb(name: str):
    with open(NB_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _source(cell) -> str:
    src = cell.get("source", "")
    if isinstance(src, list):
        return "".join(src)
    return src or ""


@pytest.mark.parametrize("name,expected_cell_count", list(NOTEBOOKS.items()))
class TestStructure:
    def test_file_is_valid_json_ipynb(self, name, expected_cell_count):
        nb = _load_nb(name)
        assert nb["nbformat"] == 4
        assert "cells" in nb

    def test_cell_count_matches_reference(self, name, expected_cell_count):
        nb = _load_nb(name)
        assert len(nb["cells"]) == expected_cell_count

    def test_first_cell_is_title_markdown(self, name, expected_cell_count):
        nb = _load_nb(name)
        c0 = nb["cells"][0]
        assert c0["cell_type"] == "markdown"
        src = _source(c0)
        assert src.startswith("# "), f"{name}: title cell must start with '# '"

    def test_concatenated_code_parses(self, name, expected_cell_count):
        nb = _load_nb(name)
        concat = "\n\n".join(_source(c) for c in nb["cells"] if c["cell_type"] == "code")
        try:
            ast.parse(concat)
        except SyntaxError as e:
            pytest.fail(f"{name}: concatenated code cells do not parse: {e}")


class TestMarkdownHeadings:
    """Verify heading sections align with the PMM reference layout.

    Multi-exchange layout (14 cells): title, code, ## 1 Configuration, code, code,
    ## 2 Discover ..., code, ## 3 Sweep ..., code, ## 4 Results Summary, code,
    ## 5 Profitable Pairs Detail ..., code, ## 6 Next Steps.

    Retest layout (16 cells): same through cell 11, then ## 6 Cross-Pair Ranking,
    code, ## 7 Next Steps.
    """

    @pytest.mark.parametrize("name", [
        "mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb",
        "ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb",
    ])
    def test_multi_exchange_section_headings(self, name):
        nb = _load_nb(name)
        expect_md_prefixes = {
            2: "## 1.",
            5: "## 2.",
            7: "## 3.",
            9: "## 4.",
            11: "## 5.",
            13: "## 6.",
        }
        for idx, prefix in expect_md_prefixes.items():
            cell = nb["cells"][idx]
            assert cell["cell_type"] == "markdown", f"{name}: cell {idx} should be markdown"
            assert _source(cell).lstrip().startswith(prefix), (
                f"{name}: cell {idx} must start with {prefix!r}"
            )

    @pytest.mark.parametrize("name", [
        "mean_reversion_bb_rsi_retest_sweep.ipynb",
        "ema_regime_hold_retest_sweep.ipynb",
    ])
    def test_retest_section_headings(self, name):
        nb = _load_nb(name)
        expect_md_prefixes = {
            2: "## 1.",
            5: "## 2.",
            7: "## 3.",
            9: "## 4.",
            11: "## 5.",
            13: "## 6.",
            15: "## 7.",
        }
        for idx, prefix in expect_md_prefixes.items():
            cell = nb["cells"][idx]
            assert cell["cell_type"] == "markdown", f"{name}: cell {idx} should be markdown"
            assert _source(cell).lstrip().startswith(prefix)


class TestCellTypeAlternation:
    @pytest.mark.parametrize("name", NOTEBOOKS.keys())
    def test_expected_cell_types(self, name):
        """Explicit type pattern matching the PMM reference notebooks."""
        nb = _load_nb(name)
        if len(nb["cells"]) == 14:
            expected = [
                "markdown", "code",   # title, imports
                "markdown", "code",   # ## 1 Configuration, config cell
                "code",               # preflight (cell 4)
                "markdown", "code",   # ## 2 Discover, discovery
                "markdown", "code",   # ## 3 Sweep, sweep loop
                "markdown", "code",   # ## 4 Results Summary, results
                "markdown", "code",   # ## 5 Profitable Pairs, profitable code
                "markdown",           # ## 6 Next Steps
            ]
        else:  # 16
            expected = [
                "markdown", "code",
                "markdown", "code",
                "code",
                "markdown", "code",
                "markdown", "code",
                "markdown", "code",
                "markdown", "code",
                "markdown", "code",   # ## 6 Cross-Pair Ranking, ranking code
                "markdown",           # ## 7 Next Steps
            ]
        actual = [c["cell_type"] for c in nb["cells"]]
        assert actual == expected, f"{name}: cell-type mismatch {actual} != {expected}"
