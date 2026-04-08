"""Deployment integrity verification.

Verifies that exported YAML files have not been modified since export
by comparing SHA-256 hashes stored in the metadata file.
"""

import hashlib
import yaml
from pathlib import Path
from typing import List, Tuple


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_deployment_integrity(
    yaml_path: str,
    meta_path: str = None,
) -> Tuple[bool, List[str]]:
    """Verify that a deployed YAML matches its metadata hash.

    Parameters
    ----------
    yaml_path : str
        Path to the exported YAML config file.
    meta_path : str, optional
        Path to the .meta.yml file. Defaults to yaml_path with .meta.yml suffix.

    Returns
    -------
    (bool, List[str])
        (matches, list_of_diffs). matches is True if hash matches.
    """
    yaml_p = Path(yaml_path)
    if meta_path is None:
        meta_p = yaml_p.with_suffix(".meta.yml")
    else:
        meta_p = Path(meta_path)

    diffs: List[str] = []

    if not yaml_p.exists():
        diffs.append(f"YAML file not found: {yaml_p}")
        return False, diffs

    if not meta_p.exists():
        diffs.append(f"Metadata file not found: {meta_p}")
        return False, diffs

    with open(meta_p, "r") as f:
        meta = yaml.safe_load(f)

    if meta is None or "yaml_sha256" not in meta:
        diffs.append("Metadata file does not contain yaml_sha256")
        return False, diffs

    expected_hash = meta["yaml_sha256"]
    actual_hash = _sha256_file(yaml_p)

    if actual_hash != expected_hash:
        diffs.append(
            f"SHA-256 mismatch: expected {expected_hash[:16]}..., "
            f"got {actual_hash[:16]}..."
        )
        return False, diffs

    return True, []
