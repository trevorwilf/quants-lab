# Bowaka v2 Lab Realism, Backtesting, and Bayesian Optimization Audit

**Prepared for:** Quant research + software engineering review  
**Scope:** `bowaka_v2_lab` inside the supplied Quants Lab repo, compared against the actual Bowaka v2 strategy archive.  
**Primary objective:** identify everything required to make `bowaka_v2_lab` a realistic, validation-grade simulator and optimization harness for Bowaka v2, using real IEX data until SIP is available and synthetic data only as a last resort.  
**Verdict date:** 2026-05-22  

---

## 0. Executive summary

### Objective reviewed

The submitted project is a new Bowaka v2 research/backtesting lab intended to replay the actual Bowaka v2 forming-daily-bar scanner and strategy, run comprehensive backtests, and run Bayesian/Optuna optimization against a shared market-data lake.

The actual Bowaka v2 strategy in the submitted strategy archive is a paper-mode, Alpaca/OpenAlgo-oriented forming daily bar strategy with:

- live/paper configuration in `bowaka_backup_v2/scripts/bowaka_v2_config.yaml`;
- scanner implementation in `bowaka_backup_v2/scripts/bowaka_intraday_scanner.py`;
- feature/gate implementation in `bowaka_backup_v2/scripts/bowaka_v2_features.py`;
- execution, risk, fill polling, OCO attach, and exit lifecycle in `bowaka_backup_v2/scripts/bowaka_v2_strategy.py`.

`bowaka_v2_lab` is a serious, well-structured attempt at a lab implementation. It has a frozen contract, parity tests, realistic-mode switches, data-quality gates, quote-coverage checks, a walk-forward Optuna runner, and a large test suite. However, it is **not yet safe to use as a production research backtester or optimizer for Bowaka v2 alpha/parameter decisions**.

### Stop-ship verdict

**Current suitability: research-only / simulator-development only.**

Do **not** use current `bowaka_v2_walkforward_optuna.yml` results, if any, to choose Bowaka v2 live/paper parameters. Do **not** treat current IEX backtests as evidence of profitability. Do **not** promote to paper/live readiness from this lab until the P0 blockers below are fixed and independently validated.

The most important blockers are:

1. **The current Optuna config is not Bowaka v2 parity.** `configs/bowaka_v2_walkforward_optuna.yml` claims `simulation.mode: current_code_parity`, but changes scanner caps, execution order style, quote thresholds, sizing, risk limits, stop/target, and hold period relative to the frozen/actual Bowaka v2 contract.
2. **The simulator is not temporally event-driven enough.** The backtester processes all scans for a session and only then evaluates exits. That means intraday stops, targets, time stops, realized losses, stopout kill-switches, and intraday mark-to-market do not affect later same-day entries.
3. **The current attached market-data sample cannot run a real replay.** The archive contains `market_data` manifests, asset master parquet, and audit parquet, but no bar parquet payloads under `bars/`. The manifest says a full external lake exists, but the attached sample cannot validate full IEX replay behavior.
4. **Real quote data is absent.** The lab itself documents that the current lake has no `quotes/` partitions. `current_code_parity` uses the actual strategy’s zero-spread quote fallback; that reproduces a live-code wart but is not realistic. `intended_realism` correctly fails without quotes.
5. **The actual strategy requires adjusted/split-adjusted daily bars, but the lab’s generated intended config omits `market_data.require_adjusted_daily_bars: true`, while the lake manifest declares `adjustment: raw`.** This can silently allow raw daily baselines to drive RVOL, ATR, EMA, and split-sensitive price gates.
6. **Marketable-limit fill logic is not realistic enough.** The fill model uses forward minute-bar highs as a proxy for quote chasing and fills at the full limit offset. A marketable buy limit at ask + offset normally should fill immediately subject to available liquidity/queue, not wait on future minute highs.
7. **OCO/protected-position lifecycle is simplified.** The real strategy has pending fills, parent fill polling, OCO attach attempts, protected-position invariants, fallback stops, and flattening on unprotected violations. The simulator creates a position with `bracket_attached=True` immediately after simulated fill.
8. **Signal-fade mode likely behaves incorrectly.** The actual config says `initial_mode: telemetry_then_active_after_validation`, but the lab treats that as active immediately.
9. **Full integration/reconciliation test execution was not validated end-to-end in this environment.** Unit/parity tests pass, and selected integration tests pass, but the full `tests/integration tests/reconcile` run did not complete in the execution window.

### Bottom-line recommendation

Proceed in phases:

- **Phase A:** fix parity/configuration and data gates before any optimization.
- **Phase B:** rebuild the simulator as an intraday event-driven replay loop that interleaves scans, order/fill events, exits, risk state, and mark-to-market.
- **Phase C:** run IEX-only backtests strictly as research/plumbing and feed-specific paper-reconciliation work; never treat IEX as a SIP-valid alpha dataset.
- **Phase D:** add real historical quotes, corporate-action-adjusted daily bars, and halt/LULD/status data.
- **Phase E:** only then run Optuna, with fold-level preflight, content-addressed dataset lineage, final holdout isolation, sensitivity/stability checks, and paper-vs-sim reconciliation.

---

## 1. Evidence reviewed

### 1.1 Submitted artifacts inspected

| Artifact | Local path inspected | Notes |
|---|---:|---|
| Quants Lab repo | `/mnt/data/quantslab_hummingbot.zip` extracted to `/mnt/data/bowaka_eval/quantslab_hummingbot/quants-lab` | Contains `research_notebooks/bowaka_v2_lab`, sibling `bowaka_common`, and `research_notebooks/market_data`. |
| Actual Bowaka v2 strategy | `/mnt/data/bowaka_backup_v2.zip` extracted to `/mnt/data/bowaka_eval/bowaka_backup_v2/scripts` | Contains actual v2 config, scanner, strategy, features, schemas, replay tools, and runner scripts. |
| Bowaka v2 lab root | `research_notebooks/bowaka_v2_lab` | Separate package with `src/`, `configs/`, `tests/`, `reference/`, `docs/`, `notebooks/`, and artifacts. |
| Market-data sample | `research_notebooks/market_data` | Only 271 KiB in the attached archive; contains manifests, asset master, audit parquet, empty bar partition directories, and no bar parquet payloads. |

### 1.2 Tests run locally

Environment note: I added the lab package and `bowaka_common` to `PYTHONPATH`. The local runtime was missing some dependencies, so `pyarrow` and `optuna` were installed before executing tests.

#### Passing tests

```bash
cd research_notebooks/bowaka_v2_lab
PYTHONPATH=src:../bowaka_common/src \
python -m pytest tests/unit tests/parity -q --tb=short \
  -m "not live_alpaca and not slow and not live_paper" --durations=10
```

Observed result:

```text
537 passed, 2 warnings in 16.80s
```

The two warnings were Optuna `TPESampler(multivariate=True)` experimental API warnings.

Selected integration tests also passed:

```bash
PYTHONPATH=src:../bowaka_common/src \
python -m pytest \
  tests/integration/test_import_actual_config_roundtrip.py \
  tests/integration/test_full_scan_replay.py \
  tests/integration/test_backtest_runner.py \
  -q --tb=short -m "not live_alpaca and not slow and not live_paper"
```

Observed result:

```text
12 passed in 16.31s
```

#### Not validated end-to-end

A full run of:

```bash
PYTHONPATH=src:../bowaka_common/src \
python -m pytest tests/integration tests/reconcile -q --tb=short \
  -m "not live_alpaca and not slow and not live_paper"
```

did not complete within the execution window. I did not observe a Python assertion failure in the partial output, but the full integration/reconciliation suite cannot be treated as validated from this audit. CI needs timeouts, segmentation, and log capture so this can be resolved deterministically.

---

## 2. External market-data facts relevant to this project

These facts matter because Bowaka v2 is a volume/range/RVOL-driven intraday microcap strategy. Feed choice changes the data-generating process.

1. Alpaca describes IEX as a single-exchange feed and SIP as consolidated data. Alpaca also states IEX is useful for initial testing when price precision is not primary, while SIP covers all U.S. exchanges and is more appropriate when precise/current prices matter. Alpaca’s own documentation notes IEX is approximately a small fraction of market volume, while SIP covers all market volume.
2. Alpaca’s market-data FAQ illustrates large differences between IEX and SIP on the same symbol/day. The example shown for AAPL has IEX volume/trade counts that are far below SIP volume/trade counts. This is exactly the kind of distortion that can bias Bowaka’s RVOL, projected RVOL, range, and liquidity features.
3. SIP/CTA/UTP sources consolidate protected quotes and trades across venues and disseminate NBBO and related regulatory data. IEX alone does not provide a consolidated tape/NBBO view.
4. Alpaca snapshot endpoints include latest trade, latest quote, minute bar, daily bar, and previous daily bar, with feed selection such as `iex`, `sip`, or delayed SIP depending on subscription. This suggests that if you remain on Alpaca, adding a quote ingestion layer should be feasible, but the current submitted lake has no quote partitions.

Practical consequence: **IEX can be used for plumbing, architecture validation, and feed-specific paper reconciliation. It cannot validate the consolidated-tape Bowaka v2 signal regime.** The actual strategy config says the same thing explicitly.

---

## 3. Actual Bowaka v2 strategy contract

The lab should be benchmarked against the actual strategy, not against a simplified research variant. The actual config and strategy establish the following contract.

### 3.1 Feed policy and explicit IEX warning

Actual file: `bowaka_backup_v2/scripts/bowaka_v2_config.yaml`

Important lines:

- Lines 12-21: explicit warning that IEX is partial-tape, biases RVOL/projected RVOL/range expansion down, and should be used only for plumbing/architecture validation until SIP.
- Lines 43-57: Alpaca provider, `feed: iex`, `allow_non_sip_for_research_only: true`, `live_requires_sip: true`, `require_adjusted_daily_bars: true`, `require_split_adjustment: true`, `max_bar_age_seconds: 90`, `max_quote_age_seconds: 15`.
- Actual strategy startup gate in `bowaka_v2_strategy.py` lines 96-120 refuses live non-SIP and logs a warning for non-SIP.

