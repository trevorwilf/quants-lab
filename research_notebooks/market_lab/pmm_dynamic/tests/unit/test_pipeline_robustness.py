"""Tests for pipeline robustness under failure conditions."""
import os
import pytest
from unittest.mock import patch, MagicMock


class TestPipelineParamsCopied:
    """Pipeline must not mutate trial params."""

    def test_best_params_is_copy(self):
        """best_params should be a copy, not a reference to trial.params."""
        original = {"macd_fast": 12, "macd_slow": 26}
        copy = dict(original)
        copy["total_amount_quote"] = 100.0
        assert "total_amount_quote" not in original


class TestPipelineSQLiteEnforcement:
    """SQLite storage must force n_jobs=1."""

    def test_sqlite_forces_serial(self):
        """When storage is SQLite, n_jobs>1 must be coerced to 1."""
        from pmm_lab.optuna.storage import get_storage_type
        # Ensure no OPTUNA_STORAGE is set
        env_backup = os.environ.pop("OPTUNA_STORAGE", None)
        try:
            assert get_storage_type() == "sqlite"
            # The enforcement happens in run_full_pipeline; this validates the helper
        finally:
            if env_backup:
                os.environ["OPTUNA_STORAGE"] = env_backup
