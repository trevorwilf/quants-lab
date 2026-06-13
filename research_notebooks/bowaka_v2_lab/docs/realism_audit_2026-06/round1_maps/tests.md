I have everything needed. Here is the final report.

---

## Purpose & data flow (how this subsystem fits the backtest pipeline)

The `tests/` tree is the regression/realism gate for the entire v2 lab. 538 test files in five categories feed the lab's CI and the operator's `make test-all`. Conftest auto-discovers repo-root `.env` (walks up for `Makefile`+`docker-compose-db.yml`), registers `--lake-source {committed|lake|auto}`, and exposes the `iex_subset`/`lab_root`/`repo_root` fixtures. The harness (pyproject: `timeout=60` thread-method, `--strict-markers`, JUnit XML) deselects `slow` tests by default (`-m "not slow"`). Tests exercise: pure-logic oracles (fills/exits/tape/compounding/metrics), full `run_backtest` runs (74 files import it) over fixture lakes, papermill notebook smokes, parity goldens (lab-vs-lab and lab-vs-archive), DQ gating, scan-matrix build+verify, and paper-vs-backtest reconciliation. The decisive realism question — does the lab's fill/return model match the live strategy on real data — is gated almost entirely behind real-lake/env flags that do not run on CI or this machine.

## Behavioral spec (precise bullets; exact file:line refs)

- conftest auto-loads `.env` via `python-dotenv` or a hand parser fallback; `load_dotenv(..., override=False)` and `setdefault` so existing env wins — conftest.py:23-37.
- `--lake-source` default is `auto` (committed→fresh-lake→synthetic) — conftest.py:51-57; `iex_subset` fixture pulls a fresh subset into `tmp_path` only for `lake` — conftest.py:66-75.
- Tape fill oracle: hand-computed VWAP, time-order partial consumption, window exclusion, stop/target trigger price-band, participation cap, empty→no-fill — test_tape_fill.py:23-105.
- Tape-replay routing is dispatch-only (explicitly "NOT a fidelity claim"); legacy model must never touch the tape (boom-supplier raises) — test_tape_replay_routing.py:1-16,122-127. Target fills AT the limit not through-VWAP (PC.3 clamp) — :83-92.
- Tape-consuming runs cap at `research_only`; legacy control with identical evidence reaches `backtesting_only` — test_tape_replay_pb6.py:46-55.
- fast_realism golden: participation-capped partial fill (80 of 800) vs CCP "manufactures liquidity" full 577 fill — test_fast_realism_fill.py:58-65; DQ gate is adjustment-only not coverage for fast_realism — :86-102.
- Golden-bundle diff round-trips and catches price/missing-trade/exit-reason/gate drift; `PRICE_TOL=1e-12` — test_golden_bundle.py:46-112.
- `fill_price_mae_bps` averaging + threshold (15bps>5bps→FAIL), largest-diff sorting — test_metrics_fill_price_mae.py:20-47.
- Archive parity compares ported `build_candidate_event` against the live archive's, field-by-field modulo §8.3 added gate keys — test_scanner_parity_with_archive.py:91-130.
- Walk-forward split math: train_end==val_start back-to-back, val never overlaps holdout, final_holdout=0 raises — test_walkforward_splits.py:11-39.
- HoldoutGuard raises on any tuning-phase read into the holdout window; only `enter_final_eval()` permits it — test_holdout_guard_blocks_tuning.py:11-29.
- StartupDQ failure raises `StartupDataQualityError` (a `DataQualityError` subclass) so the runner's structural handler propagates instead of degrading the fold — test_startup_dq_raises_structural.py:1-9,119,174-176.
- Coverage-missing ≥1% fails `intended_realism` closed, empty universe→fail, smoke records-but-doesn't-gate — test_coverage_missing_fails_realism.py:148-204.
- Compounding sizing: bankroll grows with gross realized PnL, clamped `[0, cap*base]`, floor-halt at/below `floor_fraction*base`, disabled==legacy — test_compounding_sizing.py:30-89.
- Scan-matrix: content-addressed `dataset_hash`, verify catches manifest mutation + cell-level invariants, strict raises — test_scan_matrix_dataset_hash_content_addressed.py / test_verify_scan_matrix_catches_drift.py.
- Determinism: same cfg+seed → identical `run_id` and aggregate metrics — test_backtester_determinism.py:66-79.

## Synthetic vs real-data census (estimated counts per category)