### 3.2 Session/scanner

Actual config:

- Session: `09:30` to `15:55`, scanner from `09:45` to `15:30`, loop interval `5s` (`bowaka_v2_config.yaml` lines 58-64).
- Scanner scan interval: `60s`, max candidates `25`, max entries per scan `3`, signal expiry `600s`, same-symbol entries per day `1`, cooldown `390m`, require prior baseline, require fresh bar (`bowaka_v2_config.yaml` lines 99-115).

Actual scanner implementation in `bowaka_intraday_scanner.py` lines 330-546 is simpler than the config implies:

- It reads `entered_symbols_today` and `max_candidates_per_scan` (lines 366-370).
- It loops all symbols, fetches bars, computes features/gates, appends passing candidates (lines 397-515).
- It ranks and caps by `max_candidates_per_scan` only (lines 517-523).
- It does **not** itself enforce `max_entries_per_scan`, `same_symbol_entries_per_day`, `symbol_cooldown_minutes`, or `signal_expiry_seconds` as a full lifecycle rule.

The lab intentionally adds some of those controls, which may be correct intended realism, but those additions must be clearly separated from current-code parity.

### 3.3 Universe and signal gates

Actual config:

- Allowed exchanges: NASDAQ, NYSE, AMEX, ARCA, BATS.
- Excludes OTC, ETF, leveraged/inverse ETPs, ETN, warrants, units, rights, preferreds.
- Blocklist: TSLL, CONL, SMCX.
- Price range: `$1` to `$20`.
- ADV minimum: `$250,000`.
- See `bowaka_v2_config.yaml` lines 66-87.

IEX-relaxed signal thresholds in actual config:

| Gate | Actual IEX value | Actual comment for SIP |
|---|---:|---:|
| `rvol_so_far_min` | `0.7` | `1.50` |
| `projected_full_day_rvol_min` | `0.5` | `1.50` |
| `prior_atr_pct_min` | `0.06` | unchanged |
| `range_expansion_so_far_min` | `0.5` | `1.25` |
| `close_location_so_far_min` | `0.60` | unchanged |
| `ema_distance_min` | `-0.05` | `0.0` |
| `ema_slope_min` | `-0.05` | `0.0` |

See `bowaka_v2_config.yaml` lines 117-139.

### 3.4 Feature behavior

Actual file: `bowaka_v2_features.py`

Key implementation details:

- `aggregate_forming_session_bar()` does not filter by timestamp; caller must slice through scan time. It aggregates open/high/low/last/volume and normalizes naive timestamps to UTC (`bowaka_v2_features.py` lines 145-204).
- `_et_minute_of_day()` also localizes naive timestamps to UTC (`bowaka_v2_features.py` lines 273-284).
- `instrument_gate` passes if `instrument_class is None` or `instrument_class == "operating_equity"` (`bowaka_v2_features.py` lines 473-477). That is fail-open behavior.

The lab improves this by rejecting naive timestamps and failing closed on missing instrument class in intended realism, but those changes are intended-realism deviations rather than current-code parity.

### 3.5 Execution and risk

Actual config:

- Parent order style: `market`.
- Marketable limit slippage/timeout still configured: `0.005` and `30s`.
- Bracket pricing mode: `actual_fill`.
- Quote gate: max spread `1%`, max age `15s`, positive bid/ask required.
- Price chase gate: max `+10%` above signal price, min `-3%` below signal price.
- Halt gate: block halt/pending review/recent LULD pause.
- Equal-slice sizing: `0.80 * $90,000 / 18 = $4,000` target before floor/cap effects.
- Risk: daily loss `3%`, strategy slice loss `2.5%` in config, gross exposure `80%`, daily entries `10`, max lots per symbol `3`, max stopouts/day `2`, consecutive stopouts `2`, ADV tier caps.
- See `bowaka_v2_config.yaml` lines 149-224.

Actual code:

- `_quote_gate()` rejects missing/invalid/stale/wide quotes (`bowaka_v2_strategy.py` lines 372-397).
- `_price_chase_gate()` checks quote mid vs signal price (`bowaka_v2_strategy.py` lines 400-418).
- `_halt_gate()` blocks halted/pending-review/LULD-pause statuses when supplied (`bowaka_v2_strategy.py` lines 421-430).
- `_risk_gates()` checks max concurrent, daily entry cap, gross exposure, daily realized PnL kill switch, and aggregate ADV cap (`bowaka_v2_strategy.py` lines 436-492).
- `size_position()` implements equal-slice sizing (`bowaka_v2_strategy.py` lines 529-545).
- The strategy fabricates a zero-spread quote at signal price if no quote supplier/quote exists (`bowaka_v2_strategy.py` lines 743-748). This is a current-code wart and not realistic execution.
- Accepted decision is emitted before broker submission (`bowaka_v2_strategy.py` lines 791-846).
- Pending position is recorded after successful submit, with status `pending_fill`, no entry price yet, child order IDs blank, and bracket pricing mode `actual_fill` (`bowaka_v2_strategy.py` lines 848-880 and 944-993).
- Parent fills are polled and only then is actual entry price available; OCO children are attached after fill (`bowaka_v2_strategy.py` lines 1019-1132 and 1135-1239).

### 3.6 Exits/protection

Actual config:

- Stop: `8%`.
- Target: `15%`.
- Max hold: `3` days.
- Time stop: `15:45`.
- Signal fade: `initial_mode: telemetry_then_active_after_validation`, eval `15:45`, telemetry `16:05`, exit on hard/critical thresholds.
- Protected position: max unprotected `10s`, OCO attempts `2`, fallback stop enabled, flatten if unprotected, block entries on violation.
- See `bowaka_v2_config.yaml` lines 226-254.

The simulator must model not just stop/target/time-stop math, but the fact that live exits are mediated through child orders, OCO attach attempts, protected-state checks, cancel/replace/fallback behavior, and fill polling.

---

## 4. Bowaka v2 lab strengths

The lab has a strong foundation. These parts should be preserved, not discarded.

### 4.1 Clear separation of simulation modes

`src/bowaka_v2_lab/config/models.py` lines 29-48 define three mode-coupled behaviors:

| Mode | Purpose | Important defaults |
|---|---|---|
| `current_code_parity` | Reproduce actual live code behavior, including warts | scanner-start window, pre-submit accepted events, fail-open unknown instrument class, zero-spread quote fallback |
| `intended_realism` | Model corrected intended strategy | regular-open window, post-submit accepted events, fail-closed unknown instrument class, require real quotes |
| `smoke_fixture` | Synthetic CI/plumbing fixtures only | regular-open window, pre-submit events, synthetic calibrated quotes |

This is the right architectural pattern. The issue is that configs and some implementation details are not yet safe enough.

### 4.2 Frozen contract and generated intended config

`reference/actual_bowaka_v2_contract.yaml` is a useful frozen snapshot. It pins `source_sha256` and captures execution, exits, risk, scanner, signals, sizing, session, and universe settings (`actual_bowaka_v2_contract.yaml` lines 1-187).

`configs/bowaka_v2_intended_realism.yml` is generated from the contract and mostly aligns with actual values: scanner 25/3, session 09:45-15:30, IEX-relaxed signal gates, equal-slice sizing, risk tiers, 8%/15%/3-day exits.

### 4.3 Many valid unit/parity tests

The unit/parity suite is meaningful. It validates:

- actual contract loading;
- schema shape;
- feature/gate logic;
- risk-gate pieces;
- quote fallback behavior;
- artifact contracts;
- generated config roundtrips;
- Optuna metadata pieces;
- adjustment mismatch failure when `require_adjusted_daily_bars` is explicitly true.

The local result `537 passed` is credible evidence for component-level correctness. It is **not** evidence that the whole simulator is live-realistic.

### 4.4 Data-quality gates exist

`src/bowaka_v2_lab/data/data_quality.py` includes required checks for audit missing sessions, duplicates, OHLC violations, coverage, adjustment mismatch, missing quotes, and quote coverage (lines 55-70). Intended-realism runs are failed closed when required checks fail (lines 511-520).

This is the right direction, but the checks are still shallow in several places.

### 4.5 Point-in-time universe direction is correct

The walk-forward runner builds a point-in-time universe for sessions from the lake, and builds daily feature caches per session (`optuna/walkforward_runner.py` lines 210-218). That is essential for avoiding universe look-ahead.

### 4.6 Report/artifact infrastructure is valuable

The backtester writes data-quality reports, run manifests, config diffs, entry decisions, fills, trades, positions, daily equity, execution-quality reports, and promotion evidence. This structure should be retained and hardened.

---

## 5. Critical blockers and defects

Severity definitions:

- **P0:** invalidates research inference or can produce dangerously wrong live/paper expectations.
- **P1:** materially degrades realism, reproducibility, or test validity but may not invalidate every run.
- **P2:** cleanup, maintainability, or non-blocking enhancements.

### P0-001 — Active Optuna config is not actual Bowaka v2 parity

**File:** `bowaka_v2_lab/configs/bowaka_v2_walkforward_optuna.yml`

The file claims:

- `simulation.mode: current_code_parity` (lines 16-17);
- it “reproduces the live Bowaka v2 strategy” (comments lines 1-11);
- it optimizes against the real IEX market-data lake.

But it materially changes actual Bowaka v2:

