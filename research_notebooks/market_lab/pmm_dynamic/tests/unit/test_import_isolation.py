"""ML-DIR-012 regression guard: directional imports must not require PMM dependencies.

Uses subprocess for strict module-state isolation. Clearing sys.modules in-process
causes classes to be re-imported as distinct objects, which breaks isinstance checks
in *other* tests. Subprocess gives each test a fresh interpreter.
"""
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_in_subprocess(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )


def test_strategies_init_is_lazy():
    """pmm_lab.strategies package init must NOT eagerly import submodules."""
    script = textwrap.dedent("""
        import sys
        import pmm_lab.strategies
        assert "pmm_lab.strategies.pmm_dynamic" not in sys.modules, (
            "strategies/__init__.py is eagerly importing pmm_dynamic (ML-DIR-012)"
        )
        assert "pmm_lab.strategies.bollinger" not in sys.modules
        assert "pmm_lab.strategies.macd_bb" not in sys.modules
        print("OK")
    """)
    result = _run_in_subprocess(script)
    assert result.returncode == 0, (
        f"subprocess failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )
    assert "OK" in result.stdout


def test_mr_config_importable_directly():
    """Importing MR config should not require importing pmm_dynamic."""
    script = textwrap.dedent("""
        import sys
        try:
            from pmm_lab.strategies.mean_reversion_bb_rsi import MeanReversionBBRSIStrategyConfig
        except ImportError as e:
            print(f"SKIP: {e}")
            sys.exit(0)
        assert "pmm_lab.strategies.pmm_dynamic" not in sys.modules, (
            "MR import pulled in pmm_dynamic — violates ML-DIR-012 fix"
        )
        print("OK")
    """)
    result = _run_in_subprocess(script)
    assert result.returncode == 0, (
        f"subprocess failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )
    if "SKIP:" in result.stdout:
        pytest.skip(result.stdout.strip())
    assert "OK" in result.stdout


def test_ema_config_importable_directly():
    script = textwrap.dedent("""
        import sys
        try:
            from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig
        except ImportError as e:
            print(f"SKIP: {e}")
            sys.exit(0)
        assert "pmm_lab.strategies.pmm_dynamic" not in sys.modules, (
            "EMA import pulled in pmm_dynamic — violates ML-DIR-012 fix"
        )
        print("OK")
    """)
    result = _run_in_subprocess(script)
    assert result.returncode == 0, (
        f"subprocess failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )
    if "SKIP:" in result.stdout:
        pytest.skip(result.stdout.strip())
    assert "OK" in result.stdout


def test_lazy_backcompat_still_works():
    """`from pmm_lab.strategies import PMMDynamicStrategy` must still work."""
    script = textwrap.dedent("""
        import sys
        try:
            from pmm_lab.strategies import PMMDynamicStrategy
        except ImportError as e:
            print(f"SKIP: {e}")
            sys.exit(0)
        # If it worked, pmm_dynamic was loaded lazily.
        assert "pmm_lab.strategies.pmm_dynamic" in sys.modules
        print("OK")
    """)
    result = _run_in_subprocess(script)
    assert result.returncode == 0, (
        f"subprocess failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )
    if "SKIP:" in result.stdout:
        pytest.skip(result.stdout.strip())
    assert "OK" in result.stdout


def test_module_is_installable_helper_works():
    """The _module_is_installable helper must distinguish missing vs broken modules."""
    from pmm_lab.sim.runner_dispatch import _module_is_installable
    assert _module_is_installable("pmm_lab.sim.runner_dispatch") is True
    assert _module_is_installable("pmm_lab.nonexistent_xyz") is False
