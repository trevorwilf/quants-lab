"""Regression for the 2026-05-29 lake-root silent-failure bug.

Pre-fix symptom: a workstation cfg without ``market_data.shared_root``
caused the walkforward worker dispatch to pass ``None`` to the supplier
factories. The suppliers silently read from ``Path("None")``, returned
empty DataFrames, and the worker reported
``n_trades=0, fold_status='ok', historical_quote_coverage_pct=100.0``
with no error raised.

Post-fix: any code path that bypasses :func:`resolve_lake_root` and passes
``None`` to a supplier MUST raise :class:`RuntimeError` at the boundary
(via :func:`_coerce_lake_root`), not silently produce zero results.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.data.lineage import _coerce_lake_root, resolve_lake_root


def test_resolve_lake_root_does_not_return_path_none_for_workstation_cfg():
    """The operator's actual workstation cfg shape (no shared_root key set)
    must resolve to a real path, not ``Path('None')``."""
    cfg = {
        "market_data": {
            "feed": "iex",
            "require_adjusted_daily_bars": True,
            "require_split_adjustment": True,
            # NB: deliberately no 'shared_root' key — matches the operator's
            # actual workstation YAML that triggered the bug.
        },
    }
    got = resolve_lake_root(cfg)
    assert got.name != "None", (
        "resolve_lake_root must not return Path('None') even when "
        "cfg.market_data.shared_root is unset"
    )


def test_coerce_lake_root_rejects_md_lookup_returning_none():
    """Direct boundary check: the value the raw cfg lookup returns for a
    cfg without a shared_root key (``None``) must be loudly rejected,
    never silently passed downstream."""
    md = {"feed": "iex"}  # no shared_root key
    value = md.get("shared_root")
    assert value is None  # baseline
    with pytest.raises(RuntimeError, match="None"):
        _coerce_lake_root(value)


def test_no_remaining_buggy_pattern_in_critical_paths():
    """AST-level regression: the buggy substring must not exist in any of
    the critical-path modules. We allow it in ``data/lineage.py`` — the
    ONE place the resolver legitimately consults ``cfg.market_data.shared_root``
    (and immediately delegates to the resolver chain)."""
    from pathlib import Path as P

    repo = P(__file__).resolve().parents[3]
    critical = [
        "src/bowaka_v2_lab/optuna/walkforward_runner.py",
        "src/bowaka_v2_lab/optuna/holdout.py",
        "src/bowaka_v2_lab/sim/backtester.py",
        "src/bowaka_v2_lab/backtest_runner.py",
        "src/bowaka_v2_lab/cli_runners.py",
        "src/bowaka_v2_lab/scanner/scan_matrix.py",
        "src/bowaka_v2_lab/reconcile/replay.py",
    ]
    offenders = []
    for rel in critical:
        src = (repo / rel).read_text(encoding="utf-8")
        if 'md.get("shared_root")' in src:
            offenders.append(rel)
        if "md.get('shared_root')" in src:
            offenders.append(rel)
    assert not offenders, (
        f"Files still using the raw cfg-lookup pattern; route through "
        f"resolve_lake_root(cfg) instead:\n  - " + "\n  - ".join(offenders)
    )