| Section | Actual Bowaka v2 | `bowaka_v2_walkforward_optuna.yml` | Impact |
|---|---:|---:|---|
| `market_data.allow_non_sip_for_research_only` | `true` | `false` | Contradicts actual IEX paper setup. |
| `market_data.max_bar_age_seconds` | `90` | `60` | Different freshness gate. |
| `scanner.max_candidates_per_scan` | `25` | `10` | Changes opportunity set/ranking pressure. |
| `scanner.min_signal_strength` | no equivalent minimum in actual scanner | `0.55` | Adds a new gate. |
| `execution.parent_order_style/order_type` | `market` | `marketable_limit` | Changes execution path. |
| Quote max age | `15s` | `3s` | Much stricter quote filter. |
| Max spread | `100 bps` | `25 bps` | Much stricter spread filter. |
| Sizing | equal slice, `$4,000` target | fixed dollar `$5,000`, max `$25,000` | Different risk and capacity. |
| `risk.max_total_entries_per_day` | `10` | `12` | Different entry cap. |
| `risk.max_gross_exposure_pct` | `0.80` | `0.50` | Different portfolio cap. |
| `risk.daily_loss_pct` | `0.03` | `0.02` | Different kill switch. |
| ADV tiers | configured | `[]` | Removes liquidity caps. |
| Stop/target/max hold | `8%` / `15%` / `3 days` | `2%` / `6%` / `5 days` | Completely different strategy. |
| Signal fade | telemetry-then-active-after-validation | telemetry only | Different exit policy. |

**Why this is dangerous:** Bayesian optimization on this config optimizes a different strategy while labeling it current-code parity. The resulting parameter set can be statistically “best” for the wrong simulator and wrong strategy.

**Required fix:**

1. Quarantine `bowaka_v2_walkforward_optuna.yml` as an experimental variant or delete it.
2. Create a generated `configs/bowaka_v2_actual_iex_current_code.yml` from the frozen contract and actual config, with only intentional mode/feed differences.
3. Make the Optuna runner refuse `simulation.mode: current_code_parity` unless the config diff against `actual_bowaka_v2_contract.yaml` is clean or every mismatch is declared in a sidecar with a reason and risk classification.
4. Add a test: `test_walkforward_optuna_config_is_contract_parity_or_annotated()`.
5. Add a report artifact section listing every optimized parameter and whether it is part of the actual strategy contract, an intended-realism extension, or an experimental override.

**Acceptance criteria:**

- No config used for “Bowaka v2 optimization” can differ from frozen actual contract except via explicit, reviewed, versioned sidecar.
- A CI test fails if `configs/bowaka_v2_walkforward_optuna.yml` claims parity while changing stop/target/sizing/risk/execution/scanner defaults.

---

### P0-002 — Simulator processes exits only after all scans for the day

**File:** `src/bowaka_v2_lab/sim/backtester.py`

The session loop scans all timestamps first:

- Scans are processed in `for scan_ts in session_scan_times` at lines 487-550.
- Exit evaluation happens after that entire scan loop at lines 552-590.
- Daily equity/MTM are then recorded at lines 590-609.

**Why this invalidates results:**

Bowaka v2’s key risk controls are intraday and stateful. If an early trade stops out at 10:20, then:

- `daily_realized_pnl` should update before 10:21 scans;
- `stopouts_today` and consecutive stopouts should update before later entries;
- gross exposure should reduce after an exit;
- daily loss kill switch may block later entries;
- max concurrent positions may open capacity after exits;
- time stop at 15:45 should occur before any later end-of-session logic;
- signal fade should happen at the correct timestamp and affect subsequent risk.

Current backtester behavior allows all scans and new entries to occur before any same-day stop/target/time-stop/fade exit is realized. This makes same-day risk, stopout caps, gross exposure, and entry counts materially wrong.

**Example failure mode:**

1. 09:45: position A enters.
2. 10:05: position A should hit an 8% stop and create a realized loss.
3. 10:06-15:30: daily loss or stopout cap should potentially block new trades.
4. Current simulator still processes all 10:06-15:30 scans as if A has not closed and no loss exists.
5. Exit is recognized only after the scan loop finishes.

That is not a small approximation; it changes trade count, portfolio exposure, loss limits, and objective values.

**Required fix:** convert backtesting to an event-driven intraday replay.

Minimum event loop:

```text
for session_date:
    begin_session()
    build scan schedule and minute timeline
    for event_time in chronological intraday events:
        1. ingest latest bars/quotes/status through event_time
        2. poll/update parent fills and child fills through event_time
        3. attach/protect brackets for newly filled parents
        4. evaluate stops/targets/time-stop/fade for open lots through event_time
        5. update realized/unrealized PnL, stopouts, gross exposure, kill switches
        6. if event_time is a scan timestamp and risk permits: scan and submit entries
        7. record per-event state snapshot
    perform end-of-day reconciliation and MTM
```

**Acceptance criteria:**

Add integration tests with deterministic minute bars:

- `test_intraday_stop_before_later_scan_blocks_daily_loss_entries()`
- `test_intraday_target_before_later_scan_releases_max_concurrent_slot()`
- `test_two_stopouts_before_noon_blocks_third_entry_same_day()`
- `test_time_stop_at_1545_closes_before_eod_equity_snapshot()`
- `test_signal_fade_exit_updates_gross_before_next_scan()`

These tests should fail under the current end-of-session exit loop and pass only after interleaving exits/risk with scans.

---

### P0-003 — Current market-data sample does not contain replayable bars

**Path:** `research_notebooks/market_data`

Observed attached sample:

```text
market_data size: 271 KiB
parquet files: 2
- assets/vendor=alpaca/snapshot_id=2026-05-17T024746Z_alpaca_assets/assets.parquet
- _ingestion/audits/audit_2026-05-21T054116Z_iex.parquet
```

The `bars/` tree exists as directories:

```text
bars/vendor=alpaca/feed=iex/timeframe=1d/adjustment=raw/
bars/vendor=alpaca/feed=iex/timeframe=1m/adjustment=raw/
```

but contains no parquet payloads in the attached archive.

The manifest says the full lake has:

- `feed: iex`;
- `adjustment: raw`;
- start `2024-01-01`, end `2026-05-20`;
- daily symbols written: `6460`;
- minute symbol-month pairs written: `124386`;
- audit rows: `6461`;
- lake hash `sha256:925786ddba5d6010a47a1c7ae03483fa3253d2b55a9c20b3f3180a5d2985aa4e`.

Migration report says a prior full lake had:

- daily rows: `2,255,157`;
- minute rows: `49,013,719`;
- minute symbols: `1804`;
- daily symbols: `6459`.

**Conclusion:** I can validate the intended directory/manifest structure, but I cannot validate actual bar replay, time alignment, data quality, symbol coverage, or feature values from the attached sample. The full lake must be mounted/provided for a real audit.

**Required fix:** create a small but real replay subset, not synthetic, and include it in CI:

- 10-20 real IEX symbols across multiple liquidity regimes;
- at least 20 sessions with daily and minute bars;
- at least one split/corporate-action case;
- at least one halted/stale/no-volume case if available;
- real quote snapshots if available;
- a manifest hash and expected candidate/trade counts.

**Acceptance criteria:**

- `find market_data/bars -name '*.parquet'` returns real bar payloads for the fixture subset.
- A CI test replays the real IEX subset and compares deterministic candidate/decision/fill/trade artifacts to approved snapshots.

---

### P0-004 — Real historical quotes are missing, so execution realism is blocked

**File:** `src/bowaka_v2_lab/data/suppliers.py`

The lab documents that the current lake has no quote partitions:

- Lines 183-186: “current lake — which has no `quotes/` partitions — every call returns `None`”.

`current_code_parity` then reproduces the actual live-code zero-spread fallback. This is useful for comparing against current code behavior, but it is not realistic execution.

**Why this matters for Bowaka v2:**

Bowaka v2 trades low-priced, high-volatility names where spreads, stale quotes, quote fade, and halts matter. A zero-spread, zero-age quote can turn a marginal microcap signal into a fillable trade with no adverse selection. That directly biases:

- entry acceptance rate;
- fill rate;
- slippage;
- price-chase rejections;
- spread gate rejections;
- stop/target distance after actual fill;
- PnL and drawdown.

**Required fix:** ingest real historical quotes for IEX immediately, and SIP/NBBO once SIP is available.

Minimum quote schema:

```text
quotes/vendor=alpaca/feed=iex/symbol=<SYM>/date=<YYYY-MM-DD>/part-*.parquet
columns:
  timestamp_utc
  symbol
  bid
  ask
  bid_size
  ask_size
  exchange/venue if available
  conditions if available
  feed
  source_latency_ms if measured
  ingestion_run_id
```

For SIP/NBBO:

```text
quotes/vendor=alpaca/feed=sip/symbol=<SYM>/date=<YYYY-MM-DD>/part-*.parquet
columns:
  timestamp_utc
  nbbo_bid
  nbbo_ask
  bid_size
  ask_size
  bid_exchange
  ask_exchange
  quote_conditions
  luld_state/status if available
```

**Acceptance criteria:**

- `intended_realism` refuses to run if quote coverage at candidate timestamps is below configured threshold.
- `current_code_parity` can still replay the zero-spread fallback, but reports it as a current-code artifact and caps suitability at research-only.
- Execution report includes quote coverage, median/95p spread bps, median/95p quote age, rejected-by-spread, rejected-by-stale, and rejected-by-missing-quote.

---

### P0-005 — Adjusted daily bar requirement is not enforced by generated config

Actual strategy config requires adjusted/split-adjusted daily bars:

- `bowaka_v2_config.yaml` lines 51-53: `require_adjusted_daily_bars: true`, `require_split_adjustment: true`.

Lab model default:

- `MarketDataConfig.require_adjusted_daily_bars` defaults to `False` (`config/models.py` lines 103-118).

Generated intended config:

- `configs/bowaka_v2_intended_realism.yml` lines 50-58 omit `require_adjusted_daily_bars`.

Data-quality logic:

- `build_adjustment_check()` only fails if `require_adjusted` is true and lake adjustment is raw (`data_quality.py` lines 302-325).

Current lake manifest:

- `adjustment: raw`.

**Why this is dangerous:**

Bowaka v2 baselines and gates depend on prior close, ATR, EMA, ADV, price limits, and gap/return features. Splits and corporate actions can distort all of these. A reverse split in a microcap can produce completely invalid price/ATR/gap/RVOL features if raw bars are mixed with adjusted assumptions.

