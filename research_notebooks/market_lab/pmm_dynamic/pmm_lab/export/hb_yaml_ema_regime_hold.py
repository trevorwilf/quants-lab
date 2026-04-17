"""Hummingbot YAML export for EMA regime-hold.

Matches the runtime template at
`hummingbot/conf/controllers/nonkyc_xmr_usdt_ema_regime_hold_v1.yml`.

`hold_mode` is always exported as `"reentry"` per D4.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


@dataclass(frozen=True)
class EMARegimeHoldExportParams:
    connector_name: str = "nonkyc"
    trading_pair: str = "XMR-USDT"
    signal_interval: str = "5m"
    regime_interval: str = "4h"
    leverage: int = 1
    position_mode: str = "ONEWAY"
    config_id: Optional[str] = None


def _format_trailing_stop(activation: float, delta: float) -> str:
    if activation == 0.0 and delta == 0.0:
        return ""
    return f"{activation}/{delta}"


def export_ema_regime_hold_yaml(
    strategy_config,  # EMARegimeHoldStrategyConfig
    engine_config,
    export_params: EMARegimeHoldExportParams,
    out_path: Path | str,
) -> Path:
    sc = strategy_config
    ec = engine_config

    config_id = export_params.config_id or f"{export_params.connector_name}_{export_params.trading_pair.replace('-', '_').lower()}_ema_regime_hold_v1"

    d: Dict[str, Any] = {
        "id": config_id,
        "controller_name": "ema_regime_hold_v1",
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
        "signal_interval": export_params.signal_interval,
        "regime_interval": export_params.regime_interval,
        "regime_ema_fast": int(sc.regime_ema_fast),
        "regime_ema_slow": int(sc.regime_ema_slow),
        "regime_adx_length": int(sc.regime_adx_length),
        "regime_adx_threshold": float(sc.regime_adx_threshold),
        "volume_filter_window": int(sc.volume_filter_window),
        "min_volume_quantile": float(sc.min_volume_quantile),
        "hold_mode": "reentry",  # D4
    }

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        yaml.safe_dump(d, f, default_flow_style=False, sort_keys=False)
    return out


_REQUIRED_KEYS = {
    "id", "controller_name", "controller_type", "connector_name", "trading_pair",
    "total_amount_quote", "max_executors_per_side", "cooldown_time",
    "stop_loss", "take_profit", "time_limit", "take_profit_order_type",
    "trailing_stop",
    "signal_interval", "regime_interval",
    "regime_ema_fast", "regime_ema_slow", "regime_adx_length", "regime_adx_threshold",
    "volume_filter_window", "min_volume_quantile",
    "hold_mode",
}


def validate_export_ema_regime_hold(yaml_path: Path | str) -> None:
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    if data.get("controller_name") != "ema_regime_hold_v1":
        raise ValueError(f"controller_name mismatch: {data.get('controller_name')}")

    missing = _REQUIRED_KEYS - set(data.keys())
    if missing:
        raise ValueError(f"missing keys: {sorted(missing)}")

    if data["hold_mode"] not in ("reentry", "hold"):
        raise ValueError(f"hold_mode must be 'reentry' or 'hold'; got {data['hold_mode']!r}")
    # This export should always emit 'reentry'; 'hold' is accepted for forward
    # compatibility but we don't produce it.
    if data["hold_mode"] == "hold":
        # Only warn at validator level — the export function never writes this,
        # but validating external YAMLs might.
        import warnings
        warnings.warn("hold_mode='hold' is not supported by the research pipeline (D4)")

    if not (data["regime_ema_fast"] > 5):
        raise ValueError(f"regime_ema_fast must be > 5; got {data['regime_ema_fast']}")
    if not (data["regime_ema_slow"] > 10):
        raise ValueError(f"regime_ema_slow must be > 10; got {data['regime_ema_slow']}")
    if not (data["regime_ema_fast"] < data["regime_ema_slow"]):
        raise ValueError(f"regime_ema_fast must be < regime_ema_slow")
    if not (data["regime_adx_length"] > 2):
        raise ValueError(f"regime_adx_length must be > 2")
    if not (data["regime_adx_threshold"] >= 0.0):
        raise ValueError(f"regime_adx_threshold must be >= 0")
    if not (data["volume_filter_window"] >= 0):
        raise ValueError(f"volume_filter_window must be >= 0")
    if not (0.0 <= data["min_volume_quantile"] <= 1.0):
        raise ValueError(f"min_volume_quantile out of [0,1]")

    if not isinstance(data["time_limit"], int) or data["time_limit"] < 0:
        raise ValueError(f"time_limit must be non-negative int")
    if not isinstance(data["cooldown_time"], int) or data["cooldown_time"] < 0:
        raise ValueError(f"cooldown_time must be non-negative int")
