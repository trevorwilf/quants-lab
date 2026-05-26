"""Deterministic contract -> lab-config mapper (realism remediation Phase 1).

Builds a lab :class:`~bowaka_v2_lab.config.models.BowakaV2Config` dict from the
frozen live-strategy contract (``reference/actual_bowaka_v2_contract.yaml``).

Several contract sections come straight from the *live* config and use a schema
that **differs** from the lab schema — ``universe``, ``scanner`` and
``execution`` are remapped key-by-key here. The schema-matching sections
(``session``, ``signals``, ``sizing``, ``risk``, ``exits``) are copied verbatim
(subject to a key allow-list for ``session``).

The contract-level ``data:`` block (realism remediation 2 Phase 1, audit
§P0-005) supplies the adjustment / freshness requirements; they are threaded
into ``market_data.*`` so a generated config carries the live contract's
``require_adjusted_daily_bars`` / ``require_split_adjustment`` /
``max_bar_age_seconds`` / ``max_quote_age_seconds``.

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

#: Valid ``--feed-thresholds`` values.
FEED_THRESHOLD_MODES: tuple[str, ...] = ("actual", "sip_tightened")

#: Valid ``simulation.mode`` values the mapper emits.
CONFIG_MODES: tuple[str, ...] = ("intended_realism", "current_code_parity")

#: Valid ``--purpose`` values for ``import-actual-config`` (realism remediation 2
#: Phase 8). ``backtest`` emits a one-shot backtest config; ``optuna`` adds an
#: ``optuna:`` block + sets ``run.kind: optuna`` for a walk-forward study.
CONFIG_PURPOSES: tuple[str, ...] = ("backtest", "optuna")

#: The audit's documented SIP-intended signal thresholds (audit §3.3 / §6.1).
#: ``--feed-thresholds sip_tightened`` overlays these on the contract's
#: (IEX-relaxed) thresholds and declares each as a ``scoped`` parity diff.
SIP_TIGHTENED_THRESHOLDS: dict[str, float] = {
    "rvol_so_far_min": 1.50,
    "projected_full_day_rvol_min": 1.50,
    "range_expansion_so_far_min": 1.25,
    "ema_distance_min": 0.0,
    "ema_slope_min": 0.0,
}


#: Constant header block prepended to every generated config. Filename-agnostic
#: so re-running ``import-actual-config --out <anything>`` is byte-identical
#: regardless of the output path (the byte-stable parity test relies on this).
_CONFIG_HEADER = """\
# ------------------------------------------------------------------
# GENERATED bowaka_v2 lab config (DO NOT hand-edit).
#
# Built deterministically from the frozen live-strategy contract
# (reference/actual_bowaka_v2_contract.yaml) by the contract -> config
# mapper. Regenerate with:
#   python -m bowaka_v2_lab.cli import-actual-config \\
#       --out configs/<name>.yml [--feed sip|iex] \\
#       [--mode intended_realism|current_code_parity] \\
#       [--feed-thresholds actual|sip_tightened]
#
# Re-running the command is byte-identical. Every value under the
# schema-matching sections (session/signals/sizing/risk/exits) is
# sourced verbatim from the contract; universe/scanner/execution are
# remapped from the live schema. market_data.require_adjusted_daily_bars
# / require_split_adjustment / max_bar_age_seconds / max_quote_age_seconds
# come from the contract's data: block. Phase 1's config-parity diff
# (config_diff_vs_actual_bowaka_v2.yaml) is checked against this file.
# ------------------------------------------------------------------
"""

#: Extra header block appended to ``--purpose optuna`` configs. Documents the
#: walk-forward sizing rationale (lake range, fold count, user spec) so the
#: operator reading the YAML understands why these values were chosen and the
#: path to raising train_months as the lake accrues additional sessions.
_OPTUNA_HEADER_SUFFIX = """\
#
# Walk-forward sizing rationale (2026-05-23 IEX lake snapshot)
# ------------------------------------------------------------------
# Lake range: 2023-11-27 -> 2026-05-20 (~29.8 months of IEX daily bars).
# User-supplied spec (2026-05-23 conversation):
#   - final_holdout_months = 5  (fixed).
#   - train_months >= 18        (minimum); 24 is the operator's example.
#   - holdout end = lake max    (as close to the current date as the
#                                data set will allow).
# Shipped values: train=21, val=1, final_holdout=5 -> 3 walk-forward
# folds, every fold using only real lake data (no empty-day padding).
# train=24 would need >=30 lake months (we have 29.8) and produce 0
# folds today; raise train_months toward 24 as the lake accrues data
# and regenerate via ``import-actual-config --purpose optuna``.
# ------------------------------------------------------------------
"""


def build_config_from_contract(
    contract: dict[str, Any],
    *,
    feed: str = "sip",
    mode: str = "intended_realism",
    feed_thresholds: str = "actual",
    purpose: str = "backtest",
) -> dict[str, Any]:
    """Map a frozen contract dict to a lab ``BowakaV2Config`` dict.

    ``feed`` selects ``market_data.feed`` (``sip`` default — the contract models
    the intended live strategy on consolidated tape). ``mode`` selects
    ``simulation.mode`` (``intended_realism`` or ``current_code_parity``).
    ``feed_thresholds`` is ``actual`` (contract thresholds verbatim) or
    ``sip_tightened`` (the audit's documented SIP-intended thresholds overlaid).
    ``purpose`` is ``backtest`` (one-shot run) or ``optuna`` (adds an ``optuna:``
    block + ``run.kind: optuna`` for a walk-forward study — realism remediation 2
    Phase 8).
    """
    if feed not in ("sip", "iex"):
        raise ValueError(f"feed must be 'sip' or 'iex', got {feed!r}")
    if mode not in CONFIG_MODES:
        raise ValueError(f"mode must be one of {CONFIG_MODES}, got {mode!r}")
    if feed_thresholds not in FEED_THRESHOLD_MODES:
        raise ValueError(
            f"feed_thresholds must be one of {FEED_THRESHOLD_MODES}, got {feed_thresholds!r}"
        )
    if purpose not in CONFIG_PURPOSES:
        raise ValueError(f"purpose must be one of {CONFIG_PURPOSES}, got {purpose!r}")
    c_data = dict(contract.get("data") or {})
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

    # --- scanner: emit EVERY live scanner key (audit 2026-05-23 §P1-003) ---
    # Iterating the contract's scanner mapping (rather than enumerating keys
    # in code) means the generated config automatically expands when the
    # actual contract grows. ``min_signal_strength`` is the lab-schema knob
    # the optimizer overlays on — it inherits from the contract when present
    # and otherwise defaults to 0.0 (the live scanner's effective default).
    scanner: dict[str, Any] = {k: v for k, v in c_scanner.items()}
    scanner.setdefault("min_signal_strength", 0.0)

    # --- signals: research flag + all 16 thresholds verbatim ---
    signals: dict[str, Any] = {"allow_unknown_instrument_class_for_research": False}
    for key in SIGNAL_THRESHOLD_KEYS:
        signals[key] = c_signals.get(key)
    if feed_thresholds == "sip_tightened":
        # Overlay the audit's documented SIP-intended thresholds.
        for key, value in SIP_TIGHTENED_THRESHOLDS.items():
            signals[key] = value

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

    # --- market_data: feed + the contract data: block's adjustment / freshness ---
    # The live contract requires adjusted + split-adjusted daily bars; thread
    # those into market_data so the generated config carries them explicitly
    # (the BowakaV2Config validator requires the field for real-mode configs).
    market_data: dict[str, Any] = {
        "feed": feed,
        "allow_non_sip_for_research_only": (feed == "iex"),
        "max_bar_age_seconds": int(c_data.get("max_bar_age_seconds", 90)),
        "max_quote_age_seconds": int(c_data.get("max_quote_age_seconds", 15)),
        "minute_bar_source": "alpaca",
        "daily_bar_source": "alpaca",
        "quote_source": "alpaca",
        "assume_naive_timezone": False,
        "require_adjusted_daily_bars": bool(c_data.get("require_adjusted_daily_bars", True)),
        "require_split_adjustment": bool(c_data.get("require_split_adjustment", True)),
    }

    cfg: dict[str, Any] = {
        "strategy_id": "bowaka_v2",
        "strategy_version": "0.1.0",
        "simulation": {"mode": mode},
        "market_data": market_data,
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
        "run": {"kind": ("optuna" if purpose == "optuna" else "backtest"), "seed": 1337},
        "paths": {
            "lab_root": "research_notebooks/bowaka_v2_lab",
            "data_root": "research_notebooks/bowaka_v2_lab/data",
            "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts",
        },
    }
    if purpose == "optuna":
        # Realism remediation 2 Phase 12 — walk-forward sizing locked to the
        # user spec (2026-05-23): final_holdout_months=5, train_months>=18,
        # holdout end = lake max date. Dates derived from the current IEX
        # lake snapshot (2023-11-27 -> 2026-05-20, ~29.8 months); train=21
        # fits 3 clean walk-forward folds inside (rolling_budget=~23.8m,
        # 3*val_step + train + final_holdout = 3 + 21 + 5 = 29 <= 29.8).
        # See _OPTUNA_HEADER_SUFFIX for the full rationale (rendered into
        # the YAML so the operator can read it without grepping the source).
        cfg["backtest"] = {
            "start_date": "2023-11-27",
            "end_date": "2026-05-20",
            "cost_stress": "conservative",
            "entry_delay_minutes": 0,
        }
        # Realism remediation 2 Phase 8 — walk-forward study scaffolding. The
        # commit-shipped optuna configs carry conservative defaults the runner
        # honours; the operator overrides per-study via --n-trials / --n-jobs.
        cfg["optuna"] = {
            # Audit 2026-05-23 §P1-006 — relative SQLite URIs resolve against
            # the lab root at runtime via
            # ``bowaka_v2_lab.optuna.storage_path.resolve_storage_uri``, so
            # launching the runner from the lab directory works. For a
            # production study use a PostgreSQL URI:
            #   OPTUNA_STORAGE="postgresql+psycopg://user:pass@host:5432/bowaka_optuna"
            "storage": (
                "${OPTUNA_STORAGE:-postgresql+psycopg2://optuna:optuna@"
                "optuna-postgres:5432/optuna}"
            ),
            "n_trials": 200,
            # Speedup report §6.1 / §11.3 Phase 5 — process-parallel default.
            # Capped at MemoryBudget.max_optuna_workers (default 8) at runtime.
            # PostgreSQL storage required; the dispatcher falls back to serial
            # on a non-PostgreSQL URL unless ``parallel.strict_parallel`` is set.
            "n_jobs": 8,
            "n_startup_trials": 25,
            "study_name_prefix": f"bowaka_v2_actual_{feed}_{mode}",
            "cost_stress": "conservative",
            # Speedup report §5.1 / §11.2 Phase 1 — flipped on now that Phase
            # 1 parity is proven (per-trial fold backtests skip every disk
            # artifact write; FoldResult is built from the in-memory
            # BacktestResult identically to the legacy report.json path).
            "objective_artifact_mode": "objective_minimal",
            # Speedup report §5.3 / §11.2 Phase 3 — flipped on now that
            # Phase 3 parity is proven (cached LRU adapter eliminates
            # repeated Parquet reads while preserving the inclusive
            # boundary semantics + quote-supplier dict shape exactly).
            "cached_suppliers": True,
            # Speedup report §6.1 / §11.3 Phase 5 — parallel launcher knobs.
            "parallel": {
                "memory_reserve_gib": 32,
                "max_workers": 8,
                "strict_parallel": False,
                "blas_thread_pin": True,
            },
            # Speedup report §6.4 / matrix doc §17 Phase 8 — scan-matrix
            # acceleration. Default off (Phase 9 wires it to the runtime).
            "acceleration": {
                "scan_matrix": {
                    "enabled": False,
                    "build_if_missing": False,
                    "scope": "validation",
                    "separate_holdout_matrix": True,
                    "root": "research_notebooks/bowaka_v2_lab/artifacts/cache/scan_matrix",
                    "dtype_policy": "float64_first",
                    "storage_format": "numpy_memmap",
                    "precompute_workers": 8,
                    "max_optuna_workers": 8,
                    "require_parity_manifest": True,
                    "fail_on_matrix_sensitive_search_space": True,
                    "allow_full_history_matrix": False,
                    # Speedup report v2 §4 P6 / §6.1 / Phase 6 — three-mode
                    # runtime: disabled (default; legacy scanner) /
                    # compatibility (matrix-backed evaluator returning
                    # bit-equal candidate events) / vectorized (numpy gate
                    # masks). Both non-disabled modes are scaffolding-only
                    # until the parity matrix lands.
                    "runtime_mode": "disabled",
                },
            },
            "walkforward": {
                "train_months": 21,
                "val_months": 1,
                "final_holdout_months": 5,
            },
            "search_space_overrides": {},
        }
        # Speedup report v2 §1.4 / §8.3 / §9 / Phase 5 — staged finalist
        # evaluation defaults. The Stage B pipeline re-runs the top-K
        # candidates + the incumbent in full artifact mode, scores the
        # final holdout (once), runs the fold-local stress matrix, and
        # runs a local parameter-neighborhood sweep. Operator-driven —
        # invoke via ``bowaka_v2_lab.optuna.evaluate_finalists`` or the
        # ``evaluate-finalists`` CLI subcommand.
        cfg["finalist_evaluation"] = {
            "top_k": 15,
            "include_incumbent": True,
            "full_artifacts": True,
            "score_final_holdout": True,
            "stress_scenarios": [
                {"name": "wider_spreads",
                 "overrides": {"execution.max_spread_bps_multiplier": 1.5}},
                {"name": "stale_quote_pressure",
                 "overrides": {"execution.max_quote_age_seconds_multiplier": 0.5}},
                {"name": "higher_cost_stress",
                 "overrides": {"backtest.cost_stress": "aggressive"}},
            ],
            "local_parameter_perturbation": {
                "enabled": True,
                "relative_delta": 0.05,
                "max_neighbors_per_param": 2,
            },
        }
    return cfg


def render_config_yaml(cfg: dict[str, Any], *, purpose: str = "backtest") -> str:
    """Deterministic YAML text for a config dict (header + optional suffix + sorted body).

    The body is always sorted-key YAML and both header pieces are
    filename-agnostic, so re-running ``import-actual-config`` is byte-identical.
    ``purpose="optuna"`` appends :data:`_OPTUNA_HEADER_SUFFIX` (walk-forward
    sizing rationale) so the rendered YAML documents why the train/val/holdout
    values were chosen against the current lake snapshot.
    """
    body = yaml.safe_dump(
        cfg,
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=True,
        width=1000,
    )
    header = _CONFIG_HEADER + (_OPTUNA_HEADER_SUFFIX if purpose == "optuna" else "")
    return header + body


def build_sip_tightened_sidecar_rows(contract: dict[str, Any]) -> list[dict[str, Any]]:
    """Parity-sidecar rows declaring the ``sip_tightened`` threshold diffs.

    Each overlaid SIP-intended threshold differs from the contract's
    (IEX-relaxed) value; declare every one as a ``scoped`` divergence so the
    config stays parity-clean against the frozen contract.
    """
    c_signals = dict(contract.get("signals") or {})
    rows: list[dict[str, Any]] = []
    for key, value in SIP_TIGHTENED_THRESHOLDS.items():
        rows.append(
            {
                "field_path": f"signals.{key}",
                "actual_value": c_signals.get(key),
                "lab_value": value,
                "reason": (
                    "SIP-intended threshold (audit §3.3): the contract carries "
                    "IEX-relaxed thresholds; SIP consolidated tape supports the "
                    "tighter documented value."
                ),
                "risk_classification": "scoped",
            }
        )
    return rows


def render_parity_sidecar_yaml(rows: list[dict[str, Any]]) -> str:
    """Deterministic YAML text for a ``<config>.parity_sidecar.yaml`` file."""
    doc = {"schema_version": 1, "declared_diffs": rows}
    return yaml.safe_dump(doc, sort_keys=True, default_flow_style=False, width=1000)


def import_actual_config(
    *,
    out_path: str | Path,
    feed: str = "sip",
    mode: str = "intended_realism",
    feed_thresholds: str = "actual",
    purpose: str = "backtest",
    contract: dict[str, Any] | None = None,
) -> Path:
    """Generate a config from the frozen contract. Returns the written path.

    Validates the mapped dict with :class:`BowakaV2Config` before writing, so a
    mapping defect surfaces immediately. When ``feed_thresholds=="sip_tightened"``
    a ``<config-stem>.parity_sidecar.yaml`` declaring the threshold diffs is
    written alongside the config. ``purpose="optuna"`` emits a walk-forward study
    config (adds an ``optuna:`` block + ``run.kind: optuna``) — realism
    remediation 2 Phase 8.
    """
    from . import load_actual_contract

    if contract is None:
        contract = load_actual_contract()
    cfg = build_config_from_contract(
        contract, feed=feed, mode=mode, feed_thresholds=feed_thresholds,
        purpose=purpose,
    )
    # Fail fast on a mapping defect.
    BowakaV2Config.model_validate(dict(cfg))
    dest = Path(out_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    # write_bytes bypasses Windows text-mode CRLF translation so the file's
    # newlines match ``.gitattributes`` (``*.yml text eol=lf``) on every host —
    # the byte-stable parity test was passing on the Linux container but
    # failing on a Windows checkout because ``write_text`` injected ``\r\n``.
    dest.write_bytes(render_config_yaml(cfg, purpose=purpose).encode("utf-8"))
    if feed_thresholds == "sip_tightened":
        sidecar = dest.with_name(f"{dest.stem}.parity_sidecar.yaml")
        sidecar.write_bytes(
            render_parity_sidecar_yaml(
                build_sip_tightened_sidecar_rows(contract)
            ).encode("utf-8")
        )
    return dest


__all__ = [
    "SIGNAL_THRESHOLD_KEYS",
    "FEED_THRESHOLD_MODES",
    "CONFIG_MODES",
    "CONFIG_PURPOSES",
    "SIP_TIGHTENED_THRESHOLDS",
    "build_config_from_contract",
    "build_sip_tightened_sidecar_rows",
    "render_config_yaml",
    "render_parity_sidecar_yaml",
    "import_actual_config",
]
