# Lab-vs-production parity — speedup benchmark

Measured on the workstation (Windows, `C:/Python312`, in-repo IEX lake), `dev` at
Phase 1 merged (`90d6eb8`). This is the Phase 4 "decision gate" measurement.

## Headline

| | Baseline (pre-speedup) | After Phase 1 | Speedup |
|---|---|---|---|
| **Lab** per session (full ~833-symbol PIT universe) | ~70–95 min | **64.5 s** | **~65–88×** |
| **Prod** (reference strategy) per session | ~25–37 s | 15.2 s | ~2× |
| **Total per session** | **~70–95 min** | **~80 s (~1.3 min)** | **~55–70×** |

**Hard ceiling < 5 min/session: MET (~1.3 min/session).**
Stretch goal < 1 min/session: not yet — the lab is 64.5 s; closing it needs the
scan-matrix path (Phases 5–6). Phase 3 (parallelize sessions) cuts multi-session
*wall-clock* but not single-session time.

## Run

- `python -m bowaka_v2_lab.cli parity --start-date 2026-05-19 --end-date 2026-05-19
  --cost-stress base --chunk-per-session`
- Universe: **833 symbols** (full PIT screen, `pit_screen`); one session.
- `prod = 15.2 s`, `lab = 64.5 s`; one-time universe build ~19 s; total run 1m19s.
- `prod_n_trades = 10`, `lab_n_trades = 6`. The prod-vs-lab divergence
  (`trade_intersection_rate` below threshold) is **pre-existing** — it is the
  parity gap the project measures, locked by the golden; the speedups preserve
  it exactly, they do not change it.

## Fidelity

Phase 1 reproduces the Phase 0 golden EXACTLY — report fields + every prod/lab
trade row + the candidate stream, at price 1e-12 / pnl 1e-9, in both chunk modes
(`scripts/verify_golden_diff.py`). The accelerated lab data path is independently
proven byte-identical to the legacy path
(`tests/integration/test_parity_runner_cached_path_parity.py`).

## Decision gate

Per the speedup prompt: with **< 5 min/session met**, Phases 2 (vectorize prod —
"barely moves the notebook"), 3 (parallelize sessions), and 5–6 (scan-matrix) are
**optional upside**. They were not required to hit the goal.

## Phase 2 + 3 (optional upside, landed on top of Phase 1)

- **Phase 2 (vectorize prod reference)** — the prod backtester now uses
  searchsorted per-scan windows + NaN-aware prefix-array forming bars + a numpy
  first-touch exit walk. **Golden diff = 0** (byte-identical), and the prod side
  is faster per session.
- **Phase 3 (parallelize sessions)** — `run_parity(parallel_workers=N)` (and
  `cli parity --parallel-workers N`) runs contiguous session blocks across spawn
  workers; output is **identical to serial** (golden-bundle diff = 0). Golden
  window (4 sessions, 40 symbols): **serial 49.6 s → 4 workers 31.1 s (~1.6×)**.
  The ratio is cold-start-limited on short windows (each worker re-imports the
  lab + warms caches once) and scales toward N× as sessions-per-worker grows —
  the intended regime is a long multi-session parity run. Note: spawn parallelism
  works from the CLI / scripts / pytest, not from a Jupyter `<stdin>` main.

## Scan-matrix (Phases 5–6): evaluated, not adopted for parity

The scan-matrix compat/vectorized runtime makes the *scan* fast but requires a
matrix **build** that costs ≈ the original slow lab (uncached feature precompute,
~hours at 833 symbols). For a single parity run it cannot beat Phase 1; it only
pays off **amortized** across many reruns of the same window (a parameter sweep,
since the matrix is invalidated by feature keys, not signals/sizing/exits). Wrong
tool for single-run parity — Phase 1 is the practical optimum.
