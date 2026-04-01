"""
Strategy-agnostic candidate bundle for the optimization pipeline.

CandidateBundle wraps a strategy config + engine config + export metadata,
providing a uniform interface for the pipeline regardless of strategy type.
"""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class CandidateBundle:
    """Strategy-agnostic candidate for the optimization pipeline.

    Attributes
    ----------
    strategy_name : str
        Strategy identifier (e.g., "pmm_dynamic", "macd_bb").
    strategy_config : Any
        Strategy-specific config (MACDBBStrategyConfig, PMMDynamicStrategyConfig, etc.).
    engine_config : EngineConfig
        Generic execution parameters (barriers, fills, timing).
    export_meta : dict
        Controller metadata for YAML export (controller_name, controller_type, etc.).
    provenance : dict
        Tracking metadata (trial ID, dataset hash, etc.).
    """
    strategy_name: str
    strategy_config: Any
    engine_config: Any  # EngineConfig
    export_meta: Dict[str, Any] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)
