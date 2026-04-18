"""Trading strategy implementations for the generic SimEngine.

Lazy imports (PEP 562): names are resolved on attribute access, so directional-only
imports do NOT trigger PMM's pandas_ta dependency. This fixes ML-DIR-012.

Backwards-compatible: `from pmm_lab.strategies import PMMDynamicStrategy` still works.
"""
from __future__ import annotations


_LAZY_ATTRS = {
    "PMMDynamicStrategy": ("pmm_lab.strategies.pmm_dynamic", "PMMDynamicStrategy"),
    "PMMDynamicStrategyConfig": ("pmm_lab.strategies.pmm_dynamic", "PMMDynamicStrategyConfig"),
    "BollingerStrategy": ("pmm_lab.strategies.bollinger", "BollingerStrategy"),
    "BollingerStrategyConfig": ("pmm_lab.strategies.bollinger", "BollingerStrategyConfig"),
    "MACDBBStrategy": ("pmm_lab.strategies.macd_bb", "MACDBBStrategy"),
    "MACDBBStrategyConfig": ("pmm_lab.strategies.macd_bb", "MACDBBStrategyConfig"),
    "create_strategy": ("pmm_lab.strategies.factory", "create_strategy"),
    "available_strategies": ("pmm_lab.strategies.factory", "available_strategies"),
    "register_strategy": ("pmm_lab.strategies.factory", "register_strategy"),
}


def __getattr__(name):
    if name in _LAZY_ATTRS:
        module_name, attr_name = _LAZY_ATTRS[name]
        import importlib
        mod = importlib.import_module(module_name)
        value = getattr(mod, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(list(_LAZY_ATTRS) + list(globals()))