**Required fix:**

1. Add `market_data.require_adjusted_daily_bars: true` to generated configs derived from actual Bowaka v2.
2. Generate/ingest adjusted daily bars or split-adjusted baseline features before any research run.
3. Keep raw intraday bars if needed for execution, but daily baselines must be adjustment-aware and lineaged.
4. Add manifest fields distinguishing daily adjustment from intraday adjustment.
5. Add tests that a generated intended-realism config against the current raw manifest fails before running.

**Acceptance criteria:**

- `import-actual-config` output includes `require_adjusted_daily_bars: true` and `require_split_adjustment: true` or equivalent typed fields.
- Any Bowaka v2 research/optimization run with raw daily baselines fails closed unless explicitly labeled as `plumbing_only`.

---

### P0-006 — Marketable-limit fill model is not realistic

**File:** `src/bowaka_v2_lab/sim/fills.py`

Current marketable-limit fill behavior:

- Buy limit = `quote.ask * (1 + offset)` (lines 211-214).
- Timeout window rounds seconds to whole minutes, minimum one minute (lines 216-219).
- Uses forward minute-bar highs as “ask path” (`_ask_path_from_bars()` lines 165-177).
- For a buy, if `min(path) > limit_price`, no fill; otherwise fill at full limit price (lines 220-225 and 239-254).

**Problems:**

1. A buy marketable limit priced above the current ask is immediately executable if displayed/available liquidity exists; it does not need future minute highs to stay below the limit.
2. Filling at the full limit offset is conservative in price, but not realistic as a fill model. Real fills may occur at ask, through multiple levels, partially, or not at all depending on size and liquidity.
3. A 30-second timeout rounded to one minute is too coarse for a strategy whose scanner/loop timing is seconds-sensitive.
4. Liquidity is derived from a fraction of prior ADV, not contemporaneous quote size, minute volume, or order book state.
5. The model does not simulate queue, adverse selection, cancel/replace, or partial fills over multiple events.

**Required fix:** implement execution models by data availability tier.

| Tier | Data available | Model |
|---|---|---|
| Tier 0 | no quotes | no research-grade execution; only current-code-parity zero-spread or synthetic smoke fixtures |
| Tier 1 | historical top-of-book quotes | immediate marketable-limit execution against quote ask/bid size; partial if qty > visible size; slippage if stress model crosses beyond top-of-book |
| Tier 2 | quotes + minute volume | quote-size + participation cap; fill probability/partial fill conditioned on spread, volume, volatility, and order size |
| Tier 3 | SIP/NBBO or depth/order-book data | NBBO/depth-aware, queue/probabilistic fill, adverse-selection model |
| Tier 4 | paper/live reconciliation | calibrate slippage/fill probability to real broker fills |

**Acceptance criteria:**

- Market order and marketable-limit order models are separately tested.
- Buy marketable limit with ask `10.00`, limit `10.05`, ask size greater than qty fills immediately near ask under base stress.
- Buy marketable limit with ask size below qty produces partial fill or staged fill, not automatic full fill.
- Timeout tests use sub-minute event times, not rounded one-minute proxies.

---

### P0-007 — Protected-position/OCO lifecycle is materially simplified

Actual strategy lifecycle:

- Emit accepted decision.
- Submit parent.
- Record `pending_fill` position only after broker accepts submit (`bowaka_v2_strategy.py` lines 848-880 and 944-993).
- Poll parent fill (`poll_fills_v2()` lines 1135-1239).
- Only after actual fill, attach OCO children (`submit_oco_children_v2()` and `submit_pending_oco_children_v2()` around lines 1019-1132).
- Enforce protected-position invariant from config: max unprotected `10s`, attach attempts `2`, fallback stop, flatten if unprotected, block entries on violation (`bowaka_v2_config.yaml` lines 248-254).

Lab behavior:

- After fill simulation, it creates a `Position` with `bracket_attached=True` immediately (`strategy_consumer.py` lines 490-529).

**Why this matters:**

The unprotected interval between parent fill and bracket attach is one of the most important live risks in the strategy. It also affects whether new entries are allowed. If OCO attach fails or is delayed, live behavior should include fallback stop/flatten/block-entry logic. The current simulator cannot expose this failure mode.

**Required fix:** add a state machine:

```text
candidate_emitted
  -> order_planned
  -> parent_submitted
  -> parent_acknowledged or parent_rejected
  -> parent_partially_filled / parent_filled / parent_canceled
  -> oco_attach_pending
  -> oco_attached or oco_attach_failed
  -> protected / unprotected_violation
  -> fallback_stop_submitted / flatten_submitted / entries_blocked
  -> child_exit_filled / manual_exit_filled
```

**Acceptance criteria:**

- Tests cover parent rejected, parent partial, parent filled + OCO attached, OCO attach failed once then succeeded, OCO attach failed twice then fallback stop, OCO attach failed and flatten, block entries while violation active.
- Report includes `max_unprotected_seconds_observed`, `oco_attach_attempts`, `fallback_stop_count`, `flatten_unprotected_count`, and `entries_blocked_by_protection_count`.

---

### P0-008 — Signal fade `telemetry_then_active_after_validation` is treated as active immediately

**File:** `src/bowaka_v2_lab/sim/exits.py`

Current lab code:

```python
fade_mode = str(fade_cfg.get("initial_mode", cfg.get("signal_fade_mode", "telemetry_only")))
fade_active = fade_mode in ("active", "telemetry_then_active_after_validation")
```

See lines 336-342.

Actual config:

```yaml
signal_fade:
  enabled: true
  initial_mode: telemetry_then_active_after_validation
```

See `bowaka_v2_config.yaml` lines 235-246.

**Why this is likely wrong:**

The phrase “telemetry_then_active_after_validation” strongly implies the initial state is telemetry, not immediate trading exit. Treating it as active immediately changes exit timing, hold period, PnL, stop/target interactions, and optimization objectives.

**Required fix:** add explicit state:

```yaml
exits:
  signal_fade:
    initial_mode: telemetry_then_active_after_validation
    activation_state: telemetry   # telemetry | active
    activation_criteria_artifact: null
```

or encode it in a run/promotion artifact after validation.

**Acceptance criteria:**

- In default actual-contract replay, signal fade records would-exit telemetry but does not close positions unless a validation flag/artifact explicitly activates it.
- Tests prove `telemetry_then_active_after_validation` is telemetry before activation and active only after a documented activation state.

---

### P0-009 — Price-chase and halt/LULD gates are not fully simulated

Actual strategy has:

- `_price_chase_gate()` (`bowaka_v2_strategy.py` lines 400-418).
- `_halt_gate()` (`bowaka_v2_strategy.py` lines 421-430).
- Configured halt/LULD gate (`bowaka_v2_config.yaml` lines 162-170).

Lab strategy consumer handles quote spread and age (`strategy_consumer.py` lines 195-215), but I did not find equivalent non-tunable price-chase and halt/status gates in the execution path.

`optuna/search_space.py` documents that price-chase and halt gates are excluded from the search space because they are non-tunable or data-dependent (lines 103-130). Excluding them from tuning is reasonable. Excluding them from simulation is not.

**Required fix:**

- Implement price-chase gate as fixed strategy logic in `StrategyConsumer`.
- Add quote/status fields needed for halt/LULD gating.
- If status data is unavailable, report `halt_gate_unavailable` and cap suitability. Do not silently assume no halts.

**Acceptance criteria:**

- Candidate with quote mid > signal price by more than 10% rejects with `price_chase_band`.
- Candidate with quote/status `halted`, `pending_review`, or `luld_pause` rejects with `halt_or_pending_review`.
- Dataset/report states halt/status coverage.

---

### P0-010 — Data-quality coverage checks are too shallow

**File:** `src/bowaka_v2_lab/data/data_quality.py`

`build_coverage_check()` checks:

- one daily bar per symbol/session;
- minute bars only at the session’s first scan timestamp (`probe_ts = scan_times[0]`) (`data_quality.py` lines 207-296).

This misses:

- missing minute bars later in the scan window;
- missing bars during exit path after entry;
- gaps inside a session;
- out-of-order rows;
- duplicate timestamps;
- stale bars at each scan;
- missing last bar needed for time stop or max-hold exit;
- quote coverage by timestamp beyond candidates;
- split/corporate-action alignment;
- delisted/symbol-change issues.

**Required fix:**

Make coverage checks multi-level:

1. **Ingestion-level checks:** partition existence, schema, sorted timestamps, duplicates, OHLC validity, zero/negative prices, volume anomalies.
2. **Session-level checks:** expected minute count per XNYS session, early closes, gaps, stale segments.
3. **Replay-level checks:** every scan timestamp has needed bars for each eligible symbol; every accepted entry has forward exit path data through max hold; every candidate requiring a quote has quote within max age.
4. **Feature-level checks:** daily baselines use only completed prior sessions; no same-day leakage; corporate-action-adjusted daily features.
5. **Quote/status-level checks:** quote coverage, quote age distribution, spread distribution, halt/status availability.

**Acceptance criteria:**

- A dataset with missing minute bars after the first scan fails intended realism.
- A dataset with valid first scan but missing exit path fails intended realism or marks trades unexecutable, not successful.
- Report distinguishes “no candidates” from “no data” and includes a minimum statistical-power gate.

---

### P0-011 — Current-code parity permits bad data by design, so it must not be optimized for research claims

`evaluate_startup_dq()` only gates `intended_realism`; `current_code_parity` and `smoke_fixture` always return `None` (data_quality.py lines 511-520). Optuna preflight also documents that current-code parity only warns on failing DQ/low quote coverage (`optuna/preflight.py` lines 1-28).

This makes sense for reproducing the actual code’s warts. It is dangerous for Bayesian optimization.

**Required fix:**

