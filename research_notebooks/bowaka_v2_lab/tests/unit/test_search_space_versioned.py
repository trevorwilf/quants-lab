"""SEARCH_SPACE_VERSION is present and bumped on every spec change (Phase 9).

The search space is a frozen contract: the optimizer's results are only
comparable across runs that used the same bounds. ``SEARCH_SPACE_VERSION`` makes
that explicit, and this test enforces the discipline:

* ``tests/fixtures/search_space_v<N>.json`` freezes the spec for version N.
* If ``SEARCH_SPACE_SPEC`` changed but ``SEARCH_SPACE_VERSION`` did not, the
  frozen-fixture comparison fails — forcing a version bump (and a new fixture).

When you intentionally change the spec: bump ``SEARCH_SPACE_VERSION`` in
``search_space.py`` AND add a matching ``search_space_v<new>.json`` fixture.
"""
from __future__ import annotations

import json
from pathlib import Path

from bowaka_v2_lab.optuna.search_space import (
    SEARCH_SPACE_SPEC,
    SEARCH_SPACE_VERSION,
)

_FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _normalised_spec() -> dict[str, list]:
    """The live spec as plain JSON-comparable data (tuples -> lists)."""
    out: dict[str, list] = {}
    for name, spec in SEARCH_SPACE_SPEC.items():
        out[name] = json.loads(json.dumps(list(spec)))
    return out


def test_search_space_version_is_a_positive_int() -> None:
    assert isinstance(SEARCH_SPACE_VERSION, int)
    assert SEARCH_SPACE_VERSION >= 1


def test_frozen_fixture_exists_for_current_version() -> None:
    fixture = _FIXTURE_DIR / f"search_space_v{SEARCH_SPACE_VERSION}.json"
    assert fixture.is_file(), (
        f"no frozen fixture {fixture.name} for SEARCH_SPACE_VERSION="
        f"{SEARCH_SPACE_VERSION}; freeze the spec into that file when you bump "
        f"the version"
    )


def test_spec_matches_frozen_fixture_for_current_version() -> None:
    """The live spec must equal the frozen fixture for the current version.

    If this fails, the spec dict changed: either revert the change, or bump
    SEARCH_SPACE_VERSION and add a new search_space_v<N>.json fixture.
    """
    fixture = _FIXTURE_DIR / f"search_space_v{SEARCH_SPACE_VERSION}.json"
    frozen = json.loads(fixture.read_text(encoding="utf-8"))
    assert frozen["search_space_version"] == SEARCH_SPACE_VERSION
    assert frozen["spec"] == _normalised_spec(), (
        "SEARCH_SPACE_SPEC differs from the frozen fixture for version "
        f"{SEARCH_SPACE_VERSION} — bump SEARCH_SPACE_VERSION and add a new "
        "fixture, or revert the spec change"
    )
