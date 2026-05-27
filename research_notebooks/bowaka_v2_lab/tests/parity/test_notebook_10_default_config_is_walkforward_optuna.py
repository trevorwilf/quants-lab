"""Notebook 10's default ``CONFIG_PATH`` points at a walk-forward Optuna config.

Realism remediation 2 Phase 12 (CLAUDE conversation 2026-05-23). The earlier
notebook builder defaulted to ``bowaka_v2_intended_realism.yml`` -- a
single-window backtest config with a 4-month date range that produced zero
walk-forward splits at runtime. The Phase-12 fix points the default at
``bowaka_v2_actual_iex_current_code_optuna.yml`` (the walk-forward-purpose,
lake-matched config). This test pins that default so a future regression
cannot silently flip it back to a single-window config.

Tests both:
  (1) the BUILDER source (``_build_10_optuna_walkforward.py``); and
  (2) the GENERATED notebook (``10_optuna_walkforward.ipynb``), since the
      builder is a copier and the notebook is what JupyterLab actually loads.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_LAB_ROOT = Path(__file__).resolve().parents[2]
_BUILDER = _LAB_ROOT / "notebooks" / "_build_10_optuna_walkforward.py"
_NOTEBOOK = _LAB_ROOT / "notebooks" / "10_optuna_walkforward.ipynb"

#: Phase-12 default: walk-forward-purpose, IEX, current_code_parity. The lake
#: today is IEX-only so resolve_walkforward_config('auto') is a no-op against
#: this base; when SIP+quotes land it auto-upgrades simulation.mode upward.
#:
#: Speedup report v2 hotfix 2026-05-26 (post-Phase-6): the notebook 10 builder
#: now defaults to the workstation OVERLAY
#: (``bowaka_v2_actual_iex_current_code_optuna.workstation.yml``) which is
#: built on top of the base optuna config + the operator-spec memory /
#: parallel knobs. The base ``_optuna.yml`` is still accepted (so a manual
#: override stays valid). Both must contain ``optuna.walkforward`` — the
#: defense-in-depth test below catches single-window backtest configs.
_EXPECTED_DEFAULT_BASE = "bowaka_v2_actual_iex_current_code_optuna.yml"
_EXPECTED_DEFAULT_WORKSTATION = (
    "bowaka_v2_actual_iex_current_code_optuna.workstation.yml"
)
_ACCEPTED_DEFAULT_SUFFIXES = (
    _EXPECTED_DEFAULT_BASE,
    _EXPECTED_DEFAULT_WORKSTATION,
)

#: Matches ``CONFIG_PATH = 'literal'`` (or ``"literal"``) ANYWHERE in the text,
#: including inside a Python-quoted notebook-cell-source string in the builder.
#: Captured group 2 is the inner literal.
_CONFIG_PATH_RE = re.compile(r"""CONFIG_PATH\s*=\s*(['"])(.+?)\1""")


def _config_path_from_text(text: str) -> str | None:
    """Return the literal inside the first ``CONFIG_PATH = '...'`` assignment."""
    m = _CONFIG_PATH_RE.search(text)
    return m.group(2) if m else None


def _endswith_any(cfg_path: str, suffixes: tuple[str, ...]) -> bool:
    return any(
        cfg_path.endswith(f"/{s}") or cfg_path.endswith(f"\\{s}") for s in suffixes
    )


def test_builder_default_config_path_is_walkforward_optuna() -> None:
    text = _BUILDER.read_text(encoding="utf-8")
    cfg_path = _config_path_from_text(text)
    assert cfg_path is not None, (
        "_build_10_optuna_walkforward.py: no CONFIG_PATH = '...' literal found"
    )
    assert _endswith_any(cfg_path, _ACCEPTED_DEFAULT_SUFFIXES), (
        f"_build_10_optuna_walkforward.py: CONFIG_PATH={cfg_path!r}; "
        f"expected it to end with one of {_ACCEPTED_DEFAULT_SUFFIXES!r} "
        f"(the walk-forward-purpose contract-parity config, or its "
        f"workstation overlay, that matches the current IEX-only lake)."
    )


def test_notebook_default_config_path_is_walkforward_optuna() -> None:
    nb = json.loads(_NOTEBOOK.read_text(encoding="utf-8"))
    found: str | None = None
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        cfg_path = _config_path_from_text(src)
        if cfg_path is not None:
            found = cfg_path
            break
    assert found is not None, (
        "10_optuna_walkforward.ipynb: no CONFIG_PATH literal found in any cell"
    )
    assert _endswith_any(found, _ACCEPTED_DEFAULT_SUFFIXES), (
        f"10_optuna_walkforward.ipynb: CONFIG_PATH={found!r}; "
        f"expected it to end with one of {_ACCEPTED_DEFAULT_SUFFIXES!r}. "
        f"Re-run notebooks/_build_10_optuna_walkforward.py to regenerate."
    )


def test_notebook_default_config_path_is_an_optuna_yml() -> None:
    """Defense in depth: even if the specific filename changes, never default
    to a single-window backtest config (which lacks the optuna.walkforward
    block and produces a ValueError at runtime)."""
    nb = json.loads(_NOTEBOOK.read_text(encoding="utf-8"))
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        cfg_path = _config_path_from_text(src)
        if cfg_path is None:
            continue
        # Accept either the base optuna config OR a workstation overlay that
        # carries the same optuna.walkforward block.
        ok = cfg_path.endswith("_optuna.yml") or cfg_path.endswith(
            "_optuna.workstation.yml"
        ) or bool(re.search(r"_optuna\.workstation_\d+w\.yml$", cfg_path))
        assert ok, (
            f"10_optuna_walkforward.ipynb: CONFIG_PATH={cfg_path!r} must point "
            f"at a *_optuna.yml (or *_optuna.workstation*.yml) file "
            f"(walk-forward-purpose, with an optuna.walkforward block); a "
            f"single-window backtest config produces 0 walk-forward splits."
        )
        return
    raise AssertionError("no CONFIG_PATH cell found in the generated notebook")