- Add a separate `optimization_requires_realism: true` gate.
- Refuse Optuna on `current_code_parity` unless the study is explicitly labeled `paper_reconciliation_only` and output suitability is capped at research-only.
- For any “parameter recommendation” study, require `intended_realism` plus real quotes and adjusted daily baselines.

**Acceptance criteria:**

- `bowaka-v2-lab optuna` refuses `current_code_parity` unless `--allow-current-code-parity-study --tier research_only` is explicitly supplied.
- Result artifacts prominently label such studies as “current-code wart replay; not parameter recommendation evidence.”

---

### P1-001 — Synthetic quote RNG is constructed but not passed, and Python hash is nondeterministic

**File:** `src/bowaka_v2_lab/sim/strategy_consumer.py`

Lines 170-182 construct:

```python
rng = random.Random(hash((symbol, str(candidate_event.get("scan_timestamp", decision_ts)))))
resolution = resolve_quote(...)
```

but `rng` is not passed to `resolve_quote()`. Therefore `quote_model.resolve_quote()` falls back to its own deterministic default for synthetic quotes. Also, Python’s built-in `hash()` is process-salted and not stable across runs if it were used.

**Required fix:**

```python
seed_material = f"{run_seed}|{symbol}|{candidate_event.get('scan_timestamp', decision_ts)}"
seed_int = int(hashlib.sha256(seed_material.encode()).hexdigest()[:16], 16)
rng = random.Random(seed_int)
resolution = resolve_quote(..., rng=rng)
```

**Acceptance criteria:**

- Synthetic fallback tests prove two identical runs produce identical quotes across separate Python processes.
- Synthetic fallback remains prohibited for research-grade intended-realism runs.

---

### P1-002 — Quote supplier records request timestamp, not actual quote timestamp

**File:** `src/bowaka_v2_lab/data/suppliers.py`

Lines 190-205 map a quote row to a dict, but set:

```python
"quote_timestamp": str(pd.Timestamp(ts)),
```

This appears to use the requested timestamp rather than the stored quote row timestamp. If the quote is at-or-before `ts`, the actual quote timestamp matters for age, audit, and stale quote analysis.

**Required fix:** use the `QuoteRow` timestamp field if available. If `QuoteRow` does not carry it, extend `MarketDataStore.quotes_at_or_before()` to return it.

**Acceptance criteria:**

- Quote-age test with a quote 12 seconds before scan records quote timestamp at scan-12s and quote age 12, not scan timestamp.

---

### P1-003 — Scanner increments per-symbol daily entry count on candidate emission, not accepted/filled entry

**File:** `src/bowaka_v2_lab/scanner/scan_loop.py`

Lines 336-338 increment `entries_per_symbol_today` when a candidate is emitted.

This is a reasonable scanner-dedup choice if “entry” means “signal emitted,” but actual strategy entry count/risk should be based on accepted/submitted/filled orders depending on the rule. If a candidate is emitted and then rejected by quote/risk/broker, the current scanner state may suppress later valid candidates for the same symbol.

**Required fix:** clarify semantics:

- `signal_emits_per_symbol_today` for scanner dedup;
- `entries_per_symbol_today` for accepted/filled portfolio entries.

**Acceptance criteria:**

- Test emitted-but-missing-quote candidate does not consume same-symbol entry allowance unless the intended policy says it should.
- Report includes both emitted signal counts and actual entry counts.

---

### P1-004 — Holdout scoring does not use full report metrics

**File:** `src/bowaka_v2_lab/optuna/holdout.py`

Holdout calls `_run_fold_backtest()` without `return_report=True` (lines 103-111), then sets `worst_day_loss=0.0` in the `FoldResult` (lines 114-126).

The walk-forward objective can use daily mark-to-market drawdown from `report.json` when `return_report=True` (`optuna/walkforward_runner.py` lines 171-252). The final holdout should be evaluated with the same metric basis.

**Required fix:**

- Call `_run_fold_backtest(..., return_report=True)` in holdout.
- Use `fold_result_from_report()` for holdout as for validation folds.
- Fail if report is missing/corrupt.

**Acceptance criteria:**

- Holdout result includes daily equity, daily MTM drawdown, worst-day loss, quote coverage, fill rate, and missing quote penalties computed identically to validation folds.

---

### P1-005 — Walk-forward dataset hash is not content-addressed enough

**File:** `src/bowaka_v2_lab/optuna/walkforward_runner.py`

Lines 657-659 create `dataset_hash` from `[symbols, feed, dates]`. This is not enough to reproduce a study because the same symbols/feed/dates can map to different parquet contents, adjustment policies, asset-master snapshots, quote data, or ingestion versions.

**Required fix:** include:

- market-data manifest lake hash;
- bar partition paths and parquet footer hashes or content hashes;
- asset snapshot ID/hash;
- quote partition hashes;
- audit parquet hash;
- adjustment policy;
- config hash;
- code manifest hash.

**Acceptance criteria:**

- Editing one bar parquet changes the study dataset hash.
- Re-running with same data/config/code produces byte-identical lineage IDs.

---

### P1-006 — Walk-forward preflight probes only a small sample

`optuna/walkforward_runner.py` probes only the first validation window’s first five sessions (lines 594-617), and `probe_quote_coverage()` samples at most 200 `(symbol, scan_ts)` pairs and only one scan timestamp per session (`optuna/preflight.py` lines 290-331).

This is fine as a cheap early warning but not enough to launch a high-cost study with confidence.

**Required fix:**

- Keep cheap preflight as fast fail.
- Add full fold preflight before each fold/trial group or at least before the study starts for all validation/holdout windows.
- Cache preflight results by dataset/config hash.

**Acceptance criteria:**

- Study artifact contains coverage metrics for every fold, not just first validation probe.
- Study refuses when any fold lacks required daily/minute/quote/exit-path coverage.

---

### P1-007 — Full integration/reconciliation suite needs deterministic CI handling

The unit/parity suite is strong, but integration/reconciliation did not complete in the local execution window. This could be test duration, plugin interaction, subprocess teardown, or a hanging test. Individual selected tests pass.

**Required fix:**

- Split integration and reconcile jobs by topic.
- Add `pytest-timeout` per test or per module.
- Emit JUnit XML and logs for hangs.
- Mark tests requiring paper logs or live credentials explicitly.
- Add a `make test-fast`, `make test-integration`, `make test-reconcile`, `make test-live` matrix.

**Acceptance criteria:**

- CI can run all non-live tests within a known budget and fails deterministically on hangs.
- Each hang produces a stack trace.

---

### P1-008 — Objective scale and penalty units need validation

`optuna/objective.py` has a conservative objective, which is good, but the units need locking. It combines net return, drawdown, CVaR/worst-day loss, trade count, missing quotes, quote coverage, turnover, concentration, ambiguous bars, and fill rate penalties.

Potential issue: fields like `net_return_pct` and penalties must use consistent units. If `net_return_pct` is stored as `3.0` for 3% but penalties assume `0.03`, or vice versa, the objective can be dominated by the wrong term.

**Required fix:**

- Add a `MetricUnits` test table.
- Assert `net_return`, drawdown, loss, and penalties are all in either decimal returns or percentages, never mixed.
- Include objective term breakdown in every Optuna trial’s user attrs.

**Acceptance criteria:**

- A known toy fold with known net return/drawdown/penalties produces an exact expected objective.
- Trial dataframe contains columns for every objective term.

---

### P1-009 — Actual scanner/live cadence mismatch should be explicitly reconciled

Actual config has `loop_interval_seconds: 5`, scanner config has `scan_interval_seconds: 60`, and live scanner implementation uses its own behavior. Lab schedule appears to replay scan cadence at 60s. This may be correct for candidate emission, but the live strategy runner may run risk/execution polling more frequently.

**Required fix:**

- Separate scanner cadence, strategy consumer cadence, fill polling cadence, OCO attach cadence, and quote-refresh cadence.
- A 60-second scanner does not imply exits/fills/protection are checked only once per minute.

**Acceptance criteria:**

- Event loop can poll fills/protection every 5 seconds while scanning every 60 seconds.
- OCO unprotected 10-second invariant can be represented.

---

### P1-010 — IEX-only optimization should be feed-specific and non-portable

Even after simulator fixes, IEX-only backtests are not SIP-valid. The actual config already says the IEX signal regime cannot be trusted. IEX thresholds are intentionally relaxed. Optimizing those thresholds on IEX risks creating a parameter set that is only an artifact of IEX routing/coverage.

**Required fix:**

- Any IEX study name/report must include `feed=iex`, `partial_tape=true`, `suitability=research_only`.
- IEX studies should optimize plumbing/execution settings only if those settings are feed-specific and later revalidated on SIP.
- Signal thresholds learned on IEX must not be carried to SIP without a new SIP study.

**Acceptance criteria:**

- Promotion gate cannot advance any IEX result beyond research-only/backtesting-only, as already intended in README and dispatcher.
- Reports explicitly state that IEX RVOL/range/volume features are partial-tape features.

---

## 6. Config-by-config assessment

### 6.1 `configs/bowaka_v2_intended_realism.yml`

**Status:** closest to actual contract, but not ready.

Strengths:

- Generated from frozen contract.
- Scanner cap `25`, entries `3`.
- Equal-slice sizing matches actual.
- Stop/target/max-hold match actual.
- Risk and ADV tiers match actual.
- Signal thresholds match actual IEX-relaxed thresholds.

Issues:

- `market_data.feed: sip` while current attached lake is IEX-only.
- `market_data.allow_non_sip_for_research_only: false`, appropriate for SIP but not IEX.
- `max_bar_age_seconds: 60` differs from actual `90`.
- Missing `require_adjusted_daily_bars: true` despite actual config.
- Requires real quotes in intended-realism mode, but current lake has no quotes.
- Uses IEX-relaxed thresholds despite `feed: sip`; actual comments say SIP should tighten RVOL/range/EMA thresholds.

Recommended use:

- Use as a generated baseline for intended realism, but fix data adjustment and feed-specific threshold handling.
- For SIP, decide whether to use actual IEX-relaxed thresholds as frozen paper contract or SIP-intended thresholds as a deliberate variant. Do not mix silently.

