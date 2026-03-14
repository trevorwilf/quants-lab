"""Tests for seed_everything and environment snapshot."""

import json
import os
import random

import numpy as np
import pytest

from pmm_lab.utils.reproducibility import (
    seed_everything,
    get_environment_snapshot,
    save_environment_snapshot,
    compute_snapshot_hash,
)


# ── seed_everything tests ────────────────────────────────────────


class TestSeedEverythingPythonRandom:
    def test_seed_everything_sets_python_random(self):
        seed_everything(42)
        r1 = random.random()
        seed_everything(42)
        r2 = random.random()
        assert r1 == r2


class TestSeedEverythingNumpyRandom:
    def test_seed_everything_sets_numpy_random(self):
        seed_everything(42)
        n1 = np.random.rand()
        seed_everything(42)
        n2 = np.random.rand()
        assert n1 == n2


class TestSeedEverythingThreadVars:
    def test_seed_everything_sets_thread_vars(self):
        # Remove if present so seed_everything sets them
        for var in ["OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
            os.environ.pop(var, None)
        seed_everything(42)
        assert os.environ.get("OMP_NUM_THREADS") == "1"
        assert os.environ.get("MKL_NUM_THREADS") == "1"
        assert os.environ.get("OPENBLAS_NUM_THREADS") == "1"
        assert os.environ.get("NUMEXPR_NUM_THREADS") == "1"


class TestSeedEverythingDifferentSeeds:
    def test_seed_everything_different_seeds_different_results(self):
        seed_everything(42)
        r42 = random.random()
        seed_everything(99)
        r99 = random.random()
        assert r42 != r99


class TestSeedEverythingIdempotent:
    def test_seed_everything_idempotent(self):
        seed_everything(42)
        r1 = random.random()
        n1 = np.random.rand()

        seed_everything(42)
        seed_everything(42)
        r2 = random.random()
        n2 = np.random.rand()

        assert r1 == r2
        assert n1 == n2


# ── Environment snapshot tests ───────────────────────────────────


class TestSnapshotRequiredKeys:
    def test_get_environment_snapshot_has_required_keys(self):
        snap = get_environment_snapshot()
        for key in ("timestamp", "python_version", "key_packages", "all_packages", "environment_variables"):
            assert key in snap, f"Missing key: {key}"


class TestSnapshotKeyPackagesNumpy:
    def test_snapshot_key_packages_includes_numpy(self):
        snap = get_environment_snapshot()
        assert "numpy" in snap["key_packages"]
        assert snap["key_packages"]["numpy"] != "not installed"


class TestSnapshotKeyPackagesPmmLab:
    def test_snapshot_key_packages_includes_pmm_lab(self):
        snap = get_environment_snapshot()
        assert "pmm_lab" in snap["key_packages"]


class TestSaveSnapshotCreatesFile:
    def test_save_environment_snapshot_creates_file(self, tmp_path):
        path = str(tmp_path / "snap.json")
        save_environment_snapshot(path, seed=42)
        assert os.path.exists(path)


class TestSaveSnapshotValidJson:
    def test_save_environment_snapshot_valid_json(self, tmp_path):
        path = str(tmp_path / "snap.json")
        save_environment_snapshot(path, seed=42)
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert "timestamp" in data


class TestSnapshotWithSeed:
    def test_snapshot_with_seed(self, tmp_path):
        path = str(tmp_path / "snap.json")
        save_environment_snapshot(path, seed=123)
        with open(path) as f:
            data = json.load(f)
        assert data["seed"] == 123


class TestSnapshotRedactsSensitiveVars:
    def test_snapshot_redacts_sensitive_vars(self):
        # Temporarily set sensitive vars
        old_mongo = os.environ.get("MONGO_URI")
        old_optuna = os.environ.get("OPTUNA_STORAGE")
        os.environ["MONGO_URI"] = "mongodb://secret:password@host/db"
        os.environ["OPTUNA_STORAGE"] = "postgresql://secret@host/db"
        try:
            snap = get_environment_snapshot()
            assert snap["environment_variables"]["MONGO_URI"] == "SET (redacted)"
            assert snap["environment_variables"]["OPTUNA_STORAGE"] == "SET (redacted)"
        finally:
            if old_mongo is None:
                os.environ.pop("MONGO_URI", None)
            else:
                os.environ["MONGO_URI"] = old_mongo
            if old_optuna is None:
                os.environ.pop("OPTUNA_STORAGE", None)
            else:
                os.environ["OPTUNA_STORAGE"] = old_optuna


class TestSnapshotHashDeterministic:
    def test_compute_snapshot_hash_deterministic(self):
        snap = get_environment_snapshot(seed=42)
        h1 = compute_snapshot_hash(snap)
        h2 = compute_snapshot_hash(snap)
        assert h1 == h2
        assert len(h1) == 16


class TestSnapshotHashChangesWithVersion:
    def test_compute_snapshot_hash_changes_with_version(self):
        snap1 = get_environment_snapshot()
        h1 = compute_snapshot_hash(snap1)

        snap2 = get_environment_snapshot()
        snap2["key_packages"]["numpy"] = "999.999.999"
        h2 = compute_snapshot_hash(snap2)

        assert h1 != h2
