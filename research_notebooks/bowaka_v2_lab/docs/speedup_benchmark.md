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
