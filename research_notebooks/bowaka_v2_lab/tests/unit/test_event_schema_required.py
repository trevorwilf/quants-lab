"""Every gate key returned by apply_v2_gates is in CANDIDATE_EVENT_REQUIRED_FIELDS.

Per [Report §8.3]: the archive's required-field list was incomplete (missing
projected_rvol_gate, max_rvol_gate, max_range_expansion_gate). This test would
have caught it at schema-load time.
"""
from __future__ import annotations

from bowaka_v2_lab.features import apply_v2_gates
from bowaka_v2_lab.schemas.events import CANDIDATE_EVENT_REQUIRED_FIELDS


def test_all_gate_keys_in_required_fields() -> None:
    _, gates = apply_v2_gates(
        features={
            "rvol_so_far": 1.0, "projected_full_day_rvol": 1.0,
            "range_expansion_so_far": 1.0, "close_location_so_far": 0.5,
            "ema_distance": 0.01, "gap_pct": 0.0,
        },
        signals_cfg={},
        price=10.0, avg_dollar_volume_20d=1_000_000,
        prior_atr_pct=0.02, ema_slope_prior=0.01,
        instrument_class="operating_equity",
    )
    required_gate_keys = {
        f[1] for f in CANDIDATE_EVENT_REQUIRED_FIELDS
        if isinstance(f, tuple) and len(f) == 2 and f[0] == "gate_results"
    }
    missing = set(gates.keys()) - required_gate_keys
    assert not missing, (
        f"these gate keys are returned by apply_v2_gates but not required by "
        f"CANDIDATE_EVENT_REQUIRED_FIELDS: {sorted(missing)}"
    )


def test_p0_remediation_gate_keys_present() -> None:
    """The three keys that Report §8.3 specifically called out."""
    required_gate_keys = {
        f[1] for f in CANDIDATE_EVENT_REQUIRED_FIELDS
        if isinstance(f, tuple) and len(f) == 2 and f[0] == "gate_results"
    }
    for key in ("projected_rvol_gate", "max_rvol_gate", "max_range_expansion_gate"):
        assert key in required_gate_keys, f"required gate key missing: {key}"
