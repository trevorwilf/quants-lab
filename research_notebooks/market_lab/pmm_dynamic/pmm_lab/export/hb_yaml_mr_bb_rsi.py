"""Hummingbot YAML export for MR BB+RSI.

The produced YAML matches the runtime template at
`hummingbot/conf/controllers/nonkyc_xmr_usdt_mean_reversion_bb_rsi_v1.yml`.

Numeric fields are emitted exactly per the live Pydantic model:
  - bb_length, rsi_length, atr_length, trend_ema_length, volume_filter_window,
    time_limit, cooldown_time: int
  - bb_std, bbp_entry_threshold, rsi_entry_threshold, min_trend_slope,
    max_atr_pct_for_entry, min_volume_quantile, max_spread_pct: float
  - stop_loss, take_profit: string (matches the live YAML convention)
  - total_amount_quote: string
  - trailing_stop: "" when disabled, else formatted `"<activation>/<delta>"`
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


@dataclass(frozen=True)
class MRBBRSIExportParams:
    connector_name: str = "nonkyc"
    trading_pair: str = "XMR-USDT"
    interval: str = "5m"
    leverage: int = 1
    position_mode: str = "ONEWAY"
    config_id: Optional[str] = None
    max_spread_pct: float = 0.006
    max_trades_per_day: int = 6


def _format_trailing_stop(activation: float, delta: float) -> str:
    """Empty string when disabled, `activation/delta` otherwise (matches live template)."""
    if activation == 0.0 and delta == 0.0:
        return ""
    return f"{activation}/{delta}"


def export_mr_bb_rsi_yaml(
    strategy_config,  # MeanReversionBBRSIStrategyConfig
    engine_config,    # EngineConfig
    export_params: MRBBRSIExportParams,
    out_path: Path | str,
) -> Path:
    """Write an MR BB+RSI controller YAML to `out_path`. Returns the Path."""
    sc = strategy_config
    ec = engine_config

    config_id = export_params.config_id or f"{export_params.connector_name}_{export_params.trading_pair.replace('-', '_').lower()}_mr_bb_rsi_v1"

    d: Dict[str, Any] = {
        "id": config_id,
        "controller_name": "mean_reversion_bb_rsi_v1",
        "controller_type": "directional_trading",
        "connector_name": export_params.connector_name,
        "trading_pair": export_params.trading_pair,
        "total_amount_quote": str(ec.total_amount_quote),
        "manual_kill_switch": False,
        "initial_positions": [],
        "max_executors_per_side": int(sc.max_executors_per_side),
        "cooldown_time": int(ec.cooldown_time),
        "leverage": int(export_params.leverage),
        "position_mode": export_params.position_mode,
        "stop_loss": str(ec.stop_loss),
        "take_profit": str(ec.take_profit),
        "time_limit": int(ec.time_limit),
        "take_profit_order_type": str(ec.take_profit_order_type),
        "trailing_stop": _format_trailing_stop(
            float(ec.trailing_stop_activation), float(ec.trailing_stop_delta)
        ),
        "candles_connector": "",
        "candles_trading_pair": "",
        "interval": export_params.interval,
        "bb_length": int(sc.bb_length),
        "bb_std": float(sc.bb_std),
        "bbp_entry_threshold": float(sc.bbp_entry_threshold),
        "rsi_length": int(sc.rsi_length),
        "rsi_entry_threshold": float(sc.rsi_entry_threshold),
        "use_trend_filter": bool(sc.use_trend_filter),
        "trend_ema_length": int(sc.trend_ema_length),
        "min_trend_slope": float(sc.min_trend_slope),
        "atr_length": int(sc.atr_length),
        "max_atr_pct_for_entry": float(sc.max_atr_pct_for_entry),
        "volume_filter_window": int(sc.volume_filter_window),
        "min_volume_quantile": float(sc.min_volume_quantile),
        "max_spread_pct": float(getattr(sc, "max_spread_pct", export_params.max_spread_pct)),
        "max_trades_per_day": int(getattr(sc, "max_trades_per_day", export_params.max_trades_per_day)),
    }

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        yaml.safe_dump(d, f, default_flow_style=False, sort_keys=False)
    return out


# --- Validator ---

_REQUIRED_KEYS = {
    "id", "controller_name", "controller_type", "connector_name", "trading_pair",
    "total_amount_quote", "max_executors_per_side", "cooldown_time",
    "stop_loss", "take_profit", "time_limit", "take_profit_order_type",
    "trailing_stop", "interval",
    "bb_length", "bb_std", "bbp_entry_threshold",
    "rsi_length", "rsi_entry_threshold",
    "use_trend_filter", "trend_ema_length", "min_trend_slope",
    "atr_length", "max_atr_pct_for_entry",
    "volume_filter_window", "min_volume_quantile",
    "max_spread_pct", "max_trades_per_day",
}


def validate_export_mr_bb_rsi(yaml_path: Path | str) -> None:
    """Validate an MR BB+RSI YAML file. Raises ValueError on violation."""
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    if data.get("controller_name") != "mean_reversion_bb_rsi_v1":
        raise ValueError(f"controller_name mismatch: {data.get('controller_name')}")

    missing = _REQUIRED_KEYS - set(data.keys())
    if missing:
        raise ValueError(f"missing keys: {sorted(missing)}")

    # Numeric constraints mirrored from the live Pydantic model
    if not (data["bb_length"] > 10):
        raise ValueError(f"bb_length must be > 10; got {data['bb_length']}")
    if not (data["bb_std"] > 0.1):
        raise ValueError(f"bb_std must be > 0.1; got {data['bb_std']}")
    if not (0.0 <= data["bbp_entry_threshold"] <= 1.0):
        raise ValueError(f"bbp_entry_threshold out of [0,1]: {data['bbp_entry_threshold']}")
    if not (data["rsi_length"] > 2):
        raise ValueError(f"rsi_length must be > 2; got {data['rsi_length']}")
    if not (0.0 <= data["rsi_entry_threshold"] <= 100.0):
        raise ValueError(f"rsi_entry_threshold out of [0,100]: {data['rsi_entry_threshold']}")
    if not (data["trend_ema_length"] > 20):
        raise ValueError(f"trend_ema_length must be > 20; got {data['trend_ema_length']}")
    if not (data["atr_length"] > 2):
        raise ValueError(f"atr_length must be > 2; got {data['atr_length']}")
    if not (data["max_atr_pct_for_entry"] > 0.0):
        raise ValueError(f"max_atr_pct_for_entry must be > 0; got {data['max_atr_pct_for_entry']}")
    if not (data["volume_filter_window"] >= 0):
        raise ValueError(f"volume_filter_window must be >= 0; got {data['volume_filter_window']}")
    if not (0.0 <= data["min_volume_quantile"] <= 1.0):
        raise ValueError(f"min_volume_quantile out of [0,1]: {data['min_volume_quantile']}")
    if not (data["max_spread_pct"] >= 0.0):
        raise ValueError(f"max_spread_pct must be >= 0; got {data['max_spread_pct']}")
    if not (data["max_trades_per_day"] >= 0):
        raise ValueError(f"max_trades_per_day must be >= 0; got {data['max_trades_per_day']}")

    if not isinstance(data["time_limit"], int) or data["time_limit"] < 0:
        raise ValueError(f"time_limit must be non-negative int; got {data['time_limit']!r}")
    if not isinstance(data["cooldown_time"], int) or data["cooldown_time"] < 0:
        raise ValueError(f"cooldown_time must be non-negative int; got {data['cooldown_time']!r}")
