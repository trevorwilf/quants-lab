"""Run the REAL study-start preflight for /tmp/ir2m.yml and stop right after it
(before the heavy fold build / trials) — confirms Option A unblocks the gate."""
import sys
sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]
from bowaka_v2_lab.optuna import walkforward_runner as W  # noqa: E402

_orig = W.run_preflight
result = {}


class _StopAfterPreflight(BaseException):
    pass


def _spy(*a, **k):
    r = _orig(*a, **k)
    result["passed"] = r.passed
    result["checks"] = [(c.name, c.status, getattr(c, "detail", "")) for c in r.checks]
    raise _StopAfterPreflight()


W.run_preflight = _spy

try:
    W.run_walkforward_study("/tmp/ir2m.yml", n_trials=1)
except _StopAfterPreflight:
    pass
except Exception as e:  # noqa: BLE001
    print("study raised BEFORE preflight (config/parity/build error):", type(e).__name__, str(e)[:400])

print("\n=== STUDY-START PREFLIGHT (Option A) ===")
print("overall passed:", result.get("passed"))
for n, s, d in result.get("checks", []):
    line = "  [%-5s] %s" % (s, n)
    if s in ("fail", "warn") and d:
        line += "  -- " + str(d)[:160]
    print(line)
