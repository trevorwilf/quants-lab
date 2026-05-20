"""Smoke import + version test."""
from __future__ import annotations


def test_package_imports_and_has_version() -> None:
    import bowaka_v2_lab

    assert bowaka_v2_lab.__version__ == "0.1.0"
    assert bowaka_v2_lab.STRATEGY_ID == "bowaka_v2"


def test_config_models_import() -> None:
    from bowaka_v2_lab.config.models import BowakaV2Config

    assert BowakaV2Config.__name__ == "BowakaV2Config"


def test_cli_module_importable() -> None:
    from bowaka_v2_lab import cli

    parser = cli.build_parser()
    assert "env-check" in parser.format_help()
