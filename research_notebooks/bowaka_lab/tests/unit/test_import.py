"""Phase 0: smoke-import test."""

from __future__ import annotations

import re


def test_bowaka_lab_imports_and_has_version():
    import bowaka_lab

    assert hasattr(bowaka_lab, "__version__")
    assert isinstance(bowaka_lab.__version__, str)
    # Semantic-ish: X.Y.Z, allow pre-release suffixes
    assert re.match(r"^\d+\.\d+\.\d+", bowaka_lab.__version__)


def test_bowaka_lab_version_is_0_1_0():
    import bowaka_lab

    assert bowaka_lab.__version__ == "0.1.0"


def test_cli_module_imports():
    from bowaka_lab import cli

    assert hasattr(cli, "main")
    assert callable(cli.main)


def test_cli_smoke_offline_fixtures_exits_zero(capsys):
    from bowaka_lab.cli import main

    rc = main(["smoke", "--offline-fixtures"])
    assert rc == 0
    captured = capsys.readouterr().out
    assert "0.1.0" in captured
    assert "offline_fixtures" in captured


def test_cli_env_check_exits_zero(capsys):
    from bowaka_lab.cli import main

    rc = main(["env-check"])
    assert rc == 0
    captured = capsys.readouterr().out
    assert "bowaka_lab_version" in captured
