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

import copy
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

import yaml

from ..config.loader import load_config

# autoconfig.py -> optuna -> bowaka_v2_lab -> src -> bowaka_v2_lab(lab) ->
# research_notebooks -> quants-lab (repo root)
_REPO_ROOT = Path(__file__).resolve().parents[5]
_VALID_FEED_OVERRIDES = ("auto", "sip", "iex", "synthetic")
#: Simulation modes a caller may pin via ``resolve_walkforward_config(mode_override=...)``
#: when the feed-derived mode is infeasible (e.g. SIP+quotes auto-picks
#: intended_realism but the lake lacks halt data -> pin current_code_parity).
_VALID_MODE_OVERRIDES = (
    "intended_realism",
    "current_code_parity",
    "fast_realism",
    "smoke_fixture",
)


@dataclass
class ResolvedWalkforwardConfig:
    """Outcome of :func:`resolve_walkforward_config`."""

    path: Path         # adapted config file, ready for run_walkforward_study
    feed: str          # "sip" | "iex"
    mode: str          # intended_realism | current_code_parity | smoke_fixture
    allow_smoke: bool  # True iff mode == smoke_fixture
    reason: str        # human-readable explanation of the choice
    # Realism remediation 2 Phase 8 (audit §P0-011): notebook 10's autoconfig
    # picks current_code_parity when the lake has IEX bars / SIP bars without
    # quotes; Optuna refuses that mode without an explicit opt-in. These two
    # flags surface the auto-pick's intent to ``run_walkforward_study`` so the
    # notebook does not have to manually thread them. ``tier`` is always
    # ``research_only`` for an auto-picked current_code_parity (the mechanical
    # cap from :mod:`promotion.suitability`); explicitly None for other modes.
    allow_current_code_parity_study: bool = False
    tier: Optional[str] = None


def resolve_lake_root(shared_root: Optional[str] = None) -> Path:
    """Resolve the market-data lake root: explicit > ``$MARKET_DATA_ROOT`` > in-repo."""
    if shared_root:
        return Path(shared_root)
    env = os.environ.get("MARKET_DATA_ROOT")
    if env:
        return Path(env)
    return _REPO_ROOT / "research_notebooks" / "market_data"


def _lake_has_daily_partition(lake_root: Path, feed: str, adjustment: str) -> bool:
    """True when the lake has >=1 daily-bar symbol for ``(feed, adjustment)``."""
    try:
        from bowaka_common.marketdata import available_symbols

        return bool(
            available_symbols(
                str(lake_root), timeframe="1d", feed=feed, adjustment=adjustment
            )
        )
    except Exception:  # noqa: BLE001 — a probe failure means "not available"
        return False


def lake_has_bars(lake_root: Path, feed: str) -> bool:
    """True when the lake has at least one daily-bar symbol for ``feed`` under any
    backfilled adjustment.

    Checks legacy ``raw`` AND ``split_adjusted`` (the current backfill default —
    the bowaka_v2 actual-IEX/SIP config requires split-adjusted bars). A fresh
    feed (e.g. a first SIP backfill, which writes ONLY ``split_adjusted``) would
    be invisible to a raw-only probe, so ``feed='auto'`` would never cut over to
    SIP even with SIP bars+quotes present. Mirrors ``probe_lake_capability``,
    which already checks ``raw`` OR the required adjustment.
    """
    return (
        _lake_has_daily_partition(lake_root, feed, "raw")
        or _lake_has_daily_partition(lake_root, feed, "split_adjusted")
    )


@dataclass(frozen=True)
class LakeCapability:
    """Structured lake-capability probe (audit 2026-05-29 §A.1 / Phase 1).

    Replaces the bare ``lake_has_bars`` bool so callers can see not just
    *whether* bars exist but whether the daily partition for the adjustment
    the config REQUIRES exists. ``__bool__`` returns ``has_bars`` so existing
    truthy callers (``if lake_has_bars(...)``) keep working when migrated.
    """

    feed: str
    required_adjustment: str
    has_bars: bool
    has_required_daily_adjustment: bool
    has_quotes: bool

    def __bool__(self) -> bool:
        return self.has_bars


