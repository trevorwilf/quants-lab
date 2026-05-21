"""Deterministic contract -> lab-config mapper (realism remediation Phase 1).

Builds a lab :class:`~bowaka_v2_lab.config.models.BowakaV2Config` dict from the
frozen live-strategy contract (``reference/actual_bowaka_v2_contract.yaml``).

Several contract sections come straight from the *live* config and use a schema
that **differs** from the lab schema — ``universe``, ``scanner`` and
``execution`` are remapped key-by-key here. The schema-matching sections
(``session``, ``signals``, ``sizing``, ``risk``, ``exits``) are copied verbatim
(subject to a key allow-list for ``session``).

The output is rendered with :func:`render_config_yaml`, which sorts keys and
pins the header so re-running ``import-actual-config`` is byte-identical.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ..config.models import BowakaV2Config

#: All 16 live signal-gate threshold keys, copied verbatim from contract.signals.
SIGNAL_THRESHOLD_KEYS: tuple[str, ...] = (
    "rvol_so_far_min",
    "projected_full_day_rvol_min",
    "prior_atr_pct_min",
    "range_expansion_so_far_min",
    "close_location_so_far_min",
    "ema_distance_min",
    "ema_slope_min",
    "price_min",
    "price_max",
    "avg_dollar_volume_min",
    "avg_dollar_volume_max",
    "rvol_so_far_max",
    "projected_full_day_rvol_max",
    "range_expansion_so_far_max",
    "gap_pct_max",
    "current_return_pct_max",
)

#: contract.session keys the lab SessionConfig accepts (copied verbatim).
_SESSION_KEYS: tuple[str, ...] = (
    "timezone",
    "start",
    "end",
    "scanner_start",
    "scanner_end",
    "loop_interval_seconds",
)

_CONFIG_HEADER = """\
# ------------------------------------------------------------------
# bowaka_v2_intended_realism.yml -- GENERATED config (DO NOT hand-edit).
#
# Built deterministically from the frozen live-strategy contract
# (reference/actual_bowaka_v2_contract.yaml) by the contract -> config
# mapper. Regenerate with:
#   python -m bowaka_v2_lab.cli import-actual-config \\
#       --out configs/bowaka_v2_intended_realism.yml [--feed sip|iex]
#
# Re-running the command is byte-identical. Every value under the
# schema-matching sections (session/signals/sizing/risk/exits) is
# sourced verbatim from the contract; universe/scanner/execution are
# remapped from the live schema. Phase 1's config-parity diff
# (config_diff_vs_actual_bowaka_v2.yaml) is checked against this file.
# ------------------------------------------------------------------
"""


def build_config_from_contract(contract: dict[str, Any], *, feed: str = "sip") -> dict[str, Any]:
    """Map a frozen contract dict to a lab ``BowakaV2Config`` dict.

    ``feed`` selects the ``market_data.feed`` (``sip`` default — the contract
    models the intended live strategy on consolidated tape).
    """
    if feed not in ("sip", "iex"):
        raise ValueError(f"feed must be 'sip' or 'iex', got {feed!r}")
    c_session = dict(contract.get("session") or {})
    c_universe = dict(contract.get("universe") or {})
    c_scanner = dict(contract.get("scanner") or {})
    c_signals = dict(contract.get("signals") or {})
    c_execution = dict(contract.get("execution") or {})
    c_sizing = dict(contract.get("sizing") or {})
    c_risk = dict(contract.get("risk") or {})
    c_exits = dict(contract.get("exits") or {})

    # --- session: copy lab-accepted keys + the lab calendar default ---
    session: dict[str, Any] = {"calendar": "XNYS"}
    for key in _SESSION_KEYS:
        if key in c_session:
            session[key] = c_session[key]

    # --- universe: MAP from the live universe schema ---
    universe: dict[str, Any] = {
        "asset_classes": ["operating_equity"],
        "min_price": c_universe.get("price_min"),
        "max_price": c_universe.get("price_max"),
        "min_adv_dollars": c_universe.get("avg_dollar_volume_min"),
        "exclude_pattern_class": True,
    }

    # --- scanner: MAP from the live scanner schema ---
    scanner: dict[str, Any] = {
        "max_candidates_per_scan": c_scanner.get("max_candidates_per_scan"),
        "max_entries_per_scan": c_scanner.get("max_entries_per_scan"),
        "min_signal_strength": 0.0,
    }

    # --- signals: research flag + all 16 thresholds verbatim ---
    signals: dict[str, Any] = {"allow_unknown_instrument_class_for_research": False}
    for key in SIGNAL_THRESHOLD_KEYS:
        signals[key] = c_signals.get(key)

    # --- execution: MAP from the live execution schema ---
    quote_gate = dict(c_execution.get("quote_gate") or {})
    execution: dict[str, Any] = {
        "order_type": c_execution.get("parent_order_style"),
        "limit_offset_bps": round(float(c_execution.get("marketable_limit_slippage_pct", 0.0)) * 10000),
        "max_quote_age_seconds": quote_gate.get("max_quote_age_seconds"),
        "max_spread_bps": round(float(quote_gate.get("max_spread_pct", 0.0)) * 10000),
    }

    # --- sizing / risk / exits: copy verbatim (lab schema matches live) ---
    sizing: dict[str, Any] = dict(c_sizing)
    risk: dict[str, Any] = dict(c_risk)
    exits: dict[str, Any] = dict(c_exits)

    cfg: dict[str, Any] = {
        "strategy_id": "bowaka_v2",
        "strategy_version": "0.1.0",
        "simulation": {"mode": "intended_realism"},
        "market_data": {
            "feed": feed,
            "allow_non_sip_for_research_only": False,
            "max_bar_age_seconds": 60,
            "minute_bar_source": "alpaca",
            "daily_bar_source": "alpaca",
            "quote_source": "alpaca",
            "assume_naive_timezone": False,
        },
        "session": session,
        "universe": universe,
        "scanner": scanner,
        "signals": signals,
        "execution": execution,
        "sizing": sizing,
        "risk": risk,
        "exits": exits,
        "backtest": {
            "start_date": "2024-09-01",
            "end_date": "2024-12-31",
            "cost_stress": "conservative",
            "entry_delay_minutes": 0,
        },
        "artifacts": {"write_parquet": True, "write_jsonl": True},
        "run": {"kind": "backtest", "seed": 1337},
        "paths": {
            "lab_root": "research_notebooks/bowaka_v2_lab",
            "data_root": "research_notebooks/bowaka_v2_lab/data",
            "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts",
        },
    }
    return cfg


def render_config_yaml(cfg: dict[str, Any]) -> str:
    """Deterministic YAML text for a config dict (header + sorted body)."""
    body = yaml.safe_dump(
        cfg,
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=True,
        width=1000,
    )
    return _CONFIG_HEADER + body


def import_actual_config(
    *, out_path: str | Path, feed: str = "sip", contract: dict[str, Any] | None = None
) -> Path:
    """Generate the intended-realism config from the frozen contract.

    Validates the mapped dict with :class:`BowakaV2Config` before writing, so a
    mapping defect surfaces immediately. Returns the written path.
    """
    from . import load_actual_contract

    if contract is None:
        contract = load_actual_contract()
    cfg = build_config_from_contract(contract, feed=feed)
    # Fail fast on a mapping defect.
    BowakaV2Config.model_validate(dict(cfg))
    dest = Path(out_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_config_yaml(cfg), encoding="utf-8")
    return dest


__all__ = [
    "SIGNAL_THRESHOLD_KEYS",
    "build_config_from_contract",
    "render_config_yaml",
    "import_actual_config",
]
