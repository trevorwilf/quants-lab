"""Export-anchor regressions (Phase A.1 §1 + A.2 §1/§2): exports rebuild at
the deploy anchor (never fold anchors), literal ladders are anchor-invariant,
divergence warnings reach the YAML, and the market-bracket validator."""

from pathlib import Path

import numpy as np
import pytest
import yaml

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.export.hb_yaml_range_ladder import (
    RangeLadderExportParams,
    export_range_ladder_yaml,
)
from pmm_lab.export.validate_export import validate_yaml_file
from pmm_lab.strategies.range_ladder import RangeLadderConfig, compute_anchor
from pmm_lab.strategies.range_ladder_gen import build_rungs


def _rules(tick=0.01):
    return PairRules(
        price_tick=tick, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.002, taker_fee=0.002),
    )


def _config(**overrides):
    base = dict(
        n_buy=4, n_sell=4,
        buy_near_pct=0.02, buy_far_pct=0.15,
        sell_near_pct=0.02, sell_far_pct=0.15,
        buy_gamma=1.0, sell_gamma=1.0, k_buy=0.5, k_sell=0.5,
        fund_quote=1000.0, fee=0.002,
    )
    base.update(overrides)
    return RangeLadderConfig(**base)


def _export(tmp_path, config, anchor, comments=None):
    out = tmp_path / "export.yml"
    export_range_ladder_yaml(
        config, anchor, _rules(),
        RangeLadderExportParams(connector_name="nonkyc", trading_pair="XMR-USDT"),
        out, extra_comment_lines=comments,
    )
    with open(out) as f:
        return out, yaml.safe_load(f)


# ----------------------------------------------------------------------
# A.2 §1 — export rungs come from the deploy anchor, never fold anchors
# ----------------------------------------------------------------------

def test_export_rebuilds_at_deploy_anchor_not_fold_anchor():
    """Fold train anchor (200) and deploy anchor (300) differ by 50%:
    every exported rung must match build_rungs at 300 and none at 200."""
    config = _config()
    fold_anchor, deploy_anchor = 200.0, 300.0
    assert abs(deploy_anchor / fold_anchor - 1) > 0.15

    fold_rungs = build_rungs(fold_anchor, config, 0.01)
    deploy_rungs = build_rungs(deploy_anchor, config, 0.01)

    out = Path(__file__)  # placeholder; real path from tmp fixture below
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        _, d = _export(Path(td), config, deploy_anchor)
    exported = d["buy_prices"] + d["sell_prices"]
    expected = [float(x) for x in deploy_rungs.buys] + [float(x) for x in deploy_rungs.sells]
    stale = [float(x) for x in fold_rungs.buys] + [float(x) for x in fold_rungs.sells]
    assert exported == expected
    assert not any(p in stale for p in exported)


def test_export_brackets_last_close_on_trending_series():
    """On a 100→300 ramp, the exported ladder brackets the CURRENT price,
    not the full-history median (~200)."""
    n = 4000
    close = np.linspace(100.0, 300.0, n)
    deploy_anchor = compute_anchor(close)
    hist_median = float(np.median(close))
    assert abs(deploy_anchor - 300.0) < 1.0
    assert abs(hist_median - 200.0) < 1.0

    config = _config()
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        _, d = _export(Path(td), config, deploy_anchor)
    last_close = float(close[-1])
    assert max(d["buy_prices"]) < last_close < min(d["sell_prices"])
    # ...and does NOT bracket the historical median
    assert not (max(d["buy_prices"]) < hist_median < min(d["sell_prices"]))


def test_stale_data_export_still_sane():
    """A last close far from the historical median still produces a ladder
    with the configured offsets around the deploy anchor."""
    config = _config()
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        _, d = _export(Path(td), config, 50.0)   # market collapsed to 50
    assert max(d["buy_prices"]) == pytest.approx(50.0 * 0.98, abs=0.01)
    assert min(d["sell_prices"]) == pytest.approx(50.0 * 1.02, abs=0.01)


def test_literal_rungs_invariant_under_anchor(tmp_path):
    """A.1 §1: literal incumbent rungs are absolute — identical under two
    very different anchors."""
    lit = _config(
        literal_buy_prices=(98.0, 95.0), literal_buy_weights=(1.0, 1.0),
        literal_sell_prices=(102.0, 105.0), literal_sell_weights=(1.0, 1.0),
    )
    r1 = lit.resolve_rungs(100.0, 0.01)
    r2 = lit.resolve_rungs(999.0, 0.01)
    assert np.array_equal(r1.buys, r2.buys)
    assert np.array_equal(r1.sells, r2.sells)
    _, d1 = _export(tmp_path / "a", lit, 100.0)
    _, d2 = _export(tmp_path / "b", lit, 999.0)
    assert d1["buy_prices"] == d2["buy_prices"]
    assert d1["sell_prices"] == d2["sell_prices"]


def test_divergence_warning_written_into_yaml_comment(tmp_path):
    config = _config()
    warning = "WARNING: deploy anchor 300 diverged 6.2% from last close 283"
    out, _ = _export(tmp_path, config, 300.0,
                     comments=[warning, "Selected under gate policy: {'mode': 'strict'}"])
    text = out.read_text(encoding="utf-8")
    assert f"# {warning}" in text
    assert "# Selected under gate policy" in text
    # comments must not break YAML parsing
    with open(out) as f:
        assert yaml.safe_load(f)["controller_name"] == "range_inventory_ladder"


# ----------------------------------------------------------------------
# A.2 §2 — market-bracket validation
# ----------------------------------------------------------------------

def test_bracket_validation_passes_when_anchored(tmp_path):
    config = _config()
    out, _ = _export(tmp_path, config, 300.0)
    vr = validate_yaml_file(str(out), price_tick=0.01, deploy_anchor=300.0,
                            buy_near_pct=0.02, sell_near_pct=0.02)
    assert vr.valid, vr.errors
    assert not any("sits wide" in w for w in vr.warnings)


def test_bracket_validation_hard_fails_off_market(tmp_path):
    """The 2026-07-07 failure case: a ladder exported at a stale anchor sits
    entirely above/below the market — must hard-fail."""
    config = _config()
    out, _ = _export(tmp_path, config, 392.0)   # ladder around 392
    vr = validate_yaml_file(str(out), price_tick=0.01, deploy_anchor=326.0)
    assert not vr.valid
    assert any("does not bracket" in e for e in vr.errors)


def test_bracket_validation_warns_when_absurdly_wide(tmp_path):
    """Brackets price but the nearest rungs sit >3× the configured near
    offset away — non-fatal warning."""
    config = _config(buy_near_pct=0.08, buy_far_pct=0.20,
                     sell_near_pct=0.08, sell_far_pct=0.20)
    out, _ = _export(tmp_path, config, 300.0)
    # validate claiming the config was tuned with 2% near offsets
    vr = validate_yaml_file(str(out), price_tick=0.01, deploy_anchor=300.0,
                            buy_near_pct=0.02, sell_near_pct=0.02)
    assert vr.valid
    assert any("sits wide" in w for w in vr.warnings)


def test_bracket_check_skipped_without_anchor(tmp_path):
    config = _config()
    out, _ = _export(tmp_path, config, 300.0)
    vr = validate_yaml_file(str(out), price_tick=0.01)
    assert vr.valid
    assert any("bracket check skipped" in w for w in vr.warnings)
