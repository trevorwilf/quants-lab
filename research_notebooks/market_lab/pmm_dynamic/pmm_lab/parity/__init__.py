"""
Hummingbot parity testing framework.

Provides tools to compare local pmm_lab feature computation and YAML export
against native Hummingbot controller behavior.

Two modes:
1. Native parity: replicates controller logic using pandas_ta (no Hummingbot required)
2. Frozen fixture regression: compares against committed baselines

The native parity check now replicates the controller logic directly
using pandas_ta, so it doesn't require the full Hummingbot installation.
HAS_HUMMINGBOT is kept for export parity (which needs PMMDynamicControllerConfig).
"""

HAS_HUMMINGBOT = False
try:
    from controllers.market_making.pmm_dynamic import PMMDynamicControllerConfig
    HAS_HUMMINGBOT = True
except ImportError:
    pass
