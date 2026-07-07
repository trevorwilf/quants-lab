"""Walk-forward Optuna objective for range_ladder (Phase A).

Per-trial flow (Phase A spec §3):

1. Suggest generative params → canonicalize. Invalid → ``optuna.TrialPruned``
   (hard constraints prune; they are not scored REJECT).
2. Per fold, the ANCHOR is the median of the last 3 TRAIN closes — rungs are
   rebuilt per fold from the SAME %-offset params. This is what makes the
   exported config deployable: we tune offsets, not prices.
3. Each fold runs the base kernel AND the conservative (stress) kernel on the
   test slice. Fold raw score = test annualized pnl_pct (base fills).
4. Fold hard gates → violation count: endinv_pct > 75, or the fold is not
   two-sided (both sides >= 1 fill). A trial failing gates in a MAJORITY of
   folds is pruned. Per-fold scores are reported as intermediate values so a
   pruner (HyperbandPruner recommended; startup trials exempt via
   n_startup_trials) can act.
5. Aggregate: winsorize fold scores to median ± 2*MAD, then
   objective = median(winsorized) − 0.5 * MAD(winsorized).

Fold layout (§3.6): target 3 folds; test window = min(60d, floor(total/5)),
additionally capped so the fixed train window keeps >= 90d; the notebook
preflight aborts below 150 usable days rather than silently shrinking folds.
"""

from __future__ import annotations

