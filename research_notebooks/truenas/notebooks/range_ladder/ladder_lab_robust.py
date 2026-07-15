"""
ladder_lab_robust.py -- rolling 60d/15d generative ladder optimizer
=====================================================================

This module extends the existing `ladder_lab.py` shared engine without replacing it.
It keeps the original exchange adapters, cache, screener, fill simulator, depth checks,
min-quantity checks, hourly realism checks, and output helpers, then adds a leakage-safe
candidate generator and walk-forward workflow for roughly 180 days of history.

Primary additions
-----------------
* Generative rung placement families: percent-distance, volatility-scaled, and
  train-window quantile placement.
* Rung-count search: configurable buy/sell rung ranges, default 4-12 per side.
* Rolling walk-forward: train on the previous 60 days, freeze the generated ladder,
  test the next 15 days, then step forward by 15 days.
* Robust score: lower-quartile fold score minus fold variability, with penalties for
  drawdown, downside equity moves, inventory imbalance, one-sided fills, low trade
  count, and degradation under conservative fill assumptions.
* 45-day and 60-day block summaries so the same 15-day folds can be reviewed as
  pseudo-quarters or four-consecutive-holdout robustness blocks.
* Deploy config generation from the most recent 60-day training window.

The module intentionally uses the same `sim()` kernel from ladder_lab.py for every
train/test/final/stress path to avoid optimizer/backtest drift.
"""
from __future__ import annotations

import copy
import hashlib
import math
import os
import time
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

import ladder_lab as _base
from ladder_lab import *  # re-export the base engine API for notebook compatibility

__version__ = "2.4.9-robust-60x15-artifacts-copy-md-always-review"

# Explicit aliases used below. Keeping these names local makes the source easier to audit.
_base_default_config = _base.default_config


# ======================================================================
# Always-review market helpers
# ======================================================================
DEFAULT_ALWAYS_REVIEW_MARKETS = ("XMR/USDT", "XMR/USD", "SAL/USDT")


def _review_pair_key(value: Any) -> str:
    """Normalize BASE/QUOTE, BASE-QUOTE, or BASE_QUOTE to uppercase BASE/QUOTE."""
    s = str(value or "").strip().upper().replace("-", "/").replace("_", "/")
    parts = [p.strip() for p in s.split("/") if p.strip()]
    return "/".join(parts)


def merge_unique_markets(*market_lists: Optional[Sequence[Any]]) -> List[str]:
    """Merge market lists while de-duplicating slash/dash/underscore variants."""
    out: List[str] = []
    seen: set = set()
    for market_list in market_lists:
        for m in market_list or []:
            key = _review_pair_key(m)
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(key)
    return out


def normalize_market_list(markets: Optional[Sequence[Any]] = None) -> List[str]:
    """Normalize a market list to unique uppercase BASE/QUOTE values."""
    return merge_unique_markets(markets or [])


def _universe_pair_lookup(uni: Dict[str, Any]) -> Dict[str, str]:
    try:
        pairkeys = list(uni.get("df", pd.DataFrame()).pairkey)
    except Exception:
        pairkeys = []
    return {_review_pair_key(pk): str(pk) for pk in pairkeys}


def resolve_present_markets(uni: Dict[str, Any], requested: Sequence[Any]) -> Tuple[List[str], List[str]]:
    """Return (present, missing) requested markets using the active exchange universe."""
    lookup = _universe_pair_lookup(uni)
    present: List[str] = []
    missing: List[str] = []
    for key in merge_unique_markets(requested):
        pk = lookup.get(key)
        if pk is None:
            missing.append(key)
        else:
            present.append(pk)
    return merge_unique_markets(present), merge_unique_markets(missing)




def configured_always_review_markets(cfg: Optional[Dict[str, Any]] = None, extra: Optional[Sequence[Any]] = None) -> List[str]:
    """Return configured always-review markets in normalized BASE/QUOTE form."""
    cfg = cfg or {}
    return merge_unique_markets(cfg.get("always_review_markets", DEFAULT_ALWAYS_REVIEW_MARKETS), extra or [])

def market_presence_status(
    uni: Dict[str, Any],
    requested: Optional[Sequence[Any]],
    hist: Optional[Dict[str, Any]] = None,
) -> Dict[str, List[str]]:
    """Report whether requested markets are listed and whether history was loaded."""
    req = merge_unique_markets(DEFAULT_ALWAYS_REVIEW_MARKETS if requested is None else requested)
    present, missing = resolve_present_markets(uni, req)
    if hist is None:
        present_history: List[str] = []
        missing_history: List[str] = []
    else:
        present_history = [pk for pk in present if pk in hist]
        missing_history = [pk for pk in present if pk not in hist]
    return dict(
        requested=req,
        present_universe=present,
        missing_universe=missing,
        present_history=merge_unique_markets(present_history),
        missing_history=merge_unique_markets(missing_history),
    )


def force_review_candidates(
    candidates: Sequence[str],
    uni: Dict[str, Any],
    hist: Optional[Dict[str, Any]] = None,
    always_review_markets: Optional[Sequence[Any]] = None,
    focus_markets: Optional[Sequence[Any]] = None,
    focus_only: bool = False,
    require_history: bool = False,
) -> Dict[str, List[str]]:
    """Force always-review markets into the robust-search candidate set before WF."""
    requested = merge_unique_markets(always_review_markets or DEFAULT_ALWAYS_REVIEW_MARKETS, focus_markets or [])
    present, missing = resolve_present_markets(uni, requested)
    forced: List[str] = []
    no_history: List[str] = []
    for pk in present:
        if require_history and hist is not None and pk not in hist:
            no_history.append(pk)
        else:
            forced.append(pk)
    base = [] if focus_only else list(candidates or [])
    return dict(
        candidates=merge_unique_markets(forced if focus_only else base + forced),
        forced=merge_unique_markets(forced),
        present=merge_unique_markets(present),
        requested=merge_unique_markets(requested),
        missing=merge_unique_markets(missing),
        no_history=merge_unique_markets(no_history),
    )


def build_candidate_review_sets(
    uni: Dict[str, Any],
    base_candidates: Sequence[Any],
    always_review_markets: Optional[Sequence[Any]] = None,
    focus_markets: Optional[Sequence[Any]] = None,
    focus_only: bool = False,
) -> Dict[str, List[str]]:
    """Resolve robust-search candidates and final-review watch lists."""
    present_always, missing_always = resolve_present_markets(uni, always_review_markets or DEFAULT_ALWAYS_REVIEW_MARKETS)
    present_focus, missing_focus = resolve_present_markets(uni, focus_markets or [])
    forced_review = merge_unique_markets(present_always, present_focus)
    candidates = forced_review if focus_only else merge_unique_markets(base_candidates, forced_review)
    return dict(
        candidates=candidates,
        forced_review=forced_review,
        present_always=present_always,
        missing_always=missing_always,
        present_focus=present_focus,
        missing_focus=missing_focus,
    )


