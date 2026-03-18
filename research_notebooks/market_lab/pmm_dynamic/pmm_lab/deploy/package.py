"""
Deployment package generator.

Bundles an optimized config with its expected metrics, dataset info,
environment snapshot, and stop-ship check results into a single
deployable artifact.

Usage:
    package = create_deployment_package(
        config, metrics, objective, holdout_report,
        sensitivity_report, study_name, ...
    )
    save_deployment_package(package, "artifacts/deploy/XMR-USDT")
"""

import json
import logging
import yaml
import shutil
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional, List

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.metrics.metrics import Metrics
from pmm_lab.objective.objective import ObjectiveDecomposition
from pmm_lab.export.hb_yaml import export_yaml, ExportParams, sim_config_to_hb_dict

logger = logging.getLogger(__name__)


@dataclass
class ExpectedPerformance:
    """Backtest-predicted performance metrics for drift detection."""
    pnl_pct: float
    max_drawdown_pct: float
    trade_count: int
    sharpe: float
    profit_factor: float
    fee_drag_pct: float
    median_trade_pnl_quote: float
    # Walk-forward aggregates
    wf_median_pnl_pct: Optional[float] = None
    wf_median_sharpe: Optional[float] = None
    wf_fold_count: Optional[int] = None
    # Holdout results
    holdout_pnl_pct: Optional[float] = None
    holdout_score: Optional[float] = None
    # Stress
    stress_worst_score: Optional[float] = None
    # Sensitivity
    sensitivity_penalty: Optional[float] = None
    # Monitoring-compatible fields (Phase 2)
    evaluation_hours: Optional[float] = None
    total_volume_quote: Optional[float] = None
    fee_rate_pct_of_volume: Optional[float] = None
    buy_fraction: Optional[float] = None
    sell_fraction: Optional[float] = None
    inventory_exposure_mean: Optional[float] = None
    inventory_exposure_p95: Optional[float] = None


@dataclass
class DeploymentPackage:
    """Complete deployment artifact for one optimized config."""
    # Identity
    study_name: str
    connector: str
    trading_pair: str
    interval: str
    created_at: str

    # Config
    config_dict: Dict[str, Any]        # Hummingbot-ready YAML dict
    sim_config_params: Dict[str, Any]  # raw SimConfig fields for replay

    # Expected performance
    expected: ExpectedPerformance

    # Audit trail
    dataset_hash: str
    dataset_bars: int
    objective_score: float
    objective_version: int
    environment_hash: Optional[str] = None
    stop_ship_checks: Optional[Dict[str, bool]] = None

    # Certified run
    certified: bool = False
    n_jobs: int = 1

    # Lineage (added per expert review v4)
    dev_dataset_hash: Optional[str] = None
    holdout_fraction: Optional[float] = None
    holdout_bars: Optional[int] = None
    start_ts: Optional[int] = None
    end_ts: Optional[int] = None

    # Deployment state
    deployed: bool = False
    deployed_at: Optional[str] = None
    deployment_notes: str = ""


