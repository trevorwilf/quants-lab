"""Walk-forward Optuna objectives for range_ladder (Phase A / A.1 / A.2).

Two search modes share ONE fold-evaluation core (`evaluate_ladder_walkforward`),
which is also what the notebook's incumbent benchmark calls — so incumbents
and trials are always judged under the SAME gate policy and objective mode:

- generative (`_create_range_ladder_objective`): 10-param generative family;
  rungs rebuilt per fold at the train-only median-3 anchor.
- refine_incumbent (`create_range_ladder_refine_objective`): overlay (stage 1,
  6-param TPE) or per-rung nudge (stage 2, CMA-ES box) applied to a literal
  live ladder; rungs are absolute and identical across folds.

Gate policy (Phase A.1 §2): GatePolicy(mode=strict|accumulate_ok|soft).
Library defaults preserve Phase A behavior exactly (strict endinv 75 gate,
two-sided, no fill-frequency/touch constraints); the notebook surfaces the
Phase A.2 defaults (touches 8 over 270d, 6 trades/mo, 3 fills/side).

Fold scoring (Phase A.2 §3c): objective_mode="median_ann" is the Phase A
annualized-PnL fold score (bit-identical); "consistency" multiplies it by
(0.5 + 0.5 * frac_positive_windows) over rolling 30d/7d test windows.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

import numpy as np
import optuna

from pmm_lab.config.params import PairRules
from pmm_lab.objective.objective import REJECT_SCORE

logger = logging.getLogger(__name__)

ENDINV_GATE_PCT = 75.0
WINSOR_CLAMP_MAD = 2.0
DEFAULT_LAMBDA_MAD = 0.5
TARGET_FOLDS = 3
MAX_TEST_DAYS = 60.0
MIN_TRAIN_DAYS = 90.0
MIN_TOTAL_DAYS = 150.0

GATE_MODES = ("strict", "accumulate_ok", "soft")
OBJECTIVE_MODES = ("median_ann", "consistency")

CONSISTENCY_WINDOW_DAYS = 30.0
CONSISTENCY_STEP_DAYS = 7.0


@dataclass(frozen=True)
class GatePolicy:
    """Fold gate policy (Phase A.1 §2 + Phase A.2 §3a/3b).

    The DATACLASS defaults reproduce Phase A behavior exactly (strict endinv
    gate, plain two-sidedness, no fill-frequency or train-touch constraints).
    The notebook parameter defaults enable the Phase A.2 fill-frequency
    preference (touches 8/270d, 6 trades/mo, 3 fills per side).
    """

    mode: str = "strict"                    # strict | accumulate_ok | soft
    endinv_gate_pct: float = ENDINV_GATE_PCT
    endinv_penalty: float = 20.0            # soft mode: score penalty scale
    cons_floor_ann_pct: float = 0.0         # accumulate_ok: stress-score floor
    max_dd_pct: float = 60.0                # accumulate_ok: fold max-DD ceiling
    # Fill-frequency preference (Phase A.2 §3b). 0 / 1 = disabled (Phase A).
    min_trades_per_month: float = 0.0
    min_side_fills_per_fold: int = 1
    # Per-rung train-touch constraint (Phase A.2 §3a). 0 = disabled.
    min_rung_touches_train: int = 0
    touch_lookback_days: float = 270.0

    def __post_init__(self):
        if self.mode not in GATE_MODES:
            raise ValueError(f"GatePolicy.mode must be one of {GATE_MODES}; got {self.mode!r}")

    def describe(self) -> dict:
        """JSON-friendly form for user_attrs / reports / YAML comments."""
        return {
            "mode": self.mode,
            "endinv_gate_pct": self.endinv_gate_pct,
            "endinv_penalty": self.endinv_penalty,
            "cons_floor_ann_pct": self.cons_floor_ann_pct,
            "max_dd_pct": self.max_dd_pct,
            "min_trades_per_month": self.min_trades_per_month,
            "min_side_fills_per_fold": self.min_side_fills_per_fold,
            "min_rung_touches_train": self.min_rung_touches_train,
            "touch_lookback_days": self.touch_lookback_days,
        }


def evaluate_fold_gates(fold: dict, policy: GatePolicy) -> Tuple[bool, list, float]:
    """Judge one fold result under the policy.

    Returns (violated, reasons, soft_penalty). `fold` needs: buy_fills,
    sell_fills, endinv_pct, maxdd, trades_per_month, cons_ann_pct (None when
    stress was not run — the accumulate_ok cons gate is then skipped).
    """
    reasons = []
    penalty = 0.0
    bf, sf = int(fold["buy_fills"]), int(fold["sell_fills"])

    # Two-sidedness — kept in ALL modes.
    if bf < 1 or sf < 1:
        reasons.append(f"not two-sided ({bf}b/{sf}s)")

    # Fill-frequency gates (Phase A.2 §3b) — count in all modes.
    m = policy.min_side_fills_per_fold
    if m > 1 and (bf < m or sf < m):
        reasons.append(f"per-side fills below {m} ({bf}b/{sf}s)")
    if policy.min_trades_per_month > 0 and fold["trades_per_month"] < policy.min_trades_per_month:
        reasons.append(
            f"trades/month {fold['trades_per_month']:.1f} below "
            f"{policy.min_trades_per_month:g}"
        )

    endinv = float(fold["endinv_pct"])
    if policy.mode == "strict":
        if endinv > policy.endinv_gate_pct:
            reasons.append(f"endinv {endinv:.1f}% > {policy.endinv_gate_pct:g}%")
    elif policy.mode == "accumulate_ok":
        # endinv gate waived; replacement risk gates instead.
        cons = fold.get("cons_ann_pct")
        if cons is not None and cons < policy.cons_floor_ann_pct:
            reasons.append(
                f"conservative ann {cons:.1f}% below floor "
                f"{policy.cons_floor_ann_pct:g}%"
            )
        if float(fold["maxdd"]) > policy.max_dd_pct:
            reasons.append(f"max drawdown {fold['maxdd']:.1f}% > {policy.max_dd_pct:g}%")
    elif policy.mode == "soft":
        # endinv never prunes; it subtracts from the fold score instead.
        penalty = policy.endinv_penalty * max(0.0, endinv - policy.endinv_gate_pct) / 100.0

    return (len(reasons) > 0), reasons, penalty


def frac_positive_windows(
    equity: np.ndarray,
    bar_interval_seconds: int,
    window_days: float = CONSISTENCY_WINDOW_DAYS,
    step_days: float = CONSISTENCY_STEP_DAYS,
) -> float:
    """Fraction of rolling windows with positive PnL (Phase A.2 §3c).

    Windows are `window_days` long, stepping `step_days`, fully inside the
    equity curve; window PnL = equity[end] − equity[start]. When the curve is
    shorter than one window, the whole curve is a single window.
    """
    eq = np.asarray(equity, dtype=np.float64)
    n = len(eq)
    if n < 2:
        return 0.0
    wbars = max(2, int(window_days * 86400.0 / bar_interval_seconds))
    sbars = max(1, int(step_days * 86400.0 / bar_interval_seconds))
    if wbars >= n:
        return 1.0 if eq[-1] > eq[0] else 0.0
    starts = range(0, n - wbars + 1, sbars)
    pnls = [eq[s + wbars - 1] - eq[s] for s in starts]
    return float(np.mean([p > 0 for p in pnls]))


def plan_range_ladder_folds(
    n_bars: int,
    bar_interval_seconds: int,
    target_folds: int = TARGET_FOLDS,
    max_test_days: float = MAX_TEST_DAYS,
    min_train_days: float = MIN_TRAIN_DAYS,
) -> Tuple[float, float, float]:
    """Compute (train_days, test_days, step_days) per the §3.6 fold layout.

    test = min(60d, floor(total/5)), further capped so that
    train = total − target_folds*test stays >= min_train_days. step = test
    (non-overlapping test windows). Raises ValueError when the history can't
    support the layout — the notebook preflight surfaces this as an abort.
    """
    total_days = n_bars * bar_interval_seconds / 86400.0
    test_days = min(
        max_test_days,
        math.floor(total_days / 5.0),
        math.floor((total_days - min_train_days) / target_folds),
    )
    if test_days < 1.0:
        raise ValueError(
            f"insufficient history for the range_ladder fold layout: "
            f"{total_days:.1f} usable days (need >= {MIN_TOTAL_DAYS:.0f}d for "
            f"{target_folds} folds with train >= {min_train_days:.0f}d)"
        )
    bars_per_day = 86400.0 / bar_interval_seconds
    test_bars = int(test_days * bars_per_day)
    train_bars = n_bars - target_folds * test_bars
    train_days = train_bars / bars_per_day
    return float(train_days), float(test_days), float(test_days)


def winsorized_fold_objective(
    scores,
    clamp_mad: float = WINSOR_CLAMP_MAD,
    lambda_mad: float = DEFAULT_LAMBDA_MAD,
) -> Tuple[float, list]:
    """Winsorize fold scores to median ± clamp_mad*MAD, then
    median(winsorized) − lambda_mad * MAD(winsorized).

    Returns (objective, winsorized_scores). Empty input → REJECT_SCORE.
    """
    arr = np.asarray(list(scores), dtype=np.float64)
    if arr.size == 0:
        return REJECT_SCORE, []
    med = float(np.median(arr))
    mad = float(np.median(np.abs(arr - med)))
    lo, hi = med - clamp_mad * mad, med + clamp_mad * mad
    w = np.clip(arr, lo, hi)
    w_med = float(np.median(w))
    w_mad = float(np.median(np.abs(w - w_med)))
    return w_med - lambda_mad * w_mad, [float(x) for x in w]


def evaluate_ladder_walkforward(
    candles,
    fold_defs,
    bar_interval_seconds: int,
    *,
    rung_provider: Callable,
    fund: float,
    quote_frac: float,
    fee: float,
    slip: float = 0.0,
    cooldown_bars: int = 1,
    max_fills_per_bar: int = 0,
    body_only: bool = False,
    stress_config=None,
    run_stress: bool = True,
    gate_policy: Optional[GatePolicy] = None,
    objective_mode: str = "median_ann",
    lambda_mad: float = DEFAULT_LAMBDA_MAD,
    trial: Optional[optuna.Trial] = None,
) -> dict:
    """Shared fold evaluator — used by BOTH objectives and the incumbent
    benchmark, so every ladder is judged identically.

    Parameters
    ----------
    rung_provider : callable(fold_def) -> (RungSet | None, anchor, reason)
        Generative mode rebuilds+validates rungs at the fold's train anchor;
        refine/benchmark modes return the same absolute rungs every fold.
    trial : optuna.Trial, optional
        When given: per-fold intermediate reports + pruner hook, the
        train-touch constraint prunes, and majority gate violations prune.
        When None (benchmark mode): everything is recorded, nothing prunes.

    Returns
    -------
    dict with fold_detail, fold_scores, fold_scores_winsorized, objective,
    violations, n_folds, cons_scores, min_rung_touches,
    trades_per_month_median.
    """
    from pmm_lab.features._numba_range_ladder import run_ladder_sim
    from pmm_lab.objective.stress_range_ladder import run_range_ladder_stress
    from pmm_lab.strategies.range_ladder_gen import count_rung_touches

    policy = gate_policy or GatePolicy()
    if objective_mode not in OBJECTIVE_MODES:
        raise ValueError(
            f"objective_mode must be one of {OBJECTIVE_MODES}; got {objective_mode!r}"
        )

    closes_high = candles["high"].astype(np.float64)
    closes_low = candles["low"].astype(np.float64)
    bars_per_day = 86400.0 / bar_interval_seconds

    # ---- Pass 1: build rungs + count train touches (cheap, before any sim) ----
    prepared = []
    for fold_def in fold_defs:
        rungs, anchor, reason = rung_provider(fold_def)
        touches = None
        if rungs is not None and policy.min_rung_touches_train > 0:
            lb_bars = int(policy.touch_lookback_days * bars_per_day)
            lo = max(fold_def.train_start_idx, fold_def.train_end_idx - lb_bars)
            touches = {
                "buys": [int(x) for x in count_rung_touches(
                    closes_high[lo:fold_def.train_end_idx],
                    closes_low[lo:fold_def.train_end_idx], rungs.buys)],
                "sells": [int(x) for x in count_rung_touches(
                    closes_high[lo:fold_def.train_end_idx],
                    closes_low[lo:fold_def.train_end_idx], rungs.sells)],
            }
        prepared.append((fold_def, rungs, anchor, reason, touches))

    touch_failures = []
    for fold_def, rungs, anchor, reason, touches in prepared:
        if touches is None:
            continue
        min_touch = min(touches["buys"] + touches["sells"])
        if min_touch < policy.min_rung_touches_train:
            touch_failures.append(
                f"fold {fold_def.fold_index}: min rung touches {min_touch} < "
                f"{policy.min_rung_touches_train} over last "
                f"{policy.touch_lookback_days:g}d of train"
            )
    if touch_failures and trial is not None:
        trial.set_user_attr("reject_reason", "; ".join(touch_failures))
        trial.set_user_attr(
            "rung_touches",
            [t for (_, _, _, _, t) in prepared if t is not None],
        )
        raise optuna.TrialPruned("train-touch constraint: " + touch_failures[0])

    # ---- Pass 2: simulate folds ----
    fold_scores = []
    fold_detail = []
    cons_scores = []
    violations = 0
    last_rungs = None
    all_min_touches = []

    for fold_def, rungs, anchor, reason, touches in prepared:
        if rungs is None:
            violations += 1
            fold_detail.append({
                "fold": fold_def.fold_index, "anchor": anchor,
                "violation": f"rung build failed: {reason}",
            })
            continue
        last_rungs = rungs

        test_slice = candles[fold_def.test_start_idx:fold_def.test_end_idx]
        test_days_actual = len(test_slice) * bar_interval_seconds / 86400.0

        base = run_ladder_sim(
            test_slice["open"], test_slice["high"],
            test_slice["low"], test_slice["close"],
            rungs.buys, rungs.sells, rungs.buy_weights, rungs.sell_weights,
            fund=fund, quote_frac=quote_frac, fee=fee, slip=slip,
            cooldown_bars=cooldown_bars, max_fills_per_bar=max_fills_per_bar,
            body_only=body_only, bar_interval_seconds=bar_interval_seconds,
        )

        cons = None
        cons_ann = None
        if run_stress and stress_config is not None:
            cons = run_range_ladder_stress(
                test_slice, stress_config, rungs, bar_interval_seconds,
            )
            cons_ann = cons["pnl_pct"] * 365.0 / test_days_actual
            cons_scores.append(cons_ann)

        ann_pnl = base["pnl_pct"] * 365.0 / test_days_actual
        frac_pos = None
        if objective_mode == "consistency":
            frac_pos = frac_positive_windows(base["equity"], bar_interval_seconds)
            fold_score = ann_pnl * (0.5 + 0.5 * frac_pos)
        else:
            fold_score = ann_pnl

        detail = {
            "fold": fold_def.fold_index,
            "anchor": anchor,
            "ann_pnl_pct": ann_pnl,
            "pnl_pct": base["pnl_pct"],
            "hold_pct": base["hold_pct"],
            "maxdd": base["maxdd"],
            "endinv_pct": base["endinv_pct"],
            "buy_fills": int(sum(base["buy_fills"])),
            "sell_fills": int(sum(base["sell_fills"])),
            "rung_fills": {"buys": base["buy_fills"], "sells": base["sell_fills"]},
            "trades_per_month": base["trades_per_month"],
            "two_sided": sum(base["buy_fills"]) >= 1 and sum(base["sell_fills"]) >= 1,
            "cons_ann_pct": cons_ann,
            "cons_endinv_pct": cons["endinv_pct"] if cons else None,
            "frac_positive_windows": frac_pos,
            "rung_touches": touches,
        }
        if touches is not None:
            all_min_touches.append(min(touches["buys"] + touches["sells"]))

        gated, reasons, penalty = evaluate_fold_gates(detail, policy)
        fold_score -= penalty
        detail["score_ann_pct"] = fold_score
        detail["gated"] = gated
        detail["gate_reasons"] = reasons
        detail["soft_penalty"] = penalty
        if gated:
            violations += 1

        fold_scores.append(fold_score)
        fold_detail.append(detail)

        if trial is not None:
            trial.report(float(fold_score), step=fold_def.fold_index)
            if trial.should_prune():
                trial.set_user_attr("fold_detail", fold_detail)
                raise optuna.TrialPruned()

    n_folds = len(fold_defs)
    if trial is not None:
        trial.set_user_attr("n_folds", n_folds)
        trial.set_user_attr("gate_violations", violations)
        trial.set_user_attr("fold_detail", fold_detail)
        if last_rungs is not None:
            trial.set_user_attr("last_fold_rungs", {
                "buys": [float(x) for x in last_rungs.buys],
                "sells": [float(x) for x in last_rungs.sells],
                "buy_weights": [float(x) for x in last_rungs.buy_weights],
                "sell_weights": [float(x) for x in last_rungs.sell_weights],
            })
        if violations > n_folds / 2.0:
            trial.set_user_attr(
                "reject_reason",
                f"gate violations in majority of folds ({violations}/{n_folds})",
            )
            raise optuna.TrialPruned(
                f"gate violations in majority of folds ({violations}/{n_folds})"
            )

    objective, winsorized = winsorized_fold_objective(
        fold_scores, clamp_mad=WINSOR_CLAMP_MAD, lambda_mad=lambda_mad,
    )
    tpm = [d["trades_per_month"] for d in fold_detail if "trades_per_month" in d]
    return {
        "fold_detail": fold_detail,
        "fold_scores": [float(s) for s in fold_scores],
        "fold_scores_winsorized": winsorized,
        "objective": float(objective),
        "violations": violations,
        "n_folds": n_folds,
        "cons_scores": cons_scores,
        "min_rung_touches": (min(all_min_touches) if all_min_touches else None),
        "trades_per_month_median": (float(np.median(tpm)) if tpm else None),
        "last_rungs": last_rungs,
    }


def _set_summary_attrs(trial, result, policy: GatePolicy, objective_mode: str):
    """Common post-evaluation trial attributes."""
    trial.set_user_attr("fold_scores", result["fold_scores"])
    trial.set_user_attr("fold_scores_winsorized", result["fold_scores_winsorized"])
    trial.set_user_attr("objective_score", result["objective"])
    trial.set_user_attr("gate_policy", policy.describe())
    trial.set_user_attr("objective_mode", objective_mode)
    if result["cons_scores"]:
        trial.set_user_attr("cons_score_median", float(np.median(result["cons_scores"])))
    if result["min_rung_touches"] is not None:
        trial.set_user_attr("min_rung_touches", result["min_rung_touches"])
    if result["trades_per_month_median"] is not None:
        trial.set_user_attr("trades_per_month_median", result["trades_per_month_median"])
    detail = result["fold_detail"]
    endinvs = [d["endinv_pct"] for d in detail if "endinv_pct" in d]
    if endinvs:
        trial.set_user_attr("endinv_pct_median", float(np.median(endinvs)))
    pnls = [d["pnl_pct"] for d in detail if "pnl_pct" in d]
    if pnls:
        trial.set_user_attr("pnl_pct_median", float(np.median(pnls)))


def _build_fold_defs(n_bars, bar_interval_seconds, train_days, test_days, step_days):
    from pmm_lab.objective.walkforward import TimeSeriesCV
    from pmm_lab.strategies.range_ladder import ANCHOR_LOOKBACK_BARS

    if train_days is None or test_days is None or step_days is None:
        train_days, test_days, step_days = plan_range_ladder_folds(
            n_bars, bar_interval_seconds
        )
    cv = TimeSeriesCV(
        n_bars=n_bars,
        bar_interval_seconds=bar_interval_seconds,
        train_days=train_days,
        test_days=test_days,
        step_days=step_days,
        embargo_bars=0,
        macd_slow=ANCHOR_LOOKBACK_BARS,
        natr_length=ANCHOR_LOOKBACK_BARS,
    )
    return cv.get_folds(), (train_days, test_days, step_days)


def _reject_objective(reason: str):
    """Objective stub for insufficient walk-forward data — every trial
    records the reason and scores REJECT (Phase A behavior; the notebook's
    zero-completed-trial guard surfaces it)."""
    def objective(trial: optuna.Trial) -> float:
        trial.set_user_attr("strategy_name", "range_ladder")
        trial.set_user_attr("reject_reason", reason)
        trial.set_user_attr("objective_score", REJECT_SCORE)
        return REJECT_SCORE
    return objective


# ----------------------------------------------------------------------
# Generative objective (Phase A search mode)
# ----------------------------------------------------------------------

def _create_range_ladder_objective(
    candles,
    pair_rules: PairRules,
    bar_interval_seconds: int,
    dataset_hash: str,
    reference_price: float,
    train_days: Optional[float],
    test_days: Optional[float],
    step_days: Optional[float],
    embargo_bars,
    objective_version: int,
    run_stress: bool,
    lambda_mad: float,
    fixed_quote: Optional[float],
    strategy_search_space,
    strategy_canonicalizer,
    gate_policy: Optional[GatePolicy] = None,
    objective_mode: str = "median_ann",
):
    """Create the generative-mode Optuna objective for range_ladder.

    Notes
    -----
    - `objective_version` is accepted for dispatch-signature uniformity but
      unused: fold scores are annualized ladder PnL% (or the consistency
      blend), not objective_v1/v2 over engine metrics.
    - `reference_price` should be the DEPLOY anchor (median of the last 3
      closes) — feasibility/min-notional constraints are checked at it
      (Phase A.1 §1). Per-fold trial anchoring stays train-only median-3.
    - Pass train/test/step = None to auto-plan folds per §3.6.
    """
    from pmm_lab.optuna.canonicalizer_range_ladder import (
        canonicalize_range_ladder_params, effective_min_order_quote,
    )
    from pmm_lab.optuna.search_space_range_ladder import suggest_range_ladder_params
    from pmm_lab.strategies.range_ladder import compute_anchor
    from pmm_lab.strategies.range_ladder_gen import build_rungs, validate_rungs

    _suggest = strategy_search_space or suggest_range_ladder_params
    _canonicalize = strategy_canonicalizer or canonicalize_range_ladder_params
    _policy = gate_policy or GatePolicy()
    _lambda = lambda_mad if lambda_mad is not None else DEFAULT_LAMBDA_MAD

    n_bars = len(candles)
    try:
        fold_defs, plan = _build_fold_defs(
            n_bars, bar_interval_seconds, train_days, test_days, step_days
        )
    except ValueError:
        return _reject_objective("insufficient data for walk-forward folds")
    closes = candles["close"].astype(np.float64)
    min_order_quote = effective_min_order_quote(pair_rules, reference_price)

    def objective(trial: optuna.Trial) -> float:
        raw_params = _suggest(
            trial, fixed_quote=fixed_quote, bar_interval_seconds=bar_interval_seconds
        )
        bundle, reject_reason = _canonicalize(
            raw_params, pair_rules, reference_price,
            bar_interval_seconds=bar_interval_seconds,
        )
        trial.set_user_attr("strategy_name", "range_ladder")
        trial.set_user_attr("search_mode", "generative")
        trial.set_user_attr("dataset_hash", dataset_hash)
        if bundle is None:
            trial.set_user_attr("reject_reason", reject_reason)
            raise optuna.TrialPruned(f"canonicalizer rejected: {reject_reason}")
        trial.set_user_attr("reject_reason", None)
        config = bundle.strategy_config

        def rung_provider(fold_def):
            anchor = compute_anchor(closes[:fold_def.train_end_idx])
            try:
                rungs = build_rungs(anchor, config, pair_rules.price_tick)
            except ValueError as e:
                return None, anchor, f"rung build failed: {e}"
            ok, reason = validate_rungs(
                rungs,
                anchor=anchor,
                fee=config.fee,
                price_tick=pair_rules.price_tick,
                min_order_quote=min_order_quote,
                fund=config.fund_quote,
                quote_frac=config.quote_frac,
                buy_near_pct=config.buy_near_pct,
                buy_far_pct=config.buy_far_pct,
                sell_near_pct=config.sell_near_pct,
                sell_far_pct=config.sell_far_pct,
            )
            if not ok:
                return None, anchor, f"rung validation failed: {reason}"
            return rungs, anchor, None

        trial.set_user_attr(
            "fold_plan_days", {"train": plan[0], "test": plan[1], "step": plan[2]}
        )
        result = evaluate_ladder_walkforward(
            candles, fold_defs, bar_interval_seconds,
            rung_provider=rung_provider,
            fund=config.fund_quote, quote_frac=config.quote_frac,
            fee=config.fee, slip=config.slip,
            cooldown_bars=config.cooldown_bars,
            max_fills_per_bar=config.max_fills_per_bar,
            body_only=config.body_only,
            stress_config=config, run_stress=run_stress,
            gate_policy=_policy, objective_mode=objective_mode,
            lambda_mad=_lambda, trial=trial,
        )
        _set_summary_attrs(trial, result, _policy, objective_mode)
        return float(result["objective"])

    return objective


# ----------------------------------------------------------------------
# refine_incumbent objective (Phase A.1 §3)
# ----------------------------------------------------------------------

def create_range_ladder_refine_objective(
    candles,
    pair_rules: PairRules,
    bar_interval_seconds: int,
    dataset_hash: str,
    deploy_anchor: float,
    base_rungs: dict,
    stage: str = "overlay",
    train_days: Optional[float] = None,
    test_days: Optional[float] = None,
    step_days: Optional[float] = None,
    fund: float = 1000.0,
    quote_frac: float = 0.5,
    cooldown_bars: int = 1,
    stress_spread_pct: float = 0.0,
    run_stress: bool = True,
    lambda_mad: float = DEFAULT_LAMBDA_MAD,
    gate_policy: Optional[GatePolicy] = None,
    objective_mode: str = "median_ann",
):
    """Create the refine_incumbent objective (stage 1 overlay / stage 2 nudge).

    base_rungs: {'buy_prices','buy_weights','sell_prices','sell_weights'}
    plain lists (picklable) — the incumbent for stage 1, the stage-1 winner
    for stage 2. Rungs are ABSOLUTE (already deploy-priced): the same ladder
    is scored on every fold, constraints validated once at `deploy_anchor`.
    The identity overlay/nudge reproduces base_rungs bit-for-bit, so enqueue
    it as trial 0 and the study can never lose to its baseline.
    """
    from pmm_lab.optuna.canonicalizer_range_ladder import effective_min_order_quote
    from pmm_lab.optuna.search_space_range_ladder import (
        suggest_range_ladder_nudge_params, suggest_range_ladder_overlay_params,
    )
    from pmm_lab.strategies.range_ladder import RangeLadderConfig
    from pmm_lab.strategies.range_ladder_gen import (
        RungSet, apply_ladder_overlay, apply_per_rung_nudge, validate_rungs,
    )

    if stage not in ("overlay", "nudge"):
        raise ValueError(f"stage must be 'overlay' or 'nudge'; got {stage!r}")

    _policy = gate_policy or GatePolicy()
    _lambda = lambda_mad if lambda_mad is not None else DEFAULT_LAMBDA_MAD
    fee = float(pair_rules.fees.maker_fee)

    base = RungSet(
        buys=np.sort(np.asarray(base_rungs["buy_prices"], dtype=np.float64))[::-1],
        sells=np.sort(np.asarray(base_rungs["sell_prices"], dtype=np.float64)),
        buy_weights=np.asarray(base_rungs["buy_weights"], dtype=np.float64),
        sell_weights=np.asarray(base_rungs["sell_weights"], dtype=np.float64),
    )
    n_buy, n_sell = len(base.buys), len(base.sells)

    try:
        fold_defs, plan = _build_fold_defs(
            len(candles), bar_interval_seconds, train_days, test_days, step_days
        )
    except ValueError:
        return _reject_objective("insufficient data for walk-forward folds")
    min_order_quote = effective_min_order_quote(pair_rules, deploy_anchor)

    # Stress dials come from a literal config carrying the fund/fee context.
    stress_config = RangeLadderConfig(
        fund_quote=fund, quote_frac=quote_frac, fee=fee,
        cooldown_bars=cooldown_bars, stress_spread_pct=stress_spread_pct,
        literal_buy_prices=tuple(float(x) for x in base.buys),
        literal_buy_weights=tuple(float(x) for x in base.buy_weights),
        literal_sell_prices=tuple(float(x) for x in base.sells),
        literal_sell_weights=tuple(float(x) for x in base.sell_weights),
    )

    def objective(trial: optuna.Trial) -> float:
        trial.set_user_attr("strategy_name", "range_ladder")
        trial.set_user_attr("search_mode", f"refine_incumbent:{stage}")
        trial.set_user_attr("dataset_hash", dataset_hash)

        if stage == "overlay":
            params = suggest_range_ladder_overlay_params(trial)
            rungs = apply_ladder_overlay(
                base, price_tick=pair_rules.price_tick, **params
            )
        else:
            params = suggest_range_ladder_nudge_params(trial, n_buy, n_sell)
            rungs = apply_per_rung_nudge(
                base,
                params["buy_price_mults"], params["sell_price_mults"],
                params["buy_weight_mults"], params["sell_weight_mults"],
                price_tick=pair_rules.price_tick,
            )

        ok, reason = validate_rungs(
            rungs,
            anchor=deploy_anchor,
            fee=fee,
            price_tick=pair_rules.price_tick,
            min_order_quote=min_order_quote,
            fund=fund,
            quote_frac=quote_frac,
        )
        if not ok:
            trial.set_user_attr("reject_reason", reason)
            raise optuna.TrialPruned(f"overlay violates constraints: {reason}")
        trial.set_user_attr("reject_reason", None)
        trial.set_user_attr("refined_rungs", {
            "buys": [float(x) for x in rungs.buys],
            "sells": [float(x) for x in rungs.sells],
            "buy_weights": [float(x) for x in rungs.buy_weights],
            "sell_weights": [float(x) for x in rungs.sell_weights],
        })
        trial.set_user_attr(
            "fold_plan_days", {"train": plan[0], "test": plan[1], "step": plan[2]}
        )

        result = evaluate_ladder_walkforward(
            candles, fold_defs, bar_interval_seconds,
            rung_provider=lambda fold_def: (rungs, deploy_anchor, None),
            fund=fund, quote_frac=quote_frac, fee=fee,
            cooldown_bars=cooldown_bars,
            stress_config=stress_config, run_stress=run_stress,
            gate_policy=_policy, objective_mode=objective_mode,
            lambda_mad=_lambda, trial=trial,
        )
        _set_summary_attrs(trial, result, _policy, objective_mode)
        return float(result["objective"])

    return objective