def _rebuild_universe_from_df(uni: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
    """Rebuild universe lookup dictionaries after preserving always-review rows."""
    out = dict(uni)
    df = df.copy().drop_duplicates("pairkey").reset_index(drop=True)
    out["df"] = df
    if "pairkey" in df.columns:
        pairs = list(df.pairkey)
        if "quote" in df.columns:
            out["quote_of"] = dict(zip(pairs, df.quote))
        if "coin" in df.columns:
            out["base_of"] = dict(zip(pairs, df.coin))
        if "last" in df.columns:
            out["last_of"] = dict(zip(pairs, df["last"]))
        if "min_qty" in df.columns:
            out["min_qty"] = dict(zip(pairs, df.min_qty))
        if "pdec" in df.columns:
            out["pdec"] = dict(zip(pairs, df.pdec))
    return out


def _filter_universe_preserve_always(uni: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Apply min_vol/max_scan while preserving always-review markets when listed."""
    df = uni.get("df", pd.DataFrame()).copy()
    if df.empty or "pairkey" not in df.columns:
        return uni
    vol_floor = float(cfg.get("min_vol_usd", 0.0) or 0.0)
    normal = df[df.vol_usd.fillna(0) >= vol_floor].copy() if "vol_usd" in df.columns else df.copy()
    if "vol_usd" in normal.columns:
        normal = normal.sort_values("vol_usd", ascending=False)
    max_scan = cfg.get("max_scan")
    if max_scan:
        normal = normal.head(int(max_scan)).copy()
    always_present, _ = resolve_present_markets({"df": df}, cfg.get("always_review_markets", DEFAULT_ALWAYS_REVIEW_MARKETS))
    always_rows = df[df.pairkey.isin(always_present)].copy()
    combined = pd.concat([normal, always_rows], ignore_index=True).drop_duplicates("pairkey")
    return _rebuild_universe_from_df(uni, combined)


def nonkyc_universe(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """NonKYC universe wrapper that preserves always-review markets after caps."""
    full_cfg = dict(cfg or {})
    full_cfg["max_scan"] = None
    full_cfg["min_vol_usd"] = 0.0
    uni = _base.nonkyc_universe(full_cfg)
    return _filter_universe_preserve_always(uni, cfg or {})


def kraken_universe(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Kraken universe wrapper that preserves always-review markets after caps."""
    full_cfg = dict(cfg or {})
    full_cfg["max_scan"] = None
    full_cfg["min_vol_usd"] = 0.0
    uni = _base.kraken_universe(full_cfg)
    return _filter_universe_preserve_always(uni, cfg or {})


def select_robust_review_markets(
    ev: pd.DataFrame,
    uni: Dict[str, Any],
    cfg: Dict[str, Any],
    always_review_markets: Optional[Sequence[Any]] = None,
    focus_markets: Optional[Sequence[Any]] = None,
    hist: Optional[Dict[str, Any]] = None,
    focus_only: bool = False,
) -> Dict[str, List[str]]:
    """Build robust-search candidates plus forced final-review markets.

    The in-sample screener remains only a tractability filter. Markets in
    `always_review_markets` are appended after the normal candidate cap and are
    finalized/reported when they exist on the exchange. If `hist` is supplied,
    requested markets without history are reported separately.
    """
    if ev is None or not isinstance(ev, pd.DataFrame) or ev.empty:
        base_candidates: List[str] = []
    else:
        viable = ev.copy()
        if "stale" in viable.columns:
            viable = viable[~viable["stale"].fillna(False)]
        if "tier" in viable.columns:
            viable = viable[viable["tier"] == "full"]
        top_composite = list(viable.sort_values("composite", ascending=False).head(int(cfg.get("wf_top_n", 40))).base) if "composite" in viable.columns and "base" in viable.columns else []
        top_activity = list(viable.sort_values("trades_mo", ascending=False).head(min(20, len(viable))).base) if "trades_mo" in viable.columns and "base" in viable.columns else []
        old_qualifiers = list(viable[viable["qualifies"] == True].base) if "qualifies" in viable.columns and "base" in viable.columns else []
        positive_diagnostic = list(viable[viable["p12"] > 0].head(min(20, len(viable))).base) if "p12" in viable.columns and "base" in viable.columns else []
        base_candidates = merge_unique_markets(top_composite + top_activity + old_qualifiers + positive_diagnostic)
        if cfg.get("wf_max_candidates"):
            base_candidates = base_candidates[:int(cfg.get("wf_max_candidates"))]

    always_requested = configured_always_review_markets(cfg, extra=always_review_markets)
    focus_requested = normalize_market_list(focus_markets or cfg.get("optional_focus_markets", ()))
    sets = build_candidate_review_sets(
        uni=uni,
        base_candidates=base_candidates,
        always_review_markets=always_requested,
        focus_markets=focus_requested,
        hist=hist,
        focus_only=focus_only,
    )
    return dict(
        candidates=sets["candidates"],
        base_candidates=base_candidates,
        forced_review=sets["forced_review"],
        always_requested=always_requested,
        always_present=sets["present_always"],
        always_missing=sets["missing_always"],
        always_present_with_history=sets["with_history_always"],
        always_missing_history=sets["missing_history_always"],
        focus_requested=focus_requested,
        focus_present=sets["present_focus"],
        focus_missing=sets["missing_focus"],
        focus_present_with_history=sets["with_history_focus"],
        focus_missing_history=sets["missing_history_focus"],
    )



def artifact_files_dir(
    exchange: str,
    run_datetime: Optional[str] = None,
    root: str = "artifacts",
    timezone: str = "America/Boise",
) -> str:
    """Return/create artifacts/{exchange}/{datetime}/files.

    `run_datetime` is deterministic if supplied. Otherwise LADDER_RUN_DATETIME is
    respected; if that is not set, a local timestamp is created using `timezone`.
    The returned value is a string so notebooks can use it directly in path joins.
    """
    from pathlib import Path
    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(timezone)
    except Exception:
        tz = None
    if run_datetime is None:
        run_datetime = os.environ.get("LADDER_RUN_DATETIME")
    if not run_datetime:
        now = datetime.now(tz) if tz else datetime.now()
        run_datetime = now.strftime("%Y%m%d-%H%M%S")
    path = Path(root) / str(exchange).lower() / str(run_datetime) / "files"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def artifact_prefix(
    exchange: str,
    basename: str,
    run_datetime: Optional[str] = None,
    root: str = "artifacts",
    timezone: str = "America/Boise",
) -> str:
    """Return a file prefix inside artifacts/{exchange}/{datetime}/files."""
    from pathlib import Path
    return str(Path(artifact_files_dir(exchange, run_datetime, root, timezone)) / basename)


def make_artifact_run_dir(
    exchange: str,
    root: Optional[str] = None,
    timestamp: Optional[str] = None,
    subdir: Optional[str] = None,
) -> "Path":
    """Backward-compatible notebook helper returning artifacts/{exchange}/{datetime}/files as a Path."""
    from pathlib import Path
    from datetime import datetime
    root = root or "artifacts"
    subdir = subdir or "files"
    if timestamp is None:
        timestamp = os.environ.get("LADDER_RUN_DATETIME") or os.environ.get("LADDER_RUN_TIMESTAMP")
    if not timestamp:
        try:
            from zoneinfo import ZoneInfo
            now = datetime.now(ZoneInfo("America/Boise"))
        except Exception:
            now = datetime.now()
        timestamp = now.strftime("%Y%m%d-%H%M%S")
    path = Path(root) / str(exchange).lower() / str(timestamp) / str(subdir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def robust_default_config(exchange: str) -> Dict[str, Any]:
    """Return a config dict for the rolling 60d/15d generative optimizer.

    The values are conservative defaults. The notebooks expose the most important
    knobs near the top so they can be tuned per exchange or per universe size.
    """
    cfg = _base_default_config(exchange)
    cfg.update(dict(
        # Work with about 180 days by default. If the exchange/proxy has more data,
        # the rolling 60+15 validation still slices only by timestamps.
        years=0.55,                  # ~201 days fetch/request budget
        min_days=75,                 # need one 60d train + one 15d test to do anything
        full_days=150,               # 180d histories are considered mature for this workflow
        months=2,                    # placement lookback fallback if needed

        # Rolling walk-forward: previous 60d train, next 15d OOS, step 15d.
        gen_train_days=60,
        gen_test_days=15,
        gen_step_days=15,
        gen_min_train_days=54,       # tolerate modest gaps
        gen_min_test_days=10,
        gen_max_folds=None,          # None = every available 60+15 fold
        gen_min_folds=4,

        # Block summaries over the same 15d OOS folds.
        pseudo_quarter_days=45,      # 3 x 15d blocks = 45d pseudo-quarter
        robustness_block_days=60,    # 4 x 15d blocks = four consecutive holdouts

        # Generative candidate search.
        gen_seed=20260707,
        always_review_markets=DEFAULT_ALWAYS_REVIEW_MARKETS,
        focus_markets=(),
        finalize_gated_top_n=8,
        gen_n_candidates=360,        # stage-1 random/structured candidates per fit
        gen_stage2_top_k=18,         # candidates receiving train-window weight optimization
        gen_n_buy_range=(4, 12),
        gen_n_sell_range=(4, 12),
        gen_families=("pct", "volatility", "quantile"),
        gen_spacing_curves=("linear", "geometric", "front_loaded", "back_loaded"),
        gen_weight_curves=("equal", "near", "mild_near", "slight_deep"),
        gen_weight_optimizer="shape",    # shape | equal | none. shape is robust 1-dof/side.

        # Distance constraints, in percent from the train-window anchor.
        gen_inner_pct_range=(0.6, 3.0),
        gen_outer_pct_range=(4.0, 24.0),
        gen_min_outer_inner_ratio=2.0,
        gen_min_cycle_edge_pct=None,      # None => max(1.0%, 2.5x round-trip fee)
        gen_max_outer_pct=35.0,

        # Volatility-scaled family multipliers.
        gen_vol_inner_mult_range=(0.45, 1.50),
        gen_vol_outer_mult_range=(3.0, 10.0),
        gen_vol_floor_pct=0.35,
        gen_vol_cap_pct=30.0,

        # Quantile family percentile ranges.
        gen_quantile_inner_range=(35.0, 65.0),
        gen_quantile_outer_range=(78.0, 97.0),
        gen_quantile_jitter=(0.85, 1.20),
        gen_max_inner_pct=8.0,       # cap nearest rung distance for frequent-small-trade style

        # Frequent-small-trade preference and deployment safety.
        target_trades_per_15d=8,
        min_train_trades=6,
        min_train_two_sided=True,
        max_single_rung_weight_pct=18.0,
        preferred_max_rungs_per_side=10,  # soft penalty; optimizer may exceed it if robust
        hard_max_active_orders=24,        # buy+rung + sell+rung max per market

        # Robust objective weights. Units are percentage points.
        score_drawdown_w=0.75,
        score_downside_w=0.35,
        score_inventory_w=0.08,
        score_balance_w=1.50,
        score_one_sided_penalty=12.0,
        score_zero_usage_penalty=8.0,
        score_low_trade_penalty=2.25,
        score_stress_degrade_w=0.55,
        score_negative_stress_w=0.35,
        score_trade_bonus=1.25,
        score_usage_bonus=0.75,
        score_rung_count_w=0.15,
        score_std_penalty=0.50,
        score_instability_penalty=0.20,

        # OOS acceptance gates.
        gen_min_pos_rate=0.625,
        gen_min_two_sided_rate=0.625,
        gen_min_median_score=0.0,
        gen_min_median_cons_pct=-1.0,
        gen_max_bad_fold_loss_pct=-8.0,

        # Conservative stress. Use measured spread in finalize; use slip_floor in folds.
        max_fills_per_bar=1,
        rearm_cooldown=1,
        slip_floor=0.001,
        body_only=False,

        # Deployment fit: train the live config on the most recent 60 days.
        deploy_train_days=60,
        deploy_eval_days=180,
        deploy_refit_on_full_history=False,
    ))
    # Existing default_config has older 91d/270d WF fields. Keep them for backward
    # compatibility, but make any old workflow less likely to run accidentally.
    cfg.update(dict(
        wf_folds=0,
        wf_test_days=15,
        wf_min_train_days=60,
        n_buy=8,
        n_sell=8,
        n_side=8,
        spacing="geom",
        weight_mode="shape",
    ))
    return cfg


def _stable_int(*parts: Any) -> int:
    txt = "|".join(str(p) for p in parts)
    return int(hashlib.sha256(txt.encode("utf-8")).hexdigest()[:8], 16)


def _rng_for(cfg: Dict[str, Any], label: str, fold_idx: int = 0, salt: str = "") -> np.random.Generator:
    seed = int(cfg.get("gen_seed", 0)) + _stable_int(label, fold_idx, salt)
    return np.random.default_rng(seed % (2 ** 32 - 1))


def _pct_distance_grid(inner: float, outer: float, n: int, curve: str) -> np.ndarray:
    inner = float(max(inner, 1e-9))
    outer = float(max(outer, inner + 1e-9))
    n = int(n)
    if n <= 0:
        return np.array([], dtype=float)
    if n == 1:
        return np.array([inner], dtype=float)
    x = np.linspace(0.0, 1.0, n)
    if curve == "geometric" and inner > 0 and outer > 0:
        d = inner * (outer / inner) ** x
    elif curve == "front_loaded":
        # More rungs close to the anchor; useful for frequent smaller trades.
        d = inner + (outer - inner) * (x ** 1.65)
    elif curve == "back_loaded":
        # More spacing close to the anchor, more density near the outer edge.
        d = inner + (outer - inner) * (1.0 - (1.0 - x) ** 1.65)
    else:
        d = inner + (outer - inner) * x
    return np.asarray(d, dtype=float)


def _weights_for_curve(n: int, curve: str, max_single_pct: float) -> np.ndarray:
    n = int(n)
    if n <= 0:
        return np.array([], dtype=float)
    if curve == "near":
        k = 1.35
        w = np.exp(-k * np.linspace(0, 1, n))
    elif curve == "mild_near":
        k = 0.65
        w = np.exp(-k * np.linspace(0, 1, n))
    elif curve == "slight_deep":
        k = 0.45
        w = np.exp(k * np.linspace(0, 1, n))
    else:
        w = np.ones(n)
    w = np.maximum(w.astype(float), 1e-9)
    w = _cap_weight_share(w, max_single_pct)
    return w


def _cap_weight_share(w: Sequence[float], max_single_pct: float, passes: int = 20) -> np.ndarray:
    """Flatten a raw weight vector until no rung exceeds max_single_pct of side budget."""
    arr = np.asarray(w, dtype=float)
    if len(arr) == 0:
        return arr
    arr = np.maximum(arr, 1e-12)
    max_share = float(max_single_pct) / 100.0
    if max_share <= 0:
        return np.ones_like(arr)
    min_possible = 1.0 / len(arr)
    max_share = max(max_share, min_possible)
    for _ in range(passes):
        shares = arr / arr.sum()
        if shares.max() <= max_share + 1e-12:
            break
        cap_abs = max_share * arr.sum()
        over = arr > cap_abs
        excess = float(np.sum(arr[over] - cap_abs))
        arr[over] = cap_abs
        if excess <= 0 or (~over).sum() == 0:
            break
        arr[~over] += excess / (~over).sum()
    return arr


def _anchor_price(bars: np.ndarray, cfg: Dict[str, Any], label: str = "") -> float:
    try:
        return float(_base.compute_anchor(bars, cfg, label=label, quiet=True))
    except Exception:
        return float(_base.closes(bars)[-1])


def _train_vol_pct(bars: np.ndarray) -> float:
    bars = np.asarray(bars, dtype=float)
    if len(bars) < 5:
        return 1.0
    ohlc = bars[:, -4:]
    o, h, l, c = ohlc[:, 0], ohlc[:, 1], ohlc[:, 2], ohlc[:, 3]
    prev_c = np.roll(c, 1)
    prev_c[0] = o[0]
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    denom = np.where(prev_c > 0, prev_c, c)
    tr_pct = tr / np.where(denom > 0, denom, 1.0) * 100.0
    med_tr = float(np.nanmedian(tr_pct[-min(len(tr_pct), 60):]))
    ret_vol = float(np.nanstd(np.diff(np.log(np.maximum(c, 1e-12)))) * 100.0)
    val = np.nanmedian([med_tr, ret_vol * 1.5])
    if not np.isfinite(val) or val <= 0:
        val = 1.0
    return float(val)


def _quantile_distances(bars: np.ndarray, anchor: float, cfg: Dict[str, Any], rng: np.random.Generator) -> Tuple[float, float, float, float]:
    ohlc = np.asarray(bars, dtype=float)[:, -4:]
    highs = ohlc[:, 1]
    lows = ohlc[:, 2]
    if anchor <= 0:
        anchor = float(ohlc[-1, 3])
    down = np.maximum(0.0, (anchor - lows) / anchor * 100.0)
    up = np.maximum(0.0, (highs - anchor) / anchor * 100.0)
    down = down[down > 0]
    up = up[up > 0]
    if len(down) < 5 or len(up) < 5:
        # Fall back to percent distances if the window is too flat or too short.
        inner_lo, inner_hi = cfg["gen_inner_pct_range"]
        outer_lo, outer_hi = cfg["gen_outer_pct_range"]
        bi = rng.uniform(inner_lo, inner_hi)
        si = rng.uniform(inner_lo, inner_hi)
        bo = rng.uniform(max(outer_lo, bi * cfg["gen_min_outer_inner_ratio"]), outer_hi)
        so = rng.uniform(max(outer_lo, si * cfg["gen_min_outer_inner_ratio"]), outer_hi)
        return bi, bo, si, so
    qi = rng.uniform(*cfg["gen_quantile_inner_range"])
    qo = rng.uniform(max(qi + 5.0, cfg["gen_quantile_outer_range"][0]), cfg["gen_quantile_outer_range"][1])
    jit_lo, jit_hi = cfg["gen_quantile_jitter"]
    bi = float(np.percentile(down, qi) * rng.uniform(jit_lo, jit_hi))
    bo = float(np.percentile(down, qo) * rng.uniform(jit_lo, jit_hi))
    si = float(np.percentile(up, qi) * rng.uniform(jit_lo, jit_hi))
    so = float(np.percentile(up, qo) * rng.uniform(jit_lo, jit_hi))
    return bi, bo, si, so


def _sanitize_distances(bi: float, bo: float, si: float, so: float, cfg: Dict[str, Any]) -> Tuple[float, float, float, float]:
    min_cycle = cfg.get("gen_min_cycle_edge_pct")
    if min_cycle is None:
        min_cycle = max(1.0, 2.5 * _base._rt_fee_pct(cfg))
    inner_floor = max(float(cfg["gen_inner_pct_range"][0]), float(min_cycle) / 2.0)
    outer_floor = float(cfg["gen_outer_pct_range"][0])
    outer_cap = float(cfg.get("gen_max_outer_pct", cfg["gen_outer_pct_range"][1]))
    ratio = float(cfg.get("gen_min_outer_inner_ratio", 2.0))
    inner_cap = cfg.get("gen_max_inner_pct")

    bi = max(float(bi), inner_floor)
    si = max(float(si), inner_floor)
    if inner_cap is not None:
        cap = max(float(inner_cap), inner_floor)
        bi = min(bi, cap)
        si = min(si, cap)
    # If the two nearest rungs do not clear the desired cycle edge, widen them symmetrically.
    if bi + si < min_cycle:
        extra = (min_cycle - bi - si) / 2.0
        bi += extra
        si += extra
    bo = max(float(bo), bi * ratio, outer_floor)
    so = max(float(so), si * ratio, outer_floor)
    bo = min(bo, outer_cap)
    so = min(so, outer_cap)
    if bo <= bi:
        bo = min(outer_cap, bi * ratio + 0.25)
    if so <= si:
        so = min(outer_cap, si * ratio + 0.25)
    return bi, bo, si, so


def _make_candidate_from_distances(
    anchor: float,
    n_buy: int,
    n_sell: int,
    bi: float,
    bo: float,
    si: float,
    so: float,
    spacing: str,
    weight_curve: str,
    family: str,
    cfg: Dict[str, Any],
    pdec: Optional[int] = None,
    serial: int = 0,
) -> Optional[Dict[str, Any]]:
    if anchor <= 0 or n_buy <= 0 or n_sell <= 0:
        return None
    if n_buy + n_sell > int(cfg.get("hard_max_active_orders", 10 ** 9)):
        return None
    bi, bo, si, so = _sanitize_distances(bi, bo, si, so, cfg)
    bd = _pct_distance_grid(bi, bo, n_buy, spacing)
    sd = _pct_distance_grid(si, so, n_sell, spacing)
    buys = [float(_base.round_price(anchor * (1.0 - d / 100.0), pdec)) for d in bd]
    sells = [float(_base.round_price(anchor * (1.0 + d / 100.0), pdec)) for d in sd]
    # Remove duplicates caused by coarse price decimals. Preserve nearest->deep ordering.
    buys = list(dict.fromkeys([p for p in buys if p > 0 and p < anchor]))
    sells = list(dict.fromkeys([p for p in sells if p > anchor]))
    if len(buys) < 2 or len(sells) < 2:
        return None
    bw = _weights_for_curve(len(buys), weight_curve, cfg["max_single_rung_weight_pct"])
    sw = _weights_for_curve(len(sells), weight_curve, cfg["max_single_rung_weight_pct"])
    cand = dict(
        candidate_id=f"{family}-{serial:04d}-{len(buys)}x{len(sells)}-{spacing}-{weight_curve}",
        family=family,
        spacing_curve=spacing,
        weight_curve=weight_curve,
        n_buy=len(buys),
        n_sell=len(sells),
        anchor=float(anchor),
        buy_inner_pct=float(bd[0]) if len(bd) else float("nan"),
        buy_outer_pct=float(bd[-1]) if len(bd) else float("nan"),
        sell_inner_pct=float(sd[0]) if len(sd) else float("nan"),
        sell_outer_pct=float(sd[-1]) if len(sd) else float("nan"),
        buy_prices=buys,
        sell_prices=sells,
        bw=np.asarray(bw, dtype=float),
        sw=np.asarray(sw, dtype=float),
    )
    return cand


def generate_ladder_candidates(
    train_bars: np.ndarray,
    cfg: Dict[str, Any],
    pdec: Optional[int] = None,
    label: str = "",
    fold_idx: int = 0,
    n_candidates: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Generate deterministic candidate ladder shapes from TRAIN data only."""
    n_candidates = int(n_candidates or cfg["gen_n_candidates"])
    rng = _rng_for(cfg, label, fold_idx, "candidates")
    anchor = _anchor_price(train_bars, cfg, label)
    vol_pct = _train_vol_pct(train_bars)
    candidates: List[Dict[str, Any]] = []
    seen: set = set()

    n_buy_lo, n_buy_hi = map(int, cfg["gen_n_buy_range"])
    n_sell_lo, n_sell_hi = map(int, cfg["gen_n_sell_range"])
    families = tuple(cfg["gen_families"])
    spacings = tuple(cfg["gen_spacing_curves"])
    weight_curves = tuple(cfg["gen_weight_curves"])

    # Deterministic rung-count spine: every count pair gets at least one simple candidate
    # where possible. The random candidates then explore distance/shape variations.
    serial = 0
    spine_pairs = [(nb, ns) for nb in range(n_buy_lo, n_buy_hi + 1)
                   for ns in range(n_sell_lo, n_sell_hi + 1)
                   if nb + ns <= int(cfg.get("hard_max_active_orders", 10 ** 9))]
    rng.shuffle(spine_pairs)
    for nb, ns in spine_pairs[:max(0, min(len(spine_pairs), n_candidates // 4))]:
        inner_mid = float(np.mean(cfg["gen_inner_pct_range"]))
        outer_mid = float(np.mean(cfg["gen_outer_pct_range"]))
        cand = _make_candidate_from_distances(anchor, nb, ns, inner_mid, outer_mid,
                                              inner_mid, outer_mid, "geometric", "equal",
                                              "pct", cfg, pdec, serial)
        serial += 1
        if cand is not None:
            key = (tuple(cand["buy_prices"]), tuple(cand["sell_prices"]), cand["weight_curve"])
            if key not in seen:
                seen.add(key)
                candidates.append(cand)

    while len(candidates) < n_candidates and serial < n_candidates * 4:
        family = str(rng.choice(families))
        spacing = str(rng.choice(spacings))
        weight_curve = str(rng.choice(weight_curves))
        nb = int(rng.integers(n_buy_lo, n_buy_hi + 1))
        ns = int(rng.integers(n_sell_lo, n_sell_hi + 1))
        if nb + ns > int(cfg.get("hard_max_active_orders", 10 ** 9)):
            serial += 1
            continue

        if family == "volatility":
            im_lo, im_hi = cfg["gen_vol_inner_mult_range"]
            om_lo, om_hi = cfg["gen_vol_outer_mult_range"]
            bi = vol_pct * float(rng.uniform(im_lo, im_hi))
            si = vol_pct * float(rng.uniform(im_lo, im_hi))
            bo = vol_pct * float(rng.uniform(max(om_lo, im_lo * 2.0), om_hi))
            so = vol_pct * float(rng.uniform(max(om_lo, im_lo * 2.0), om_hi))
            bi = float(np.clip(bi, cfg["gen_vol_floor_pct"], cfg["gen_vol_cap_pct"]))
            si = float(np.clip(si, cfg["gen_vol_floor_pct"], cfg["gen_vol_cap_pct"]))
            bo = float(np.clip(bo, cfg["gen_vol_floor_pct"] * 2.0, cfg["gen_vol_cap_pct"]))
            so = float(np.clip(so, cfg["gen_vol_floor_pct"] * 2.0, cfg["gen_vol_cap_pct"]))
        elif family == "quantile":
            bi, bo, si, so = _quantile_distances(train_bars, anchor, cfg, rng)
        else:
            inner_lo, inner_hi = cfg["gen_inner_pct_range"]
            outer_lo, outer_hi = cfg["gen_outer_pct_range"]
            bi = float(rng.uniform(inner_lo, inner_hi))
            si = float(rng.uniform(inner_lo, inner_hi))
            bo = float(rng.uniform(max(outer_lo, bi * cfg["gen_min_outer_inner_ratio"]), outer_hi))
            so = float(rng.uniform(max(outer_lo, si * cfg["gen_min_outer_inner_ratio"]), outer_hi))

        cand = _make_candidate_from_distances(anchor, nb, ns, bi, bo, si, so,
                                              spacing, weight_curve, family,
                                              cfg, pdec, serial)
        serial += 1
        if cand is None:
            continue
        key = (tuple(cand["buy_prices"]), tuple(cand["sell_prices"]), cand["weight_curve"])
        if key in seen:
            continue
        seen.add(key)
        candidates.append(cand)
    return candidates


def _equity_downside_pct(eq: Sequence[float]) -> float:
    eq = np.asarray(eq, dtype=float)
    if len(eq) < 3:
        return 0.0
    denom = np.where(eq[:-1] > 0, eq[:-1], 1.0)
    ret = np.diff(eq) / denom * 100.0
    neg = ret[ret < 0]
    if len(neg) == 0:
        return 0.0
    return float(np.std(neg))


def _rung_usage(result: Dict[str, Any]) -> float:
    bf = np.asarray(result.get("bf", []), dtype=float)
    sf = np.asarray(result.get("sf", []), dtype=float)
    total = len(bf) + len(sf)
    if total <= 0:
        return 0.0
    return float((np.sum(bf > 0) + np.sum(sf > 0)) / total)


def score_sim_result(
    result: Dict[str, Any],
    cfg: Dict[str, Any],
    days: float,
    stress_result: Optional[Dict[str, Any]] = None,
    n_buy: Optional[int] = None,
    n_sell: Optional[int] = None,
) -> float:
    """Robust objective for one train/test result.

    Positive values are good. The score intentionally rewards frequent smaller trades
    only up to a target, then lets drawdown, inventory, and stress robustness decide.
    """
    trades = int(result.get("trades", 0))
    if trades <= 0:
        return -100.0
    ret = float(result.get("pnl_pct", 0.0))
    drawdown = float(result.get("maxdd", 0.0))
    downside = _equity_downside_pct(result.get("eq", []))
    target_inv = (1.0 - float(cfg.get("quote_frac", 0.5))) * 100.0
    inv_pen = abs(float(result.get("endinv", target_inv)) - target_inv)
    buys = int(np.sum(result.get("bf", [])))
    sells = int(np.sum(result.get("sf", [])))
    balance_pen = abs(buys - sells) / max(trades, 1)

    target_trades = float(cfg.get("target_trades_per_15d", 8)) * max(float(days), 1.0) / 15.0
    low_trade_pen = max(0.0, target_trades - trades) / max(target_trades, 1.0)
    trade_bonus = min(trades / max(target_trades, 1.0), 1.0)
    usage_bonus = min(_rung_usage(result) / 0.70, 1.0)

    stress_degrade = 0.0
    negative_stress = 0.0
    if stress_result is not None:
        stress_pct = float(stress_result.get("pnl_pct", 0.0))
        stress_degrade = max(0.0, ret - stress_pct)
        negative_stress = max(0.0, -stress_pct)

    rung_pen = 0.0
    pref = int(cfg.get("preferred_max_rungs_per_side", 10))
    if n_buy is not None:
        rung_pen += max(0, int(n_buy) - pref)
    if n_sell is not None:
        rung_pen += max(0, int(n_sell) - pref)

    score = (
        ret
        - float(cfg["score_drawdown_w"]) * drawdown
        - float(cfg["score_downside_w"]) * downside
        - float(cfg["score_inventory_w"]) * inv_pen
        - float(cfg["score_balance_w"]) * balance_pen
        - float(cfg["score_low_trade_penalty"]) * low_trade_pen
        - float(cfg["score_stress_degrade_w"]) * stress_degrade
        - float(cfg["score_negative_stress_w"]) * negative_stress
        - float(cfg["score_rung_count_w"]) * rung_pen
        + float(cfg["score_trade_bonus"]) * trade_bonus
        + float(cfg["score_usage_bonus"]) * usage_bonus
    )
    return float(score)


def _stress_sim(bars: np.ndarray, cand: Dict[str, Any], cfg: Dict[str, Any], slip: Optional[float] = None) -> Dict[str, Any]:
    return _base.sim(
        bars,
        cand["buy_prices"],
        cand["sell_prices"],
        cand.get("bw"),
        cand.get("sw"),
        fund=cfg["fund_usd"],
        quote_frac=cfg["quote_frac"],
        fee=cfg["fee"],
        slip=float(cfg["slip_floor"] if slip is None else slip),
        max_fills_per_bar=cfg["max_fills_per_bar"],
        rearm_cooldown=cfg["rearm_cooldown"],
        body_only=cfg["body_only"],
    )


def _normal_sim(bars: np.ndarray, cand: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    return _base.sim(
        bars,
        cand["buy_prices"],
        cand["sell_prices"],
        cand.get("bw"),
        cand.get("sw"),
        fund=cfg["fund_usd"],
        quote_frac=cfg["quote_frac"],
        fee=cfg["fee"],
    )


def _refine_candidate_weights(train_bars: np.ndarray, cand: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    mode = str(cfg.get("gen_weight_optimizer", "shape"))
    out = copy.deepcopy(cand)
    if mode in ("", "none", "candidate"):
        return out, f"candidate-{cand.get('weight_curve', 'weights')}"
    if mode == "equal":
        out["bw"] = np.ones(len(out["buy_prices"]))
        out["sw"] = np.ones(len(out["sell_prices"]))
        return out, "equal"
    bw, sw, _r, meta = _base.optimize_weights(train_bars, out["buy_prices"], out["sell_prices"], cfg, mode=mode)
    out["bw"] = _cap_weight_share(bw, cfg["max_single_rung_weight_pct"])
    out["sw"] = _cap_weight_share(sw, cfg["max_single_rung_weight_pct"])
    out["weight_curve"] = f"optimized:{meta}"
    return out, str(meta)


def _candidate_record(cand: Dict[str, Any], result: Dict[str, Any], stress: Dict[str, Any], score: float, stage: str) -> Dict[str, Any]:
    return dict(
        candidate_id=cand["candidate_id"],
        stage=stage,
        family=cand["family"],
        spacing_curve=cand["spacing_curve"],
        weight_curve=cand["weight_curve"],
        n_buy=cand["n_buy"],
        n_sell=cand["n_sell"],
        anchor=cand["anchor"],
        buy_inner_pct=cand["buy_inner_pct"],
        buy_outer_pct=cand["buy_outer_pct"],
        sell_inner_pct=cand["sell_inner_pct"],
        sell_outer_pct=cand["sell_outer_pct"],
        score=score,
        pnl_pct=result["pnl_pct"],
        cons_pct=stress["pnl_pct"],
        maxdd=result["maxdd"],
        trades=result["trades"],
        buy_fills=int(np.sum(result["bf"])),
        sell_fills=int(np.sum(result["sf"])),
        endinv=result["endinv"],
        rung_usage=_rung_usage(result),
        buy_prices=list(cand["buy_prices"]),
        sell_prices=list(cand["sell_prices"]),
        buy_amounts_pct=_base.weights_pct(cand["bw"]),
        sell_amounts_pct=_base.weights_pct(cand["sw"]),
    )


def robust_ladder_search(
    train_bars: np.ndarray,
    cfg: Dict[str, Any],
    pdec: Optional[int] = None,
    label: str = "",
    fold_idx: int = 0,
    return_table: bool = False,
) -> Dict[str, Any]:
    """Fit a ladder on TRAIN data only.

    Stage 1 evaluates generated candidates with their simple candidate weights.
    Stage 2 refines the top K with the configured weight optimizer and rescoring.
    """
    train_bars = np.asarray(train_bars, dtype=float)
    train_days = max((train_bars[-1, 0] - train_bars[0, 0]) / 86400.0, 1.0)
    candidates = generate_ladder_candidates(train_bars, cfg, pdec, label, fold_idx)
    if not candidates:
        raise RuntimeError(f"{label}: no generated ladder candidates survived construction")

    rows: List[Dict[str, Any]] = []
    scored: List[Tuple[float, Dict[str, Any], Dict[str, Any], Dict[str, Any]]] = []
    for cand in candidates:
        r = _normal_sim(train_bars, cand, cfg)
        s = _stress_sim(train_bars, cand, cfg)
        score = score_sim_result(r, cfg, train_days, s, cand["n_buy"], cand["n_sell"])
        if cfg.get("min_train_two_sided", True) and (sum(r["bf"]) <= 0 or sum(r["sf"]) <= 0):
            score -= 5.0
        if r["trades"] < int(cfg.get("min_train_trades", 0)):
            score -= 4.0
        scored.append((score, cand, r, s))
        if return_table:
            rows.append(_candidate_record(cand, r, s, score, "stage1"))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_k = min(int(cfg["gen_stage2_top_k"]), len(scored))
    refined: List[Tuple[float, Dict[str, Any], Dict[str, Any], Dict[str, Any], str]] = []
    for _score, cand, _r, _s in scored[:top_k]:
        rcand, wmeta = _refine_candidate_weights(train_bars, cand, cfg)
        r = _normal_sim(train_bars, rcand, cfg)
        s = _stress_sim(train_bars, rcand, cfg)
        score = score_sim_result(r, cfg, train_days, s, rcand["n_buy"], rcand["n_sell"])
        if cfg.get("min_train_two_sided", True) and (sum(r["bf"]) <= 0 or sum(r["sf"]) <= 0):
            score -= 5.0
        if r["trades"] < int(cfg.get("min_train_trades", 0)):
            score -= 4.0
        refined.append((score, rcand, r, s, wmeta))
        if return_table:
            rows.append(_candidate_record(rcand, r, s, score, "stage2"))
    refined.sort(key=lambda x: x[0], reverse=True)
    best_score, best_cand, best_r, best_s, best_wmeta = refined[0]
    out = dict(
        best=best_cand,
        train_result=best_r,
        train_stress=best_s,
        train_score=float(best_score),
        weight_meta=best_wmeta,
        n_candidates=len(candidates),
        n_refined=len(refined),
        train_days=int(round(train_days)),
        leaderboard=pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True) if return_table else None,
    )
    return out


def make_rolling_windows(bars: np.ndarray, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build fixed-length rolling train/test windows by timestamp."""
    bars = np.asarray(bars, dtype=float)
    if len(bars) == 0:
        return []
    train_days = float(cfg["gen_train_days"])
    test_days = float(cfg["gen_test_days"])
    step_days = float(cfg["gen_step_days"])
    min_train = float(cfg["gen_min_train_days"])
    min_test = float(cfg["gen_min_test_days"])
    t0 = float(bars[0, 0])
    t_end = float(bars[-1, 0])
    test_lo = t0 + train_days * 86400.0
    windows: List[Dict[str, Any]] = []
    idx = 0
    while test_lo + min_test * 86400.0 <= t_end + 1:
        test_hi = test_lo + test_days * 86400.0
        train_lo = test_lo - train_days * 86400.0
        train = bars[(bars[:, 0] >= train_lo) & (bars[:, 0] < test_lo)]
        test = bars[(bars[:, 0] >= test_lo) & (bars[:, 0] < test_hi)]
        if len(train) >= max(10, int(min_train * 0.60)) and len(test) >= max(3, int(min_test * 0.60)):
            actual_train_days = (train[-1, 0] - train[0, 0]) / 86400.0 if len(train) > 1 else 0.0
            actual_test_days = (test[-1, 0] - test[0, 0]) / 86400.0 if len(test) > 1 else 0.0
            if actual_train_days >= min_train - 1 and actual_test_days >= min_test - 1:
                windows.append(dict(
                    fold_idx=idx,
                    train=train,
                    test=test,
                    train_start=train[0, 0],
                    train_end=train[-1, 0],
                    test_start=test[0, 0],
                    test_end=test[-1, 0],
                    train_days=actual_train_days,
                    test_days=actual_test_days,
                ))
                idx += 1
        test_lo += step_days * 86400.0
        max_folds = cfg.get("gen_max_folds")
        if max_folds is not None and len(windows) >= int(max_folds):
            break
    return windows


def _fold_to_record(fold: Dict[str, Any], search: Dict[str, Any], test_result: Dict[str, Any], test_stress: Dict[str, Any], test_score: float, cfg: Dict[str, Any]) -> Dict[str, Any]:
    cand = search["best"]
    return dict(
        fold_idx=int(fold["fold_idx"]),
        train_days=round(float(fold["train_days"]), 1),
        test_days=round(float(fold["test_days"]), 1),
        train_start=pd.to_datetime(fold["train_start"], unit="s").date().isoformat(),
        train_end=pd.to_datetime(fold["train_end"], unit="s").date().isoformat(),
        test_start=pd.to_datetime(fold["test_start"], unit="s").date().isoformat(),
        test_end=pd.to_datetime(fold["test_end"], unit="s").date().isoformat(),
        family=cand["family"],
        spacing_curve=cand["spacing_curve"],
        weight_curve=cand["weight_curve"],
        n_buy=cand["n_buy"],
        n_sell=cand["n_sell"],
        buy_inner_pct=round(cand["buy_inner_pct"], 3),
        buy_outer_pct=round(cand["buy_outer_pct"], 3),
        sell_inner_pct=round(cand["sell_inner_pct"], 3),
        sell_outer_pct=round(cand["sell_outer_pct"], 3),
        train_score=round(float(search["train_score"]), 3),
        train_pct=round(float(search["train_result"]["pnl_pct"]), 3),
        train_cons_pct=round(float(search["train_stress"]["pnl_pct"]), 3),
        test_score=round(float(test_score), 3),
        test_pct=round(float(test_result["pnl_pct"]), 3),
        cons_pct=round(float(test_stress["pnl_pct"]), 3),
        hold_pct=round(float(test_result["hold_pct"]), 3),
        maxdd=round(float(test_result["maxdd"]), 3),
        trades=int(test_result["trades"]),
        buy_fills=int(np.sum(test_result["bf"])),
        sell_fills=int(np.sum(test_result["sf"])),
        two_sided=bool(np.sum(test_result["bf"]) > 0 and np.sum(test_result["sf"]) > 0),
        rung_usage=round(_rung_usage(test_result), 3),
        endinv=round(float(test_result["endinv"]), 2),
        buy_prices=[float(x) for x in cand["buy_prices"]],
        sell_prices=[float(x) for x in cand["sell_prices"]],
        buy_amounts_pct=_base.weights_pct(cand["bw"]),
        sell_amounts_pct=_base.weights_pct(cand["sw"]),
    )


def _instability_penalty(folds_df: pd.DataFrame, cfg: Dict[str, Any]) -> float:
    if folds_df.empty or len(folds_df) < 2:
        return 0.0
    cols = ["n_buy", "n_sell", "buy_inner_pct", "buy_outer_pct", "sell_inner_pct", "sell_outer_pct"]
    vals = folds_df[cols].astype(float)
    # Normalize price-distance instability to roughly the same order as rung-count changes.
    spread = vals.std(ddof=0).fillna(0.0)
    penalty = float(spread["n_buy"] + spread["n_sell"] + 0.1 * spread.drop(["n_buy", "n_sell"]).sum())
    return penalty * float(cfg.get("score_instability_penalty", 0.20))


def aggregate_fold_blocks(folds_df: pd.DataFrame, block_days: int = 45, test_days: int = 15) -> pd.DataFrame:
    """Aggregate consecutive 15d OOS folds into 45d or 60d review blocks."""
    if folds_df is None or folds_df.empty:
        return pd.DataFrame()
    group_size = max(1, int(round(float(block_days) / float(test_days))))
    df = folds_df.copy().reset_index(drop=True)
    df["block"] = (df.index // group_size) + 1
    rows = []
    for b, g in df.groupby("block"):
        rows.append(dict(
            block=int(b),
            folds=len(g),
            test_start=str(g.iloc[0]["test_start"]),
            test_end=str(g.iloc[-1]["test_end"]),
            median_score=round(float(np.median(g["test_score"])), 3),
            total_pct=round(float(np.sum(g["test_pct"])), 3),
            total_cons_pct=round(float(np.sum(g["cons_pct"])), 3),
            pos_rate=round(float(np.mean(g["test_pct"] > 0)), 3),
            two_sided_rate=round(float(np.mean(g["two_sided"])), 3),
            total_trades=int(np.sum(g["trades"])),
            median_rung_usage=round(float(np.median(g["rung_usage"])), 3),
            common_rungs=f"{int(round(g['n_buy'].median()))}+{int(round(g['n_sell'].median()))}",
            families=", ".join(sorted(set(map(str, g["family"]))))
        ))
    return pd.DataFrame(rows)


def rolling_walkforward_search(
    bars: np.ndarray,
    cfg: Dict[str, Any],
    pdec: Optional[int] = None,
    label: str = "",
    return_fold_leaderboards: bool = False,
) -> Dict[str, Any]:
    """Run the generative optimizer in rolling 60d train / 15d OOS windows."""
    bars = np.asarray(bars, dtype=float)
    windows = make_rolling_windows(bars, cfg)
    records: List[Dict[str, Any]] = []
    leaderboards: Dict[int, pd.DataFrame] = {}
    for fold in windows:
        search = robust_ladder_search(
            fold["train"], cfg, pdec, label=label, fold_idx=int(fold["fold_idx"]),
            return_table=return_fold_leaderboards,
        )
        cand = search["best"]
        test_result = _normal_sim(fold["test"], cand, cfg)
        test_stress = _stress_sim(fold["test"], cand, cfg)
        test_score = score_sim_result(test_result, cfg, fold["test_days"], test_stress,
                                      cand["n_buy"], cand["n_sell"])
        records.append(_fold_to_record(fold, search, test_result, test_stress, test_score, cfg))
        if return_fold_leaderboards and search.get("leaderboard") is not None:
            leaderboards[int(fold["fold_idx"])] = search["leaderboard"]

    folds_df = pd.DataFrame(records)
    if folds_df.empty:
        return dict(
            folds=folds_df,
            block45=pd.DataFrame(),
            block60=pd.DataFrame(),
            n_folds=0,
            wf_pass=False,
            note="insufficient history for rolling 60d/15d validation",
            leaderboards=leaderboards,
        )
    scores = folds_df["test_score"].astype(float).to_numpy()
    cons = folds_df["cons_pct"].astype(float).to_numpy()
    test_pct = folds_df["test_pct"].astype(float).to_numpy()
    pos_rate = float(np.mean(test_pct > 0))
    two_rate = float(np.mean(folds_df["two_sided"].astype(bool)))
    p25 = float(np.percentile(scores, 25))
    med_score = float(np.median(scores))
    score_std = float(np.std(scores))
    instab = _instability_penalty(folds_df, cfg)
    robust_score = p25 - float(cfg["score_std_penalty"]) * score_std - instab
    worst_fold = float(np.min(test_pct))
    median_cons = float(np.median(cons))
    wf_pass = (
        len(folds_df) >= int(cfg["gen_min_folds"])
        and pos_rate >= float(cfg["gen_min_pos_rate"])
        and two_rate >= float(cfg["gen_min_two_sided_rate"])
        and med_score >= float(cfg["gen_min_median_score"])
        and median_cons >= float(cfg["gen_min_median_cons_pct"])
        and worst_fold >= float(cfg["gen_max_bad_fold_loss_pct"])
    )
    block45 = aggregate_fold_blocks(folds_df, int(cfg["pseudo_quarter_days"]), int(cfg["gen_test_days"]))
    block60 = aggregate_fold_blocks(folds_df, int(cfg["robustness_block_days"]), int(cfg["gen_test_days"]))
    summary = dict(
        n_folds=int(len(folds_df)),
        pos_rate=round(pos_rate, 3),
        two_sided_rate=round(two_rate, 3),
        median_test_pct=round(float(np.median(test_pct)), 3),
        median_cons_pct=round(median_cons, 3),
        p25_score=round(p25, 3),
        median_score=round(med_score, 3),
        score_std=round(score_std, 3),
        instability_penalty=round(instab, 3),
        robust_score=round(robust_score, 3),
        worst_fold_pct=round(worst_fold, 3),
        total_trades=int(folds_df["trades"].sum()),
        median_trades=float(np.median(folds_df["trades"])),
        median_rung_usage=round(float(np.median(folds_df["rung_usage"])), 3),
        median_n_buy=int(round(float(np.median(folds_df["n_buy"])))) if len(folds_df) else None,
        median_n_sell=int(round(float(np.median(folds_df["n_sell"])))) if len(folds_df) else None,
        wf_pass=bool(wf_pass),
    )
    return dict(
        folds=folds_df,
        block45=block45,
        block60=block60,
        leaderboards=leaderboards,
        **summary,
    )


def robust_walkforward_all(
    candidates: Sequence[str],
    hist: Dict[str, Any],
    uni: Dict[str, Any],
    cfg: Dict[str, Any],
    max_markets: Optional[int] = None,
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, Any]]]:
    """Run rolling generative walk-forward for each candidate market."""
    rows: List[Dict[str, Any]] = []
    details: Dict[str, Dict[str, Any]] = {}
    t0 = time.time()
    base_markets = list(candidates)[:max_markets] if max_markets else list(candidates)
    review_status = force_review_candidates(
        base_markets,
        uni,
        hist=hist,
        always_review_markets=cfg.get("always_review_markets", DEFAULT_ALWAYS_REVIEW_MARKETS),
        focus_markets=[],
        focus_only=False,
        require_history=False,
    )
    markets = review_status["candidates"]
    forced_set = set(review_status.get("present", []))
    if review_status.get("missing"):
        _base._log("always-review markets not present on exchange: " + ", ".join(review_status["missing"]))
    for j, pk in enumerate(markets, 1):
        h = hist.get(pk)
        if h is None:
            note = "present in exchange universe but no usable history" if pk in forced_set else "no usable history"
            details[pk] = dict(folds=pd.DataFrame(), block45=pd.DataFrame(), block60=pd.DataFrame(), n_folds=0, wf_pass=False, note=note)
            rows.append(dict(base=pk, src="n/a", folds=0, wf_pass=False, always_review=bool(pk in forced_set), note=note))
            continue
        bars = _base.slice_days(h["bars"], int(max(cfg.get("deploy_eval_days", 180), cfg["gen_train_days"] + cfg["gen_test_days"] + 5)))
        wf = rolling_walkforward_search(bars, cfg, uni.get("pdec", {}).get(pk), label=pk)
        details[pk] = wf
        if wf["n_folds"] == 0:
            rows.append(dict(base=pk, src=h["src"], folds=0, wf_pass=False,
                             always_review=bool(pk in forced_set),
            note=wf.get("note", "no folds")))
            continue
        rows.append(dict(
            base=pk,
            src=h["src"],
            folds=wf["n_folds"],
            always_review=bool(pk in forced_set),
            pos_rate=wf["pos_rate"],
            two_sided_rate=wf["two_sided_rate"],
            median_test_pct=wf["median_test_pct"],
            median_cons_pct=wf["median_cons_pct"],
            robust_score=wf["robust_score"],
            p25_score=wf["p25_score"],
            worst_fold_pct=wf["worst_fold_pct"],
            total_trades=wf["total_trades"],
            median_trades=wf["median_trades"],
            median_rung_usage=wf["median_rung_usage"],
            median_rungs=f"{wf['median_n_buy']}+{wf['median_n_sell']}",
            wf_pass=wf["wf_pass"],
        ))
        if j % 5 == 0:
            _base._log(f"  ...robust walk-forward {j}/{len(markets)} ({time.time() - t0:.0f}s)")
    df = pd.DataFrame(rows)
    if not df.empty and "robust_score" in df.columns:
        sort_cols = ["wf_pass"]
        ascending = [False]
        if "always_review" in df.columns:
            sort_cols.append("always_review"); ascending.append(False)
        sort_cols += ["robust_score", "median_cons_pct"]; ascending += [False, False]
        df = df.sort_values(sort_cols, ascending=ascending).reset_index(drop=True)
    return df, details


def fit_latest_deploy_ladder(
    bars: np.ndarray,
    cfg: Dict[str, Any],
    pdec: Optional[int] = None,
    label: str = "",
    return_table: bool = False,
) -> Dict[str, Any]:
    """Fit the deploy ladder using the most recent deploy_train_days unless configured otherwise."""
    bars = np.asarray(bars, dtype=float)
    if bool(cfg.get("deploy_refit_on_full_history", False)):
        train = bars
    else:
        train = _base.slice_days(bars, int(cfg.get("deploy_train_days", cfg["gen_train_days"])))
    return robust_ladder_search(train, cfg, pdec=pdec, label=f"{label}:deploy", fold_idx=9999,
                                return_table=return_table)


def _fund_sizing(uni: Dict[str, Any], pk: str, cfg: Dict[str, Any]) -> Tuple[int, float, float, float]:
    spread_pct, depth_usd = _base.depth_info(uni, pk, cfg["depth_band"])
    vol_usd = float(uni["df"].set_index("pairkey").vol_usd.get(pk, float("nan")))
    vol_term = cfg["vol_fraction"] * vol_usd if vol_usd == vol_usd else float("inf")
    depth_term = cfg["depth_fraction"] * depth_usd if depth_usd == depth_usd else float("inf")
    basis = min(vol_term, depth_term)
    max_fund = _base.round_fund(basis, cfg) if basis != float("inf") else cfg["fund_floor"]
    return int(max_fund), float(spread_pct), float(depth_usd), float(vol_usd)


def finalize_robust(
    candidates: Sequence[str],
    hist: Dict[str, Any],
    uni: Dict[str, Any],
    cfg: Dict[str, Any],
    cache: Optional[Any] = None,
    wf_details: Optional[Dict[str, Dict[str, Any]]] = None,
    include_gated: bool = True,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]], Dict[str, pd.DataFrame]]:
    """Generate deploy-ready configs for robust-WF survivors or selected markets."""
    cache = cache or _base.CandleCache(cfg["cache_dir"], cfg["cache_ttl_hours"])
    wf_details = wf_details or {}
    review_status = force_review_candidates(
        candidates,
        uni,
        hist=hist,
        always_review_markets=cfg.get("always_review_markets", DEFAULT_ALWAYS_REVIEW_MARKETS),
        focus_markets=cfg.get("focus_markets", ()),
        focus_only=False,
        require_history=False,
    )
    candidates = review_status["candidates"]
    rows: List[Dict[str, Any]] = []
    configs: List[Dict[str, Any]] = []
    leaderboards: Dict[str, pd.DataFrame] = {}
    for pk in candidates:
        h = hist.get(pk)
        if h is None:
            wf = wf_details.get(pk, {})
            gates = ["present in exchange universe but no usable history"]
            row = dict(
                base=pk,
                trading_pair=str(pk).replace("/", "-"),
                src="n/a",
                validation="SUSPECT",
                family="n/a",
                rungs="n/a",
                spacing="n/a",
                weights="n/a",
                deploy_train_days=0,
                buy_inner_pct=float("nan"),
                buy_outer_pct=float("nan"),
                sell_inner_pct=float("nan"),
                sell_outer_pct=float("nan"),
                pnl_eval_pct=float("nan"),
                cons_eval_pct=float("nan"),
                cons_retained=float("nan"),
                trades=0,
                buy_fills=0,
                sell_fills=0,
                maxdd=float("nan"),
                endinv=float("nan"),
                wf_robust_score=wf.get("robust_score", float("nan")),
                wf_pos_rate=wf.get("pos_rate", float("nan")),
                wf_two_sided_rate=wf.get("two_sided_rate", float("nan")),
                wf_median_cons_pct=wf.get("median_cons_pct", float("nan")),
                max_fund=float("nan"),
                spread_pct=float("nan"),
                depth_2pct=float("nan"),
                fill_ratio=float("nan"),
                diverge_pct=float("nan"),
                gates="; ".join(gates),
            )
            rows.append(row)
            continue
        wf = wf_details.get(pk, {})
        wf_pass = bool(wf.get("wf_pass", False))
        if not include_gated and not wf_pass:
            continue
        bars = _base.slice_days(h["bars"], int(cfg.get("deploy_eval_days", 180)))
        pdec = uni.get("pdec", {}).get(pk)
        fit = fit_latest_deploy_ladder(bars, cfg, pdec, pk, return_table=True)
        cand = fit["best"]
        leaderboards[pk] = fit.get("leaderboard")
        normal = _normal_sim(bars, cand, cfg)
        max_fund, spread_pct, depth_usd, vol_usd = _fund_sizing(uni, pk, cfg)
        slip = max(float(cfg["slip_floor"]), (spread_pct / 200.0) if spread_pct == spread_pct else 0.0)
        cons = _stress_sim(bars, cand, cfg, slip=slip)
        cons_retained = cons["pnl_pct"] / normal["pnl_pct"] * 100.0 if normal["pnl_pct"] > 0 else float("nan")
        mq_ok, mq_need = _base.min_qty_check(cand["buy_prices"], cand["sell_prices"], cand["bw"], cand["sw"],
                                             max_fund, cfg, uni.get("min_qty", {}).get(pk), bars[0, 4])
        hr = _base.hourly_fill_check(uni, pk, cand["buy_prices"], cand["sell_prices"], cand["bw"], cand["sw"],
                                     cfg, cache, bars, h.get("src"))
        div = (_base.proxy_divergence(uni, pk, cfg, cache)
               if h.get("src") == "MEXC" else float("nan"))
        gates: List[str] = []
        if not wf_pass:
            gates.append("robust WF failed or not run")
        if normal["trades"] <= 0:
            gates.append("no deploy-window trades")
        if sum(normal["bf"]) <= 0 or sum(normal["sf"]) <= 0:
            gates.append("deploy-window one-sided fills")
        if normal["endinv"] > cfg["max_endinv_pct"] and uni["base_of"].get(pk) not in cfg.get("accumulate_ok", set()):
            gates.append(f"bagged ({normal['endinv']:.0f}% base inventory)")
        if depth_usd == depth_usd and depth_usd < cfg["min_depth_2pct"]:
            gates.append(f"thin book (${depth_usd:,.0f})")
        if not mq_ok:
            gates.append(f"min-qty needs fund >= ${mq_need:,.0f}")
        fr = hr.get("fill_ratio", float("nan"))
        if fr == fr and fr < cfg["hourly_warn_ratio"]:
            gates.append(f"hourly fills only {fr:.0%} of daily-sim fills")
        if div == div and div > cfg["divergence_warn_pct"]:
            gates.append(f"proxy diverges {div:.1f}% from native")
        if cons["pnl_pct"] < cfg["gen_min_median_cons_pct"]:
            gates.append(f"conservative deploy sim weak ({cons['pnl_pct']:+.1f}%)")

        validation = "CONFIRMED" if wf_pass and not gates else ("GATED" if wf_pass else "SUSPECT")
        row = dict(
            base=pk,
            trading_pair=pk.replace("/", "-"),
            src=h.get("src"),
            validation=validation,
            family=cand["family"],
            rungs=f"{cand['n_buy']}+{cand['n_sell']}",
            spacing=cand["spacing_curve"],
            weights=cand["weight_curve"],
            deploy_train_days=fit["train_days"],
            buy_inner_pct=round(cand["buy_inner_pct"], 3),
            buy_outer_pct=round(cand["buy_outer_pct"], 3),
            sell_inner_pct=round(cand["sell_inner_pct"], 3),
            sell_outer_pct=round(cand["sell_outer_pct"], 3),
            pnl_eval_pct=round(normal["pnl_pct"], 2),
            cons_eval_pct=round(cons["pnl_pct"], 2),
            cons_retained=round(cons_retained, 0) if cons_retained == cons_retained else float("nan"),
            trades=normal["trades"],
            buy_fills=int(sum(normal["bf"])),
            sell_fills=int(sum(normal["sf"])),
            maxdd=round(normal["maxdd"], 2),
            endinv=round(normal["endinv"], 1),
            wf_robust_score=wf.get("robust_score", float("nan")),
            wf_pos_rate=wf.get("pos_rate", float("nan")),
            wf_two_sided_rate=wf.get("two_sided_rate", float("nan")),
            wf_median_cons_pct=wf.get("median_cons_pct", float("nan")),
            max_fund=max_fund,
            spread_pct=round(spread_pct, 4) if spread_pct == spread_pct else float("nan"),
            depth_2pct=round(depth_usd, 0) if depth_usd == depth_usd else float("nan"),
            fill_ratio=hr.get("fill_ratio", float("nan")),
            diverge_pct=round(div, 3) if div == div else float("nan"),
            gates="; ".join(gates),
        )
        rows.append(row)
        configs.append(dict(
            symbol=pk,
            trading_pair=pk.replace("/", "-"),
            exchange=uni["exchange"],
            passive_order_placement=True,
            max_fund_value_quote=max_fund,
            total_amount_quote=max_fund,
            buy_prices=[round(float(x), 8) for x in cand["buy_prices"]],
            sell_prices=[round(float(x), 8) for x in cand["sell_prices"]],
            buy_amounts_pct=_base.weights_pct(cand["bw"]),
            sell_amounts_pct=_base.weights_pct(cand["sw"]),
            validation=validation,
            gates=gates,
            optimizer=dict(
                engine="ladder_lab_robust",
                version=__version__,
                train_days=fit["train_days"],
                family=cand["family"],
                spacing_curve=cand["spacing_curve"],
                weight_curve=cand["weight_curve"],
                n_buy=cand["n_buy"],
                n_sell=cand["n_sell"],
                buy_inner_pct=round(cand["buy_inner_pct"], 4),
                buy_outer_pct=round(cand["buy_outer_pct"], 4),
                sell_inner_pct=round(cand["sell_inner_pct"], 4),
                sell_outer_pct=round(cand["sell_outer_pct"], 4),
                train_score=round(float(fit["train_score"]), 4),
                n_candidates=fit["n_candidates"],
                n_refined=fit["n_refined"],
            ),
            walkforward=dict(
                passed=wf_pass,
                robust_score=wf.get("robust_score"),
                folds=wf.get("n_folds"),
                pos_rate=wf.get("pos_rate"),
                two_sided_rate=wf.get("two_sided_rate"),
                median_test_pct=wf.get("median_test_pct"),
                median_cons_pct=wf.get("median_cons_pct"),
            ),
            conservative=dict(
                pnl_eval_pct=round(cons["pnl_pct"], 4),
                retained_pct=round(cons_retained, 2) if cons_retained == cons_retained else None,
                slip_bps=round(slip * 1e4, 1),
            ),
            hourly_check=hr,
        ))
    df = pd.DataFrame(rows)
    if not df.empty:
        order = {"CONFIRMED": 0, "GATED": 1, "SUSPECT": 2}
        df["_order"] = df["validation"].map(order).fillna(9)
        df = df.sort_values(["_order", "wf_robust_score", "cons_eval_pct"], ascending=[True, False, False]).drop(columns="_order").reset_index(drop=True)
        configs = sorted(configs, key=lambda c: (order.get(c["validation"], 9), -float(c.get("walkforward", {}).get("robust_score") or -1e9)))
    return df, configs, leaderboards



# ======================================================================
# Controller copy/paste Markdown export
# ======================================================================

def _normalize_controller_pair(value: Any) -> str:
    """Normalize BASE/QUOTE and BASE-QUOTE to BASE-QUOTE for matching."""
    return str(value or "").strip().upper().replace("/", "-")


def _safe_text(path: Any) -> str:
    from pathlib import Path
    try:
        return Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Path(path).read_text()
    except Exception:
        return ""


def _strip_yaml_comment(value: str) -> str:
    return str(value).split("#", 1)[0].strip()


def _parse_top_level_scalar(text: str, key: str) -> Optional[str]:
    import re
    m = re.search(rf"^\s*{re.escape(key)}\s*:\s*(.*?)$", text, flags=re.MULTILINE)
    if not m:
        return None
    return _strip_yaml_comment(m.group(1))


def parse_controller_yml(path: Any) -> Dict[str, Any]:
    """Parse top-level scalar fields needed for copy/paste reports."""
    from pathlib import Path
    path_obj = Path(path)
    text = _safe_text(path_obj)
    keys = [
        "id", "controller_name", "controller_type", "connector_name", "trading_pair",
        "fee_rate", "ledger_funded_budgets", "total_amount_quote", "max_fund_value_quote",
        "claimed_base_value_quote", "buy_prices", "buy_amounts_pct", "sell_prices",
        "sell_amounts_pct", "min_order_quote", "allow_partial_levels", "passive_order_placement",
        "state_file_name", "diagnostic_log_file_name",
    ]
    values: Dict[str, str] = {}
    for key in keys:
        v = _parse_top_level_scalar(text, key)
        if v is not None:
            values[key] = v
    pair = values.get("trading_pair", "")
    return dict(
        path=str(path_obj),
        file_name=path_obj.name,
        exists=path_obj.exists(),
        trading_pair=pair,
        pair_norm=_normalize_controller_pair(pair),
        values=values,
    )


def discover_controller_ymls(root: Any = ".", pattern: str = "range_inventory_ladder*_V*.yml") -> List[str]:
    from pathlib import Path
    return [str(p) for p in sorted(Path(root).glob(pattern))]


def _controller_map(paths: Optional[Sequence[Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    if paths is None:
        paths = discover_controller_ymls(".")
    for p in paths or []:
        parsed = parse_controller_yml(p)
        key = parsed.get("pair_norm")
        if key:
            out[key] = parsed
    return out


def _config_pair_norm(config: Dict[str, Any]) -> str:
    return _normalize_controller_pair(config.get("trading_pair") or config.get("symbol"))


def _format_controller_scalar(value: Any, kind: str = "number") -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    try:
        v = float(value)
    except Exception:
        return str(value)
    if not math.isfinite(v):
        return str(value)
    if abs(v - round(v)) < 1e-12 and abs(v) >= 1:
        return str(int(round(v)))
    if kind == "pct":
        return f"{v:.6g}"
    if 0 < abs(v) < 1:
        s = f"{v:.12f}".rstrip("0").rstrip(".")
        return s if s not in ("", "-0") else "0"
    return f"{v:.12g}"


def _format_controller_list(values: Any, kind: str = "number") -> str:
    if values is None:
        return ""
    if isinstance(values, str):
        return _strip_yaml_comment(values)
    return ",".join(_format_controller_scalar(v, kind=kind) for v in list(values))


def _current_ladder_block(parsed: Dict[str, Any]) -> str:
    vals = parsed.get("values", {})
    lines = []
    for key in ("buy_prices", "buy_amounts_pct", "sell_prices", "sell_amounts_pct"):
        if key in vals:
            lines.append(f"{key}: {vals[key]}")
    return "\n".join(lines)


def _count_ladder_values(csv_text: Any) -> int:
    txt = _strip_yaml_comment(str(csv_text or ""))
    if not txt:
        return 0
    return len([x for x in txt.split(",") if x.strip()])


def _summary_rows_by_pair(summary_df: Optional[pd.DataFrame]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    if summary_df is None or not isinstance(summary_df, pd.DataFrame) or summary_df.empty:
        return out
    for _, row in summary_df.iterrows():
        d = row.to_dict()
        for col in ("base", "symbol", "trading_pair"):
            if col in d and d[col] == d[col]:
                key = _normalize_controller_pair(d[col])
                if key:
                    out[key] = d
    return out


def _wf_rows_by_pair(wf_df: Optional[pd.DataFrame]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    if wf_df is None or not isinstance(wf_df, pd.DataFrame) or wf_df.empty or "base" not in wf_df.columns:
        return out
    for _, row in wf_df.iterrows():
        d = row.to_dict()
        key = _normalize_controller_pair(d.get("base"))
        if key:
            out[key] = d
    return out


def _config_notes(config: Dict[str, Any], summary: Optional[Dict[str, Any]] = None,
                  wf_row: Optional[Dict[str, Any]] = None) -> List[str]:
    summary = summary or {}
    wf_row = wf_row or {}
    notes: List[str] = []
    validation = config.get("validation") or summary.get("validation")
    if validation:
        notes.append(f"Validation: **{validation}**")
    gates = config.get("gates")
    if not gates:
        gates = summary.get("gates")
    if isinstance(gates, str):
        gate_list = [g.strip() for g in gates.split(";") if g.strip()]
    elif isinstance(gates, (list, tuple)):
        gate_list = [str(g).strip() for g in gates if str(g).strip()]
    else:
        gate_list = []
    notes.append("Gates/warnings: " + ("; ".join(gate_list) if gate_list else "none reported"))
    opt = config.get("optimizer", {}) if isinstance(config.get("optimizer"), dict) else {}
    if opt:
        notes.append(
            f"Optimizer: {opt.get('family', '?')}/{opt.get('spacing_curve', '?')}; "
            f"weights={opt.get('weight_curve', '?')}; rungs={opt.get('n_buy', len(config.get('buy_prices', []) or []))}+{opt.get('n_sell', len(config.get('sell_prices', []) or []))}"
        )
    wf = config.get("walkforward", {}) if isinstance(config.get("walkforward"), dict) else {}
    if wf:
        notes.append(
            "Walk-forward: "
            f"passed={wf.get('passed')}, robust_score={wf.get('robust_score')}, "
            f"folds={wf.get('folds')}, pos_rate={wf.get('pos_rate')}, "
            f"two_sided_rate={wf.get('two_sided_rate')}, median_cons_pct={wf.get('median_cons_pct')}"
        )
    elif wf_row:
        notes.append(
            "Walk-forward row: "
            f"passed={wf_row.get('wf_pass')}, robust_score={wf_row.get('robust_score')}, "
            f"pos_rate={wf_row.get('pos_rate')}, two_sided_rate={wf_row.get('two_sided_rate')}, "
            f"median_cons_pct={wf_row.get('median_cons_pct')}, worst_fold_pct={wf_row.get('worst_fold_pct')}"
        )
    cons = config.get("conservative", {}) if isinstance(config.get("conservative"), dict) else {}
    if cons:
        notes.append(
            "Conservative deploy sim: "
            f"pnl_eval_pct={cons.get('pnl_eval_pct')}, retained_pct={cons.get('retained_pct')}, slip_bps={cons.get('slip_bps')}"
        )
    return notes


def controller_ladder_copy_block(config: Dict[str, Any], include_cap: bool = False) -> str:
    """Return controller-ready YAML lines for the generated ladder."""
    lines: List[str] = []
    if include_cap and config.get("max_fund_value_quote") is not None:
        lines.append(f"max_fund_value_quote: {_format_controller_scalar(config.get('max_fund_value_quote'))}")
    lines.extend([
        f"buy_prices: {_format_controller_list(config.get('buy_prices', []), kind='price')}",
        f"buy_amounts_pct: {_format_controller_list(config.get('buy_amounts_pct', []), kind='pct')}",
        f"sell_prices: {_format_controller_list(config.get('sell_prices', []), kind='price')}",
        f"sell_amounts_pct: {_format_controller_list(config.get('sell_amounts_pct', []), kind='pct')}",
    ])
    return "\n".join(lines)


def render_controller_ladder_markdown(
    configs: Sequence[Dict[str, Any]],
    controller_yml_paths: Optional[Sequence[Any]] = None,
    summary_df: Optional[pd.DataFrame] = None,
    wf_df: Optional[pd.DataFrame] = None,
    focus_markets: Optional[Sequence[str]] = None,
    title: Optional[str] = None,
    include_unmatched_configs: bool = True,
) -> str:
    """Render a Markdown patch sheet with copy/paste ladder values."""
    from datetime import datetime
    configs = list(configs or [])
    yml_map = _controller_map(controller_yml_paths)
    cfg_map = {_config_pair_norm(c): c for c in configs if _config_pair_norm(c)}
    summary_map = _summary_rows_by_pair(summary_df)
    wf_map = _wf_rows_by_pair(wf_df)
    ordered: List[str] = []
    for x in (focus_markets or []):
        key = _normalize_controller_pair(x)
        if key and key not in ordered:
            ordered.append(key)
    for key in yml_map:
        if key and key not in ordered:
            ordered.append(key)
    for key in cfg_map:
        if include_unmatched_configs and key not in ordered:
            ordered.append(key)
    lines: List[str] = []
    lines.append(f"# {title or 'Suggested ladder copy/paste values'}")
    lines.append("")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("These blocks are formatted for the existing `range_inventory_ladder` controller YAML style: comma-separated scalar values, not JSON arrays.")
    lines.append("")
    lines.append("**Live-state safety:** the ladder-only block is the normal paste target for an already-running controller. The optional sizing/cap block is separated because `total_amount_quote` is usually a clean-seed/reseed value once a controller has a persisted state file.")
    lines.append("")
    if not ordered:
        lines.append("No controller YAML files or deploy configs were available for this report.")
        return "\n".join(lines).rstrip() + "\n"
    for key in ordered:
        yml = yml_map.get(key)
        cfg = cfg_map.get(key)
        file_name = yml.get("file_name") if yml else "not matched to a supplied controller YAML"
        lines.append(f"## {key} — `{file_name}`")
        lines.append("")
        if yml and yml.get("values", {}).get("id"):
            lines.append(f"Existing controller id: `{yml['values']['id']}`")
        if cfg is None:
            lines.append("**No generated deploy ladder was present for this controller in the current deploy config.**")
            wf_row = wf_map.get(key)
            if wf_row:
                lines.append(
                    f"Walk-forward row: passed={wf_row.get('wf_pass')}, robust_score={wf_row.get('robust_score')}, "
                    f"pos_rate={wf_row.get('pos_rate')}, two_sided_rate={wf_row.get('two_sided_rate')}, "
                    f"median_cons_pct={wf_row.get('median_cons_pct')}, worst_fold_pct={wf_row.get('worst_fold_pct')}"
                )
            if yml:
                lines.append("")
                lines.append("Current YAML ladder values, left unchanged:")
                lines.append("")
                lines.append("```yaml")
                lines.append(_current_ladder_block(yml) or "# No current ladder values found.")
                lines.append("```")
            lines.append("")
            lines.append("To force this market into future final output, keep it in `ALWAYS_REVIEW_MARKETS` / `FORCE_REVIEW_MARKETS` and rerun the notebook.")
            lines.append("")
            continue
        for note in _config_notes(cfg, summary_map.get(key), wf_map.get(key)):
            lines.append(f"- {note}")
        if yml:
            vals = yml.get("values", {})
            cur_b = _count_ladder_values(vals.get("buy_prices"))
            cur_s = _count_ladder_values(vals.get("sell_prices"))
            lines.append(f"- Current controller rungs: {cur_b}+{cur_s}; suggested rungs: {len(cfg.get('buy_prices', []) or [])}+{len(cfg.get('sell_prices', []) or [])}")
        lines.append("")
        lines.append("### Ladder-only copy/paste block")
        lines.append("")
        lines.append("```yaml")
        lines.append(controller_ladder_copy_block(cfg, include_cap=False))
        lines.append("```")
        lines.append("")
        lines.append("### Optional sizing/cap block")
        lines.append("")
        lines.append("Copy this only when intentionally resizing/reseeding the controller.")
        lines.append("")
        lines.append("```yaml")
        if cfg.get("max_fund_value_quote") is not None:
            lines.append(f"max_fund_value_quote: {_format_controller_scalar(cfg.get('max_fund_value_quote'))}")
        if cfg.get("total_amount_quote") is not None:
            lines.append(f"# total_amount_quote: {_format_controller_scalar(cfg.get('total_amount_quote'))}  # clean reseed only; usually inert for an existing state file")
        lines.append("```")
        lines.append("")
        if str(cfg.get("validation", "")).upper() in {"SUSPECT", "GATED", "MIXED"}:
            lines.append("> Deployment note: this block is mechanically valid YAML, but it was not a clean `CONFIRMED` result. Treat the gates/warnings above as real risk flags.")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def save_controller_ladder_markdown(
    configs: Sequence[Dict[str, Any]],
    path: Any,
    controller_yml_paths: Optional[Sequence[Any]] = None,
    summary_df: Optional[pd.DataFrame] = None,
    wf_df: Optional[pd.DataFrame] = None,
    focus_markets: Optional[Sequence[str]] = None,
    title: Optional[str] = None,
    include_unmatched_configs: bool = True,
) -> str:
    """Save render_controller_ladder_markdown(...) and return the file path."""
    from pathlib import Path
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_controller_ladder_markdown(
        configs=configs,
        controller_yml_paths=controller_yml_paths,
        summary_df=summary_df,
        wf_df=wf_df,
        focus_markets=focus_markets,
        title=title,
        include_unmatched_configs=include_unmatched_configs,
    ), encoding="utf-8")
    _base._log(f"Saved controller ladder copy/paste Markdown -> {path}")
    return str(path)

def save_robust_outputs(
    summary_df: pd.DataFrame,
    configs: List[Dict[str, Any]],
    wf_df: pd.DataFrame,
    details: Dict[str, Dict[str, Any]],
    prefix: str,
    metadata: Optional[Dict[str, Any]] = None,
    controller_yml_paths: Optional[Sequence[Any]] = None,
    focus_markets: Optional[Sequence[str]] = None,
    write_copy_paste_md: bool = True,
    include_unmatched_controller_configs: Optional[bool] = None,
) -> List[str]:
    """Save summary/configs plus fold and block diagnostics.

    `prefix` may be a plain name or a full path. Parent directories are created,
    so notebooks can pass a prefix inside artifacts/{exchange}/{datetime}/files.
    Returns the list of files written, which is useful for manifests and logs.
    """
    import json
    from pathlib import Path

    prefix_path = Path(prefix)
    if prefix_path.parent and str(prefix_path.parent) not in ("", "."):
        prefix_path.parent.mkdir(parents=True, exist_ok=True)
    prefix_str = str(prefix_path)

    written: List[str] = []

    def _write_csv(df: pd.DataFrame, path: str) -> None:
        df.to_csv(path, index=False)
        written.append(path)

    _write_csv(summary_df, f"{prefix_str}_final_summary.csv")
    _write_csv(wf_df, f"{prefix_str}_walkforward_summary.csv")
    deploy_path = f"{prefix_str}_deploy_config.json"
    with open(deploy_path, "w") as f:
        json.dump(configs, f, indent=2, default=str)
    written.append(deploy_path)

    all_folds = []
    all_b45 = []
    all_b60 = []
    for pk, d in details.items():
        folds = d.get("folds")
        if isinstance(folds, pd.DataFrame) and not folds.empty:
            x = folds.copy()
            x.insert(0, "base", pk)
            all_folds.append(x)
        b45 = d.get("block45")
        if isinstance(b45, pd.DataFrame) and not b45.empty:
            x = b45.copy(); x.insert(0, "base", pk); all_b45.append(x)
        b60 = d.get("block60")
        if isinstance(b60, pd.DataFrame) and not b60.empty:
            x = b60.copy(); x.insert(0, "base", pk); all_b60.append(x)
    if all_folds:
        _write_csv(pd.concat(all_folds, ignore_index=True), f"{prefix_str}_fold_details.csv")
    if all_b45:
        _write_csv(pd.concat(all_b45, ignore_index=True), f"{prefix_str}_45d_blocks.csv")
    if all_b60:
        _write_csv(pd.concat(all_b60, ignore_index=True), f"{prefix_str}_60d_blocks.csv")

    if write_copy_paste_md:
        md_path = f"{prefix_str}_copy_paste_ladders.md"
        save_controller_ladder_markdown(
            configs=configs,
            path=md_path,
            controller_yml_paths=controller_yml_paths,
            summary_df=summary_df,
            wf_df=wf_df,
            focus_markets=focus_markets,
            title="Suggested ladder copy/paste values",
            include_unmatched_configs=(not bool(controller_yml_paths)) if include_unmatched_controller_configs is None else bool(include_unmatched_controller_configs),
        )
        written.append(md_path)

    manifest = {
        "engine": "ladder_lab_robust",
        "version": __version__,
        "prefix": prefix_str,
        "files": written,
        "metadata": metadata or {},
    }
    manifest_path = f"{prefix_str}_artifact_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)
    written.append(manifest_path)

    _base._log(f"Saved robust outputs under: {prefix_path.parent if str(prefix_path.parent) else '.'}")
    return written



def walkforward_gate_diagnostics(wf: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Explain which robust-WF acceptance gates passed or failed for one market."""
    if not wf or int(wf.get("n_folds", 0) or 0) <= 0:
        return {"wf_pass": False, "checks": {}, "failed_gates": ["no walk-forward folds"]}
    folds = wf.get("folds")
    if isinstance(folds, pd.DataFrame) and not folds.empty and "test_score" in folds:
        med_score = float(np.median(folds["test_score"].astype(float)))
    else:
        med_score = float(wf.get("median_score", float("nan")))
    checks = dict(
        min_folds=(int(wf.get("n_folds", 0)), ">=", int(cfg.get("gen_min_folds", 0))),
        pos_rate=(float(wf.get("pos_rate", float("nan"))), ">=", float(cfg.get("gen_min_pos_rate", 0))),
        two_sided_rate=(float(wf.get("two_sided_rate", float("nan"))), ">=", float(cfg.get("gen_min_two_sided_rate", 0))),
        median_score=(med_score, ">=", float(cfg.get("gen_min_median_score", 0))),
        median_cons_pct=(float(wf.get("median_cons_pct", float("nan"))), ">=", float(cfg.get("gen_min_median_cons_pct", 0))),
        worst_fold_pct=(float(wf.get("worst_fold_pct", float("nan"))), ">=", float(cfg.get("gen_max_bad_fold_loss_pct", 0))),
    )
    failed: List[str] = []
    for name, (actual, _op, threshold) in checks.items():
        ok = actual == actual and actual >= threshold
        if ok:
            continue
        if isinstance(actual, float):
            failed.append(f"{name}: {actual:.3f} < {float(threshold):.3f}")
        else:
            failed.append(f"{name}: {actual} < {threshold}")
    return dict(wf_pass=bool(wf.get("wf_pass", False)), checks=checks, failed_gates=failed)

# ----------------------------------------------------------------------
# Compatibility helpers for v8/v7 notebooks
# ----------------------------------------------------------------------
def extend_candidates_for_review(
    candidates: Sequence[Any],
    uni: Dict[str, Any],
    cfg: Optional[Dict[str, Any]] = None,
    hist: Optional[Dict[str, Any]] = None,
    optional_focus_markets: Optional[Sequence[Any]] = None,
    focus_only: bool = False,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Return (candidates, status) while forcing always-review/focus markets."""
    cfg = cfg or {}
    always = cfg.get("always_review_markets", DEFAULT_ALWAYS_REVIEW_MARKETS)
    res = force_review_candidates(
        candidates=candidates,
        uni=uni,
        hist=hist,
        always_review_markets=always,
        focus_markets=optional_focus_markets or cfg.get("optional_focus_markets", ()),
        focus_only=focus_only,
        require_history=(hist is not None),
    )
    status = dict(res)
    status["forced_review_markets"] = res.get("forced", [])
    status["present_universe"] = res.get("present", [])
    status["present_history"] = res.get("forced", [])
    status["missing_universe"] = res.get("missing", [])
    status["missing_history"] = res.get("no_history", [])
    return res.get("candidates", []), status


def select_robust_review_markets(
    ev: pd.DataFrame,
    uni: Dict[str, Any],
    cfg: Dict[str, Any],
    always_review_markets: Optional[Iterable[Any]] = None,
    focus_markets: Optional[Iterable[Any]] = None,
    hist: Optional[Dict[str, Any]] = None,
    focus_only: bool = False,
) -> Dict[str, Any]:
    """Select robust-WF candidates while forcing mandatory review markets."""
    ev = ev if isinstance(ev, pd.DataFrame) else pd.DataFrame()
    viable = ev.copy()
    if not viable.empty:
        if "stale" in viable.columns:
            viable = viable[~viable["stale"].astype(bool)]
        if "tier" in viable.columns:
            viable = viable[viable["tier"].astype(str).str.lower() == "full"]

    def _sorted(col: str, n: int, ascending: bool = False) -> List[str]:
        if viable.empty or col not in viable.columns or "base" not in viable.columns:
            return []
        return list(viable.sort_values(col, ascending=ascending).head(min(n, len(viable))).base)

    top_composite = _sorted("composite", int(cfg.get("wf_top_n", 40)), ascending=False)
    top_activity = _sorted("trades_mo", 20, ascending=False)
    old_qualifiers = list(viable[viable["qualifies"] == True].base) if (not viable.empty and "qualifies" in viable.columns and "base" in viable.columns) else []
    positive_diagnostic = list(viable[viable["p12"] > 0].head(min(20, len(viable))).base) if (not viable.empty and "p12" in viable.columns and "base" in viable.columns) else []
    base_candidates = merge_unique_markets(top_composite, top_activity, old_qualifiers, positive_diagnostic)
    if cfg.get("wf_max_candidates") is not None:
        base_candidates = base_candidates[:int(cfg.get("wf_max_candidates"))]

    always_requested = merge_unique_markets(cfg.get("always_review_markets", DEFAULT_ALWAYS_REVIEW_MARKETS) if always_review_markets is None else always_review_markets)
    focus_requested = merge_unique_markets(cfg.get("optional_focus_markets", ()) if focus_markets is None else focus_markets)
    all_requested = merge_unique_markets(always_requested, focus_requested)
    status = force_review_candidates(
        base_candidates,
        uni,
        hist=hist,
        always_review_markets=always_requested,
        focus_markets=focus_requested,
        focus_only=focus_only,
        require_history=(hist is not None),
    )
    always_status = market_presence_status(uni, always_requested, hist=hist)
    focus_status = market_presence_status(uni, focus_requested, hist=hist)
    return dict(
        candidates=status["candidates"],
        base_candidates=base_candidates,
        always_requested=always_requested,
        always_present=always_status["present_history"] if hist is not None else always_status["present_universe"],
        always_missing=always_status["missing_universe"],
        always_missing_history=always_status["missing_history"],
        focus_requested=focus_requested,
        focus_present=focus_status["present_history"] if hist is not None else focus_status["present_universe"],
        focus_missing=focus_status["missing_universe"],
        focus_missing_history=focus_status["missing_history"],
        forced_review=status["forced"],
        requested=all_requested,
    )


# ----------------------------------------------------------------------
# Final always-review overrides
# ----------------------------------------------------------------------
def extend_candidates_for_review(
    candidates: Sequence[Any],
    uni: Dict[str, Any],
    cfg: Optional[Dict[str, Any]] = None,
    hist: Optional[Dict[str, Any]] = None,
    optional_focus_markets: Optional[Sequence[Any]] = None,
    focus_only: bool = False,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Return (candidates, status) while forcing always-review/focus markets.

    Present markets are added even when history failed to load. Downstream walk-forward
    and finalize outputs then show an explicit missing-history/SUSPECT row instead of
    silently dropping the market.
    """
    cfg = cfg or {}
    always = cfg.get("always_review_markets", DEFAULT_ALWAYS_REVIEW_MARKETS)
    focus = optional_focus_markets if optional_focus_markets is not None else cfg.get("optional_focus_markets", ())
    res = force_review_candidates(
        candidates=candidates,
        uni=uni,
        hist=hist,
        always_review_markets=always,
        focus_markets=focus,
        focus_only=focus_only,
        require_history=False,
    )
    status = dict(res)
    status["forced_review_markets"] = res.get("present", [])
    status["present_universe"] = res.get("present", [])
    status["missing_universe"] = res.get("missing", [])
    status["present_history"] = [pk for pk in res.get("present", []) if hist is not None and pk in hist] if hist is not None else []
    status["missing_history"] = [pk for pk in res.get("present", []) if hist is not None and pk not in hist] if hist is not None else []
    return res.get("candidates", []), status


def select_robust_review_markets(
    ev: pd.DataFrame,
    uni: Dict[str, Any],
    cfg: Dict[str, Any],
    always_review_markets: Optional[Iterable[Any]] = None,
    focus_markets: Optional[Iterable[Any]] = None,
    hist: Optional[Dict[str, Any]] = None,
    focus_only: bool = False,
) -> Dict[str, Any]:
    """Select robust-WF candidates while forcing mandatory review markets.

    `always_review_markets` are appended after normal candidate caps. If one exists
    on the exchange but history is unavailable, it is still returned in `candidates`
    so robust outputs can record a missing-history row.
    """
    ev = ev if isinstance(ev, pd.DataFrame) else pd.DataFrame()
    viable = ev.copy()
    if not viable.empty:
        if "stale" in viable.columns:
            viable = viable[~viable["stale"].fillna(False).astype(bool)]
        if "tier" in viable.columns:
            viable = viable[viable["tier"].astype(str).str.lower() == "full"]

    def _sorted(col: str, n: int, ascending: bool = False) -> List[str]:
        if viable.empty or col not in viable.columns or "base" not in viable.columns:
            return []
        return list(viable.sort_values(col, ascending=ascending).head(min(n, len(viable))).base)

    top_composite = _sorted("composite", int(cfg.get("wf_top_n", 40)), ascending=False)
    top_activity = _sorted("trades_mo", 20, ascending=False)
    old_qualifiers = list(viable[viable["qualifies"] == True].base) if (not viable.empty and "qualifies" in viable.columns and "base" in viable.columns) else []
    positive_diagnostic = list(viable[viable["p12"] > 0].head(min(20, len(viable))).base) if (not viable.empty and "p12" in viable.columns and "base" in viable.columns) else []
    base_candidates = merge_unique_markets(top_composite, top_activity, old_qualifiers, positive_diagnostic)
    if cfg.get("wf_max_candidates") is not None:
        base_candidates = base_candidates[:int(cfg.get("wf_max_candidates"))]

    always_requested = merge_unique_markets(always_review_markets or cfg.get("always_review_markets", DEFAULT_ALWAYS_REVIEW_MARKETS))
    focus_requested = merge_unique_markets(focus_markets or cfg.get("optional_focus_markets", ()))
    candidates, status = extend_candidates_for_review(
        base_candidates,
        uni,
        cfg={**cfg, "always_review_markets": tuple(always_requested), "optional_focus_markets": tuple(focus_requested)},
        hist=hist,
        optional_focus_markets=focus_requested,
        focus_only=focus_only,
    )
    always_status = market_presence_status(uni, always_requested, hist=hist)
    focus_status = market_presence_status(uni, focus_requested, hist=hist)
    return dict(
        candidates=candidates,
        base_candidates=base_candidates,
        always_requested=always_requested,
        always_present=always_status["present_universe"],
        always_missing=always_status["missing_universe"],
        always_present_with_history=always_status["present_history"],
        always_missing_history=always_status["missing_history"],
        focus_requested=focus_requested,
        focus_present=focus_status["present_universe"],
        focus_missing=focus_status["missing_universe"],
        focus_present_with_history=focus_status["present_history"],
        focus_missing_history=focus_status["missing_history"],
        forced_review=status.get("present_universe", status.get("forced_review_markets", [])),
        requested=merge_unique_markets(always_requested, focus_requested),
    )