### 6.2 `configs/bowaka_v2_research_iex_plumbing.yml`

**Status:** plumbing/smoke only, not actual Bowaka v2.

It explicitly uses `simulation.mode: smoke_fixture` and changes many values:

- scan start `09:30`, not actual scanner start `09:45`;
- max price `$1000`, not `$20`;
- min ADV `$1,000,000`, not `$250,000`;
- scanner max candidates `10`, min signal `0.5`;
- execution `marketable_limit`, not actual `market`;
- fixed-dollar sizing, not equal slice;
- risk and exit values very different.

Recommended use:

- Keep only for CI smoke/plumbing.
- Rename to make that unambiguous, e.g. `bowaka_v2_smoke_fixture_iex_plumbing.yml`.
- Never use for Bowaka v2 research or optimization.

### 6.3 `configs/bowaka_v2_walkforward_optuna.yml`

**Status:** **do not use for Bowaka v2 optimization.**

This is the most dangerous config because it claims current-code parity while changing the strategy materially. Quarantine until reconciled.

Recommended replacement:

- `bowaka_v2_actual_iex_current_code_optuna.yml` for paper-reconciliation-only studies.
- `bowaka_v2_intended_iex_realism_optuna.yml` only after real IEX quotes and adjusted daily baselines exist.
- `bowaka_v2_intended_sip_realism_optuna.yml` only after SIP bars/quotes/status data exist.

### 6.4 `configs/bowaka_v2_research_sip.yml`

**Status:** experimental SIP variant, not actual Bowaka v2.

It tightens thresholds and changes risk/exits/execution. That may be a reasonable hypothesis, but it is not the actual strategy contract.

Recommended use:

- Keep only with explicit parity sidecar: `variant=sip_tightened_experimental`.
- Do not compare its results directly to actual Bowaka v2 without labeling.

---

## 7. Testing completeness assessment

### 7.1 What current tests validate reasonably well

Based on inspection and local execution, the lab has meaningful coverage for:

- typed config loading and schema validation;
- generated contract/config parity mechanics;
- feature gate computation;
- scanner emission/ranking/caps at unit level;
- quote fallback behaviors;
- risk gate components;
- position ID / multi-lot portfolio mechanics;
- bracket pricing from actual fill at component level;
- data-quality gate when `require_adjusted_daily_bars` is explicitly true;
- smoke backtest artifact creation;
- Optuna study metadata and search-space coverage;
- report artifact shape.

These are useful component tests.

### 7.2 Tests that are valid but insufficient

Several tests prove a component works in isolation but not that the backtest is live-realistic:

- `tests/integration/test_backtester_risk_kills.py` preloads realized losses into a `Portfolio` and checks risk gates. It does not prove losses generated by intraday exits update state before later scans.
- Signal-fade tests validate active/telemetry behavior, but the default actual mode `telemetry_then_active_after_validation` needs explicit semantics.
- Adjustment mismatch tests prove failure when `require_adjusted=True`, but the generated intended config omits that flag.
- Synthetic quote tests prove synthetic fallback works, but synthetic fallback should not be inference-grade.
- Search-space tests prove actual values are included in ranges, but the active Optuna config is still not actual parity.

### 7.3 Missing high-priority tests

Add these before any serious backtest or optimization.

#### Temporal/event-loop tests

| Test | Purpose |
|---|---|
| `test_stop_before_later_scan_blocks_new_entries()` | Stop at 10:05 updates risk before 10:06 scan. |
| `test_target_before_later_scan_releases_concurrent_slot()` | Exit frees gross/concurrent capacity intraday. |
| `test_stopout_cap_blocks_same_day_after_two_stops()` | Stopout count updates before later entries. |
| `test_daily_loss_kill_switch_from_intraday_realized_loss()` | Realized loss from simulated exits blocks subsequent entries. |
| `test_unrealized_loss_kill_switch_if_intended_policy_uses_mtm()` | If intended realism uses total PnL, intraday MTM can block. |
| `test_1545_time_stop_occurs_before_eod_snapshot()` | Time stop not delayed to end-of-session batch. |

#### Execution/quote tests

| Test | Purpose |
|---|---|
| `test_marketable_limit_buy_fills_immediately_against_ask_size()` | Avoid future-high fill artifact. |
| `test_marketable_limit_partial_fill_when_qty_exceeds_ask_size()` | Partial fill realism. |
| `test_quote_timestamp_is_actual_quote_timestamp()` | Correct age/staleness. |
| `test_price_chase_gate_rejects_quote_mid_above_band()` | Actual gate ported. |
| `test_halt_gate_rejects_halted_symbol()` | Actual gate ported. |
| `test_missing_real_quote_fails_intended_realism_before_fill()` | No fallback in realism. |

#### OCO/protection tests

| Test | Purpose |
|---|---|
| `test_parent_fill_then_oco_attach_success()` | Normal lifecycle. |
| `test_oco_attach_retry_then_success()` | Retry behavior. |
| `test_oco_attach_two_failures_triggers_fallback_stop()` | Protected invariant. |
| `test_unprotected_violation_blocks_new_entries()` | Risk lockout. |
| `test_unprotected_violation_flatten_if_configured()` | Emergency flatten. |

#### Data lineage/quality tests

| Test | Purpose |
|---|---|
| `test_generated_actual_config_requires_adjusted_daily()` | Actual contract flag preserved. |
| `test_raw_daily_lake_fails_actual_intended_config()` | No raw daily research. |
| `test_missing_late_session_minute_fails_coverage()` | Coverage beyond first scan. |
| `test_missing_exit_path_data_fails_or_marks_trade_unexecutable()` | No fantasy exits. |
| `test_split_event_does_not_leak_raw_baseline()` | Corporate-action validation. |
| `test_content_hash_changes_on_bar_payload_edit()` | Reproducibility. |

#### Optuna tests

| Test | Purpose |
|---|---|
| `test_optuna_config_must_be_contract_parity_or_annotated()` | Prevent wrong-strategy studies. |
| `test_current_code_parity_optuna_requires_research_only_override()` | Prevent wart optimization. |
| `test_holdout_uses_report_metrics()` | Comparable validation/holdout. |
| `test_objective_units_are_consistent()` | Avoid mixed pct/decimal objective. |
| `test_trial_attrs_include_objective_term_breakdown()` | Auditability. |
| `test_final_holdout_not_accessible_during_trial_objective()` | No holdout leakage. |

---

## 8. Required data lake upgrades

The user preference is correct: use real IEX data until SIP is available; synthetic data only as a last resort. The current lab should therefore treat synthetic as CI/plumbing only.

### 8.1 Minimum IEX lake required for Bowaka v2 research-only replay

Required partitions:

```text
market_data/
  assets/vendor=alpaca/snapshot_id=<timestamp>/assets.parquet
  bars/vendor=alpaca/feed=iex/timeframe=1d/adjustment=split_adjusted/...
  bars/vendor=alpaca/feed=iex/timeframe=1m/adjustment=raw/...
  quotes/vendor=alpaca/feed=iex/...
  corporate_actions/vendor=alpaca_or_refinitiv/...   # splits/dividends/symbol changes
  statuses/vendor=alpaca_or_exchange/...             # halts/LULD if available
  _ingestion/manifest.json
  _ingestion/audits/*.parquet
```

Notes:

- Daily baselines should be split-adjusted or explicitly adjusted in feature construction.
- Intraday execution bars may remain raw, but must be aligned with actual traded prices and corporate-action events.
- Quote data is required for realistic quote/spread/age/price-chase gates.
- Halt/LULD/status data is required to model halt gate; absent status should be reported as a coverage gap, not assumed clean.

### 8.2 IEX-specific caveats

IEX is partial tape. Therefore:

- `rvol_so_far`, `projected_full_day_rvol`, and `range_expansion_so_far` are IEX-feed features, not consolidated market features.
- IEX ADV is not consolidated ADV.
- IEX quote/spread is not NBBO unless explicitly sourced as NBBO from a consolidated feed.
- Any parameter optimization on IEX must be labeled as IEX-specific and not portable to SIP without retraining/revalidation.

### 8.3 SIP migration requirements

Once SIP is available, build separate partitions:

```text
bars/vendor=alpaca/feed=sip/timeframe=1d/adjustment=split_adjusted/...
bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw/...
quotes/vendor=alpaca/feed=sip/...
```

Then rerun:

1. data-quality audits;
2. feature parity checks;
3. IEX vs SIP comparative feature analysis;
4. SIP-only walk-forward optimization;
5. SIP final holdout;
6. SIP simulation vs paper-trading reconciliation.

Do not “flip” IEX-optimized thresholds to SIP. Treat the feed change as a new dataset and potentially a new signal regime.

---

## 9. Required simulator upgrades

### 9.1 Build a true event-driven simulator

The most important engineering task is replacing the session-batch exit processing with an event-driven engine.

Recommended event types:

```python
class EventType(Enum):
    SCAN = "scan"
    QUOTE = "quote"
    MINUTE_BAR = "minute_bar"
    PARENT_ACK = "parent_ack"
    PARENT_FILL = "parent_fill"
    OCO_ATTACH_ATTEMPT = "oco_attach_attempt"
    CHILD_FILL = "child_fill"
    PROTECTION_CHECK = "protection_check"
    TIME_STOP_CHECK = "time_stop_check"
    SIGNAL_FADE_CHECK = "signal_fade_check"
    EOD_MARK = "eod_mark"
```

At minimum, each scan timestamp should first process all fills/exits/protection state up to that timestamp.

### 9.2 Maintain portfolio state continuously

State must update after every event:

- open positions;
- pending parent orders;
- pending OCO attach;
- child order status;
- realized PnL;
- unrealized PnL;
- gross exposure;
- daily entries;
- stopouts;
- consecutive stopouts;
- kill switch;
- symbols entered today;
- unprotected violations.

