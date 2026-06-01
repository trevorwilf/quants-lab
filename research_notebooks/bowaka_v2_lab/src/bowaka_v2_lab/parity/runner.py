"""Production-vs-lab parity runner.

Orchestrates a paired run of the production-side ``bowaka_v2_backtest.py``
(via subprocess) and the lab's :func:`bowaka_v2_lab.backtest_runner.run_config_backtest`
(in-process), then folds both sides' outputs into a :class:`~.schemas.ParityReport`.

Post-Phase-0, the production backtester reads the real lake (or a passed
``--lake-root``), so this runner can pin both sides to the same lake and the
parity metrics are meaningful.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

_LAB_ROOT = Path(__file__).resolve().parents[3]   # src/bowaka_v2_lab/parity/runner.py -> lab root
_BOWAKA_COMMON_SRC = (_LAB_ROOT.parent / "bowaka_common" / "src").resolve()


def build_parity_universe(
    *,
    start_date: _dt.date,
    end_date: _dt.date,
    lab_config_path: Path,
    lake_root: Path | None = None,
    max_universe_size: int | None = None,
) -> list[str]:
    """Resolve the symbols both sides should monitor — the bowaka v2 PIT screen.

    Bowaka v2's actual flow is **screen the universe via PIT (asset master +
    prior-day baselines) → monitor the survivors intraday**. To make the
    parity check mirror that, this helper:

      1. Loads the lab config (PIT criteria live under ``universe:``).
      2. Resolves the XNYS sessions in ``[start_date, end_date]``.
      3. Builds the PIT records for each session via
         :func:`build_pit_universe_for_sessions`.
      4. Reduces to ``eligible_for_bowaka_equity_bucket`` (the survivors of
         the strategy's universe screen) via :func:`eligible_symbols`.
      5. Returns the **union** of eligibles across the window, sorted.

    The production side then takes that exact symbol list via ``--symbols``
    and the lab side intersects its own PIT records with it. Both sides
    therefore monitor the same universe — what the live strategy would.

    ``max_universe_size`` (default None) caps the result for fast smoke
    runs; ``None`` returns the full PIT-resolved universe and is the right
    default for a "real" parity run.
    """
    import exchange_calendars as xcals
    import pandas as pd

    from ..cli_runners import _lake_store
    from ..config import load_config
    from ..universe.builder import build_pit_universe_for_sessions, eligible_symbols

    cfg = load_config(lab_config_path)
    if lake_root is not None:
        cfg.setdefault("market_data", {})["shared_root"] = str(lake_root)
    cal = xcals.get_calendar("XNYS")
    sessions = [
        pd.Timestamp(s).date()
        for s in cal.sessions_in_range(pd.Timestamp(start_date), pd.Timestamp(end_date))
    ] or [start_date]
    store = _lake_store(cfg.get("market_data") or {})
    by_session = build_pit_universe_for_sessions(sessions, cfg, store)
    union: set[str] = set()
    for records in by_session.values():
        union.update(eligible_symbols(records))
    out = sorted(union)
    if max_universe_size is not None and max_universe_size > 0:
        out = out[:max_universe_size]
    return out


def _build_subprocess_env(extra_paths: Sequence[Path] = ()) -> dict[str, str]:
    """Build a subprocess env that pins PYTHONPATH to the lab + bowaka_common.

    The notebook bootstrap inserts the right entries into ``sys.path`` for the
    current process but does **not** export ``PYTHONPATH`` to the environment,
    so subprocess children (the production backtester) don't inherit it. Inject
    explicitly so ``import bowaka_common`` resolves inside the subprocess.

    Existing ``PYTHONPATH`` entries (if any) are preserved and appended after
    ours so caller-set paths still win for collisions on their own packages.
    """
    paths: list[str] = []
    for p in [_LAB_ROOT / "src", _BOWAKA_COMMON_SRC, *extra_paths]:
        s = str(Path(p).resolve())
        if s not in paths:
            paths.append(s)
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    if existing:
        for chunk in existing.split(os.pathsep):
            if chunk and chunk not in paths:
                paths.append(chunk)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


@dataclass(frozen=True)
class ProductionRunResult:
    """Result of one production-side run.

    ``trades_path`` is the parquet (or json fallback) ``run_production_backtester``
    points the normalizer at. The mirror at dev HEAD writes
    ``trades.parquet`` (BacktestTrade-shape); older mirrors may have written
    ``trades.json`` instead, so the normalizer probes both.
    """

    output_dir: Path
    summary: dict
    trades_path: Path
    returncode: int
    stdout: str
    stderr: str


def run_production_backtester(
    *,
    start_date: _dt.date,
    end_date: _dt.date,
    symbols_file: Path,
    prod_config_path: Path,
    lake_root: Path | None,
    cost_stress: str = "conservative",
    ablation: str = "none",
    output_dir: Path,
    python_exe: str | None = None,
    python_extra: Sequence[str] = (),
    timeout_sec: int = 1800,
    prod_script: Path | None = None,
    progress_log: Path | None = None,
) -> ProductionRunResult:
    """Shell out to the production backtester via subprocess.

    Post-Phase-0 fix, this reads from the real lake. Use the ``--lake-root``
    override to pin both sides to the same lake even if the production
    config's resolution chain differs from the lab's.

    ``python_exe=None`` (the default) resolves to ``sys.executable`` — the
    interpreter running this code, which is the right default on every host
    (Linux container, Windows bare host, CI) because it inherits the same
    site-packages and env. Operators who specifically need the Windows
    ``py -3.12`` launcher can pass ``python_exe="py", python_extra=("-3.12",)``.
    """
    if prod_script is None:
        prod_script = (
            _LAB_ROOT / "reference" / "source_strategy" / "scripts"
            / "bowaka_v2_backtest.py"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    exe = python_exe or sys.executable
    cmd = [
        exe,
        *python_extra,
        str(prod_script),
        "--config", str(prod_config_path),
        "--from", start_date.isoformat(),
        "--to", end_date.isoformat(),
        "--symbols", str(symbols_file),
        "--output-dir", str(output_dir),
        "--cost-stress", cost_stress,
        "--ablation", ablation,
    ]
    if lake_root is not None:
        cmd.extend(["--lake-root", str(lake_root)])
    # Default a progress log inside the output dir so long runs are observable
    # via ``tail -f`` while the subprocess is still running.
    if progress_log is None:
        progress_log = output_dir / "production.stderr.log"
    progress_log = Path(progress_log)
    progress_log.parent.mkdir(parents=True, exist_ok=True)
    try:
        with progress_log.open("w", encoding="utf-8", buffering=1) as stderr_fh:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=stderr_fh,
                text=True,
                timeout=timeout_sec,
                check=False,
                env=_build_subprocess_env(),
            )
        stderr_text = progress_log.read_text(encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired as exc:
        tail = ""
        if progress_log.is_file():
            tail = progress_log.read_text(encoding="utf-8", errors="replace")
        raise RuntimeError(
            f"production backtester timed out after {timeout_sec}s. "
            f"For a real-universe window this is normal — reduce the window or "
            f"set MAX_UNIVERSE_SIZE / --max-universe-size to cap the screened "
            f"universe for a fast smoke first. Raise the cap with "
            f"`timeout_sec=` (run_parity) or `--timeout-sec` (CLI).\n"
            f"PROGRESS LOG TAIL (last 2000 chars at {progress_log}):\n"
            f"{tail[-2000:]}"
        ) from exc
    summary_path = output_dir / "summary.json"
    summary: dict = {}
    if summary_path.is_file():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — malformed summary surfaces as empty
            summary = {}
    # Probe parquet first (dev HEAD), then json (older mirror).
    trades_parquet = output_dir / "trades.parquet"
    trades_json = output_dir / "trades.json"
    trades_path = trades_parquet if trades_parquet.is_file() else trades_json
    return ProductionRunResult(
        output_dir=output_dir,
        summary=summary,
        trades_path=trades_path,
        returncode=proc.returncode,
        stdout=proc.stdout if proc.stdout is not None else "",
        stderr=stderr_text,
    )


def run_lab_backtester(
    *,
    start_date: _dt.date,
    end_date: _dt.date,
    symbols: Sequence[str],
    lab_config_path: Path,
    cost_stress: str = "conservative",
    run_dir: Path | None = None,
) -> Any:
    """Run the lab backtester in-process against a small parity universe.

    For non-smoke configs (``simulation.mode != 'smoke_fixture'``), the lab
    refuses synthetic universes — it requires the point-in-time universe built
    from the lake asset snapshot + prior-day bars. ``run_config_backtest``
    always wraps symbols in :func:`synthetic_universe`, so it can't be used
    here; this function instead replicates ``cli_runners.run_backtest_command``'s
    PIT-aware path and then intersects the PIT records with the parity
    ``symbols`` set so both sides see the same small universe.

    ``cost_stress`` is threaded through ``apply_overrides`` so the same stress
    label both sides see picks the same cost-model row. The window is
    materialized to ``sessions=[date, ...]`` so ``config_sessions`` is not
    consulted.
    """
    import exchange_calendars as xcals
    import pandas as pd

    from ..backtest_runner import apply_overrides
    from ..cli_runners import _is_smoke, _lake_store, _uses_lake
    from ..config import BowakaV2Paths, load_config
    from ..config.models import BowakaV2Config
    from ..data.adjustment import daily_adjustment_for_config
    from ..data.suppliers import (
        build_daily_cache_from_lake,
        make_forward_minute_supplier,
        make_lake_suppliers,
        make_quote_supplier,
        resolve_intraday_window_policy,
    )
    from ..sim.backtester import run_backtest
    from ..sim.replay_fixtures import synthetic_daily_cache, synthetic_universe
    from ..sim.schedule import scan_times_for_session
    from ..universe.builder import build_pit_universe_for_sessions

    cfg = load_config(lab_config_path)
    if cost_stress:
        cfg = apply_overrides(cfg, {"backtest": {"cost_stress": cost_stress}})
    validated = BowakaV2Config.model_validate(cfg)
    repo_root = Path(__file__).resolve().parents[4]
    paths = BowakaV2Paths.from_config(validated, repo_root=repo_root)
    paths.assert_strategy_isolation()
    md = cfg.get("market_data", {}) or {}

    cal = xcals.get_calendar("XNYS")
    sessions = [
        pd.Timestamp(s).date()
        for s in cal.sessions_in_range(pd.Timestamp(start_date), pd.Timestamp(end_date))
    ] or [start_date]
    parity_syms = sorted({str(s) for s in symbols})

    quote_supplier = None
    forward_minute_supplier = None
    if _uses_lake(cfg):
        from ..data.lineage import _coerce_lake_root, resolve_lake_root

        feed = md.get("feed", "iex")
        root = _coerce_lake_root(resolve_lake_root(cfg))
        adjustment = daily_adjustment_for_config(cfg)
        minute_supplier, daily_supplier = make_lake_suppliers(
            root, feed=feed,
            intraday_window_policy=resolve_intraday_window_policy(cfg),
            daily_adjustment=adjustment,
        )
        daily_cache = {
            s: build_daily_cache_from_lake(
                root, parity_syms, s, feed=feed, daily_adjustment=adjustment,
            )
            for s in sessions
        }
        quote_supplier = make_quote_supplier(
            root, feed=feed,
            default_max_age_seconds=float(
                (cfg.get("execution") or {}).get("max_quote_age_seconds", 60)
            ),
        )
        forward_minute_supplier = make_forward_minute_supplier(root, feed=feed)
    else:
        from ..backtest_runner import resolve_suppliers
        minute_supplier, daily_supplier = resolve_suppliers(cfg)
        daily_cache = {s: synthetic_daily_cache(parity_syms) for s in sessions}

    if _is_smoke(validated):
        universe = {s: synthetic_universe(parity_syms) for s in sessions}
    else:
        store = _lake_store(md)
        full_pit = build_pit_universe_for_sessions(sessions, cfg, store)
        parity_set = set(parity_syms)
        universe = {
            s: {sym: rec for sym, rec in (full_pit.get(s) or {}).items() if sym in parity_set}
            for s in sessions
        }

    return run_backtest(
        cfg=cfg,
        sessions=sessions,
        scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=minute_supplier,
        daily_bars_supplier=daily_supplier,
        quote_supplier=quote_supplier,
        forward_minute_supplier=forward_minute_supplier,
        initial_bankroll=100_000.0,
        paths=paths,
        run_dir=Path(run_dir) if run_dir else None,
    )


def _fmt_eta(seconds: float) -> str:
    """Compact ETA string: ``45s``, ``12m05s``, ``1h08m``."""
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds // 60)}m{int(seconds % 60):02d}s"
    return f"{int(seconds // 3600)}h{int((seconds % 3600) // 60):02d}m"


def _xnys_sessions(start_date: _dt.date, end_date: _dt.date) -> list[_dt.date]:
    import exchange_calendars as xcals
    import pandas as pd

    cal = xcals.get_calendar("XNYS")
    sessions = [
        pd.Timestamp(s).date()
        for s in cal.sessions_in_range(pd.Timestamp(start_date), pd.Timestamp(end_date))
    ]
    return sessions or [start_date]


def _per_session_eligible_symbols(
    sessions: Sequence[_dt.date],
    *,
    lab_config_path: Path,
    lake_root: Path | None,
    restrict_to: Sequence[str] | None = None,
) -> dict[_dt.date, list[str]]:
    """PIT eligible-survivor symbols per session, bounded by ``restrict_to``.

    Phase 0 (universe symmetry): production used to monitor the window-UNION of
    eligibles on every session (one ``universe.txt``), so it watched symbols on
    sessions where they were not PIT-eligible — diverging from the live flow.
    This builds the PIT once for the window and returns each session's eligible
    survivors, so the chunked runner can hand production the right per-session
    symbol list. The lab side already intersects its own PIT per session, so this
    makes both sides symmetric.

    ``restrict_to`` (the parity universe the caller passed — possibly capped via
    ``max_universe_size`` or given explicitly) bounds each per-session set,
    EXACTLY as the lab intersects its PIT with the parity universe. Without it a
    capped / smoke run would silently expand back to the full ~703-symbol PIT.
    """
    from ..cli_runners import _lake_store
    from ..config import load_config
    from ..universe.builder import build_pit_universe_for_sessions, eligible_symbols

    cfg = load_config(lab_config_path)
    if lake_root is not None:
        cfg.setdefault("market_data", {})["shared_root"] = str(lake_root)
    store = _lake_store(cfg.get("market_data") or {})
    by_session = build_pit_universe_for_sessions(list(sessions), cfg, store)
    restrict = set(restrict_to) if restrict_to is not None else None
    return {
        s: sorted(
            sym for sym in eligible_symbols(by_session.get(s) or {})
            if restrict is None or sym in restrict
        )
        for s in sessions
    }


def run_parity(
    *,
    start_date: _dt.date,
    end_date: _dt.date,
    symbols: Sequence[str],
    prod_config_path: Path,
    lab_config_path: Path,
    lake_root: Path,
    cost_stress: str = "conservative",
    run_root: Path,
    python_exe: str | None = None,
    python_extra: Sequence[str] = (),
    prod_script: Path | None = None,
    timeout_sec: int = 1800,
    chunk_per_session: bool = False,
    per_session_universe: bool = True,
    bundle_out: Path | None = None,
    print_progress: bool = True,
    progress_callback: Callable[[dict], None] | None = None,
) -> Any:
    """End-to-end: run both backtesters, normalize, return a :class:`ParityReport`.

    Two modes:

    - ``chunk_per_session=False`` (default): one prod subprocess and one lab
      run_backtest cover the whole window. Canonical numerics — portfolio
      state carries across sessions on the lab side. **No progress visibility
      until both finish.**

    - ``chunk_per_session=True``: the window is iterated session-by-session.
      Each session is a 1-day prod subprocess + a 1-day lab run, timed
      independently. After every session the runner prints

          [  5/255] 2026-05-19 prod= 12.3s lab=  8.7s avg=p12.5/l8.9 \\
                    ptrades=2 ltrades=1 eta=1h08m

      and invokes ``progress_callback`` (if given) with the same metrics in
      a dict shape. **Trade-off**: each lab session starts at the
      ``initial_bankroll`` instead of carry-forward equity, so sizing-
      dependent trade quantities can differ from the full-window run. Trade
      counts, entry/exit times, and exit reasons are unaffected — the
      strategy decisions don't depend on bankroll. Use this when you need
      progress visibility on a long parity run; flip back to ``False`` for
      sign-off numerics on the same window.

    Either way, this returns a single :class:`ParityReport` covering the
    full window — the chunking is purely an execution-shape concern.

    Universe contract (Phase 0): with ``per_session_universe=True`` (default)
    the chunked path hands production the PIT eligible-survivor set for EACH
    session (one symbols file per session), matching the live
    screen-per-session flow and the lab's per-session PIT intersection. Set
    ``per_session_universe=False`` to fall back to the legacy window-union
    ``universe.txt`` for every session.
    """
    from .metrics import compute_parity_metrics
    from .normalizers import normalize_lab_output, normalize_production_output

    run_root = Path(run_root)
    run_root.mkdir(parents=True, exist_ok=True)
    # Legacy window-union universe file (back-compat + the non-chunked path).
    symbols_file = run_root / "universe.txt"
    symbols_file.write_text("\n".join(str(s) for s in symbols) + "\n", encoding="utf-8")

    # The requested XNYS session list — threaded into the report so n_sessions
    # reflects requested coverage, not just trade-bearing sessions (Phase 0).
    requested_sessions = _xnys_sessions(start_date, end_date)

    if not chunk_per_session:
        prod = run_production_backtester(
            start_date=start_date,
            end_date=end_date,
            symbols_file=symbols_file,
            prod_config_path=Path(prod_config_path),
            lake_root=Path(lake_root) if lake_root is not None else None,
            cost_stress=cost_stress,
            output_dir=run_root / "production",
            python_exe=python_exe,
            python_extra=python_extra,
            prod_script=prod_script,
            timeout_sec=timeout_sec,
        )
        if prod.returncode != 0:
            raise RuntimeError(
                "production backtester failed "
                f"(exit {prod.returncode}):\n"
                f"STDOUT (tail): {prod.stdout[-2000:]}\n"
                f"STDERR (tail): {prod.stderr[-2000:]}"
            )

        lab = run_lab_backtester(
            start_date=start_date,
            end_date=end_date,
            symbols=symbols,
            lab_config_path=Path(lab_config_path),
            cost_stress=cost_stress,
            run_dir=run_root / "lab",
        )

        prod_trades, prod_cands = normalize_production_output(prod)
        lab_trades, lab_cands = normalize_lab_output(lab)
        report = compute_parity_metrics(
            window_start=start_date,
            window_end=end_date,
            universe_size=len(list(symbols)),
            prod_trades=prod_trades,
            prod_candidates=prod_cands,
            lab_trades=lab_trades,
            lab_candidates=lab_cands,
            prod_summary=prod.summary,
            lab_result=lab,
            requested_sessions=requested_sessions,
        )
        if bundle_out is not None:
            from .golden import persist_parity_bundle
            persist_parity_bundle(
                bundle_out, report=report, prod_trades=prod_trades,
                lab_trades=lab_trades, lab_candidates=lab_cands,
            )
        return report

    # Per-session chunked path.
    sessions = requested_sessions
    # Phase 0 (universe symmetry): hand production the PIT eligible-survivor set
    # for EACH session (one symbols file per session), matching the live
    # screen-per-session flow and the lab's per-session intersection. The legacy
    # window-union file stays available via ``per_session_universe=False``.
    per_sess_syms: dict[_dt.date, list[str]] = {}
    sess_symbol_file: dict[_dt.date, Path] = {}
    if per_session_universe:
        per_sess_syms = _per_session_eligible_symbols(
            sessions, lab_config_path=Path(lab_config_path),
            lake_root=Path(lake_root) if lake_root is not None else None,
            restrict_to=symbols,
        )
        uni_dir = run_root / "universe"
        uni_dir.mkdir(parents=True, exist_ok=True)
        for _s in sessions:
            _f = uni_dir / f"{_s.isoformat()}.txt"
            _f.write_text("\n".join(per_sess_syms.get(_s, [])) + "\n", encoding="utf-8")
            sess_symbol_file[_s] = _f
    all_prod_trades: list = []
    all_lab_trades: list = []
    all_lab_cands: list = []
    timings: list[tuple[float, float]] = []
    overall_t0 = time.monotonic()

    def _emit(line: str) -> None:
        """Print + force-flush. Jupyter's stdout shim usually flushes per-print,
        but explicit flushing guards against buffering when a subprocess.run
        blocks the main thread for many minutes between status lines."""
        sys.stdout.write(line + "\n")
        sys.stdout.flush()

    if print_progress:
        _emit(f"[parity] chunked mode: {len(sessions)} sessions x prod subprocess + lab run")
        _emit(f"[parity] universe={len(list(symbols))} symbols  timeout/session={timeout_sec}s")
        if len(sessions) > 0:
            _emit(
                f"[parity] starting session 1/{len(sessions)} "
                f"({sessions[0].isoformat()}) — first line tells you we're live"
            )
    width = max(1, len(str(len(sessions))))
    for i, sd in enumerate(sessions):
        session_iso = sd.isoformat()
        tag = f"  [{i + 1:>{width}}/{len(sessions):<{width}}] {session_iso}"
        if print_progress:
            _emit(f"{tag}  prod: starting subprocess at {_dt.datetime.now().strftime('%H:%M:%S')}")
        t0 = time.monotonic()
        sess_syms = (
            per_sess_syms.get(sd, list(symbols)) if per_session_universe
            else list(symbols)
        )
        prod = run_production_backtester(
            start_date=sd, end_date=sd,
            symbols_file=sess_symbol_file.get(sd, symbols_file),
            prod_config_path=Path(prod_config_path),
            lake_root=Path(lake_root) if lake_root is not None else None,
            cost_stress=cost_stress,
            output_dir=run_root / "production" / session_iso,
            python_exe=python_exe, python_extra=python_extra,
            prod_script=prod_script, timeout_sec=timeout_sec,
        )
        prod_secs = time.monotonic() - t0
        if prod.returncode != 0:
            raise RuntimeError(
                f"production backtester failed on session {session_iso} "
                f"(exit {prod.returncode}):\n"
                f"STDOUT (tail): {prod.stdout[-2000:]}\n"
                f"STDERR (tail): {prod.stderr[-2000:]}"
            )
        if print_progress:
            _emit(
                f"{tag}  prod done in {prod_secs:5.1f}s  "
                f"lab: starting in-process at {_dt.datetime.now().strftime('%H:%M:%S')}"
            )

        t1 = time.monotonic()
        lab = run_lab_backtester(
            start_date=sd, end_date=sd, symbols=sess_syms,
            lab_config_path=Path(lab_config_path),
            cost_stress=cost_stress, run_dir=run_root / "lab" / session_iso,
        )
        lab_secs = time.monotonic() - t1

        pt, _ = normalize_production_output(prod)
        lt, lc = normalize_lab_output(lab)
        all_prod_trades.extend(pt)
        all_lab_trades.extend(lt)
        all_lab_cands.extend(lc)
        timings.append((prod_secs, lab_secs))
        avg_prod = sum(p for p, _ in timings) / len(timings)
        avg_lab = sum(l for _, l in timings) / len(timings)
        remaining_sessions = len(sessions) - (i + 1)
        eta_seconds = remaining_sessions * (avg_prod + avg_lab)
        prog = {
            "session_idx": i + 1,
            "total_sessions": len(sessions),
            "session_date": sd,
            "prod_seconds": prod_secs,
            "lab_seconds": lab_secs,
            "prod_trades_this_session": len(pt),
            "lab_trades_this_session": len(lt),
            "avg_prod_seconds": avg_prod,
            "avg_lab_seconds": avg_lab,
            "elapsed_seconds": time.monotonic() - overall_t0,
            "est_remaining_seconds": eta_seconds,
        }
        if print_progress:
            _emit(
                f"{tag}  done: prod={prod_secs:5.1f}s lab={lab_secs:5.1f}s "
                f"avg=p{avg_prod:.1f}/l{avg_lab:.1f} "
                f"ptrades={len(pt)} ltrades={len(lt)} "
                f"eta={_fmt_eta(eta_seconds)}"
            )
        if progress_callback is not None:
            progress_callback(prog)

    if print_progress:
        elapsed = time.monotonic() - overall_t0
        total_pt = len(all_prod_trades)
        total_lt = len(all_lab_trades)
        _emit(
            f"[parity] done in {_fmt_eta(elapsed)}: "
            f"prod_trades={total_pt} lab_trades={total_lt}"
        )

    report = compute_parity_metrics(
        window_start=start_date,
        window_end=end_date,
        universe_size=len(list(symbols)),
        prod_trades=all_prod_trades,
        prod_candidates=[],
        lab_trades=all_lab_trades,
        lab_candidates=all_lab_cands,
        requested_sessions=requested_sessions,
    )
    if bundle_out is not None:
        from .golden import persist_parity_bundle
        persist_parity_bundle(
            bundle_out, report=report, prod_trades=all_prod_trades,
            lab_trades=all_lab_trades, lab_candidates=all_lab_cands,
        )
    return report


__all__ = [
    "ProductionRunResult",
    "build_parity_universe",
    "run_production_backtester",
    "run_lab_backtester",
    "run_parity",
]
