"""Same-bar stop/target ambiguity resolver (v2-specific policy wrapper).

Default ``stop_first`` is the conservative choice — when stop and target both
touch the same bar, we assume the stop hit first. Tests can override to
``target_first``.

Logged to ``ambiguous_bar_count`` metric so reviewers can see how often this
matters.
"""
from __future__ import annotations


_ALLOWED = {"stop_first", "target_first"}


def resolve_same_bar(policy: str = "stop_first") -> str:
    if policy not in _ALLOWED:
        raise ValueError(f"unknown same-bar policy {policy!r}; allowed: {sorted(_ALLOWED)}")
    return "stop" if policy == "stop_first" else "target"