### 9.3 Separate actual-code parity from intended realism

Keep `current_code_parity`, but do not confuse it with realism.

Examples:

| Behavior | Current-code parity | Intended realism |
|---|---|---|
| Missing quote | zero-spread signal-price quote | reject candidate; fail low quote coverage |
| Accepted event | emitted before broker submit | emitted after broker acceptance/fill policy |
| Unknown instrument class | fail open | fail closed |
| Scanner window | actual code scanner-start behavior | regular-open session features, if intended |
| Protection | actual strategy state machine | same or stricter state machine |

Each run manifest must state which contract was used.

### 9.4 Model fills conservatively and calibrate to paper data

Do not overfit fill models to PnL. Calibrate execution realism using paper/live logs:

- accepted candidate timestamp;
- quote snapshot at decision;
- order submit timestamp;
- broker ack timestamp;
- fill timestamp(s);
- fill price(s);
- child order attach timestamp;
- exit fill timestamp/price;
- rejects/cancels.

Metrics to calibrate:

- acceptance-to-fill latency;
- fill probability by spread/ADV/volatility/size;
- slippage vs quote mid/ask;
- partial-fill frequency;
- OCO attach latency/failure;
- unprotected duration;
- stop/target execution slippage.

### 9.5 Add microstructure stress scenarios

For low-priced momentum/microcap names, include stress cases:

- spread widens after signal;
- quote stale at decision;
- price gaps through stop;
- stop and target both touched in same minute;
- halt after entry before stop can execute;
- OCO attach fails;
- symbol becomes untradeable/halted;
- partial fill then reversal;
- low ADV cap rejects aggregate multi-lot position;
- split/reverse split affects baselines.

---

## 10. Bayesian optimization requirements

### 10.1 Do not optimize until P0 simulator/data blockers are fixed

Bayesian optimization amplifies simulator flaws. If the simulator has zero-spread fills, delayed exits, raw baseline leakage, or wrong config, Optuna will find parameters that exploit those defects.

### 10.2 Use a validated base config

Only run Optuna from one of these explicitly labeled configs:

1. `actual_iex_current_code_reconciliation`: reproduces live code warts; research-only; used to compare paper logs, not recommend parameters.
2. `intended_iex_realism`: IEX bars + IEX real quotes + adjusted daily baselines; research-only; feed-specific, not SIP-valid.
3. `intended_sip_realism`: SIP bars + SIP/NBBO quotes + adjusted daily baselines; candidate for backtesting-only after validation.

### 10.3 Lock the search space

Search-space rules:

- Include actual current values in every range.
- Do not tune parameters absent from actual strategy unless config is explicitly experimental.
- Do not remove fixed safety gates from the simulator just because they are non-tunable.
- Penalize high-turnover/high-concentration/low-fill/low-coverage candidates.
- Keep ranges narrow around plausible live values until evidence supports broader exploration.

### 10.4 Walk-forward design

Recommended protocol:

1. Freeze final holdout before any study.
2. Use rolling/walk-forward validation; never tune on final holdout.
3. Require each fold to pass data-quality and quote-coverage gates.
4. Store every fold’s dataset/content hash, config hash, code hash, and objective term breakdown.
5. Use median fold score minus stability penalty, not best fold score.
6. Report fold dispersion, worst fold, worst day, and parameter stability.
7. Run ablations after optimization: no signal-fade, no price-chase, no ADV cap, wider spreads, higher latency, lower fill rates.
8. Run random-search baseline and incumbent actual-config baseline.
9. Run final holdout once, after study selection, using identical objective/report metrics.

### 10.5 Objective requirements

Objective should include at minimum:

- net return after commissions, regulatory fees, slippage, and unfilled order effects;
- daily mark-to-market drawdown, not just closed-trade drawdown;
- worst-day loss / CVaR-like downside metric;
- trade count penalty for low statistical power;
- missing quote penalty;
- quote coverage penalty;
- fill-rate penalty;
- turnover penalty;
- concentration penalty;
- ambiguous-bar penalty;
- stopout/consecutive stopout penalties;
- protection-violation penalty.

Every trial should store:

```text
trial.params
trial.value
fold_scores
fold_metrics
objective_terms
config_hash
dataset_hash
code_hash
simulation_mode
feed
quote_coverage
n_trades
n_candidates
n_fills
n_rejects_by_reason
```

### 10.6 PostgreSQL/Optuna persistence

`optuna/dispatcher.py` supports PostgreSQL when configured and falls back to SQLite. For serious studies, use PostgreSQL-backed Optuna storage, not local SQLite, and ensure the study records:

- dataset content hash;
- code manifest hash;
- config hash;
- frozen search-space version;
- sampler/pruner/seed;
- objective version;
- trial-level artifacts or artifact pointers.

SQLite is acceptable only for local smoke tests.

---

## 11. Phased implementation plan

### Phase 0 — Freeze, label, and protect current state

**Goal:** prevent accidental wrong-strategy optimization.

Tasks:

1. Rename/quarantine configs that are smoke or experimental.
2. Add parity sidecar requirement for every non-generated config.
3. Add CI test refusing Optuna configs that claim parity but differ from contract.
4. Add README warning: `bowaka_v2_walkforward_optuna.yml` is not valid until reconciled.
5. Add `simulation_contract` and `suitability_tier` to every run and study artifact.

Acceptance criteria:

- Existing bad Optuna config fails the new parity test.
- Generated contract config passes.

### Phase 1 — Actual config import and adjustment enforcement

**Goal:** make the lab’s baseline config truly reflect actual Bowaka v2.

Tasks:

1. Update `import-actual-config` mapper to include `require_adjusted_daily_bars` and `require_split_adjustment`.
2. Generate separate IEX and SIP configs:
   - `bowaka_v2_actual_iex_current_code.yml`;
   - `bowaka_v2_actual_iex_intended_realism.yml`;
   - `bowaka_v2_actual_sip_intended_realism.yml`.
3. Decide explicitly whether SIP config uses frozen actual IEX-relaxed thresholds or SIP-intended tightened thresholds; label variants.
4. Update data-quality gate to fail generated actual config on raw daily bars.

Acceptance criteria:

- Raw daily lake fails intended-realism actual config.
- IEX current-code config is explicitly capped as research-only.

### Phase 2 — Real IEX replay subset and data-quality hardening

**Goal:** validate with real data, not synthetic, while keeping CI tractable.

Tasks:

1. Add a small real IEX parquet fixture subset with daily/minute bars.
2. Add quote partitions if available.
3. Add split/corporate-action case.
4. Add full-session minute coverage audit.
5. Add exit-path coverage audit.
6. Add timestamp ordering/duplicate/gap checks.
7. Add manifest/content hash.

Acceptance criteria:

- CI replays real IEX subset deterministically.
- No synthetic data is used for inference tests.

### Phase 3 — Event-driven simulator rewrite

**Goal:** fix temporal causality.

Tasks:

1. Introduce event queue or chronological replay loop.
2. Process exits/fills/protection before each scan.
3. Update portfolio state after each event.
4. Support 5-second strategy/protection polling separately from 60-second scanning.
5. Persist event-level state snapshots.

Acceptance criteria:

- Intraday stop/loss/kill-switch tests pass.
- Current session no longer defers all exits until after all scans.

### Phase 4 — Execution/quote/fill realism

**Goal:** eliminate zero-spread/synthetic execution from research-grade runs.

Tasks:

1. Ingest historical IEX quotes.
2. Fix quote timestamp mapping.
3. Implement price-chase gate.
4. Implement halt/status gate or explicit unavailability blocker.
5. Replace marketable-limit future-high model with quote/size/latency model.
6. Add partial-fill and no-fill lifecycle.
7. Calibrate stress levels from paper fills when available.

Acceptance criteria:

- Intended-realism backtest fails if quotes are absent.
- Execution-quality report includes fill/slippage/spread/quote-age distributions.

### Phase 5 — OCO/protected-position lifecycle

**Goal:** simulate live risk of unprotected positions.

Tasks:

1. Add parent order and child order state machines.
2. Simulate OCO attach attempts after parent fill.
3. Enforce max unprotected seconds.
4. Implement fallback stop and flatten behavior.
5. Block entries on protection violations.
6. Add protection metrics to reports.

Acceptance criteria:

- OCO failure scenarios are tested and visible in artifacts.
- Protection violations penalize Optuna objective.

### Phase 6 — Exit semantics and signal fade

**Goal:** make exits match actual/intended policy.

Tasks:

1. Fix `telemetry_then_active_after_validation` semantics.
2. Ensure time-stop/fade events occur at correct intraday times.
3. Recompute fade signal causally from bars available at eval time only.
4. Test gap-through, same-minute stop/target ambiguity, halt-then-exit, max-hold.

Acceptance criteria:

- Default actual config logs fade telemetry only until activation is explicit.
- Minute-path exit tests cover stop/target/time/fade/halt cases.

### Phase 7 — Optuna rebuild

**Goal:** run optimization only on validated simulator/data.

Tasks:

1. Replace `bowaka_v2_walkforward_optuna.yml` with validated config(s).
2. Require intended-realism + quotes + adjusted baselines for parameter recommendations.
3. Use content-addressed dataset hashes.
4. Fix holdout to use full report metrics.
5. Add objective unit tests and term breakdown.
6. Add fold-level data-quality preflight.
7. Add incumbent baseline and random-search baseline.

Acceptance criteria:

- Study cannot start if any fold lacks required data/quote coverage.
- Best trial is compared to actual-config baseline and must pass stability criteria.

### Phase 8 — Paper-vs-sim reconciliation

**Goal:** calibrate simulator to actual paper behavior.

Tasks:

1. Ingest Bowaka v2 paper logs: candidates, decisions, submitted orders, fills, OCO events, exits.
2. Replay same days/symbols with simulator.
3. Compare candidate emissions, accept/reject reasons, fill prices, fill latency, exits, PnL.
4. Calibrate execution and protection models.
5. Define tolerances.

Acceptance criteria:

