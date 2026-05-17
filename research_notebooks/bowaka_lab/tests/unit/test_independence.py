"""Phase 0: independence test.

Bowaka Lab must not import from the QuantLab-internal packages whose names start
with "market" + "_lab" or "pmm" + "_lab". Those literal strings are built from
short tokens below so that the source of this test does not itself match the
project-level grep gate. The README and explicit `# do not <forbidden>` comments
are the only acceptable matches in non-test source.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

BOWAKA_ROOT = Path(__file__).resolve().parents[2]

# Build the forbidden names from short tokens so this file itself contains no
# match for the regex below.
_M = "market" + "_" + "lab"
_P = "pmm" + "_" + "lab"

FORBIDDEN_PATTERN = re.compile(
    r"^(?P<lead>\s*)(?P<stmt>(?:from\s+(?:%s|%s)|import\s+(?:%s|%s)))\b" % (_M, _P, _M, _P),
    re.MULTILINE,
)

ALLOW_COMMENT_RE = re.compile(r"do\s+not\s+(?:import|reference)", re.IGNORECASE)

SEARCH_DIRS = ("src", "tests", "configs")
SEARCH_SUFFIXES = (".py", ".yml", ".yaml", ".toml", ".cfg", ".ini")


def _candidate_files() -> list[Path]:
    out: list[Path] = []
    for sub in SEARCH_DIRS:
        root = BOWAKA_ROOT / sub
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in SEARCH_SUFFIXES:
                continue
            if "__pycache__" in path.parts:
                continue
            out.append(path)
    return out


def test_no_forbidden_imports():
    bad: list[tuple[Path, int, str]] = []
    for path in _candidate_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in FORBIDDEN_PATTERN.finditer(text):
            line_start = text.rfind("\n", 0, match.start()) + 1
            line_end = text.find("\n", match.end())
            if line_end == -1:
                line_end = len(text)
            line = text[line_start:line_end]
            bad.append((path.relative_to(BOWAKA_ROOT), text[: match.start()].count("\n") + 1, line.strip()))

    if bad:
        formatted = "\n".join(f"  {p}:{lineno}: {line}" for p, lineno, line in bad)
        pytest.fail("Forbidden " + _M + "/" + _P + " import found:\n" + formatted)


def test_allow_commented_references():
    sample = "# do not " + "import " + _M + " here\n"
    assert FORBIDDEN_PATTERN.search(sample) is None
    assert ALLOW_COMMENT_RE.search(sample) is not None


def test_forbidden_pattern_detects_actual_import():
    sample = "import " + _M + "\n"
    assert FORBIDDEN_PATTERN.search(sample) is not None
    sample2 = "from " + _P + " import foo\n"
    assert FORBIDDEN_PATTERN.search(sample2) is not None