def probe_lake_capability(
    lake_root: Path, feed: str, *, required_adjustment: str = "raw",
) -> LakeCapability:
    """Probe the lake for ``feed`` bars + the ``required_adjustment`` daily
    partition + quotes. ``has_required_daily_adjustment`` is the gate the
    full-fold preflight uses to refuse a study whose config requires
    split-adjusted bars the lake does not hold."""
    has_bars = (
        _lake_has_daily_partition(lake_root, feed, "raw")
        or _lake_has_daily_partition(lake_root, feed, required_adjustment)
    )
    has_required = _lake_has_daily_partition(lake_root, feed, required_adjustment)
    return LakeCapability(
        feed=feed,
        required_adjustment=required_adjustment,
        has_bars=bool(has_bars),
        has_required_daily_adjustment=bool(has_required),
        has_quotes=lake_has_quotes(lake_root, feed),
    )


def lake_has_quotes(lake_root: Path, feed: str) -> bool:
    """True when the lake has at least one quotes partition for ``feed``."""
    # Hotfix 2026-05-29: resolve defensively so a None / empty upstream value
    # cannot become Path('None') and false-positive the directory check.
    root = resolve_lake_root(lake_root) if lake_root else resolve_lake_root(None)
    quotes = root / "quotes"
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
    mode_override: Optional[str] = None,
    lake_root: Optional[str] = None,
    out_path: str | Path | None = None,
) -> ResolvedWalkforwardConfig:
    """Adapt a base walk-forward config's feed + ``simulation.mode`` to the lake.

    ``feed_override``: ``auto`` (SIP > IEX > synthetic), or ``sip`` / ``iex`` /
    ``synthetic`` to force a choice. The adapted config is written to a temp file
    (or ``out_path``) and returned ready for :func:`run_walkforward_study`.

    ``mode_override``: pin ``simulation.mode`` regardless of the feed-derived
    mode. The auto/sip resolution couples mode to the lake (SIP-with-quotes ->
    ``intended_realism``); but IR can still be INFEASIBLE on a lake that has
    quotes yet lacks halt/LULD data (the IR halt gate fail-closes). Passing
    ``mode_override="current_code_parity"`` keeps the lake-detected feed (sip,
    so the matrix + suppliers resolve) while running the feasible parity mode.
    The returned opt-in flags (``allow_current_code_parity_study`` / ``tier`` /
    ``allow_smoke``) are derived from the EFFECTIVE mode, so the override threads
    through to :func:`run_walkforward_study` correctly.
    """
    if feed_override not in _VALID_FEED_OVERRIDES:
        raise ValueError(
            f"feed_override={feed_override!r} invalid; "
            f"expected one of {_VALID_FEED_OVERRIDES}"
        )
    if mode_override is not None and mode_override not in _VALID_MODE_OVERRIDES:
        raise ValueError(
            f"mode_override={mode_override!r} invalid; "
            f"expected one of {_VALID_MODE_OVERRIDES} or None"
        )
    cfg = dict(load_config(base_config_path))
    cfg.pop("_source_path", None)
    md = dict(cfg.get("market_data", {}) or {})
    root = resolve_lake_root(lake_root or md.get("shared_root"))
    feed, mode, reason = _feed_for_override(feed_override, root)
    if mode_override is not None and mode_override != mode:
        reason = f"{reason}; mode_override={mode_override} (was {mode})"
        mode = mode_override

    md["feed"] = feed
    cfg["market_data"] = md
    cfg["simulation"] = {**(cfg.get("simulation") or {}), "mode": mode}

    if out_path is not None:
        dest = Path(out_path)
    else:
        # Audit 2026-05-29 §8.1 / Phase 3 — persist the resolved config under the
        # lab's artifacts (durable lineage), not volatile /tmp. Falls back to a
        # temp dir only when the config declares no artifact_root.
        _artifact_root = ((cfg.get("paths") or {}).get("artifact_root"))
        if _artifact_root:
            dest = Path(_artifact_root) / "resolved_configs" / "walkforward_resolved.yml"
        else:
            dest = (
                Path(tempfile.mkdtemp(prefix="bowaka_wf_autocfg_"))
                / "walkforward_resolved.yml"
            )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    return ResolvedWalkforwardConfig(
        path=dest,
        feed=feed,
        mode=mode,
        allow_smoke=(mode == "smoke_fixture"),
        reason=reason,
        # Realism remediation 2 Phase 8 — auto-opt-in for current_code_parity
        # so notebook 10 doesn't have to manually pass the flag when the lake
        # forces parity mode (IEX-only / SIP-bars-no-quotes). The mechanical
        # cap remains research_only.
        allow_current_code_parity_study=(mode == "current_code_parity"),
        tier=("research_only"
              if mode in ("current_code_parity", "fast_realism") else None),
    )


