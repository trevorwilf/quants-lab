"""
Trial replay harness.

Stores trial records (params + canonical config + scores) and replays them
to verify exact reproducibility. This catches environment drift, code changes
that alter simulation behavior, and floating-point nondeterminism.

Usage:
    # During optimization — save trial records
    records = extract_trial_records(study)
    save_trial_records(records, "artifacts/trials.jsonl")

    # Later — replay and verify
    diffs = replay_and_verify(
        "artifacts/trials.jsonl",
        candles, pair_rules, bar_interval_seconds, reference_price
    )
    assert len(diffs) == 0, f"Replay mismatches: {diffs}"
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TrialRecord:
    """Serializable record of one Optuna trial for replay."""
    trial_number: int
    params: Dict[str, Any]              # raw suggested params
    objective_value: float               # final objective score
    reject_reason: Optional[str] = None  # None if not rejected
    dataset_hash: Optional[str] = None
    fold_scores: Optional[List[float]] = None   # per-fold objective scores
    user_attrs: Optional[Dict[str, Any]] = None  # all user attrs from the trial


def extract_trial_records(
    study,
    max_trials: Optional[int] = None,
) -> List[TrialRecord]:
    """Extract TrialRecords from a completed Optuna study.

    Parameters
    ----------
    study : optuna.Study
        A completed study.
    max_trials : int, optional
        Limit the number of records extracted. If None, extracts all completed trials.

    Returns
    -------
    List[TrialRecord]
    """
    import optuna

    records = []
    trials = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]

    if max_trials is not None:
        trials = trials[:max_trials]

    for t in trials:
        records.append(TrialRecord(
            trial_number=t.number,
            params=dict(t.params),
            objective_value=t.value,
            reject_reason=t.user_attrs.get("reject_reason"),
            dataset_hash=t.user_attrs.get("dataset_hash"),
            user_attrs={k: v for k, v in t.user_attrs.items()},
        ))

    return records


def save_trial_records(records: List[TrialRecord], path: str) -> str:
    """Save trial records to a JSONL file (one JSON object per line).

    Parameters
    ----------
    records : List[TrialRecord]
        Trial records to save.
    path : str
        Output file path.

    Returns
    -------
    str
        Path written.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out, "w") as f:
        for record in records:
            d = asdict(record)
            # Convert any non-serializable types
            f.write(json.dumps(d, default=_json_default) + "\n")

    logger.info("Saved %d trial records to %s", len(records), path)
    return str(out)


def load_trial_records(path: str) -> List[TrialRecord]:
    """Load trial records from a JSONL file.

    Parameters
    ----------
    path : str
        Input file path.

    Returns
    -------
    List[TrialRecord]
    """
    records = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            records.append(TrialRecord(**d))
    return records