The operator's distrust of synthetic validation is well-founded here: real-tape/real-lake fidelity tests are a tiny, almost-always-skipped minority.

- **unit (299):** ~99% synthetic or pure-math. Sim oracles (19 files in unit/sim), parity metrics, compounding, walk-forward, holdout, suitability, reports, DQ-logic all use hand-built frames or constant-OHLCV fixtures. 0 unit tests touch the real lake except 3 optuna preflight files that probe `resolve_market_data_root` and skip if absent.
- **integration (175):** ~95% synthetic-fixture-lake (`make_minute_bars`/`make_daily_bars`, `adjustment_lake.build_lake` at flat `close=10.0`, `iex_short_run_lake`, reconcile tiny-lakes). ~6-8 real-lake-gated files (`test_parity_runner_against_real_lake`, `test_verify_bayesian_fix_section_7…`, `test_prod_backtester_*`, `test_session_window_supplier_walkforward_parity`) all skip without the lake; section7 additionally needs `BOWAKA_RUN_REAL_LAKE_SECTION7=1`.
- **parity (55):** Mixed. The metrics/golden/normalizer oracles use synthetic `NormalizedTrade`s. Config-parity (signals/adv-tiers) reads the frozen contract and **xfails** when the contract isn't mirrored (test_config_parity_signals.py:23-25). The lab-vs-archive event parity needs `BOWAKA_V2_SOURCE_ROOT`.
- **reconcile (8):** 100% synthetic — `conftest._build_tiny_lake` + frozen `paper_logs_synthetic/`. Only proves the comparator math and "never fabricate" guard, not real paper-vs-sim agreement.
- **scanner (1):** the single most valuable real-data test (byte-parity of the two minute suppliers) — and it `pytest.skip(allow_module_level=True)` when the AAL lake probe is missing (test_session_minute_window_supplier_parity.py:46-51). On CI/this machine it contributes **zero** assertions.

Net: ~510/538 synthetic-or-pure-math; ~15-20 real-lake tests, nearly all skip-guarded; effectively **0 fill/return-fidelity-on-real-data assertions execute** in a default run. Fixture builders that claim "real IEX-shaped" are synthetic (`iex_short_run_lake.py:1-8` constant `close=10.0`; `adjustment_lake.py:1-8` flat OHLCV).

## Invariants & guards (fail-loud vs silent-fallback — every silent fallback flagged)

- Fail-loud: normalizer raises on missing/NaT entry timestamp (test_phase0_oracle_fixes.py:49-61); candidate metrics report `None` not false `1.0` (:84-99); StartupDQ subclass propagation; HoldoutGuard; matrix verify strict raises; synthetic universe refused in realism (test_synthetic_universe_refused_in_realism.py:30-55); importer never fabricates (test_reconcile_fails…:57-71).
- **SILENT FALLBACK — IEX subset loader synthetic path:** `load_iex_subset(auto)` falls through to a labelled-but-test-invisible `_synthetic_subset()` when no committed subset and no lake (loader.py:179-196). Tests must voluntarily check `synthetic_fallback`; **0 tests use `@pytest.mark.synthetic_fallback`**, so a synthetic fallback is silently accepted.
- **SILENT FALLBACK — `build_iex_subset.main()`** swallows any real-lake pull exception and writes synthetic, returning rc 0 (build_iex_subset.py:379-387). A broken lake yields a green "subset built."
- **SILENT SKIP (masks failure on this machine):** module-level skips in test_session_minute_window_supplier_parity.py:46-51 and 14 other real-lake files; `BOWAKA_V2_SOURCE_ROOT`/`BOWAKA_RUN_*`/`MARKET_DATA_ROOT` env gating (11 files) means the decisive parity tests are no-ops by default.
- **MASKING xfail:** config-parity xfails when the contract isn't generated (test_config_parity_signals.py:23-25) — a missing mirror reads as xfail, not fail.
- **VACUOUS-PASS guards:** test_backtester_with_synthetic_quotes.py:66 (`if len(decisions) and "quote.source" in columns`) — passes with zero accepted entries; test_prod_backtester_reads_fixture_lake.py:68-77 (`if trades:`…`if wins+losses>5:`) — passes vacuously on the flat-price fixture that produces no trades.

## Leads (suspected bugs / realism gaps / dead code / smells — flag only)

