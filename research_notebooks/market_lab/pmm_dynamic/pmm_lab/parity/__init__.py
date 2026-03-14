"""
Hummingbot parity testing framework.

Provides tools to compare local pmm_lab feature computation and YAML export
against native Hummingbot controller behavior.

Two modes:
1. When Hummingbot IS installed: full native comparison
2. When Hummingbot is NOT installed: frozen fixture regression only
"""

HAS_HUMMINGBOT = False
try:
    from controllers.market_making.pmm_dynamic import PMMDynamicControllerConfig
    HAS_HUMMINGBOT = True
except ImportError:
    pass
