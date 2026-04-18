"""
Validate exported YAML configs against Hummingbot's schema.

Two validation modes:
1. NATIVE: Import PMMDynamicControllerConfig from Hummingbot and load the YAML.
2. MIRROR: Use a local schema check that mirrors the expected fields.
"""

import yaml
import math
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    """Result of YAML validation."""
    valid: bool
    mode: str                    # "native" or "mirror"
    errors: list                 # list of error strings (empty if valid)
    warnings: list               # non-fatal issues


REQUIRED_KEYS = [
    "id", "controller_name", "controller_type", "connector_name",
    "trading_pair", "buy_spreads", "sell_spreads", "buy_amounts_pct",
    "sell_amounts_pct", "total_amount_quote", "macd_fast", "macd_slow",
    "macd_signal", "natr_length", "candles_connector", "candles_trading_pair",
    "interval",
]


def validate_yaml_file(yaml_path: str, **kwargs) -> ValidationResult:
    """Validate a Hummingbot YAML config file.

    Strategy-aware: detects controller_name and dispatches to the
    appropriate validator.

    Optional kwargs passed through to mirror validation:
        supports_post_only (bool): Whether the target connector supports post-only orders.
        taker_probability (float): The taker_probability used in the backtest.
    """
    with open(yaml_path, "r") as f:
        config_dict = yaml.safe_load(f)

    # Dispatch based on controller_name
    controller_name = config_dict.get("controller_name", "")
    if controller_name == "macd_bb_v1":
        return _validate_macd_bb_mirror(config_dict)
    if controller_name == "ema_regime_hold_v1":
        return _validate_ema_regime_hold_mirror(config_dict)
    if controller_name == "mean_reversion_bb_rsi_v1":
        return _validate_mean_reversion_bb_rsi_mirror(config_dict)

    # PMM Dynamic path (default)
    try:
        return _validate_native(config_dict)
    except ImportError:
        pass

    return _validate_mirror(config_dict, **kwargs)


def _validate_ema_regime_hold_mirror(config_dict: Dict[str, Any]) -> ValidationResult:
    """Mirror validator for EMA regime-hold YAMLs. ML-DIR-008: rejects hold_mode='hold'."""
    errors: List[str] = []
    warnings: List[str] = []

    ema_required = [
        "id", "controller_name", "controller_type", "connector_name", "trading_pair",
        "total_amount_quote", "max_executors_per_side", "cooldown_time",
        "stop_loss", "take_profit", "time_limit", "take_profit_order_type",
        "trailing_stop", "signal_interval", "regime_interval",
        "regime_ema_fast", "regime_ema_slow", "regime_adx_length",
        "regime_adx_threshold", "volume_filter_window", "min_volume_quantile",
        "hold_mode",
    ]
    for key in ema_required:
        if key not in config_dict:
            errors.append(f"Missing required key: {key}")

    hold_mode = config_dict.get("hold_mode")
    if hold_mode == "hold":
        errors.append(
            "hold_mode='hold' is not validated by the research backtest. Export blocked. "
            "Set hold_mode='reentry' or implement hold-mode simulation parity (ML-DIR-008)."
        )
    elif hold_mode not in ("reentry", None):
        errors.append(f"hold_mode must be 'reentry' (got {hold_mode!r})")

    # Ordering sanity
    f, s = config_dict.get("regime_ema_fast"), config_dict.get("regime_ema_slow")
    if isinstance(f, int) and isinstance(s, int) and f >= s:
        errors.append(f"regime_ema_fast ({f}) must be < regime_ema_slow ({s})")

    return ValidationResult(
        valid=(len(errors) == 0),
        mode="mirror",
        errors=errors,
        warnings=warnings,
    )


def _validate_mean_reversion_bb_rsi_mirror(config_dict: Dict[str, Any]) -> ValidationResult:
    """Minimal mirror validator for MR BB+RSI YAMLs."""
    errors: List[str] = []
    warnings: List[str] = []
    mr_required = [
        "id", "controller_name", "controller_type", "connector_name", "trading_pair",
        "total_amount_quote", "max_executors_per_side", "cooldown_time",
        "stop_loss", "take_profit", "time_limit", "take_profit_order_type",
        "bb_length", "bb_std", "bbp_entry_threshold",
        "rsi_length", "rsi_entry_threshold",
        "atr_length", "max_atr_pct_for_entry",
        "volume_filter_window", "min_volume_quantile",
    ]
    for key in mr_required:
        if key not in config_dict:
            errors.append(f"Missing required key: {key}")
    return ValidationResult(
        valid=(len(errors) == 0),
        mode="mirror",
        errors=errors,
        warnings=warnings,
    )