def derive_validation_config(
    search_config: "str | Path | Mapping[str, Any]",
    *,
    validation_mode: str = "intended_realism",
    out_path: "Optional[str | Path]" = None,
) -> dict:
    """§10i Path 3 — derive the finalist-VALIDATION config from a fast_realism SEARCH config.

    Path 4 + Path 3 pipeline: the SEARCH stage runs a fast Optuna study under
    ``fast_realism`` (honest participation/depth fills, non-blocking); the top-N
    finalists are then re-scored under ``intended_realism`` (real NBBO required,
    fail-closed coverage/quote gates) — the honest deploy gate. The two configs are
    IDENTICAL (same strategy, universe, window, search space) except
    ``simulation.mode`` and the four mode-coupled policy fields, which are dropped
    so the config validator re-resolves them from ``validation_mode`` (e.g.
    ``quote_fallback_policy`` zero_spread -> require_real; ``unknown_instrument_class
    _policy`` fail_open -> fail_closed). Optionally written to ``out_path`` (YAML).

    Usage::

        run_walkforward_study(search_cfg_path)                      # fast_realism search
        derive_validation_config(search_cfg_path, out_path="val.yml")
        # then `evaluate-finalists` / `score-final-holdout` against val.yml (intended_realism)
    """
    if isinstance(search_config, Mapping):
        cfg = copy.deepcopy(dict(search_config))
    else:
        cfg = load_config(search_config)
    # §10i — KEEP _source_path (points at the search config) so the per-fold
    # config-parity gate finds the search config's parity sidecar (the
    # halt_gate.enabled override etc.). It is stripped from any written YAML below.
    sim = dict(cfg.get("simulation") or {})
    sim["mode"] = str(validation_mode)
    # Drop the mode-coupled policy fields so they re-resolve from validation_mode.
    # A fast_realism search config leaves them mode-resolved (unset in YAML); any
    # explicit override is intentionally NOT carried across the mode switch.
    for _field in (
        "intraday_window_policy", "accepted_event_sequencing",
        "unknown_instrument_class_policy", "quote_fallback_policy",
    ):
        sim.pop(_field, None)
    cfg["simulation"] = sim
    if out_path is not None:
        _to_write = {k: v for k, v in cfg.items() if k != "_source_path"}
        Path(out_path).write_text(yaml.safe_dump(_to_write, sort_keys=False), encoding="utf-8")
    return cfg


__all__ = [
    "ResolvedWalkforwardConfig",
    "LakeCapability",
    "resolve_lake_root",
    "lake_has_bars",
    "probe_lake_capability",
    "lake_has_quotes",
    "detect_best_feed",
    "resolve_walkforward_config",
    "derive_validation_config",
]