def replay_and_verify(
    records_path: str,
    candles: np.ndarray,
    pair_rules,
    bar_interval_seconds: int,
    reference_price: float,
    tolerance: float = 1e-6,
    max_replays: Optional[int] = None,
    # Walk-forward replay params (optional — when provided, replays via walk-forward)
    train_days: Optional[float] = None,
    test_days: Optional[float] = None,
    step_days: Optional[float] = None,
    embargo_bars: Optional[int] = None,
    lambda_mad: float = 0.5,
) -> List[Dict[str, Any]]:
    """Replay stored trial records and verify objective values match.

    For each record:
    1. Canonicalize the stored params
    2. If rejected, verify the trial was also rejected (objective == REJECT_SCORE)
    3. If not rejected, run the simulation and verify objective matches within tolerance

    Parameters
    ----------
    records_path : str
        Path to JSONL file with trial records.
    candles : np.ndarray
        Same candle data used in the original study.
    pair_rules : PairRules
        Same pair rules.
    bar_interval_seconds : int
        Same bar interval.
    reference_price : float
        Same reference price used for canonicalization.
    tolerance : float
        Maximum absolute difference for objective value match.
    max_replays : int, optional
        Limit the number of trials replayed.

    Returns
    -------
    List[Dict]
        List of mismatches. Empty list means perfect replay.
        Each mismatch dict has: trial_number, expected, actual, diff, reason.
    """
    from pmm_lab.optuna.canonicalizer import canonicalize_params
    from pmm_lab.sim.runner import CandleSimRunner
    from pmm_lab.metrics.metrics import compute_metrics
    from pmm_lab.objective.objective import objective_v1, REJECT_SCORE
    from pmm_lab.data.hashing import hash_candles

    records = load_trial_records(records_path)
    if max_replays is not None:
        records = records[:max_replays]

    # Verify dataset hash if available
    current_hash = hash_candles(candles)
    for r in records:
        if r.dataset_hash and r.dataset_hash != current_hash:
            logger.warning(
                "Dataset hash mismatch for trial %d: stored=%s, current=%s",
                r.trial_number, r.dataset_hash, current_hash,
            )

    mismatches = []
    n_replayed = 0
    n_matched = 0

    for record in records:
        # Canonicalize
        config, reject_reason = canonicalize_params(record.params, pair_rules, reference_price)

        if config is None:
            # Should be rejected
            expected = REJECT_SCORE
            if abs(record.objective_value - expected) > tolerance:
                mismatches.append({
                    "trial_number": record.trial_number,
                    "expected": record.objective_value,
                    "actual": expected,
                    "diff": abs(record.objective_value - expected),
                    "reason": f"Rejection mismatch: stored={record.objective_value}, replay=REJECT ({reject_reason})",
                })
            else:
                n_matched += 1
            n_replayed += 1
            continue

        # Run simulation — walk-forward or single-run
        if train_days is not None:
            replay_score = _replay_walk_forward(
                config, candles, pair_rules, bar_interval_seconds,
                train_days, test_days, step_days, embargo_bars, lambda_mad,
            )
        else:
            runner = CandleSimRunner(config, pair_rules)
            result = runner.run(candles)
            metrics = compute_metrics(
                result, config.total_amount_quote, candles, bar_interval_seconds
            )
            obj = objective_v1(metrics)
            replay_score = obj.raw_score

        diff = abs(record.objective_value - replay_score)
        if diff > tolerance:
            mismatches.append({
                "trial_number": record.trial_number,
                "expected": record.objective_value,
                "actual": replay_score,
                "diff": diff,
                "reason": f"Objective mismatch: stored={record.objective_value:.6f}, replay={replay_score:.6f}",
            })
        else:
            n_matched += 1

        n_replayed += 1

    logger.info(
        "Replay complete: %d/%d matched within tolerance %.2e (%d mismatches)",
        n_matched, n_replayed, tolerance, len(mismatches),
    )

    return mismatches


def _replay_walk_forward(
    config, candles, pair_rules, bar_interval_seconds,
    train_days, test_days, step_days, embargo_bars, lambda_mad,
) -> float:
    """Replay a trial using walk-forward to match objective_wrapper behavior."""
    from pmm_lab.objective.walkforward import TimeSeriesCV
    from pmm_lab.sim.runner import CandleSimRunner
    from pmm_lab.metrics.metrics import compute_metrics
    from pmm_lab.sim.executor_model import SimResult
    from pmm_lab.objective.objective import objective_v1
    from pmm_lab.objective.robustness import robust_aggregate

    cv = TimeSeriesCV(
        n_bars=len(candles),
        bar_interval_seconds=bar_interval_seconds,
        train_days=train_days,
        test_days=test_days or train_days,
        step_days=step_days or train_days,
        embargo_bars=embargo_bars,
        macd_slow=config.macd_slow,
        natr_length=config.natr_length,
    )

    fold_defs = cv.get_folds()
    fold_scores = []

    for fold_def in fold_defs:
        candle_slice = candles[:fold_def.test_end_idx]
        runner = CandleSimRunner(config, pair_rules)
        sim_result = runner.run(candle_slice, sim_start_idx=fold_def.test_start_idx)

        test_eq = sim_result.equity_curve[fold_def.test_start_idx:fold_def.test_end_idx]
        test_pos = sim_result.position_history[fold_def.test_start_idx:fold_def.test_end_idx]
        test_candles = candles[fold_def.test_start_idx:fold_def.test_end_idx]
        test_trades = [t for t in sim_result.trades if t.entry_bar >= fold_def.test_start_idx]

        test_sim_result = SimResult(
            trades=test_trades,
            equity_curve=test_eq,
            position_history=test_pos,
            n_orders_placed=sim_result.n_orders_placed,
            n_orders_filled=sim_result.n_orders_filled,
            n_orders_rejected=sim_result.n_orders_rejected,
            n_market_exits=sim_result.n_market_exits,
            final_base_balance=sim_result.final_base_balance,
            final_quote_balance=sim_result.final_quote_balance,
        )

        test_metrics = compute_metrics(
            test_sim_result, config.total_amount_quote, test_candles, bar_interval_seconds
        )
        test_obj = objective_v1(test_metrics)
        fold_scores.append(test_obj.raw_score)

    return robust_aggregate(fold_scores, lambda_mad=lambda_mad)


def _json_default(obj):
    """JSON serializer for non-standard types."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)