def _validate_native(config_dict: Dict[str, Any]) -> ValidationResult:
    """Validate using Hummingbot's PMMDynamicControllerConfig."""
    from controllers.market_making.pmm_dynamic import PMMDynamicControllerConfig
    try:
        PMMDynamicControllerConfig(**config_dict)
        return ValidationResult(valid=True, mode="native", errors=[], warnings=[])
    except Exception as e:
        return ValidationResult(valid=False, mode="native", errors=[str(e)], warnings=[])


def _validate_mirror(config_dict: Dict[str, Any], **kwargs) -> ValidationResult:
    """Validate using a local mirror schema."""
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Required keys present
    for key in REQUIRED_KEYS:
        if key not in config_dict:
            errors.append(f"Missing required key: {key}")

    if errors:
        return ValidationResult(valid=False, mode="mirror", errors=errors, warnings=warnings)

    # 2. controller_name == "pmm_dynamic"
    if config_dict.get("controller_name") != "pmm_dynamic":
        errors.append(f"controller_name must be 'pmm_dynamic', got '{config_dict.get('controller_name')}'")

    # 3. controller_type == "market_making"
    if config_dict.get("controller_type") != "market_making":
        errors.append(f"controller_type must be 'market_making', got '{config_dict.get('controller_type')}'")

    # 4. buy_spreads and sell_spreads are lists of positive floats
    for key in ["buy_spreads", "sell_spreads"]:
        val = config_dict.get(key, [])
        if not isinstance(val, list):
            errors.append(f"{key} must be a list")
        else:
            for i, v in enumerate(val):
                if not isinstance(v, (int, float)):
                    errors.append(f"{key}[{i}] is not a number")
                elif v <= 0:
                    errors.append(f"{key}[{i}] must be positive, got {v}")
                elif math.isnan(v):
                    errors.append(f"{key}[{i}] is NaN")

    # 5. buy_amounts_pct and sell_amounts_pct are lists of positive floats
    for key in ["buy_amounts_pct", "sell_amounts_pct"]:
        val = config_dict.get(key, [])
        if not isinstance(val, list):
            errors.append(f"{key} must be a list")
        else:
            for i, v in enumerate(val):
                if not isinstance(v, (int, float)):
                    errors.append(f"{key}[{i}] is not a number")
                elif v <= 0:
                    errors.append(f"{key}[{i}] must be positive, got {v}")
                elif math.isnan(v):
                    errors.append(f"{key}[{i}] is NaN")

    # 6. sum(buy_amounts_pct) + sum(sell_amounts_pct) ≈ 1.0
    buy_amt = config_dict.get("buy_amounts_pct", [])
    sell_amt = config_dict.get("sell_amounts_pct", [])
    if isinstance(buy_amt, list) and isinstance(sell_amt, list):
        total = sum(buy_amt) + sum(sell_amt)
        if abs(total - 1.0) > 0.001:
            errors.append(f"buy_amounts_pct + sell_amounts_pct sum to {total}, expected ~1.0")

    # 7. len(buy_spreads) == len(buy_amounts_pct)
    bs = config_dict.get("buy_spreads", [])
    ba = config_dict.get("buy_amounts_pct", [])
    if isinstance(bs, list) and isinstance(ba, list) and len(bs) != len(ba):
        errors.append(f"len(buy_spreads)={len(bs)} != len(buy_amounts_pct)={len(ba)}")

    # 8. len(sell_spreads) == len(sell_amounts_pct)
    ss = config_dict.get("sell_spreads", [])
    sa = config_dict.get("sell_amounts_pct", [])
    if isinstance(ss, list) and isinstance(sa, list) and len(ss) != len(sa):
        errors.append(f"len(sell_spreads)={len(ss)} != len(sell_amounts_pct)={len(sa)}")

    # 9. macd_fast < macd_slow
    mf = config_dict.get("macd_fast", 0)
    ms = config_dict.get("macd_slow", 0)
    if mf >= ms:
        errors.append(f"macd_fast ({mf}) must be < macd_slow ({ms})")

    # 10. stop_loss, take_profit, time_limit positive
    for key in ["stop_loss", "take_profit", "time_limit"]:
        val = config_dict.get(key)
        if val is not None and isinstance(val, (int, float)) and val <= 0:
            errors.append(f"{key} must be positive, got {val}")

    # 11. take_profit_order_type is int (Hummingbot OrderType enum: MARKET=1, LIMIT=2, LIMIT_MAKER=3)
    tpot = config_dict.get("take_profit_order_type")
    if tpot is not None:
        if not isinstance(tpot, int):
            errors.append(f"take_profit_order_type must be int, got {type(tpot).__name__}")
        elif tpot not in (1, 2, 3):
            errors.append(f"take_profit_order_type must be 1 (MARKET), 2 (LIMIT), or 3 (LIMIT_MAKER), got {tpot}")

    # 12. trailing_stop is a dict
    ts = config_dict.get("trailing_stop")
    if ts is not None:
        if not isinstance(ts, dict):
            errors.append("trailing_stop must be a dict")
        else:
            if "activation_price" not in ts:
                errors.append("trailing_stop missing 'activation_price'")
            if "trailing_delta" not in ts:
                errors.append("trailing_stop missing 'trailing_delta'")

    # 13. NaN check on key numeric fields
    for key in ["stop_loss", "take_profit", "total_amount_quote", "cooldown_time",
                 "executor_refresh_time"]:
        val = config_dict.get(key)
        if isinstance(val, float) and math.isnan(val):
            errors.append(f"{key} is NaN")

    # 14. Integer type checks — Hummingbot expects int for these fields
    int_fields = ["macd_fast", "macd_slow", "macd_signal", "natr_length", "leverage",
                  "time_limit", "cooldown_time", "executor_refresh_time"]
    for key in int_fields:
        val = config_dict.get(key)
        if val is not None and not isinstance(val, int):
            # Allow float that is exactly an integer (e.g., 42.0)
            if isinstance(val, float) and val == int(val):
                warnings.append(f"{key} is float {val}, should be int {int(val)}")
            else:
                errors.append(f"{key} must be int, got {type(val).__name__}: {val}")

    # 15. Float type checks — these should be numeric (int or float)
    numeric_fields = [
        "stop_loss", "take_profit", "total_amount_quote",
        "position_rebalance_threshold_pct",
    ]
    for key in numeric_fields:
        val = config_dict.get(key)
        if val is not None and not isinstance(val, (int, float)):
            errors.append(f"{key} must be numeric, got {type(val).__name__}: {val}")

    # 16. Boolean checks
    bool_fields = ["skip_rebalance", "manual_kill_switch"]
    for key in bool_fields:
        val = config_dict.get(key)
        if val is not None and not isinstance(val, bool):
            errors.append(f"{key} must be bool, got {type(val).__name__}: {val}")

    # 17. String checks
    string_fields = ["connector_name", "trading_pair", "interval", "position_mode", "id"]
    for key in string_fields:
        val = config_dict.get(key)
        if val is not None and not isinstance(val, str):
            errors.append(f"{key} must be str, got {type(val).__name__}: {val}")

    # 18. Spread lists are sorted ascending (preferred for Hummingbot)
    for key in ["buy_spreads", "sell_spreads"]:
        val = config_dict.get(key, [])
        if isinstance(val, list) and len(val) > 1:
            for i in range(1, len(val)):
                if val[i] <= val[i-1]:
                    warnings.append(f"{key} is not strictly ascending at index {i}: {val}")
                    break

    # CONTRACT NOTE: The following fields are documented in
    # controller_yml_data_dictionary.md as base-class fields:
    #   - rebalance_cooldown_time (integer, default 60)
    #   - use_wallet_balance (boolean, default false)
    # These are MarketMakingControllerConfigBase defaults and are NOT
    # exported by the lab exporter. The controller uses its base-class
    # defaults at runtime. If the lab adds simulation support for these
    # fields in the future, add them to the exporter and validator.

    # 19. use_wallet_balance warning
    if config_dict.get("use_wallet_balance") is True:
        warnings.append(
            "use_wallet_balance is set to true but the simulator does not model "
            "pre-existing base inventory. Backtest results may not reflect live "
            "sell-side behavior at startup. Set initial_base_balance in SimConfig."
        )

    # 20. Rebalance fields present (v2)
    if "position_rebalance_threshold_pct" not in config_dict:
        warnings.append("Missing position_rebalance_threshold_pct (v2 field)")
    if "skip_rebalance" not in config_dict:
        warnings.append("Missing skip_rebalance (v2 field)")

    # 21. NonKYC post-only warning
    connector_name = config_dict.get("connector_name", "")
    supports_post_only = kwargs.get("supports_post_only", True)
    taker_probability = kwargs.get("taker_probability", 0.0)
    if not supports_post_only and taker_probability == 0.0:
        warnings.append(
            f"Target connector '{connector_name}' does not support post-only orders. "
            f"Backtested with taker_probability=0.0 (pure maker assumption). "
            f"Live execution may incur taker fees on some entries. "
            f"Consider re-running with taker_probability > 0 for more realistic cost estimates."
        )

    return ValidationResult(
        valid=len(errors) == 0,
        mode="mirror",
        errors=errors,
        warnings=warnings,
    )


