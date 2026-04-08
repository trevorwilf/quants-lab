"""
Hummingbot-compatible YAML config exporter for PMM Dynamic.

Converts a SimConfig (from optimization) into a YAML file that Hummingbot
can load directly as a controller config.
"""

import hashlib
import yaml
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from pmm_lab.sim.executor_model import SimConfig


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _sanitize_for_yaml(obj):
    """Convert NumPy and other non-standard types to Python primitives for safe YAML serialization."""
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_yaml(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize_for_yaml(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


# Hummingbot OrderType enum values (from hummingbot.core.data_type.common)
# MARKET = 1, LIMIT = 2, LIMIT_MAKER = 3
ORDER_TYPE_MAP = {
    "MARKET": 1,
    "LIMIT": 2,
    "LIMIT_MAKER": 3,
}


@dataclass(frozen=True)
class ExportParams:
    """Parameters that the optimizer doesn't set but the YAML needs."""
    connector_name: str = "nonkyc"
    trading_pair: str = "BTC-USDT"
    candles_connector: str = "nonkyc"
    candles_trading_pair: str = "BTC-USDT"
    interval: str = "5m"
    leverage: int = 1
    position_mode: str = "HEDGE"
    position_rebalance_threshold_pct: float = 0.05
    skip_rebalance: bool = False
    manual_kill_switch: bool = False
    config_id: Optional[str] = None


def sim_config_to_hb_dict(
    config: SimConfig,
    export_params: ExportParams = ExportParams(),
) -> Dict[str, Any]:
    """Convert a SimConfig into a Hummingbot-compatible config dict.

    Key transformations:
    1. buy/sell amounts re-normalized so combined sum = 1.0
    2. take_profit_order_type converted to numeric
    3. trailing_stop as nested dict
    4. auto-generated id
    5. keys sorted alphabetically
    """
    # Re-normalize amounts: buy_raw + sell_raw sums to 1.0
    buy_raw = [w * config.buy_side_weight for w in config.buy_amounts_pct]
    sell_raw = [w * (1.0 - config.buy_side_weight) for w in config.sell_amounts_pct]
    total = sum(buy_raw) + sum(sell_raw)
    if total > 0:
        buy_final = [v / total for v in buy_raw]
        sell_final = [v / total for v in sell_raw]
    else:
        buy_final = buy_raw
        sell_final = sell_raw

    # Auto-generate id
    config_id = export_params.config_id
    if config_id is None:
        config_id = f"{export_params.trading_pair}-PMM-DYNAMIC_{config.total_amount_quote}"

    # Export order type as integer (Hummingbot OrderType enum)
    tp_order_type = ORDER_TYPE_MAP.get(config.take_profit_order_type, 2)  # default LIMIT=2

    d = {
        "buy_amounts_pct": buy_final,
        "buy_spreads": list(config.buy_spreads),
        "candles_connector": export_params.candles_connector,
        "candles_trading_pair": export_params.candles_trading_pair,
        "connector_name": export_params.connector_name,
        "controller_name": "pmm_dynamic",
        "controller_type": "market_making",
        "cooldown_time": int(config.cooldown_time),
        "executor_refresh_time": int(config.executor_refresh_time),
        "id": config_id,
        "interval": export_params.interval,
        "leverage": export_params.leverage,
        "macd_fast": config.macd_fast,
        "macd_signal": config.macd_signal,
        "macd_slow": config.macd_slow,
        "manual_kill_switch": export_params.manual_kill_switch,
        "natr_length": config.natr_length,
        "position_mode": export_params.position_mode,
        "position_rebalance_threshold_pct": config.position_rebalance_threshold_pct if hasattr(config, 'position_rebalance_threshold_pct') else export_params.position_rebalance_threshold_pct,
        "sell_amounts_pct": sell_final,
        "sell_spreads": list(config.sell_spreads),
        "skip_rebalance": config.skip_rebalance if hasattr(config, 'skip_rebalance') else export_params.skip_rebalance,
        "stop_loss": config.stop_loss,
        "take_profit": config.take_profit,
        "take_profit_order_type": tp_order_type,
        "time_limit": int(config.time_limit),
        "total_amount_quote": config.total_amount_quote,
        "trading_pair": export_params.trading_pair,
        "trailing_stop": {
            "activation_price": config.trailing_stop_activation,
            "trailing_delta": config.trailing_stop_delta,
        },
    }

    # Sort alphabetically
    return dict(sorted(d.items()))


def export_yaml(
    config: SimConfig,
    output_path: str,
    export_params: ExportParams = ExportParams(),
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Export a SimConfig as a Hummingbot YAML file.

    NOTE: use_wallet_balance is a runtime-only Hummingbot field and is NOT exported.
    If you plan to enable use_wallet_balance on the live bot, also set
    initial_base_balance in your SimConfig to model the pre-existing base
    inventory during backtesting.
    """
    hb_dict = sim_config_to_hb_dict(config, export_params)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out, "w") as f:
        yaml.dump(hb_dict, f, default_flow_style=False, sort_keys=True)

    # Compute SHA-256 of the written YAML for integrity verification
    yaml_sha256 = _sha256_file(out)

    if metadata is not None:
        from pmm_lab import __version__ as pmm_lab_version
        metadata["yaml_sha256"] = yaml_sha256
        metadata["exported_at"] = datetime.now(timezone.utc).isoformat()
        metadata["simulator_version"] = pmm_lab_version
        # Execution realism settings for research lineage
        metadata["taker_probability"] = config.taker_probability
        metadata["touch_through"] = config.touch_through
        metadata["maker_fill_probability"] = config.maker_fill_probability
        metadata["refresh_close_mode"] = config.refresh_close_mode
        metadata["initial_base_balance"] = config.initial_base_balance
        meta_path = out.with_suffix(".meta.yml")
        with open(meta_path, "w") as f:
            yaml.dump(_sanitize_for_yaml(metadata), f, default_flow_style=False, sort_keys=True)

    return str(out)


def export_macd_bb_yaml(
    candidate,
    connector_name: str,
    trading_pair: str,
    candles_connector: str,
    candles_trading_pair: str,
    interval: str,
    output_path: str,
    config_id: Optional[str] = None,
    leverage: int = 1,
    position_mode: str = "ONEWAY",
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Export a MACD-BB CandidateBundle as a Hummingbot YAML file."""
    sc = candidate.strategy_config
    ec = candidate.engine_config

    if config_id is None:
        config_id = f"{trading_pair}-MACD-BB_{ec.total_amount_quote}"

    tp_order_type = ORDER_TYPE_MAP.get(ec.take_profit_order_type, 2)

    d = {
        "bb_length": sc.bb_length,
        "bb_long_threshold": sc.bb_long_threshold,
        "bb_short_threshold": sc.bb_short_threshold,
        "bb_std": sc.bb_std,
        "candles_connector": candles_connector,
        "candles_trading_pair": candles_trading_pair,
        "connector_name": connector_name,
        "controller_name": "macd_bb_v1",
        "controller_type": "directional_trading",
        "cooldown_time": int(ec.cooldown_time),
        "id": config_id,
        "initial_positions": None,
        "interval": interval,
        "leverage": leverage,
        "macd_fast": sc.macd_fast,
        "macd_signal": sc.macd_signal,
        "macd_slow": sc.macd_slow,
        "manual_kill_switch": None,
        "max_executors_per_side": sc.max_executors_per_side,
        "position_mode": position_mode,
        "stop_loss": ec.stop_loss,
        "take_profit": ec.take_profit,
        "take_profit_order_type": tp_order_type,
        "time_limit": int(ec.time_limit),
        "total_amount_quote": ec.total_amount_quote,
        "trading_pair": trading_pair,
        "trailing_stop": {
            "activation_price": ec.trailing_stop_activation,
            "trailing_delta": ec.trailing_stop_delta,
        },
    }

    d = dict(sorted(d.items()))

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out, "w") as f:
        yaml.dump(_sanitize_for_yaml(d), f, default_flow_style=False, sort_keys=True)

    if metadata is not None:
        meta_path = out.with_suffix(".meta.yml")
        with open(meta_path, "w") as f:
            yaml.dump(_sanitize_for_yaml(metadata), f, default_flow_style=False, sort_keys=True)

    return str(out)


def export_top_n(
    configs: list,
    output_dir: str,
    export_params: ExportParams = ExportParams(),
    study_name: str = "study",
) -> list:
    """Export top-N configs as individual YAML files.

    Files are named: {output_dir}/{study_name}/rank_{i:02d}.yml
    Also writes a summary.yml with all configs' key metrics.
    """
    out_dir = Path(output_dir) / study_name
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = []
    summaries = []
    for i, (cfg, meta) in enumerate(configs):
        path = str(out_dir / f"rank_{i:02d}.yml")
        export_yaml(cfg, path, export_params, metadata=meta)
        paths.append(path)
        summaries.append({
            "rank": i,
            "file": f"rank_{i:02d}.yml",
            "objective_score": meta.get("objective_score") if meta else None,
        })

    # Write summary
    summary_path = out_dir / "summary.yml"
    with open(summary_path, "w") as f:
        yaml.dump({"configs": summaries}, f, default_flow_style=False)

    return paths
