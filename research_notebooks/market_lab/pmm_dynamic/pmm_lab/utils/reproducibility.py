"""
Reproducibility utilities.

Provides:
- seed_everything(seed): locks all known randomness sources
- get_environment_snapshot(): captures Python/package versions and env vars
- save_environment_snapshot(path): writes snapshot to JSON

Usage in notebooks:
    from pmm_lab.utils.reproducibility import seed_everything, save_environment_snapshot
    seed_everything(42)
    save_environment_snapshot("artifacts/env_snapshot.json")
"""

import os
import sys
import json
import random
import hashlib
import platform
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

import numpy as np

logger = logging.getLogger(__name__)


def seed_everything(seed: int = 42) -> None:
    """Lock all known randomness sources for reproducible results.

    Sets:
    - Python's random module
    - NumPy's global RNG (legacy) and default_rng seed memo
    - PYTHONHASHSEED (if not already set — can only take effect before Python starts)
    - OMP_NUM_THREADS, MKL_NUM_THREADS, OPENBLAS_NUM_THREADS, NUMEXPR_NUM_THREADS = 1
      (forces single-threaded BLAS to avoid nondeterministic reduction order)

    Parameters
    ----------
    seed : int
        Master seed. All sub-seeds are derived from this.

    Notes
    -----
    For full determinism:
    - Call this BEFORE any imports that trigger NumPy/BLAS initialization
    - Set PYTHONHASHSEED=<seed> as an environment variable BEFORE starting Python
    - Use n_jobs=1 in Optuna for deterministic trial ordering
    """
    # Python stdlib random
    random.seed(seed)

    # NumPy legacy global RNG
    np.random.seed(seed)

    # Environment variables for single-threaded BLAS
    # These must be set before BLAS libraries are loaded, but setting them
    # here is still useful as documentation and for late-loaded libraries.
    thread_vars = {
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
    }
    for var, val in thread_vars.items():
        if var not in os.environ:
            os.environ[var] = val

    # PYTHONHASHSEED — warn if not set (can only take effect at Python startup)
    current_hash_seed = os.environ.get("PYTHONHASHSEED")
    if current_hash_seed is None:
        os.environ["PYTHONHASHSEED"] = str(seed)
        logger.info(
            "Set PYTHONHASHSEED=%d (note: only effective if set before Python starts)",
            seed,
        )
    elif current_hash_seed != str(seed):
        logger.warning(
            "PYTHONHASHSEED is '%s' but seed_everything was called with seed=%d. "
            "For full determinism, set PYTHONHASHSEED=%d before starting Python.",
            current_hash_seed, seed, seed,
        )

    logger.info("seed_everything(%d): all randomness sources locked", seed)


def get_environment_snapshot(seed: Optional[int] = None) -> Dict[str, Any]:
    """Capture a snapshot of the current environment for reproducibility auditing.

    Includes:
    - Python version
    - Platform info
    - Key package versions (numpy, pandas, optuna, pandas_ta, etc.)
    - All installed packages (pip freeze equivalent)
    - Relevant environment variables
    - Timestamp
    - Optional seed

    Returns
    -------
    Dict[str, Any]
        Snapshot dict suitable for JSON serialization.
    """
    # Key packages
    key_packages = {}
    for pkg_name in ["numpy", "pandas", "optuna", "pandas_ta", "pymongo", "pyyaml",
                      "psycopg2", "scipy", "pmm_lab"]:
        try:
            mod = __import__(pkg_name.replace("-", "_"))
            key_packages[pkg_name] = getattr(mod, "__version__", "unknown")
        except ImportError:
            key_packages[pkg_name] = "not installed"

    # All installed packages
    all_packages = {}
    try:
        import importlib.metadata
        for dist in importlib.metadata.distributions():
            all_packages[dist.metadata["Name"]] = dist.version
    except Exception:
        all_packages = {"error": "could not enumerate installed packages"}

    # Environment variables
    env_vars = {}
    for var in ["PYTHONHASHSEED", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                "MONGO_URI", "OPTUNA_STORAGE", "CUDA_VISIBLE_DEVICES"]:
        val = os.environ.get(var)
        if val is not None:
            # Redact sensitive values
            if var in ("MONGO_URI", "OPTUNA_STORAGE"):
                env_vars[var] = "SET (redacted)"
            else:
                env_vars[var] = val
        else:
            env_vars[var] = "NOT SET"

    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "seed": seed,
        "key_packages": key_packages,
        "all_packages": all_packages,
        "environment_variables": env_vars,
    }

    return snapshot


def save_environment_snapshot(
    path: str,
    seed: Optional[int] = None,
) -> str:
    """Save an environment snapshot to a JSON file.

    Parameters
    ----------
    path : str
        Output file path.
    seed : int, optional
        The seed used for this run (included in snapshot).

    Returns
    -------
    str
        The path written.
    """
    from pathlib import Path
    snapshot = get_environment_snapshot(seed=seed)

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out, "w") as f:
        json.dump(snapshot, f, indent=2, default=str)

    logger.info("Environment snapshot saved to %s", path)
    return str(out)


def compute_snapshot_hash(snapshot: Dict[str, Any]) -> str:
    """Compute a hash of the key reproducibility fields in a snapshot.

    This can be used to quickly check if two environments are equivalent
    for the packages that matter.
    """
    key_str = json.dumps(snapshot.get("key_packages", {}), sort_keys=True)
    key_str += snapshot.get("python_version", "")
    return hashlib.sha256(key_str.encode()).hexdigest()[:16]
