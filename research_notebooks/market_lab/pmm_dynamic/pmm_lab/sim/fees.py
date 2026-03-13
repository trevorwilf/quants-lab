"""
Fee calculation with maker/taker distinction.
"""

from pmm_lab.config.params import FeeConfig


def compute_fee(
    price: float,
    quantity: float,
    fee_config: FeeConfig,
    fee_type: str = "maker",
) -> float:
    """Compute the fee in quote currency for a trade.

    Parameters
    ----------
    price : float
        Execution price.
    quantity : float
        Trade quantity in base.
    fee_config : FeeConfig
        Contains maker_fee and taker_fee rates.
    fee_type : str
        "maker" for passive limit fills, "taker" for market exits (SL/TL/TS).

    Returns
    -------
    float
        Fee amount in quote currency.
    """
    rate = fee_config.maker_fee if fee_type == "maker" else fee_config.taker_fee
    return price * quantity * rate


def compute_slippage(price: float, slippage_bps: float, side: str) -> float:
    """Compute adverse slippage for market exits.

    For a buy trade exiting (selling): price moves DOWN -> exit_price = price * (1 - slippage)
    For a sell trade exiting (buying back): price moves UP -> exit_price = price * (1 + slippage)

    Parameters
    ----------
    price : float
        The reference exit price before slippage.
    slippage_bps : float
        Slippage in basis points (e.g., 5.0 = 0.05%).
    side : str
        "buy" or "sell" — the ORIGINAL trade side (determines slippage direction).

    Returns
    -------
    float
        The adjusted exit price after adverse slippage.
    """
    slip_frac = slippage_bps / 10000.0
    if side == "buy":
        # Exiting a buy = selling -> price goes down
        return price * (1 - slip_frac)
    else:
        # Exiting a sell = buying back -> price goes up
        return price * (1 + slip_frac)
