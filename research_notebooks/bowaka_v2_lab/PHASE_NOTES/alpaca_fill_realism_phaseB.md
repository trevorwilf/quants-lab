# Alpaca fill realism — Part B/C phase notes (hooks + validation)

Completion notes for PB.4 (hooks) → PB.5 → PB.6 → PC.1 → PC.3, finished 2026-06-12.
Part A (PA.1–PA.4 data) and PB.1–PB.3 / PB.4-core are in the plan + phase0 note.
Nothing here is committed (per the standing guardrail); all on the `dev` working tree.

## PB.4 — sim hooks (sell + buy), default-off / byte-identical

**Sell / exit** (`sim/exits.py`): `_XFill` gained `fill_model` / `trades_supplier`
/ `tape_window_seconds` / `tape_participation`. New `_tape_replay_bracket` helper +
a `kind` arg on `_bracket_fill` (`kind="stop"` → `max_price=bracket`, `"target"` →
`min_price=bracket`) calling `replay_tape_fill`; a no-tape / no-qualifying-print
window falls through to the PB.1–3 / legacy base (byte-identical). `trades_supplier`
threaded through both walks, the dispatcher, `exit_driver.drive_session_exits_minute`,
and `backtester.run_backtest` → the live exit `walk_lot_exit`.

**Buy / entry** (`sim/fills.py`): new `_tape_replay_fill` builds a `FillResult`
from the tape VWAP — a `market` buy takes no price ceiling, a `marketable_limit`
buy uses `ask·(1+slip)`. Threaded `run_backtest → run_one_scan →
StrategyConsumer.consume → fills` as a **lazy** supplier (fetched only when
`execution.fill_model == "tape_replay"`).

**Orchestration gate**: `data/suppliers.make_trades_supplier_for_config(cfg, …)`
returns a supplier ONLY when `execution|exits.fill_model == "tape_replay"`, else
`None`. Wired into `cli_runners`, `optuna/fold_context` (new
`FoldSupplierBundle.trades`), and `optuna/walkforward_runner` (both calls, ctx +
no-ctx). **Skipped** (byte-identical, no validation value): `parity/runner` (prod
has no tape_replay), `backtest_runner` (ablation helper, wires no quote_supplier
either), `reconcile/replay` (forces CCP).

Tests: `tests/unit/sim/test_tape_replay_routing.py` (10, stub-supplier wiring).

## PB.6 — hash + suitability + derive_validation

- `dataset_hash`: gated `trades_partitions_hash` (only when a run consumes the
  tape) — done in PB.4-core; legacy byte-identical.
- **Mode lattice decision**: `tape_replay` is an **opt-in knob**, NOT a new mode
  and NOT default-on in IR. Promote into IR only after PB.5/PC.3 validate it.
- **Suitability**: `decide_suitability` caps a tape-consuming run at
  `research_only` regardless of mode/feed. The run manifest gains
  `fill_model.consumes_trade_tape` (`build_run_manifest` extras).
- `derive_validation_config(enable_tape_replay=True)` opt-in sets execution+exits
  `fill_model` for the finalist validation run.
- Honesty guard: `data/lineage.trades_partitions_available` + a loud warning when
  `tape_replay` is requested on a lake with no `trades/`.

Tests: `tests/unit/sim/test_tape_replay_pb6.py` (4).

## PC.1 — regression (byte-identical)

`tests/unit + tests/parity` = **1592 pass / 8 pre-existing fail / 1 skip**
(1578 baseline + the 14 new tape tests; the 8 fails are the pre-existing contract
mirror drift + nb-bootstrap, all untouched by this work). `bowaka_common` = 136
pass. = **0 regressions.**

## PB.5 / PC.3 — measured on the REAL tape

`scripts/_validate_fillmodel.py` (PB.5, `artifacts/pb5_fill_fidelity.txt`) and
`scripts/_pc3_exit_pnl.py` (PC.3, `artifacts/pc3_exit_pnl.txt`). Key numbers:

- **PB.5**: a $4 k order fills 82 % (sell) / 79 % (buy) on the real tape with a
  few-bps median give-up; a $25 k order fills only **33 %** (fill-frac 0.49) —
  legacy over-fills ~2×. Size-sensitive and directionally correct.
- **PC.3**: through the real `walk_lot_exit`, tape realized PnL is **27.6 % worse
  at $8 k / 38.1 % worse at $30 k** than legacy bracket fills; all of the delta is
  on bracket (stop/target) lots and every tape lot is ≤ legacy (0 fill better).

**PC.3 caveat**: the full scanner/PIT-universe backtest A/B yields an empty PIT
universe on a scoped window (universe-screening issue, orthogonal to the fill
model — the CCP run completes, just emits 0 candidates), so PC.3 drives the exit
engine directly.

**Target-side clamp (done)**: a take-profit is a RESTING limit sell, so
`_tape_replay_bracket` fills a `kind="target"` exit AT the limit (the bracket
price), not at the ≥target through-VWAP (a passive limit gets no price improvement
above its price). Triggered stops + marketable buys are aggressors → still pay the
swept VWAP. Before the clamp ~25 % of bracket lots filled better than legacy; after
it the model is uniformly ≤ legacy (PC.3: 48 worse / 0 better / 96 equal). The
model is opt-in / capped at `research_only`.
