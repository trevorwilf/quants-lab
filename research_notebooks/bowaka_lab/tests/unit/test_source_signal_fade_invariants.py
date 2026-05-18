"""Phase fidelity-6: exact-mode source-fade invariants."""

from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_lab.config import assert_exact_mode_invariants, load_config_file


EXACT_YAML = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "bowaka_exact_current_strategy.yml"
)


@pytest.fixture(autouse=True)
def _stub_env(monkeypatch):
    monkeypatch.setenv("MONGO_URI", "mongodb://stub:stub@localhost:27017/db?authSource=admin")


def test_exact_profile_loads_with_source_signal_fade():
    cfg = load_config_file(EXACT_YAML)
    assert cfg.source_signal_fade is not None
    assert cfg.source_signal_fade.enabled is False
    assert "soft" in cfg.source_signal_fade.score_thresholds
    assert "hard" in cfg.source_signal_fade.exit_on or "critical" in cfg.source_signal_fade.exit_on


def test_exact_invariants_require_source_signal_fade():
    cfg = load_config_file(EXACT_YAML)
    bad = cfg.model_copy(update={"source_signal_fade": None})
    with pytest.raises(ValueError, match="source_signal_fade must be configured"):
        assert_exact_mode_invariants(bad)


def test_exact_invariants_block_enabled_source_signal_fade():
    cfg = load_config_file(EXACT_YAML)
    bad = cfg.model_copy(update={
        "source_signal_fade": cfg.source_signal_fade.model_copy(update={"enabled": True}),
    })
    with pytest.raises(ValueError, match="source_signal_fade.enabled must be false"):
        assert_exact_mode_invariants(bad)