def create_deployment_package(
    config: SimConfig,
    metrics: Metrics,
    objective: ObjectiveDecomposition,
    study_name: str,
    dataset_hash: str,
    dataset_bars: int,
    export_params: ExportParams = ExportParams(),
    objective_version: int = 1,
    wf_median_pnl: Optional[float] = None,
    wf_median_sharpe: Optional[float] = None,
    wf_fold_count: Optional[int] = None,
    holdout_pnl_pct: Optional[float] = None,
    holdout_score: Optional[float] = None,
    stress_worst_score: Optional[float] = None,
    sensitivity_penalty: Optional[float] = None,
    stop_ship_checks: Optional[Dict[str, bool]] = None,
    environment_hash: Optional[str] = None,
    certified: bool = False,
    n_jobs: int = 1,
    dev_dataset_hash: Optional[str] = None,
    holdout_fraction: Optional[float] = None,
    holdout_bars: Optional[int] = None,
    start_ts: Optional[int] = None,
    end_ts: Optional[int] = None,
    evaluation_hours: Optional[float] = None,
    total_volume_quote: Optional[float] = None,
    fee_rate_pct_of_volume: Optional[float] = None,
    buy_fraction: Optional[float] = None,
    sell_fraction: Optional[float] = None,
    inventory_exposure_mean: Optional[float] = None,
    inventory_exposure_p95: Optional[float] = None,
) -> DeploymentPackage:
    """Create a deployment package from optimization results.

    Parameters
    ----------
    config : SimConfig
        The optimized configuration.
    metrics : Metrics
        Full-dataset metrics for the config.
    objective : ObjectiveDecomposition
        Objective score breakdown.
    study_name : str
        Study identifier.
    dataset_hash : str
        Hash of the candle data used.
    dataset_bars : int
        Number of candle bars in the dataset.
    export_params : ExportParams
        Hummingbot export parameters.
    Plus optional walk-forward, holdout, stress, sensitivity results.

    Returns
    -------
    DeploymentPackage
    """
    config_dict = sim_config_to_hb_dict(config, export_params)

    # Build SimConfig params dict for replay
    import dataclasses
    sim_params = {}
    for f in dataclasses.fields(config):
        val = getattr(config, f.name)
        if isinstance(val, list):
            sim_params[f.name] = list(val)
        else:
            sim_params[f.name] = val

    expected = ExpectedPerformance(
        pnl_pct=metrics.pnl_pct,
        max_drawdown_pct=metrics.max_drawdown_pct,
        trade_count=metrics.trade_count,
        sharpe=metrics.sharpe,
        profit_factor=metrics.profit_factor,
        fee_drag_pct=metrics.fee_drag_pct,
        median_trade_pnl_quote=metrics.median_trade_pnl_quote,
        wf_median_pnl_pct=wf_median_pnl,
        wf_median_sharpe=wf_median_sharpe,
        wf_fold_count=wf_fold_count,
        holdout_pnl_pct=holdout_pnl_pct,
        holdout_score=holdout_score,
        stress_worst_score=stress_worst_score,
        sensitivity_penalty=sensitivity_penalty,
        evaluation_hours=evaluation_hours,
        total_volume_quote=total_volume_quote,
        fee_rate_pct_of_volume=fee_rate_pct_of_volume,
        buy_fraction=buy_fraction,
        sell_fraction=sell_fraction,
        inventory_exposure_mean=inventory_exposure_mean,
        inventory_exposure_p95=inventory_exposure_p95,
    )

    return DeploymentPackage(
        study_name=study_name,
        connector=export_params.connector_name,
        trading_pair=export_params.trading_pair,
        interval=export_params.interval,
        created_at=datetime.now(timezone.utc).isoformat(),
        config_dict=config_dict,
        sim_config_params=sim_params,
        expected=expected,
        dataset_hash=dataset_hash,
        dataset_bars=dataset_bars,
        objective_score=objective.raw_score,
        objective_version=objective_version,
        environment_hash=environment_hash,
        stop_ship_checks=stop_ship_checks,
        certified=certified,
        n_jobs=n_jobs,
        dev_dataset_hash=dev_dataset_hash,
        holdout_fraction=holdout_fraction,
        holdout_bars=holdout_bars,
        start_ts=start_ts,
        end_ts=end_ts,
    )


def save_deployment_package(
    package: DeploymentPackage,
    output_dir: str,
) -> str:
    """Save a deployment package to disk.

    Creates:
    - config.yml — Hummingbot controller config (ready to copy to trading pod)
    - package.json — full deployment metadata
    - expected_metrics.json — expected performance for drift detection

    Parameters
    ----------
    package : DeploymentPackage
        The package to save.
    output_dir : str
        Output directory.

    Returns
    -------
    str
        Path to the output directory.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 1. Hummingbot config YAML
    config_path = out / "config.yml"
    with open(config_path, "w") as f:
        yaml.dump(package.config_dict, f, default_flow_style=False, sort_keys=True)

    # 2. Expected metrics JSON (for live tracker)
    expected_path = out / "expected_metrics.json"
    with open(expected_path, "w") as f:
        json.dump(asdict(package.expected), f, indent=2, default=_json_default)

    # 3. Full package JSON
    package_path = out / "package.json"
    with open(package_path, "w") as f:
        json.dump(asdict(package), f, indent=2, default=_json_default)

    logger.info("Deployment package saved to %s", out)
    return str(out)


def load_deployment_package(package_dir: str) -> DeploymentPackage:
    """Load a deployment package from disk.

    Parameters
    ----------
    package_dir : str
        Path to the package directory.

    Returns
    -------
    DeploymentPackage
    """
    p = Path(package_dir)

    with open(p / "package.json", "r") as f:
        data = json.load(f)

    expected = ExpectedPerformance(**data["expected"])
    data["expected"] = expected

    return DeploymentPackage(**data)


def _json_default(obj):
    """JSON serializer for non-standard types."""
    import numpy as np
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)