# --- MACD-BB validation ---

MACD_BB_REQUIRED_KEYS = [
    "id", "controller_name", "controller_type", "connector_name",
    "trading_pair", "candles_connector", "candles_trading_pair", "interval",
    "total_amount_quote", "max_executors_per_side", "cooldown_time",
    "stop_loss", "take_profit", "time_limit",
    "bb_length", "bb_std", "bb_long_threshold", "bb_short_threshold",
    "macd_fast", "macd_slow", "macd_signal",
]


def _validate_macd_bb_mirror(config_dict: Dict[str, Any]) -> ValidationResult:
    """Validate a MACD-BB v1 YAML config using local mirror schema."""
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Required keys
    for key in MACD_BB_REQUIRED_KEYS:
        if key not in config_dict:
            errors.append(f"Missing required key: {key}")

    if errors:
        return ValidationResult(valid=False, mode="mirror", errors=errors, warnings=warnings)

    # 2. controller_name == "macd_bb_v1"
    if config_dict.get("controller_name") != "macd_bb_v1":
        errors.append(f"controller_name must be 'macd_bb_v1', got '{config_dict.get('controller_name')}'")

    # 3. controller_type == "directional_trading"
    if config_dict.get("controller_type") != "directional_trading":
        errors.append(f"controller_type must be 'directional_trading', got '{config_dict.get('controller_type')}'")

    # 4. macd_fast < macd_slow
    mf = config_dict.get("macd_fast", 0)
    ms = config_dict.get("macd_slow", 0)
    if mf >= ms:
        errors.append(f"macd_fast ({mf}) must be < macd_slow ({ms})")

    # 5. bb_long_threshold < bb_short_threshold
    blt = config_dict.get("bb_long_threshold", 0)
    bst = config_dict.get("bb_short_threshold", 0)
    if blt >= bst:
        errors.append(f"bb_long_threshold ({blt}) must be < bb_short_threshold ({bst})")

    # 6. Barrier params positive
    for key in ["stop_loss", "take_profit", "time_limit"]:
        val = config_dict.get(key)
        if val is not None and isinstance(val, (int, float)) and val <= 0:
            errors.append(f"{key} must be positive, got {val}")

    # 7. take_profit_order_type is valid
    tpot = config_dict.get("take_profit_order_type")
    if tpot is not None:
        if not isinstance(tpot, int):
            errors.append(f"take_profit_order_type must be int, got {type(tpot).__name__}")
        elif tpot not in (1, 2, 3):
            errors.append(f"take_profit_order_type must be 1/2/3, got {tpot}")

    # 8. trailing_stop is dict
    ts = config_dict.get("trailing_stop")
    if ts is not None:
        if not isinstance(ts, dict):
            errors.append("trailing_stop must be a dict")
        else:
            if "activation_price" not in ts:
                errors.append("trailing_stop missing 'activation_price'")
            if "trailing_delta" not in ts:
                errors.append("trailing_stop missing 'trailing_delta'")

    # 9. NaN checks
    for key in ["stop_loss", "take_profit", "total_amount_quote", "cooldown_time"]:
        val = config_dict.get(key)
        if isinstance(val, float) and math.isnan(val):
            errors.append(f"{key} is NaN")

    # 10. Integer type checks
    int_fields = ["macd_fast", "macd_slow", "macd_signal", "bb_length",
                   "leverage", "time_limit", "cooldown_time", "max_executors_per_side"]
    for key in int_fields:
        val = config_dict.get(key)
        if val is not None and not isinstance(val, int):
            if isinstance(val, float) and val == int(val):
                warnings.append(f"{key} is float {val}, should be int {int(val)}")
            else:
                errors.append(f"{key} must be int, got {type(val).__name__}: {val}")

    # 11. Float type checks
    numeric_fields = ["stop_loss", "take_profit", "total_amount_quote",
                       "bb_std", "bb_long_threshold", "bb_short_threshold"]
    for key in numeric_fields:
        val = config_dict.get(key)
        if val is not None and not isinstance(val, (int, float)):
            errors.append(f"{key} must be numeric, got {type(val).__name__}: {val}")

    # 12. String checks
    string_fields = ["connector_name", "trading_pair", "interval", "id"]
    for key in string_fields:
        val = config_dict.get(key)
        if val is not None and not isinstance(val, str):
            errors.append(f"{key} must be str, got {type(val).__name__}: {val}")

    return ValidationResult(
        valid=len(errors) == 0,
        mode="mirror",
        errors=errors,
        warnings=warnings,
    )
