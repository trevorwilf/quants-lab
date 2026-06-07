"""TEMP diagnostic — instrument the real preflight minute-bar probe.

Monkeypatches make_lake_suppliers so every minute_bars_supplier(symbol, cutoff)
call the preflight makes is logged with the returned bar count. Then runs the
actual $2M intended_realism preflight (it aborts at the coverage gate, which is
exactly the probe set we want). Output: /tmp/probe_log.jsonl
"""
import sys, json
import bowaka_v2_lab.data.suppliers as S

_orig = S.make_lake_suppliers
_logf = open("/tmp/probe_log.jsonl", "w")


def _wrapped(*a, **k):
    mbs, dbs = _orig(*a, **k)

    def logged(symbol, cutoff):
        m = mbs(symbol, cutoff)
        try:
            n = 0 if m is None else len(m)
        except Exception:
            n = -1
        _logf.write(json.dumps({"sym": str(symbol), "ts": str(cutoff), "n": int(n)}) + "\n")
        return m

    return logged, dbs


S.make_lake_suppliers = _wrapped

from bowaka_v2_lab.cli import main  # noqa: E402

sys.argv = ["cli", "optuna", "--config", "/tmp/ir2m.yml", "--incumbent-trial"]
try:
    main()
except SystemExit as e:
    print("cli exit code:", getattr(e, "code", e))
except Exception as e:  # noqa: BLE001
    print("cli raised:", type(e).__name__, str(e)[:200])
finally:
    _logf.close()

n = sum(1 for _ in open("/tmp/probe_log.jsonl"))
print("PROBE_LOG_LINES:", n)
