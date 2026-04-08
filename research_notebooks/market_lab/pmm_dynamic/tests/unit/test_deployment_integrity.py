"""Tests for deployment integrity verification (Priority 4)."""

import os
import yaml
import pytest
from pathlib import Path

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.export.hb_yaml import export_yaml, ExportParams
from pmm_lab.deploy.integrity import verify_deployment_integrity


def _make_sim_config():
    return SimConfig(
        buy_spreads=[1.0, 2.0],
        sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5],
        sell_amounts_pct=[0.5, 0.5],
        buy_side_weight=0.5,
        total_amount_quote=100.0,
        executor_refresh_time=3120,
        cooldown_time=3120,
        stop_loss=0.03,
        take_profit=0.015,
        time_limit=43200,
        macd_fast=21,
        macd_slow=42,
        macd_signal=9,
        natr_length=14,
    )


class TestExportIncludesHash:
    """Export should include yaml_sha256 in metadata."""

    def test_hash_in_metadata(self, tmp_path):
        config = _make_sim_config()
        yaml_path = str(tmp_path / "test_config.yml")
        metadata = {"objective_score": 0.5}

        export_yaml(config, yaml_path, metadata=metadata)

        meta_path = tmp_path / "test_config.meta.yml"
        assert meta_path.exists()

        with open(meta_path) as f:
            meta = yaml.safe_load(f)

        assert "yaml_sha256" in meta
        assert isinstance(meta["yaml_sha256"], str)
        assert len(meta["yaml_sha256"]) == 64  # SHA-256 hex digest length

    def test_exported_at_in_metadata(self, tmp_path):
        config = _make_sim_config()
        yaml_path = str(tmp_path / "test_config.yml")
        metadata = {"objective_score": 0.5}

        export_yaml(config, yaml_path, metadata=metadata)

        meta_path = tmp_path / "test_config.meta.yml"
        with open(meta_path) as f:
            meta = yaml.safe_load(f)

        assert "exported_at" in meta
        assert "simulator_version" in meta


class TestIntegrityCheckPassesUnmodified:
    """Integrity check should pass on unmodified exports."""

    def test_passes_unmodified(self, tmp_path):
        config = _make_sim_config()
        yaml_path = str(tmp_path / "test_config.yml")
        metadata = {"objective_score": 0.5}

        export_yaml(config, yaml_path, metadata=metadata)

        matches, diffs = verify_deployment_integrity(yaml_path)
        assert matches is True
        assert len(diffs) == 0


class TestIntegrityCheckFailsOnModification:
    """Integrity check should fail when YAML is modified after export."""

    def test_fails_on_param_change(self, tmp_path):
        config = _make_sim_config()
        yaml_path = str(tmp_path / "test_config.yml")
        metadata = {"objective_score": 0.5}

        export_yaml(config, yaml_path, metadata=metadata)

        # Modify the YAML
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        data["stop_loss"] = 0.99
        with open(yaml_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=True)

        matches, diffs = verify_deployment_integrity(yaml_path)
        assert matches is False
        assert len(diffs) > 0
        assert "mismatch" in diffs[0].lower()

    def test_detects_use_wallet_balance_addition(self, tmp_path):
        """Adding use_wallet_balance manually should be detected."""
        config = _make_sim_config()
        yaml_path = str(tmp_path / "test_config.yml")
        metadata = {"objective_score": 0.5}

        export_yaml(config, yaml_path, metadata=metadata)

        # Add use_wallet_balance
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        data["use_wallet_balance"] = True
        with open(yaml_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=True)

        matches, diffs = verify_deployment_integrity(yaml_path)
        assert matches is False


class TestIntegrityMissingFiles:
    """Edge cases with missing files."""

    def test_missing_yaml(self, tmp_path):
        matches, diffs = verify_deployment_integrity(str(tmp_path / "nonexistent.yml"))
        assert matches is False
        assert "not found" in diffs[0].lower()

    def test_missing_meta(self, tmp_path):
        # Create a YAML but no meta
        yaml_path = tmp_path / "test.yml"
        yaml_path.write_text("stop_loss: 0.03\n")

        matches, diffs = verify_deployment_integrity(str(yaml_path))
        assert matches is False
        assert "not found" in diffs[0].lower() or "does not contain" in diffs[0].lower()