- test_session_minute_window_supplier_parity.py:46-51 — the only real-lake byte-parity test skips at module level on CI; the realism guard it advertises does not run.
- test_prod_backtester_reads_fixture_lake.py:68-77 — "must look different from synthetic" assertion is triple-guarded; flat `close=10.0` fixture (adjustment_lake) likely yields 0 trades → vacuous pass; doesn't actually prove the real strategy diverges from synthetic.
- iex_short_run_lake.py:1-8 & adjustment_lake.py:1-8 — docstrings say "small but real IEX-shaped lake" but data is fully synthetic flat OHLCV; misleading; any test trusting these as "real" is validating against synthetic.
- build_iex_subset.py:379-387 + loader.py:179-196 — synthetic fallback paths return success silently; a CI green can hide an unreachable lake; no test asserts the committed subset is non-synthetic (`synthetic_fallback==False`).
- test_backtester_with_synthetic_quotes.py:66 — soft `if` makes the synthetic-quote-source assertion skippable; can't fail when no entries occur.
- test_config_parity_signals.py:23-25 — `pytest.xfail` on missing contract converts a real drift-detection gap into a non-failure.
- test_notebooks_execute.py:52 / test_papermill_execute_notebook_10:35 / test_notebook_10_iex_short_run.py — only assert `out.is_file()` / returncode==0; no output-value assertions → pure smoke, won't catch silent numerical regressions in notebooks.
- test_optuna_dispatcher_short_run.py:18-26 — objective is a closed-form synthetic function, not the real backtest; tests only Optuna plumbing; the file's docstring "5-trial run on a synthetic fixture" overstates coverage.
- test_verify_scan_matrix_catches_drift.py:95-110 (`test_verifier_catches_static_float_column_corruption`) — asserts only "doesn't crash" / status key present; the comment admits static-column corruption is undetectable → tautological/smoke, gives false confidence the verifier catches prior_close tampering.
- test_scan_matrix_dataset_hash…:100-125 — the byte-flip drift test has an `if "dataset_hash_drift" not in kinds` branch that downgrades to "hash unchanged is fine," so on synthetic lakes a real corruption can pass.
- test_tape_replay_routing.py:1-16 — explicitly disclaims fidelity ("Fidelity vs the REAL tape is validated separately PB.5/PC.3"); PB.5 fidelity test against the real tape is not present in this tree (no `tape` test reads the lake) → the tape fill model has **no real-data fidelity test that runs**.
- 74 files import `run_backtest` but every one feeds synthetic suppliers/lakes; no executed test compares lab `run_backtest` trade prices/PnL to the live strategy on real bars (the real-lake parity runner skips).
- conftest.py:13 — repo-root discovery requires both `Makefile` and `docker-compose-db.yml`; if either is absent `.env` silently isn't loaded, and lake-dependent tests then skip rather than fail (compounding the masking).
- reconcile/conftest.py:1-7 + all 8 reconcile tests — 100% synthetic paper logs; "paper-vs-backtest reconciliation" never validated against a real paper session in CI.
- pyproject timeout=60 thread-method — `slow`/real tests need explicit overrides; any un-marked genuinely-slow real test silently times-out→errors rather than running (potential flaky-mask).

## Test coverage hooks (which files exercise what; untested surfaces)

- Fills/exits: unit/sim/* (19 files) — tape, fast_realism, adv-bucket cap, stress (spread/slippage/adverse/late-day), partial, cost-model. Strong oracle coverage on synthetic inputs.
- Parity goldens: unit/parity/* + parity/* + integration/test_scanner_parity_with_archive (archive, env-gated).
- Walk-forward/holdout: unit/test_walkforward_splits, test_holdout_guard_blocks_tuning, unit/optuna/* (59 files).
- DQ/coverage: unit/data/* (11), test_coverage_missing_fails_realism, test_startup_dq_raises_structural.
- Tape replay: unit/sim/test_tape_fill, _tape_replay_pb6, _tape_replay_routing — routing only; **no real-tape fidelity test runs**.
- Compounding: unit/sim/test_compounding_sizing (pure-math, claims prod parity).
- Scan matrix: unit/scanner/* (26) + parity/test_scan_matrix_*.
- **UNTESTED surfaces (no executing test):** (1) lab `run_backtest` fill price/PnL vs live strategy on real bars; (2) tape-replay fill fidelity vs real trade tape (PB.5 absent); (3) minute-supplier byte-parity on real lake (skips); (4) real paper-vs-sim reconciliation; (5) any assertion that the committed IEX subset is real-not-synthetic; (6) notebook numerical outputs (only file-exists smokes).