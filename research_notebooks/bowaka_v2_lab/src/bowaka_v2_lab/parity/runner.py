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
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

_LAB_ROOT = Path(__file__).resolve().parents[2]


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
    python_exe: str = "py",
    python_extra: Sequence[str] = ("-3.12",),
    timeout_sec: int = 600,
    prod_script: Path | None = None,
) -> ProductionRunResult:
    """Shell out to the production backtester via subprocess.

    Post-Phase-0 fix, this reads from the real lake. Use the ``--lake-root``
    override to pin both sides to the same lake even if the production
    config's resolution chain differs from the lab's.

    The default ``python_exe="py"`` plus ``python_extra=("-3.12",)`` matches
    the operator's box (default ``python`` is 3.14 and missing pyarrow).
    Tests override with the current interpreter's ``sys.executable``.
    """
    if prod_script is None:
        prod_script = (
            _LAB_ROOT / "reference" / "source_strategy" / "scripts"
            / "bowaka_v2_backtest.py"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        python_exe,
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
    """Call the lab's ``run_config_backtest`` in-process.

    Symbols are injected by mutating the loaded config's ``universe.symbols``
    (the same field ``resolve_symbols`` reads first). The window is injected
    via ``sessions=[date, ...]`` so ``config_sessions`` is not consulted —
    the call works regardless of what the config's ``backtest.start_date`` /
    ``backtest.end_date`` happen to be.

    ``cost_stress`` is wired through ``param_overrides`` so the same stress
    label both sides see picks the same cost-model row. The config's default
    stress label remains in effect when ``cost_stress`` is None or unset.
    """
    import exchange_calendars as xcals
    import pandas as pd

    from ..backtest_runner import run_config_backtest
    from ..config import load_config

    cfg = load_config(lab_config_path)
    cfg.setdefault("universe", {})["symbols"] = [str(s) for s in symbols]
    cal = xcals.get_calendar("XNYS")
    sessions = [
        pd.Timestamp(s).date()
        for s in cal.sessions_in_range(pd.Timestamp(start_date), pd.Timestamp(end_date))
    ] or [start_date]
    overrides: dict[str, Any] | None = None
    if cost_stress:
        overrides = {"cost_model": {"stress_label": cost_stress}}
    return run_config_backtest(
        cfg,
        param_overrides=overrides,
        sessions=sessions,
        run_dir=run_dir,
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
    python_exe: str = "py",
    python_extra: Sequence[str] = ("-3.12",),
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
