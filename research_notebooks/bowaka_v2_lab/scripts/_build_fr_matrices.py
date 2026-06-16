"""Build + verify the fast_realism scan matrices (validation + holdout), mirroring
rebuild_scan_matrices.ps1 BUT forcing mode_override='fast_realism' (the stock script
resolves feed=auto with no mode override, which on the SIP lake auto-derives
intended_realism and would clobber fast_realism + mismatch the matrix hash).

Resolves the base config the SAME way the study will, writes the resolved config to a
persisted repo path, then builds + verifies each scope at the resolved store root.
Run from the lab dir inside the container. argv: <base_config> [workers]."""
import subprocess
import sys

from bowaka_v2_lab.config.loader import load_config
from bowaka_v2_lab.optuna.autoconfig import resolve_walkforward_config
from bowaka_v2_lab.scanner.scan_matrix import resolve_scan_matrix_store_root

base = sys.argv[1] if len(sys.argv) > 1 else "configs/_fastrealism_study.yml"
workers = sys.argv[2] if len(sys.argv) > 2 else "8"
resolved = "configs/_fr_study_resolved.yml"

r = resolve_walkforward_config(base, feed_override="auto", mode_override="fast_realism",
                               out_path=resolved)
print(f"[fr-matrix] resolved feed={r.feed} mode={r.mode} -> {resolved}", flush=True)
assert r.mode == "fast_realism", f"mode resolved to {r.mode}, expected fast_realism"

sm = load_config(resolved)["optuna"]["acceleration"]["scan_matrix"]
roots = {scope: str(resolve_scan_matrix_store_root(sm, scope)) for scope in ("validation", "holdout")}
print(f"[fr-matrix] store roots: {roots}", flush=True)

for scope, root in roots.items():
    print(f"[fr-matrix] ===== build {scope} -> {root} =====", flush=True)
    subprocess.run([sys.executable, "-m", "bowaka_v2_lab.cli", "scan-matrix", "build",
                    "--config", resolved, "--scope", scope, "--workers", workers,
                    "--store-root", root], check=True)
    print(f"[fr-matrix] ===== verify {scope} =====", flush=True)
    subprocess.run([sys.executable, "-m", "bowaka_v2_lab.cli", "scan-matrix", "verify",
                    "--config", resolved, "--store-root", root, "--vectorized-check"], check=True)

print(f"[fr-matrix] DONE — study config = {resolved}", flush=True)
