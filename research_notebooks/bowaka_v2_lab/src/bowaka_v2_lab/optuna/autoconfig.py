"""Auto-select the market-data feed for a walk-forward Optuna run (notebook 10).

:func:`resolve_walkforward_config` probes the shared market-data lake and adapts
a base walk-forward config so the study runs on the best data available:

    SIP bars + SIP quotes  -> feed=sip, simulation.mode=intended_realism
    SIP bars, no SIP quotes-> feed=sip, simulation.mode=current_code_parity
    IEX bars               -> feed=iex, simulation.mode=current_code_parity
    neither                -> simulation.mode=smoke_fixture (synthetic data)

The simulation mode is coupled to the feed so the resolved config is always
executable: ``intended_realism`` only when the lake can satisfy its quote /
coverage gates; ``current_code_parity`` (zero-spread quote fallback, not
quote-gated) for any real feed; ``smoke_fixture`` when there is no lake data.
"""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from ..config.loader import load_config

# autoconfig.py -> optuna -> bowaka_v2_lab -> src -> bowaka_v2_lab(lab) ->
# research_notebooks -> quants-lab (repo root)
_REPO_ROOT = Path(__file__).resolve().parents[5]
_VALID_FEED_OVERRIDES = ("auto", "sip", "iex", "synthetic")


@dataclass
class ResolvedWalkforwardConfig:
    """Outcome of :func:`resolve_walkforward_config`."""

    path: Path         # adapted config file, ready for run_walkforward_study
    feed: str          # "sip" | "iex"
    mode: str          # intended_realism | current_code_parity | smoke_fixture
    allow_smoke: bool  # True iff mode == smoke_fixture
    reason: str        # human-readable explanation of the choice


def resolve_lake_root(shared_root: Optional[str] = None) -> Path:
    """Resolve the market-data lake root: explicit > ``$MARKET_DATA_ROOT`` > in-repo."""
    if shared_root:
        return Path(shared_root)
    env = os.environ.get("MARKET_DATA_ROOT")
    if env:
        return Path(env)
    return _REPO_ROOT / "research_notebooks" / "market_data"


def lake_has_bars(lake_root: Path, feed: str) -> bool:
    """True when the lake has at least one daily-bar symbol for ``feed``."""
    try:
        from bowaka_common.marketdata import available_symbols

        return bool(available_symbols(str(lake_root), timeframe="1d", feed=feed))
    except Exception:  # noqa: BLE001 — a probe failure means "feed not available"
        return False


def lake_has_quotes(lake_root: Path, feed: str) -> bool:
    """True when the lake has at least one quotes partition for ``feed``."""
    quotes = Path(lake_root) / "quotes"
    if not quotes.is_dir():
        return False
    try:
        return any(quotes.glob(f"vendor=*/feed={feed}/**/*.parquet"))
    except OSError:
        return False


def detect_best_feed(lake_root: Path) -> tuple[str, str, str]:
    """Return ``(feed, simulation_mode, reason)`` for the best data the lake holds."""
    if lake_has_bars(lake_root, "sip"):
        if lake_has_quotes(lake_root, "sip"):
            return (
                "sip",
                "intended_realism",
                "SIP bars and SIP quotes present — full intended_realism run",
            )
        return (
            "sip",
            "current_code_parity",
            "SIP bars present but no SIP quotes — current_code_parity "
            "(zero-spread quote fallback)",
        )
    if lake_has_bars(lake_root, "iex"):
        return (
            "iex",
            "current_code_parity",
            "no SIP data; IEX bars present — current_code_parity on IEX "
            "(reproduces the live IEX paper strategy; IEX is partial-tape)",
        )
    return (
        "iex",
        "smoke_fixture",
        "no SIP or IEX lake data — smoke_fixture (deterministic synthetic data)",
    )


def _feed_for_override(override: str, lake_root: Path) -> tuple[str, str, str]:
    """Resolve ``(feed, mode, reason)`` for an explicit override or ``auto``."""
    if override == "auto":
        return detect_best_feed(lake_root)
    if override == "synthetic":
        return ("iex", "smoke_fixture", "feed override = synthetic — smoke_fixture")
    if override == "sip":
        if lake_has_quotes(lake_root, "sip"):
            return ("sip", "intended_realism", "feed override = sip (SIP quotes present)")
        return (
            "sip",
            "current_code_parity",
            "feed override = sip (no SIP quotes — current_code_parity)",
        )
    if override == "iex":
        return ("iex", "current_code_parity", "feed override = iex")
    raise ValueError(
        f"feed override {override!r} invalid; expected one of {_VALID_FEED_OVERRIDES}"
    )


def resolve_walkforward_config(
    base_config_path: str | Path,
    *,
    feed_override: str = "auto",
    lake_root: Optional[str] = None,
    out_path: str | Path | None = None,
) -> ResolvedWalkforwardConfig:
    """Adapt a base walk-forward config's feed + ``simulation.mode`` to the lake.

    ``feed_override``: ``auto`` (SIP > IEX > synthetic), or ``sip`` / ``iex`` /
    ``synthetic`` to force a choice. The adapted config is written to a temp file
    (or ``out_path``) and returned ready for :func:`run_walkforward_study`.
    """
    if feed_override not in _VALID_FEED_OVERRIDES:
        raise ValueError(
            f"feed_override={feed_override!r} invalid; "
            f"expected one of {_VALID_FEED_OVERRIDES}"
        )
    cfg = dict(load_config(base_config_path))
    cfg.pop("_source_path", None)
    md = dict(cfg.get("market_data", {}) or {})
    root = resolve_lake_root(lake_root or md.get("shared_root"))
    feed, mode, reason = _feed_for_override(feed_override, root)

    md["feed"] = feed
    cfg["market_data"] = md
    cfg["simulation"] = {**(cfg.get("simulation") or {}), "mode": mode}

    if out_path is not None:
        dest = Path(out_path)
    else:
        dest = Path(tempfile.mkdtemp(prefix="bowaka_wf_autocfg_")) / "walkforward_resolved.yml"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    return ResolvedWalkforwardConfig(
        path=dest,
        feed=feed,
        mode=mode,
        allow_smoke=(mode == "smoke_fixture"),
        reason=reason,
    )


__all__ = [
    "ResolvedWalkforwardConfig",
    "resolve_lake_root",
    "lake_has_bars",
    "lake_has_quotes",
    "detect_best_feed",
    "resolve_walkforward_config",
]
