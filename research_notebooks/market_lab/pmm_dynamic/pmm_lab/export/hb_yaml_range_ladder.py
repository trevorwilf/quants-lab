"""Hummingbot YAML export for range_ladder → live `range_inventory_ladder`.

Converts a tuned generative config + a DEPLOY-TIME anchor into the live
controller schema: absolute tick-quantized rung prices (`buy_prices`
highest→lowest, `sell_prices` lowest→highest) and per-side percentage
weights that sum to exactly 100.0.

The anchor is an explicit argument — the notebook passes the latest
median-3 close and warns loudly if it diverges > 2% from the last close
(trending, not ranging).

Timing fields are the FROZEN Phase A live values (`executor_refresh_time`
43200, `buy_cooldown_time`/`sell_cooldown_time` 3600); the bar-path sim
cannot express refresh, so Phase B owns tuning them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import yaml

from pmm_lab.config.params import PairRules

# Frozen Phase A timing (seconds) — mirrors the live configs
FROZEN_EXECUTOR_REFRESH_TIME = 43200
FROZEN_BUY_COOLDOWN_TIME = 3600
FROZEN_SELL_COOLDOWN_TIME = 3600


@dataclass(frozen=True)
class RangeLadderExportParams:
    connector_name: str = "nonkyc"
    trading_pair: str = "XMR-USDT"
    config_id: Optional[str] = None


def weights_to_pct(weights) -> list:
    """Normalized weights × 100, 1 dp, re-adjusted to sum exactly 100.0.

    The rounding residual is absorbed by the LARGEST rung so no small rung
    can be pushed below the live controller's compression threshold.
    """
    w = np.asarray(weights, dtype=np.float64)
    pct = np.round(w / w.sum() * 100.0, 1)
    residual = round(100.0 - float(pct.sum()), 1)
    if abs(residual) >= 0.05:
        i = int(np.argmax(pct))
        pct[i] = round(pct[i] + residual, 1)
    return [round(float(x), 1) for x in pct]


def export_range_ladder_yaml(
    config,                      # RangeLadderConfig
    anchor_price: float,
    pair_rules: PairRules,
    export_params: RangeLadderExportParams,
    out_path: Path | str,
    total_amount_quote: Optional[float] = None,
    max_fund_value_quote: Optional[float] = None,
    claimed_base_value_quote: Optional[float] = None,
) -> Path:
    """Write a `range_inventory_ladder` controller YAML. Returns the Path.

    Fund fields default from `config.fund_quote`; override per deployment.
    """
    rungs = config.resolve_rungs(float(anchor_price), pair_rules.price_tick)

    # buys nearest→farthest == highest→lowest; sells nearest→farthest ==
    # lowest→highest — exactly the live YAML ordering.
    buy_prices = [float(p) for p in rungs.buys]
    sell_prices = [float(p) for p in rungs.sells]

    fund = float(config.fund_quote)
    total_q = float(total_amount_quote) if total_amount_quote is not None else fund
    max_fund_q = float(max_fund_value_quote) if max_fund_value_quote is not None else total_q
    claimed_base_q = (
        float(claimed_base_value_quote)
        if claimed_base_value_quote is not None
        else round(total_q * (1.0 - config.quote_frac), 2)
    )

    config_id = export_params.config_id or (
        f"{export_params.connector_name}_"
        f"{export_params.trading_pair.replace('-', '_').lower()}_range_ladder"
    )

    d: Dict[str, Any] = {
        "id": config_id,
        "controller_name": "range_inventory_ladder",
        "controller_type": "market_making",
        "connector_name": export_params.connector_name,
        "trading_pair": export_params.trading_pair,
        "buy_prices": buy_prices,
        "buy_amounts_pct": weights_to_pct(rungs.buy_weights),
        "sell_prices": sell_prices,
        "sell_amounts_pct": weights_to_pct(rungs.sell_weights),
        "fee_rate": float(config.fee),
        "min_order_quote": float(pair_rules.min_notional_quote),
        "allow_partial_levels": True,
        "passive_order_placement": True,
        "event_refresh_enabled": True,
        "executor_refresh_time": FROZEN_EXECUTOR_REFRESH_TIME,
        "buy_cooldown_time": FROZEN_BUY_COOLDOWN_TIME,
        "sell_cooldown_time": FROZEN_SELL_COOLDOWN_TIME,
        "total_amount_quote": total_q,
        "max_fund_value_quote": max_fund_q,
        "claimed_base_value_quote": claimed_base_q,
    }

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# range_inventory_ladder config exported by pmm_lab (range_ladder Phase A)\n"
        f"# anchor_price: {float(anchor_price)} (deploy-time median-3 close; rung\n"
        "#   prices are absolute — re-export if price has drifted since tuning)\n"
        "# Fund fields are PLACEHOLDERS sized from the study's FUND_USD:\n"
        "#   total_amount_quote        — total quote capital the ladder may deploy\n"
        "#   max_fund_value_quote      — hard cap on fund value claimed by the bot\n"
        "#   claimed_base_value_quote  — base inventory (quote-valued) claimed at start\n"
        "#   Review against the live account before deploying.\n"
        "# Timing fields are FROZEN Phase A live values (refresh/cooldowns are\n"
        "# not modeled by the bar-path sim — Phase B tunes them).\n"
    )
    with open(out, "w") as f:
        f.write(header)
        yaml.safe_dump(d, f, default_flow_style=False, sort_keys=False)
    return out


def _parse_ladder_field(value, field: str) -> list:
    """Parse a rung/weight field from a live controller YAML.

    The live range_inventory_ladder configs store these as comma-separated
    scalars (``buy_prices: 328,324,321``), which YAML loads as a single
    string; lab-generated exports use proper YAML lists. Accept both.
    """
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",")]
        values = [float(p) for p in parts if p]
    elif isinstance(value, (list, tuple)):
        values = [float(x) for x in value]
    elif isinstance(value, (int, float)):
        values = [float(value)]
    else:
        raise ValueError(
            f"{field}: expected a comma-separated string or a list, "
            f"got {type(value).__name__}"
        )
    if not values:
        raise ValueError(f"{field}: no values parsed from {value!r}")
    return values


def load_range_ladder_incumbent(yaml_path: Path | str) -> Optional[dict]:
    """Load a live incumbent ladder YAML for benchmarking.

    Returns None when the file does not exist (the incumbent machinery must
    degrade gracefully — e.g. pairs with no live ladder yet). Live files are
    accepted VERBATIM: ladder fields may be comma-separated strings (the
    live controller format) or YAML lists (lab exports).
    """
    p = Path(yaml_path)
    if not p.exists():
        return None
    with open(p, "r") as f:
        data = yaml.safe_load(f)
    result = {
        "buy_prices": _parse_ladder_field(data["buy_prices"], "buy_prices"),
        "buy_weights": _parse_ladder_field(data["buy_amounts_pct"], "buy_amounts_pct"),
        "sell_prices": _parse_ladder_field(data["sell_prices"], "sell_prices"),
        "sell_weights": _parse_ladder_field(data["sell_amounts_pct"], "sell_amounts_pct"),
        "raw": data,
    }
    if len(result["buy_prices"]) != len(result["buy_weights"]):
        raise ValueError(
            f"{p.name}: buy_prices ({len(result['buy_prices'])}) and "
            f"buy_amounts_pct ({len(result['buy_weights'])}) length mismatch"
        )
    if len(result["sell_prices"]) != len(result["sell_weights"]):
        raise ValueError(
            f"{p.name}: sell_prices ({len(result['sell_prices'])}) and "
            f"sell_amounts_pct ({len(result['sell_weights'])}) length mismatch"
        )
    return result


def incumbent_yaml_path(
    incumbents_dir: Path | str, connector: str, trading_pair: str
) -> Path:
    """Repo convention: configs/incumbents/<connector>__<pair>.yml."""
    return Path(incumbents_dir) / f"{connector}__{trading_pair}.yml"
