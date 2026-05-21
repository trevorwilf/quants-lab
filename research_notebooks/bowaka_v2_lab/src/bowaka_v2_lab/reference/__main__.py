"""Regenerate the frozen contract: ``python -m bowaka_v2_lab.reference``.

Reads the live Bowaka v2 config (resolved via ``$BOWAKA_V2_SOURCE_ROOT`` or the
in-repo mirror) and writes ``reference/actual_bowaka_v2_contract.yaml``.
"""
from __future__ import annotations

import sys

from . import actual_contract_hash, resolve_source_root, source_config_path, write_contract_file


def main() -> int:
    src = source_config_path()
    if src is None:
        root = resolve_source_root()
        print(
            "ERROR: live Bowaka v2 config (bowaka_v2_config.yaml) not found.\n"
            f"  resolved source root: {root}\n"
            "  Set $BOWAKA_V2_SOURCE_ROOT, or mirror the live source into\n"
            "  reference/source_strategy/scripts/ (run mirror_bowaka_v2_source.ps1).",
            file=sys.stderr,
        )
        return 1
    dest = write_contract_file(src)
    print(f"wrote frozen contract: {dest}")
    print(f"  live source       : {src}")
    print(f"  contract sha256   : {actual_contract_hash()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
