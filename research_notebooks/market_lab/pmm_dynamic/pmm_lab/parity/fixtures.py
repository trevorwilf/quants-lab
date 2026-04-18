"""
Frozen fixture management for parity testing.

Generates and loads frozen test data (candles + expected features + expected YAML)
that can be used for regression testing even without Hummingbot installed.

Usage:
    # Generate (run once, commit the fixtures):
    generate_frozen_fixture(candles, config, output_dir="fixtures/pmm_dynamic_btc_5m")

    # Load (in tests):
    fixture = load_frozen_fixture("fixtures/pmm_dynamic_btc_5m")
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Canonical candle dtype
CANDLE_DTYPE = np.dtype([
    ("timestamp", "int64"),
    ("open", "float64"),
    ("high", "float64"),
    ("low", "float64"),
    ("close", "float64"),
    ("volume", "float64"),
    ("is_forward_fill", "bool"),
])


@dataclass
class FrozenFixture:
    """A frozen test fixture with candles, config params, and expected outputs."""
    name: str
    candles: np.ndarray
    config_params: Dict[str, Any]           # raw params dict
    expected_features: Dict[str, float]     # {bar_idx: {field: value}} — spot checks
    expected_yaml_fields: Dict[str, Any]    # key YAML field values to verify
    metadata: Dict[str, Any]                # extra info (dataset hash, creation date, etc.)
    # Optional regime-timeframe candles for multi-timeframe strategies (EMA regime-hold).
    # Populated from regime_candles.npy or regime_candles.npz when present.
    regime_candles: Optional[np.ndarray] = None


def generate_frozen_fixture(
    candles: np.ndarray,
    config_params: Dict[str, Any],
    name: str = "default",
    output_dir: str = "fixtures",
    check_bars: Optional[list] = None,
) -> str:
    """Generate a frozen fixture from current code and save to disk.

    Parameters
    ----------
    candles : np.ndarray
        Candle data to freeze.
    config_params : Dict
        Raw params dict (as used by canonicalizer).
    name : str
        Fixture name.
    output_dir : str
        Output directory.
    check_bars : list, optional
        Bar indices to store feature values for. Default: [60, 70, 80, 90].

    Returns
    -------
    str
        Path to the generated fixture directory.
    """
    from pmm_lab.features.pmm_dynamic_features import compute_pmm_dynamic_features, PMMDynamicConfig
    from pmm_lab.data.hashing import hash_candles
    from datetime import datetime, timezone

    if check_bars is None:
        check_bars = [60, 70, 80, 90]

    out = Path(output_dir) / name
    out.mkdir(parents=True, exist_ok=True)

    # Save candles as .npy
    np.save(str(out / "candles.npy"), candles)

    # Compute features with current code
    feat_config = PMMDynamicConfig(
        macd_fast=config_params.get("macd_fast", 21),
        macd_slow=config_params.get("macd_slow", 42),
        macd_signal=config_params.get("macd_signal", 9),
        natr_length=config_params.get("natr_length", 14),
    )
    features = compute_pmm_dynamic_features(candles, feat_config)

    # Extract spot-check values
    expected_features = {}
    for bar in check_bars:
        if bar < len(features.reference_price):
            expected_features[str(bar)] = {
                "reference_price": float(features.reference_price[bar]),
                "spread_multiplier": float(features.spread_multiplier[bar]),
                "natr": float(features.natr[bar]),
                "macd_signal_z": float(features.macd_signal_z[bar]),
                "price_multiplier": float(features.price_multiplier[bar]),
            }

    # Build expected YAML fields
    from pmm_lab.optuna.canonicalizer import canonicalize_params
    from pmm_lab.config.params import PairRules, FeeConfig
    from pmm_lab.export.hb_yaml import sim_config_to_hb_dict

    rules = PairRules(
        price_tick=0.01, amount_step=0.00001, min_notional_quote=1.0,
        fees=FeeConfig(0.001, 0.002),
    )
    ref_price = float(np.median(candles["close"]))
    config, reject = canonicalize_params(config_params, rules, ref_price)

    expected_yaml = {}
    if config is not None:
        hb_dict = sim_config_to_hb_dict(config)
        # Store key fields
        for key in ["controller_name", "controller_type", "macd_fast", "macd_slow",
                     "macd_signal", "natr_length", "total_amount_quote",
                     "stop_loss", "take_profit"]:
            if key in hb_dict:
                expected_yaml[key] = hb_dict[key]

    # Metadata
    metadata = {
        "name": name,
        "created": datetime.now(timezone.utc).isoformat(),
        "n_bars": len(candles),
        "dataset_hash": hash_candles(candles),
        "warmup_end": int(features.warmup_end),
        "config_params": config_params,
    }

    # Save JSON
    fixture_data = {
        "expected_features": expected_features,
        "expected_yaml_fields": expected_yaml,
        "metadata": metadata,
    }
    with open(out / "fixture.json", "w") as f:
        json.dump(fixture_data, f, indent=2, default=str)

    logger.info("Frozen fixture saved to %s", out)
    return str(out)


def _load_candles_any(p: Path, stem: str) -> Optional[np.ndarray]:
    """Load a candle array from {stem}.npy or {stem}.npz (supports both)."""
    npy = p / f"{stem}.npy"
    if npy.exists():
        return np.load(str(npy), allow_pickle=False)
    npz = p / f"{stem}.npz"
    if npz.exists():
        arch = np.load(str(npz), allow_pickle=False)
        # Archive may have a "candles" key (directional fixture convention) or
        # a single unnamed array (legacy).
        if "candles" in arch.files:
            return arch["candles"]
        # Fallback: first array
        return arch[arch.files[0]]
    return None


def load_frozen_fixture(fixture_dir: str) -> FrozenFixture:
    """Load a frozen fixture from disk.

    Supports two layouts:
    - Legacy PMM fixture: candles.npy + fixture.json
    - Directional (MR/EMA) fixture: candles.npz + expected_features.json +
      config_params.json [+ regime_candles.npz for EMA]

    Parameters
    ----------
    fixture_dir : str
        Path to the fixture directory.

    Returns
    -------
    FrozenFixture
    """
    p = Path(fixture_dir)
    candles = _load_candles_any(p, "candles")
    if candles is None:
        raise FileNotFoundError(f"No candles file in {fixture_dir}")
    regime_candles = _load_candles_any(p, "regime_candles")

    # Directional layout: separate JSON files
    expected_path = p / "expected_features.json"
    params_path = p / "config_params.json"
    legacy_fixture = p / "fixture.json"

    if expected_path.exists() and params_path.exists():
        with open(expected_path, "r", encoding="utf-8") as f:
            expected_features = json.load(f)
        with open(params_path, "r", encoding="utf-8") as f:
            config_params = json.load(f)
        name = p.name
        metadata = {
            "name": name,
            "n_bars": len(candles),
            "config_params": config_params,
        }
        return FrozenFixture(
            name=name,
            candles=candles,
            config_params=config_params,
            expected_features=expected_features,
            expected_yaml_fields={},
            metadata=metadata,
            regime_candles=regime_candles,
        )

    # Legacy layout
    with open(legacy_fixture, "r", encoding="utf-8") as f:
        data = json.load(f)

    return FrozenFixture(
        name=data["metadata"]["name"],
        candles=candles,
        config_params=data["metadata"]["config_params"],
        expected_features=data["expected_features"],
        expected_yaml_fields=data["expected_yaml_fields"],
        metadata=data["metadata"],
        regime_candles=regime_candles,
    )
