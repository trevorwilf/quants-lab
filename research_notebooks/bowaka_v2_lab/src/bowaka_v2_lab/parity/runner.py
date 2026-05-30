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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

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
    timeout_sec: int = 600,
    prod_script: Path | None = None,
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
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout_sec, check=False,
        env=_build_subprocess_env(),
    )
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
        stdout=proc.stdout,
        stderr=proc.stderr,
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
        feed = md.get("feed", "iex")
        root = md.get("shared_root")
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
) -> Any:
    """End-to-end: run both backtesters, normalize, return a :class:`ParityReport`."""
    from .metrics import compute_parity_metrics
    from .normalizers import normalize_lab_output, normalize_production_output

    run_root = Path(run_root)
    run_root.mkdir(parents=True, exist_ok=True)
    symbols_file = run_root / "universe.txt"
    symbols_file.write_text("\n".join(str(s) for s in symbols) + "\n", encoding="utf-8")

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
    return compute_parity_metrics(
        window_start=start_date,
        window_end=end_date,
        universe_size=len(list(symbols)),
        prod_trades=prod_trades,
        prod_candidates=prod_cands,
        lab_trades=lab_trades,
        lab_candidates=lab_cands,
        prod_summary=prod.summary,
        lab_result=lab,
    )


__all__ = [
    "ProductionRunResult",
    "run_production_backtester",
    "run_lab_backtester",
    "run_parity",
]
