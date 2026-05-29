# Production backtester fix — 2026-05-29 (dead-ternary always-synth bug)

## The bug

The 2026-05-29 attempt to build a lab-vs-production parity notebook surfaced
a 100% win rate from `reference/source_strategy/scripts/bowaka_v2_backtest.py`
on real-symbol universes:

    backtest done: trades=20, total_pnl=11279.00, win_rate=1.000        # 5 syms x 5 days
    backtest done: trades=2625, total_pnl=1480368.91, win_rate=1.000    # 2-year window

The script's supplier-selection lines (around `main`) read:

```python
minute_bars = _synth_minute_bars if args.synth else _synth_minute_bars
daily_bars  = _synth_daily_bars  if args.synth else _synth_daily_bars
```

Both branches of each ternary point at the `_synth_*` helpers. The `--synth`
flag was dead code; the script **always** read the deterministic synthetic
$10-stock generator (`_synth_minute_bars` / `_synth_daily_bars`) regardless of
flag, regardless of symbol, regardless of the real lake on disk. The synthetic
390-bar session rises from $10.00 to ~$11.95 (+19.5%), which guarantees the
+15% target hits before the -8% stop — the 100% win rate is a property of the
fake data, not of the strategy.

**Implication.** The production backtester has been a smoke harness
masquerading as a backtester. The production strategy code
(`bowaka_v2_features`, `bowaka_v2_cost_model`, the scanner gates, exits) is
fine and runs end-to-end without errors — it has just been fed fake data via
the script's data layer. The lab simulator
(`bowaka_v2_lab.backtest_runner.run_config_backtest`) **is** the real
backtester and always was; any earlier framing of "the lab is a facsimile of
the production backtester" was based on the wrong assumption that the
production backtester was a working reference.

## What the fix changes

In `reference/source_strategy/scripts/bowaka_v2_backtest.py`:

- Three new helpers above `main`:
  - `_resolve_backtest_lake_root(args, cfg)` — same resolution chain
    `bowaka_common` uses (`--lake-root` > `cfg.market_data.shared_root` >
    `$MARKET_DATA_ROOT` > the in-repo default
    `<repo>/research_notebooks/market_data`).
  - `_resolve_required_adjustment(cfg)` — returns `split_adjusted` when the
    config requires it (mirrors the lab's `daily_adjustment_for_config`).
  - `_make_lake_suppliers(*, lake_root, feed, adjustment)` — builds the two
    callables `run_backtest` expects, both routed through `MarketDataStore`.
- New `--lake-root <path>` CLI argument (override the resolution chain).
- New `import os` at the top.
- The supplier-selection in `main` is rewritten:
  - `--synth` is preserved (smoke-mode still works) and now logs a
    `WARNING` that the data is fictitious.
  - Without `--synth`, the script calls `_make_lake_suppliers(...)` so it
    reads the lake — the path the live scanner uses.
- The top-of-file docstring gains a `DATA REQUIREMENTS:` section that
  documents the resolution chain and the `--synth` warning behaviour.

The patch is at [`production_backtester_fix.patch`](production_backtester_fix.patch).

## Action required — apply the same fix to the LIVE production source

The mirror at `research_notebooks/bowaka_v2_lab/reference/source_strategy/` is
one-way *downstream* of the live strategy source. `mirror_bowaka_v2_source.ps1`
copies live → mirror; running it again would overwrite this mirror-only fix
on the next refresh. The operator must apply the patch to the live source so
the next mirror refresh leaves the fix in place.

```powershell
# 1. Apply the patch to the live source.
cd $env:BOWAKA_V2_SOURCE_ROOT
git apply <path-to-lab>\docs\production_backtester_fix.patch

# 2. Verify the live source + mirror are in sync.
cd <lab repo>\research_notebooks\bowaka_v2_lab
.\..\..\mirror_bowaka_v2_source.ps1
# After the mirror refresh, bowaka_v2_backtest.py in the mirror should match
# the live source exactly. The mirror is gitignored, so there is no git diff
# to inspect — instead, run the regression test:
py -3.12 -m pytest tests/unit/reference/test_prod_backtester_default_uses_lake.py -q
```

If the regression test passes after the mirror refresh, the fix is now in
both places.

## Verification (operator smoke)

The decisive smoke confirms the fix actually reads the lake. With the
$1-$20 price gate active and a mega-cap universe, post-fix should produce
**zero trades** (the price gate correctly rejects every entry):

```powershell
cd research_notebooks\bowaka_v2_lab\reference\source_strategy\scripts
@"
AAPL
TSLA
NVDA
AMD
SPY
"@ | Set-Content my_universe.txt

py -3.12 bowaka_v2_backtest.py `
    --config bowaka_v2_config.yaml `
    --from 2026-05-19 --to 2026-05-23 `
    --symbols my_universe.txt `
    --output-dir backtest_output_megacaps\ `
    --cost-stress conservative --ablation none
# Expect: "backtest done: trades=0, total_pnl=0.00, win_rate=0.000"
```

Non-zero trades on this universe means either the price gate isn't firing
or the synthetic-data bug has regressed — investigate before trusting any
downstream output.

A non-trivial trade count with a non-100% win rate on a microcap-shaped
universe (e.g. derived from the lab's PIT universe) confirms the backtester
is reading real data and the strategy logic is firing against actual names.