import logging
import math
from typing import Optional, Tuple

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
):
    """Create the Optuna objective for range_ladder.

    Notes
    -----
    - `objective_version` is accepted for dispatch-signature uniformity but
      unused: Phase A fold scores are annualized test PnL% from the ladder
      kernel, not objective_v1/v2 over engine metrics.
    - Pass train_days/test_days/step_days=None to auto-plan folds per §3.6
      (the notebook does this); explicit values are honored for tests.
    """
    from pmm_lab.features._numba_range_ladder import run_ladder_sim
    from pmm_lab.objective.stress_range_ladder import run_range_ladder_stress
    from pmm_lab.objective.walkforward import TimeSeriesCV
    from pmm_lab.optuna.canonicalizer_range_ladder import canonicalize_range_ladder_params
    from pmm_lab.optuna.search_space_range_ladder import suggest_range_ladder_params
    from pmm_lab.strategies.range_ladder import ANCHOR_LOOKBACK_BARS, compute_anchor
    from pmm_lab.strategies.range_ladder_gen import build_rungs, validate_rungs
    from pmm_lab.optuna.canonicalizer_range_ladder import effective_min_order_quote

    _suggest = strategy_search_space or suggest_range_ladder_params
    _canonicalize = strategy_canonicalizer or canonicalize_range_ladder_params

    n_bars = len(candles)
    if train_days is None or test_days is None or step_days is None:
        _train_days, _test_days, _step_days = plan_range_ladder_folds(
            n_bars, bar_interval_seconds
        )
    else:
        _train_days, _test_days, _step_days = train_days, test_days, step_days

    _lambda = lambda_mad if lambda_mad is not None else DEFAULT_LAMBDA_MAD

    def objective(trial: optuna.Trial) -> float:
        # 1. Suggest + canonicalize (invalid → pruned)
        raw_params = _suggest(
            trial, fixed_quote=fixed_quote, bar_interval_seconds=bar_interval_seconds
        )
        bundle, reject_reason = _canonicalize(
            raw_params, pair_rules, reference_price,
            bar_interval_seconds=bar_interval_seconds,
        )
        trial.set_user_attr("strategy_name", "range_ladder")
        trial.set_user_attr("dataset_hash", dataset_hash)
        if bundle is None:
            trial.set_user_attr("reject_reason", reject_reason)
            raise optuna.TrialPruned(f"canonicalizer rejected: {reject_reason}")
        trial.set_user_attr("reject_reason", None)

        config = bundle.strategy_config

        # 2. Fold layout — no indicator warmup, so embargo is 0 and the
        # anchor's 3-bar lookback lives inside the train window.
        cv = TimeSeriesCV(
            n_bars=n_bars,
            bar_interval_seconds=bar_interval_seconds,
            train_days=_train_days,
            test_days=_test_days,
            step_days=_step_days,
            embargo_bars=embargo_bars if embargo_bars is not None else 0,
            macd_slow=ANCHOR_LOOKBACK_BARS,   # warmup hint slots (unused: embargo=0)
            natr_length=ANCHOR_LOOKBACK_BARS,
        )
        try:
            fold_defs = cv.get_folds()
        except ValueError:
            trial.set_user_attr("reject_reason", "insufficient data for walk-forward folds")
            trial.set_user_attr("objective_score", REJECT_SCORE)
            return REJECT_SCORE

        min_order_quote = effective_min_order_quote(pair_rules, reference_price)
        closes = candles["close"].astype(np.float64)

        fold_scores = []
        fold_detail = []
        violations = 0
        last_rungs = None
        cons_scores = []

        for fold_def in fold_defs:
            test_slice = candles[fold_def.test_start_idx:fold_def.test_end_idx]
            test_days_actual = (
                len(test_slice) * bar_interval_seconds / 86400.0
            )

            # §3.2 — anchor from TRAIN closes only (leakage-tested)
            anchor = compute_anchor(closes[:fold_def.train_end_idx])

            try:
                rungs = build_rungs(anchor, config, pair_rules.price_tick)
            except ValueError as e:
                violations += 1
                fold_detail.append({
                    "fold": fold_def.fold_index, "anchor": anchor,
                    "violation": f"rung build failed: {e}",
                })
                continue
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
                violations += 1
                fold_detail.append({
                    "fold": fold_def.fold_index, "anchor": anchor,
                    "violation": f"rung validation failed: {reason}",
                })
                continue
            last_rungs = rungs

            base = run_ladder_sim(
                test_slice["open"], test_slice["high"],
                test_slice["low"], test_slice["close"],
                rungs.buys, rungs.sells, rungs.buy_weights, rungs.sell_weights,
                fund=config.fund_quote,
                quote_frac=config.quote_frac,
                fee=config.fee,
                slip=config.slip,
                cooldown_bars=config.cooldown_bars,
                max_fills_per_bar=config.max_fills_per_bar,
                body_only=config.body_only,
                bar_interval_seconds=bar_interval_seconds,
            )

            cons = None
            if run_stress:
                cons = run_range_ladder_stress(
                    test_slice, config, rungs, bar_interval_seconds,
                )
                cons_scores.append(cons["pnl_pct"] * 365.0 / test_days_actual)

            fold_score = base["pnl_pct"] * 365.0 / test_days_actual
            buy_fills = int(sum(base["buy_fills"]))
            sell_fills = int(sum(base["sell_fills"]))
            two_sided = buy_fills >= 1 and sell_fills >= 1
            gated = base["endinv_pct"] > ENDINV_GATE_PCT or not two_sided
            if gated:
                violations += 1

            fold_scores.append(fold_score)
            fold_detail.append({
                "fold": fold_def.fold_index,
                "anchor": anchor,
                "score_ann_pct": fold_score,
                "pnl_pct": base["pnl_pct"],
                "hold_pct": base["hold_pct"],
                "maxdd": base["maxdd"],
                "endinv_pct": base["endinv_pct"],
                "buy_fills": buy_fills,
                "sell_fills": sell_fills,
                "two_sided": two_sided,
                "gated": gated,
                "cons_ann_pct": (
                    cons["pnl_pct"] * 365.0 / test_days_actual if cons else None
                ),
                "cons_endinv_pct": cons["endinv_pct"] if cons else None,
            })

            # §3.4 — intermediate values for the pruner
            trial.report(float(fold_score), step=fold_def.fold_index)
            if trial.should_prune():
                trial.set_user_attr("fold_detail", fold_detail)
                raise optuna.TrialPruned()

        n_folds = len(fold_defs)
        trial.set_user_attr("n_folds", n_folds)
        trial.set_user_attr("gate_violations", violations)
        trial.set_user_attr("fold_detail", fold_detail)
        trial.set_user_attr(
            "fold_plan_days",
            {"train": _train_days, "test": _test_days, "step": _step_days},
        )
        if last_rungs is not None:
            trial.set_user_attr("last_fold_rungs", {
                "buys": [float(x) for x in last_rungs.buys],
                "sells": [float(x) for x in last_rungs.sells],
                "buy_weights": [float(x) for x in last_rungs.buy_weights],
                "sell_weights": [float(x) for x in last_rungs.sell_weights],
            })

        # §3.4 — majority gate failure prunes the trial
        if violations > n_folds / 2.0:
            trial.set_user_attr(
                "reject_reason",
                f"gate violations in majority of folds ({violations}/{n_folds})",
            )
            raise optuna.TrialPruned(
                f"gate violations in majority of folds ({violations}/{n_folds})"
            )

        # §3.5 — winsorized robust aggregate
        final_score, winsorized = winsorized_fold_objective(
            fold_scores, clamp_mad=WINSOR_CLAMP_MAD, lambda_mad=_lambda,
        )
        trial.set_user_attr("fold_scores", [float(s) for s in fold_scores])
        trial.set_user_attr("fold_scores_winsorized", winsorized)
        trial.set_user_attr("objective_score", float(final_score))
        if cons_scores:
            trial.set_user_attr("cons_score_median", float(np.median(cons_scores)))
        endinvs = [d["endinv_pct"] for d in fold_detail if "endinv_pct" in d]
        if endinvs:
            trial.set_user_attr("endinv_pct_median", float(np.median(endinvs)))
        pnls = [d["pnl_pct"] for d in fold_detail if "pnl_pct" in d]
        if pnls:
            trial.set_user_attr("pnl_pct_median", float(np.median(pnls)))

        return float(final_score)

    return objective
