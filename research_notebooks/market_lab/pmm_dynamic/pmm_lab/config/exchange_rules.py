"""Exchange rules YAML parser and resolver."""

import math
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from typing import Optional

import yaml

from pmm_lab.config.params import FeeConfig, PairRules


_DEFAULT_YAML_PATH = (
    Path(__file__).resolve().parent.parent.parent / "configs" / "exchange_rules.yaml"
)


def load_exchange_rules(yaml_path: Optional[Path] = None) -> dict:
    """Load exchange rules from YAML config file.

    Parameters
    ----------
    yaml_path : Path, optional
        Path to the YAML file. Defaults to configs/exchange_rules.yaml
        relative to the project root.

    Returns
    -------
    dict
        Parsed YAML as a dictionary.
    """
    path = yaml_path or _DEFAULT_YAML_PATH
    with open(path, "r") as f:
        return yaml.safe_load(f)


def _resolve_fees(fee_cfg: dict, tier: Optional[str] = None) -> FeeConfig:
    """Resolve fee configuration from a fee block.

    Parameters
    ----------
    fee_cfg : dict
        The 'fees' block from the YAML.
    tier : str, optional
        For tiered mode, the tier name to look up.

    Returns
    -------
    FeeConfig
    """
    mode = fee_cfg.get("mode", "static")

    if mode == "static":
        return FeeConfig(
            maker_fee=float(fee_cfg["maker_fee"]),
            taker_fee=float(fee_cfg["taker_fee"]),
        )

    if mode == "tiered":
        tiers = fee_cfg.get("tiers", [])
        if tier is not None:
            for t in tiers:
                if t["name"] == tier:
                    return FeeConfig(
                        maker_fee=float(t["maker_fee"]),
                        taker_fee=float(t["taker_fee"]),
                    )
            raise KeyError(f"Tier '{tier}' not found in fee tiers")
        # Default to first tier if no tier specified
        if tiers:
            t = tiers[0]
            return FeeConfig(
                maker_fee=float(t["maker_fee"]),
                taker_fee=float(t["taker_fee"]),
            )

    return FeeConfig(0.001, 0.002)


def resolve_pair_rules(
    rules_data: dict,
    connector: str,
    trading_pair: str,
    tier: Optional[str] = None,
) -> PairRules:
    """Resolve rules for a specific (connector, pair) combination.

    Pair-specific overrides take precedence over connector defaults.

    Parameters
    ----------
    rules_data : dict
        The full parsed YAML (from load_exchange_rules).
    connector : str
        Connector name (e.g. 'mexc', 'nonkyc').
    trading_pair : str
        Trading pair (e.g. 'BTC-USDT').
    tier : str, optional
        Fee tier name for tiered connectors.

    Returns
    -------
    PairRules

    Raises
    ------
    KeyError
        If the connector is not found in the config.
    """
    connectors = rules_data.get("connectors", {})
    if connector not in connectors:
        raise KeyError(f"Connector '{connector}' not found in exchange rules")

    connector_cfg = connectors[connector]
    default_cfg = connector_cfg.get("default", {})
    pairs_cfg = connector_cfg.get("pairs", {})

    # Start with defaults
    merged = dict(default_cfg)

    # Override with pair-specific values
    if trading_pair in pairs_cfg:
        pair_overrides = pairs_cfg[trading_pair]
        for k, v in pair_overrides.items():
            merged[k] = v

    # Resolve fees
    fee_block = merged.get("fees", default_cfg.get("fees", {}))
    fees = _resolve_fees(fee_block, tier=tier)

    return PairRules(
        price_tick=float(merged["price_tick"]),
        amount_step=float(merged["amount_step"]),
        min_notional_quote=float(merged.get("min_notional_quote", 5.0)),
        min_order_size_base=float(merged.get("min_order_size_base", 0.0)),
        max_order_size_base=(
            float(merged["max_order_size_base"])
            if merged.get("max_order_size_base") is not None
            else None
        ),
        fees=fees,
    )


def round_price(price: float, rules: PairRules) -> float:
    """Round price DOWN to the nearest price_tick.

    Uses Decimal arithmetic to avoid float precision issues.

    Parameters
    ----------
    price : float
        The price to round.
    rules : PairRules
        Rules containing price_tick.

    Returns
    -------
    float
        Price rounded down to nearest tick.
    """
    tick = Decimal(str(rules.price_tick))
    p = Decimal(str(price))
    return float((p / tick).to_integral_value(rounding=ROUND_DOWN) * tick)


def round_amount(amount: float, rules: PairRules) -> float:
    """Round amount DOWN to the nearest amount_step.

    Uses Decimal arithmetic to avoid float precision issues.

    Parameters
    ----------
    amount : float
        The amount to round.
    rules : PairRules
        Rules containing amount_step.

    Returns
    -------
    float
        Amount rounded down to nearest step.
    """
    step = Decimal(str(rules.amount_step))
    a = Decimal(str(amount))
    return float((a / step).to_integral_value(rounding=ROUND_DOWN) * step)


def check_min_notional(price: float, amount: float, rules: PairRules) -> bool:
    """Check if price * amount meets the minimum notional requirement.

    Parameters
    ----------
    price : float
    amount : float
    rules : PairRules

    Returns
    -------
    bool
        True if notional >= min_notional_quote.
    """
    return price * amount >= rules.min_notional_quote


def check_order_size(
    amount: float, rules: PairRules
) -> tuple[float, Optional[str]]:
    """Clamp order size to min/max and return (clamped_amount, rejection_reason).

    Parameters
    ----------
    amount : float
        Requested order amount.
    rules : PairRules

    Returns
    -------
    tuple[float, str | None]
        (clamped_amount, rejection_reason_or_None).
        If rejection_reason is not None, the order should be rejected.
    """
    clamped = amount

    # Clamp to min
    if rules.min_order_size_base > 0 and clamped < rules.min_order_size_base:
        clamped = rules.min_order_size_base

    # Clamp to max
    if rules.max_order_size_base is not None and clamped > rules.max_order_size_base:
        clamped = rules.max_order_size_base

    # Round to step
    rounded = round_amount(clamped, rules)

    # Check if rounded amount falls below min after rounding
    if rules.min_order_size_base > 0 and rounded < rules.min_order_size_base:
        return rounded, f"Amount {rounded} below min_order_size_base {rules.min_order_size_base} after rounding"

    return rounded, None