- Candidate replay match rate above agreed threshold.
- Fill slippage distribution within tolerance.
- Exit reason/timing match within tolerance.
- Discrepancies are categorized and tracked.

### Phase 9 — SIP migration and promotion gate

**Goal:** move from IEX plumbing to consolidated-tape validation.

Tasks:

1. Ingest SIP bars and SIP/NBBO quotes.
2. Build SIP adjusted daily baselines.
3. Run IEX-vs-SIP feature divergence report.
4. Re-run walk-forward optimization on SIP only.
5. Run final holdout once.
6. Run paper-vs-sim reconciliation on SIP/paper setup.
7. Only then consider paper candidate status.

Acceptance criteria:

- SIP data coverage and quote coverage pass.
- SIP backtests beat actual-config baseline robustly out of sample.
- Paper reconciliation passes.
- Human operator approves promotion.

---

## 12. Concrete next actions for engineering

### Immediate actions

1. **Stop using `configs/bowaka_v2_walkforward_optuna.yml` for strategy optimization.** Mark it experimental or delete.
2. **Generate an actual IEX parity config from the frozen contract.** It should match actual config except for explicitly labeled simulation-mode fields.
3. **Add `require_adjusted_daily_bars` and split-adjustment flags to generated configs.**
4. **Add real IEX bar fixture payloads to CI.** The attached sample has no bars.
5. **Add quote ingestion or fail intended realism.** No quote partitions means no realistic execution.
6. **Build the event-driven simulation loop.** This is the largest and highest-value fix.
7. **Patch signal fade semantics.** Default should not become active until validation activation is explicit.
8. **Patch synthetic quote RNG.** Use stable hash and pass `rng` to `resolve_quote()`.
9. **Patch quote timestamp mapping.** Use actual quote row timestamp.
10. **Run full non-live tests in segmented CI with timeouts.**

### Suggested commands/checks

```bash
# Unit + parity
PYTHONPATH=src:../bowaka_common/src \
python -m pytest tests/unit tests/parity -q --tb=short \
  -m "not live_alpaca and not slow and not live_paper"

# Targeted integration
PYTHONPATH=src:../bowaka_common/src \
python -m pytest tests/integration/test_import_actual_config_roundtrip.py \
                 tests/integration/test_full_scan_replay.py \
                 tests/integration/test_backtest_runner.py \
                 -q --tb=short \
                 -m "not live_alpaca and not slow and not live_paper"

# Full integration with timeout in CI, not ad hoc shell sessions
PYTHONPATH=src:../bowaka_common/src \
python -m pytest tests/integration tests/reconcile \
  --timeout=60 --timeout-method=thread \
  -q --tb=short -m "not live_alpaca and not slow and not live_paper"

# Data lake sanity
find research_notebooks/market_data/bars -name '*.parquet' | head
find research_notebooks/market_data/quotes -name '*.parquet' | head
python -m bowaka_v2_lab.cli env-check --config configs/<actual-generated-config>.yml
```

---

## 13. Acceptance criteria before any serious Bowaka v2 optimization

A Bowaka v2 optimization run is acceptable only when all of the following are true:

### Data

- Real IEX or SIP bar payloads are present; not synthetic.
- Daily baselines are split/corporate-action adjusted as required by actual strategy.
- Minute bars cover every scan and exit path.
- Real historical quotes cover candidate timestamps above threshold.
- Asset master is point-in-time or clearly frozen with date limitations.
- Dataset hash is content-addressed.

### Simulator

- Event loop interleaves scans, fills, exits, risk, and MTM.
- Quote, spread, age, price-chase, halt/status gates are modeled.
- Fill model handles immediate execution, partial fills, no fills, latency, and costs.
- OCO/protection lifecycle is modeled.
- Signal fade default semantics are correct.
- Reports expose all assumptions and coverage gaps.

### Tests

- Unit/parity tests pass.
- Full integration/reconcile tests pass deterministically in CI.
- Real IEX subset replay passes.
- Temporal causality tests pass.
- Data-quality failure tests pass.
- Objective/unit-scale tests pass.

### Optimization

- Config is actual contract or explicit sidecar variant.
- Walk-forward folds pass full data preflight.
- Final holdout is untouched until final evaluation.
- Objective term breakdown is stored.
- Best result is stable across folds/regimes and beats actual baseline after costs.
- IEX results are capped as research-only and feed-specific.

### Promotion

- IEX: research-only/plumbing only, no live/paper promotion claim.
- SIP: backtesting-only until paper-vs-sim reconciliation passes.
- Paper candidate: requires SIP data, successful walk-forward/holdout, realistic execution, and paper reconciliation.
- Live candidate: requires separate operator risk review, capital/risk controls, live dry run, kill-switch validation, and human approval.

---

## 14. Final conclusion

`bowaka_v2_lab` is a strong foundation but not yet a realistic enough simulator for Bowaka v2 parameter recommendations. The codebase already contains many of the right ideas: frozen contract, simulation modes, data-quality gates, artifact lineage, walk-forward Optuna scaffolding, and extensive tests. The main problem is that the current system can still run or optimize the wrong thing: wrong config, no quotes, raw daily baselines, delayed exits, simplified fills, simplified OCO protection, and incomplete full-suite validation.

The safest path is not to discard the lab, but to harden it in the phases above. The highest-priority engineering tasks are:

1. fix config parity and generated actual configs;
2. enforce adjusted daily baselines;
3. add real IEX bar/quote fixtures;
4. rebuild the simulator as an event-driven intraday replay;
5. implement quote/fill/OCO/protection realism;
6. only then run Bayesian optimization under strict walk-forward/holdout discipline.

Until those are complete, the lab should be treated as **research-only simulator infrastructure under development**, not a production-grade Bowaka v2 optimizer.

---

## Appendix A — Key file references

### Actual Bowaka v2

| File | Key lines / content |
|---|---|
| `bowaka_backup_v2/scripts/bowaka_v2_config.yaml` | IEX warning lines 12-21; data/feed lines 43-57; session lines 58-64; universe lines 66-87; scanner lines 99-115; signal gates lines 117-139; execution lines 149-170; sizing lines 172-179; risk lines 181-224; exits/protection lines 226-254. |
| `bowaka_backup_v2/scripts/bowaka_v2_strategy.py` | Startup gate lines 96-120; quote/price/halt gates lines 372-430; risk lines 436-492; sizing lines 529-545; zero-spread fallback lines 743-748; accepted-before-submit lines 791-846; pending position lines 848-880 and 944-993; OCO/fill polling lines 1019-1239. |
| `bowaka_backup_v2/scripts/bowaka_intraday_scanner.py` | Scanner pure function lines 330-546; rank/cap lines 517-523. |
| `bowaka_backup_v2/scripts/bowaka_v2_features.py` | Forming bar aggregation lines 145-204; ET minute conversion lines 273-284; instrument gate fail-open lines 473-477. |

### Bowaka v2 lab

| File | Key lines / content |
|---|---|
| `bowaka_v2_lab/README.md` | Research-only warning lines 1-15; market-data lake description lines 63-74. |
| `bowaka_v2_lab/reference/actual_bowaka_v2_contract.yaml` | Frozen contract lines 1-187. |
| `bowaka_v2_lab/configs/bowaka_v2_intended_realism.yml` | Generated config; market data lines 50-58; scanner lines 99-102; signals lines 111-128; simulation/sizing/universe lines 129-147. |
| `bowaka_v2_lab/configs/bowaka_v2_walkforward_optuna.yml` | Claims current-code parity lines 1-17 but changes strategy values lines 19-91. |
| `bowaka_v2_lab/src/bowaka_v2_lab/config/models.py` | Simulation mode defaults lines 29-48; market-data config default adjustment false lines 103-118. |
| `bowaka_v2_lab/src/bowaka_v2_lab/sim/backtester.py` | Data-quality gate lines 352-393; config diff gate lines 395-411; scan loop lines 487-550; exits after scan loop lines 552-590. |
| `bowaka_v2_lab/src/bowaka_v2_lab/sim/strategy_consumer.py` | Sizing lines 62-88; quote resolution/RNG issue lines 160-182; spread/age gates lines 195-215; event sequencing lines 338-403; fill/position creation lines 404-529. |
| `bowaka_v2_lab/src/bowaka_v2_lab/sim/fills.py` | Marketable-limit fill model lines 165-259. |
| `bowaka_v2_lab/src/bowaka_v2_lab/sim/exits.py` | Signal fade activation lines 336-342; fade exit behavior lines 446-485. |
| `bowaka_v2_lab/src/bowaka_v2_lab/data/data_quality.py` | Required checks lines 55-70; coverage first-scan probe lines 207-296; adjustment check lines 302-325; quote checks lines 331-436; startup DQ only intended realism lines 511-520. |
| `bowaka_v2_lab/src/bowaka_v2_lab/data/suppliers.py` | Current no-quotes note and quote supplier lines 168-205. |
| `bowaka_v2_lab/src/bowaka_v2_lab/optuna/walkforward_runner.py` | Fold backtest lines 171-252; limited preflight lines 583-628; dataset hash lines 657-659. |
| `bowaka_v2_lab/src/bowaka_v2_lab/optuna/holdout.py` | Holdout summary-only scoring lines 103-126. |
| `bowaka_v2_lab/src/bowaka_v2_lab/optuna/dispatcher.py` | PostgreSQL/SQLite study storage note lines 1-8; IEX promotion block lines 57-67. |

---

## Appendix B — External reference notes

- Alpaca Market Data FAQ: IEX vs SIP feed behavior and example volume/trade-count differences.
- Alpaca Historical Stock Data documentation: IEX is a single-exchange feed useful for testing; SIP covers all U.S. exchanges.
- NYSE CTA/UTP public materials: SIP consolidates protected quotes/trades and disseminates NBBO/LULD-related information.
- Alpaca snapshot API documentation: snapshots include latest trade, latest quote, minute bar, daily bar, and previous daily bar with feed selection.
