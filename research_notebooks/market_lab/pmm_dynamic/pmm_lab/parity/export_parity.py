"""
Export parity checker.

Validates that exported YAML files can be loaded by native Hummingbot
config models when available.
"""

import yaml
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from pmm_lab.export.validate_export import ValidationResult, validate_yaml_file

logger = logging.getLogger(__name__)


def validate_export_comprehensive(
    yaml_path: str,
    expected_fields: Optional[Dict[str, Any]] = None,
) -> ValidationResult:
    """Comprehensive export validation.

    1. Run mirror validation (always)
    2. Attempt native Hummingbot validation (if installed)
    3. Check expected field values from frozen fixture (if provided)

    Parameters
    ----------
    yaml_path : str
        Path to the YAML file.
    expected_fields : Dict, optional
        Expected field values to verify (from frozen fixture).

    Returns
    -------
    ValidationResult
    """
    # Step 1: mirror validation
    mirror_result = validate_yaml_file(yaml_path)

    if not mirror_result.valid:
        return mirror_result

    errors = list(mirror_result.errors)
    warnings = list(mirror_result.warnings)
    mode = mirror_result.mode

    # Step 2: native validation (if available)
    from pmm_lab.parity import HAS_HUMMINGBOT
    if HAS_HUMMINGBOT:
        try:
            with open(yaml_path, "r") as f:
                config_dict = yaml.safe_load(f)
            from controllers.market_making.pmm_dynamic import PMMDynamicControllerConfig
            PMMDynamicControllerConfig(**config_dict)
            mode = "native"
            logger.info("Native Hummingbot validation: PASSED")
        except Exception as e:
            errors.append(f"Native Hummingbot validation failed: {e}")
            mode = "native_failed"

    # Step 3: expected field check
    if expected_fields and mirror_result.valid:
        with open(yaml_path, "r") as f:
            config_dict = yaml.safe_load(f)

        for key, expected_val in expected_fields.items():
            actual_val = config_dict.get(key)
            if actual_val is None:
                warnings.append(f"Expected field '{key}' not found in YAML")
            elif isinstance(expected_val, float):
                if abs(actual_val - expected_val) > 1e-6:
                    errors.append(
                        f"Field '{key}': expected {expected_val}, got {actual_val}"
                    )
            elif actual_val != expected_val:
                errors.append(
                    f"Field '{key}': expected {expected_val}, got {actual_val}"
                )

    return ValidationResult(
        valid=len(errors) == 0,
        mode=mode,
        errors=errors,
        warnings=warnings,
    )
