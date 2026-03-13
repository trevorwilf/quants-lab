"""
Latency gating for the simulator.

Orders placed at bar t become eligible for fills at bar t + latency_bars.
"""


def is_order_active(current_bar: int, placed_bar: int, latency_bars: int = 1) -> bool:
    """Return True if the order is past its latency window and eligible for fills."""
    return current_bar >= placed_bar + latency_bars
