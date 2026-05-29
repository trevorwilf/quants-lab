"""Phase 4 (audit 2026-05-29 §9 Phase 6) — bucketed fill-error per ADV."""
from __future__ import annotations

from bowaka_v2_lab.reconcile.slippage_residuals import bucket_fill_errors


def test_bucketed_by_adv_has_expected_medians() -> None:
    fills = [
        {"adv_dollar": 5.0e5, "fill_error_bps": 10.0, "symbol": "AAA"},   # micro
        {"adv_dollar": 5.0e5, "fill_error_bps": 20.0, "symbol": "AAA"},   # micro
        {"adv_dollar": 1.0e8, "fill_error_bps": 2.0, "symbol": "BBB"},    # large
        {"adv_dollar": 1.0e8, "fill_error_bps": 4.0, "symbol": "BBB"},    # large
    ]
    df = bucket_fill_errors(fills)
    adv_rows = df[df["dimension"] == "adv_bucket"].set_index("bucket")
    assert adv_rows.loc["micro", "n_fills"] == 2
    assert adv_rows.loc["micro", "median_bps"] == 15.0
    assert adv_rows.loc["large", "n_fills"] == 2
    assert adv_rows.loc["large", "median_bps"] == 3.0
