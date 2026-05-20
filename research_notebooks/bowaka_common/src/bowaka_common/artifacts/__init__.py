"""Atomic artifact writers and manifest builders.

Provides:

- ``run_manifest`` — generic run manifest builder ([Report §18.2])
- ``dataset_manifest`` — dataset manifest builder ([Report §7.2])
- ``code_manifest`` — code manifest (git sha, source-tree hash)
- ``writer`` — atomic run-dir writer (Parquet + JSONL pair)
"""
from .run_manifest import build_run_manifest, RUN_MANIFEST_SCHEMA_VERSION
from .dataset_manifest import build_dataset_manifest, DATASET_MANIFEST_SCHEMA_VERSION
from .code_manifest import build_code_manifest, CODE_MANIFEST_SCHEMA_VERSION
from .writer import write_run_dir

__all__ = [
    "build_run_manifest",
    "build_dataset_manifest",
    "build_code_manifest",
    "write_run_dir",
    "RUN_MANIFEST_SCHEMA_VERSION",
    "DATASET_MANIFEST_SCHEMA_VERSION",
    "CODE_MANIFEST_SCHEMA_VERSION",
]
