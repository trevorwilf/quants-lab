# intended_realism minute-bar coverage preflight — expert findings

**Date:** 2026-06-07
**Subsystem:** `bowaka_v2_lab` walk-forward preflight (replay-level data-quality gates)
**Config under test:** `$2M`-floor `intended_realism` SIP walk-forward (`/tmp/ir2m.yml`, `universe.max_price=20`, `min_adv_dollars=2000000`)
**Lake:** Alpaca SIP minute bars (`adjustment=raw`) + SIP NBBO quotes + SIP daily (`adjustment=split_adjusted`), Aug-2025..Jun-2026, native FS at `/opt/market_data_cache`
**Status:** Diagnosis complete **for the probed window**. The headline failure is dominated by over-inclusive-PIT-universe symbols, not a realism deficiency. Restricted to the actually-tradeable universe the minute-coverage replay gates fall well inside threshold on the 5 probed sessions (late-session 2.16%, exit-path 0.39%, both < 5%; the combined tradeable rate is 3.42%). **This is established only on the lake's first 5 sessions (2025-08-27..09-03); it is NOT yet confirmed on an interior fold** (see §10 to-do #1). The recommended fix touches an intentional P0 design decision (the uncapped PIT-union preflight, audit 2026-05-23 §6.6) and must be reconciled with it (§6.1) before it can be acted on; a secondary `coverage_missing` probe-construction issue (§7.2) is also open.

---

## 1. Executive summary

The `$2M`-floor `intended_realism` walk-forward preflight fails four replay-coverage checks, headlined by `coverage_missing_late_session` at **35.65%** missing minute bars (34,584 / 97,000 probes) against a 5% fail threshold. The question is whether this is a genuine gap in the lake's faithful minute-by-minute replay, or an artifact of *which symbols* the preflight probes. We instrumented the real preflight (143,075 minute-bar probes, 52,622 misses = 36.78% overall) and staged a per-(symbol, session) dataset, then re-derived eligibility against the actual PIT universe builder and spot-checked the lake. **The decisive number on the probed window: restricting probes to the genuinely-tradeable universe (PIT-eligible on a `$2M`/`$1-$20` basis AND having a minute month-file) gives miss = 2,304 / 67,464 = 3.42% — inside the 5% gate, with a 1,069-probe (1.6 pp) headroom on these 5 sessions.** The 35.65% headline is dominated by symbols the strategy could never trade on the probed dates: out-of-band price (>$20 or <$1), below-`$2M` ADV, and not-yet-listed names. **94.66% of all misses (49,813 / 52,622) come from `daily_eligible==0` symbols.**

Two material caveats temper the verdict, both surfaced by adversarial review and **not yet closed** (§6.1, §10): (a) the recommended fix (filter the coverage probe to the per-session PIT-eligible set, §6) narrows the symbol set the preflight scores, which is in tension with the **intentional** audit-2026-05-23 §6.6 P0 decision to probe the *full, uncapped* PIT-union precisely to stop coverage under-reporting — this tension must be reconciled before Option A is adopted (§6.1); and (b) the 3.42% is measured on the lake's **first 5 sessions only**, where the ingestion-boundary residual (§7.2) is over-represented, and is **not yet verified on an interior fold**. The genuine residual on the probed window (§7) is thin-stock no-trade microstructure plus a lake-start ingestion boundary; on this window it sits inside the gate, but lake-wide generalization is an open question, not a settled result.

---

## 2. Background & the realism contract

`bowaka_v2_lab` supports two simulation fidelities:

- **`current_code_parity`** — reproduces the live scanner/executor code path bug-for-bug (including its documented warts, e.g. the halt gate failing open). A finalist already exists under this mode.
- **`intended_realism`** — the stricter contract: a *faithful minute-by-minute replay*. Every scan timestamp the live scanner would evaluate must be backed by real minute bars; every entry candidate must have forward minute data through its max-hold exit; quotes must be present within the max-age window; halts must be modelable (or the gate explicitly disabled). It **fails closed**: absent data that *should* exist is a hard failure, not a warning.

The strategy trades a US-equity intraday scanner universe. Point-in-time (PIT) eligibility per session: prior-session close in **\$1–\$20**, trailing-20-session prior ADV (mean of `close × volume`) **≥ \$2,000,000** (raised from the legacy \$250k floor), operating-equity instrument class, not delisted, not blocklisted. The lake holds SIP minute bars + SIP NBBO quotes for Aug-2025..Jun-2026 and SIP split-adjusted daily bars (the only daily partition present; the raw-daily union is empty).

Going in, two checks were already resolved: `quote_coverage` passes (the SIP quote backfill landed prevailing-NBBO-per-minute coverage), and `halt_data_unavailable_when_required` was cleared by a parity sidecar declaring `execution.halt_gate.enabled=false` (so halts need not be modeled). The four remaining failures are all minute-bar coverage checks.

---

## 3. The exact check mechanism

Replay-level coverage is built in `research_notebooks/bowaka_v2_lab/src/bowaka_v2_lab/data/dq_levels.py::build_replay_checks` (lines 346–488) and the first-scan coverage check in `…/data/data_quality.py::build_coverage_check`. The minute-bar supplier is `…/data/suppliers.py::make_lake_suppliers` (lines 121–166).

**Probe window.** `minute_bars_supplier(sym, cutoff)` returns `store.minute_bars(sym, intraday_window_start(cutoff, policy), cutoff)` (`suppliers.py:152–157`). The default policy `scanner_start_to_scan` sets the window start to **09:45 ET** (`suppliers.py:37–44, 47–71`), matching the live scanner. So each probe asks: *does the lake have minute bars in `[09:45 ET, scan_ts]`?*

**Thresholds.** `REPLAY_COVERAGE_FAIL_FRACTION = 0.05` (`dq_levels.py:72`) gates `coverage_missing_late_session` and `coverage_missing_exit_path`; `_coverage_check` (`dq_levels.py:429–457`) fails when `missing/probes ≥ 0.05`. `build_coverage_check` (`data_quality.py:391`) gates `coverage_missing` at `COVERAGE_MISSING_FAIL_FRACTION = 0.01` (1%). `audit_missing_sessions` is a hard gate at threshold 0 (any missing session fails) and is sourced from the pre-computed lake audit parquet, not the minute supplier.

**`coverage_missing` is a daily-OR-minute union (provenance note).** `build_coverage_check` records a pair as missing if it lacks a daily bar **or** a minute bar at the first scan: `missing_pairs = set(missing_daily) | set(missing_minute)` (`data_quality.py:442`). Our 6,619/12,125 figure below is the **minute-only** 09:45 first-scan miss; the daily leg (`missing_daily`) is a separate contributor we did not isolate from the CSV. The true `coverage_missing` numerator is therefore **≥ 6,619** (minute ∪ daily), and any fix to `coverage_missing` (§7.2, §10) must address the daily-coverage leg as well as the minute-window construction. We label the 6,619 a *minute-leg lower bound*, not the full `coverage_missing` count.

**`coverage_missing_exit_path` numerator is deduplicated; the denominator is not (disclosure).** `_coverage_check` reports `n_missing = len(set(missing))` where each miss string is `f"{sym}@{fwd.isoformat()}"` — symbol + forward-session date, **no timestamp** (`dq_levels.py:427, 430`). In the raw log the exit-path family has **7,332 total miss-rows but only 3,264 unique `sym@date` strings**. The check's published rate (and ours, below) is therefore `3,264 unique / 21,825 total probes` — a deduplicated numerator over a non-deduplicated denominator. This is the check's own (debatable) arithmetic; we inherit it but flag it as apples-to-oranges. The same caveat applies to the tradeable "40 unique / 10,325 total."

**8-scan sampling.** `LATE_SESSION_PROBE_CAP_PER_SESSION = 8` (`dq_levels.py:80`). The check does not visit all ~350 60-second scans; it samples 8 evenly-spaced post-first scan timestamps per session (`dq_levels.py:384–394`), plus the first-scan probe (counted by `coverage_missing`) and a forward exit-path probe per `max_hold_days` session (`dq_levels.py:406–427`). This bounds an O(scans × symbols × sessions) walk while still detecting *systemic* missing minutes.

**The four minute-probe families (full census of the 143,075 probes).** ET-time-of-day bucketing of `_probe_log_2m.jsonl` (UTC−4 = EDT for these dates) resolves the raw log into exactly four probe families, three of which map to the failing checks and one of which (16:00 ET) we had previously left unaccounted:

| ET time | Probes | Miss | Check it feeds |
|---|---:|---:|---|
| 09:45 (first scan) | 12,125 | 6,619 | `coverage_missing` (minute leg) |
| 09:46, 10:29, 11:12, 11:55, 12:38, 13:21, 14:04, 14:47 (8 sampled post-first) | 97,000 | 34,584 | `coverage_missing_late_session` |
| 15:30 (last-scan-of-forward-session) | 21,825 | 7,332 rows | `coverage_missing_exit_path` |
| **16:00** (session-close fallback) | **12,125** | **4,087** | **Level-2 `session_minute_count_violation` / `intraday_gap`** (NOT a `coverage_*` check) |

The 16:00 ET family is **not** part of any `coverage_*` check. It is the Level-2 session-check fallback in `data_quality.py:1142–1146`: when `session_minute_supplier` is `None`, `_build_multi_level_checks` probes `minute_bars_supplier(sym, session+16h)` to obtain a per-(symbol, session) minute frame for the session-level checks (`session_minute_count_violation`, `intraday_gap`, `session_stale_segment`). Its 4,087 misses (49 on the tradeable set) feed those session-level gates, not late-session coverage — so 12,125 + 97,000 + 21,825 + 12,125 = **143,075** is the complete probe census and the late-session denominator is **97,000** (the 16:00 family does NOT inflate it). The session-level checks did not appear in the four-failing-checks list, consistent with their permissive fail-fractions (`SESSION_MINUTE_COUNT_FAIL_FRACTION = 0.80`, `INTRADAY_GAP_FAIL_FRACTION = 0.50`).

**Symbol set (the load-bearing input).** Both replay checks iterate `requested_symbols` (`dq_levels.py:372, 396`). `_probe_fold` (`preflight.py:570`) receives this `symbols` list from its caller and **does not re-filter PIT eligibility per session before probing** — it probes the full set on every session of every fold. This is **by design** under `intended_realism`: see §6.1 for the audit-2026-05-23 §6.6 P0 rationale (the uncapped PIT-union is the deliberate anti-under-reporting mechanism), which the over-inclusion framing below must be reconciled with.

---

## 4. Method: how we instrumented the real preflight

We did not synthesize the probe set — we captured the *real* one. `scripts/_tmp_instrument_preflight.py` monkeypatches `bowaka_v2_lab.data.suppliers.make_lake_suppliers` to wrap `minute_bars_supplier`, logging `{sym, ts, n}` (bar count) for every probe, then runs the actual `$2M` `intended_realism` preflight via the CLI (`cli optuna --config /tmp/ir2m.yml --incumbent-trial`). The preflight aborts at the coverage gate — which is exactly the probe set we want.

This produced **`scripts/_probe_log_2m.jsonl`** (host `E:\…\scripts\_probe_log_2m.jsonl`; container `/quants-lab/scripts/_probe_log_2m.jsonl`): **143,075 probes / 52,622 misses (36.78%) over 2,425 symbols**.

`scripts/_extract_pair_dataset.py` joins the probe log against the lake (minute month-files, split-adjusted daily, quote month-files) and reconstructs PIT eligibility, staging a clean per-(symbol, session) CSV at **`scripts/_pair_dataset.csv`** (12,125 rows; **2,424** distinct symbols; 5 sessions 2025-08-27..2025-09-03 — the lake's earliest, which is the first validation window the preflight probes). Downstream analysis reads only this CSV (`C:/Python312/python.exe` + pandas) plus targeted lake spot-checks.

**Symbol-count reconciliation (2,425 vs 2,424) — resolved.** The raw probe log `_probe_log_2m.jsonl` carries **2,425** distinct symbols; the staged CSV has **12,125 rows = 2,425 symbols × 5 sessions**, but `df.symbol.nunique()` returns **2,424** because **one symbol's ticker is `NaN` in the CSV** (5 rows, one per session — verified: `df.symbol.isna().sum() == 5`, and `df.symbol.nunique(dropna=False) == 2,425`). The null ticker is a probe-log symbol whose name parsed to null in the CSV staging (most likely a literal `"NA"`/`"NaN"`/`"NULL"` ticker coerced to `NaN` by pandas' default NA-parsing). Its 5 rows carry only 10–13 probes/session with 0–2 misses each — a low-probe `no_minute_file`-class name, **not** a tradeable symbol: it has no minute month-file and would be excluded from the tradeable restriction regardless, so it has **zero** effect on the 3.42% (which conditions on `has_min_month_file==1 & daily_eligible==1`). **We use 2,424 (the CSV non-null distinct count) as the canonical figure**; "2,425" refers to the raw probe log (= 2,424 named + 1 null). *Minor open item:* recover the original ticker by disabling NA-parsing in the staging read (`keep_default_na=False`) — cosmetic, no numeric impact.

**Column dictionary (`_pair_dataset.csv`):**

| Column | Meaning |
|---|---|
| `symbol`, `session` | the probed (symbol, ET session date) |
| `n_probes`, `n_miss` | probes issued / probes returning 0 bars for this pair |
| `max_n` | max bars returned across the session's probes (`>0` ⇒ the symbol DID trade the regular session) |
| `has_min_month_file` | a minute month-file exists in the lake for this symbol/year/month |
| `has_session_bars`, `has_regular_bars` | the month-file has any bar / any 09:30–15:59 bar for this session |
| `prior_close`, `prior_adv` | reconstructed from split-adjusted daily: last close before the session / trailing-20 mean(`close×volume`) |
| `has_quote_month_file` | a SIP quote month-file exists |
| `daily_eligible` | `1` iff `1 ≤ prior_close ≤ 20` AND `prior_adv ≥ 2e6` (PIT-eligibility reconstruction) |
| `first_trade_et` | session-wide first trade time |
| `category` | one of {`no_minute_file`, `no_session_bars_has_month_file`, `no_daily_history`, `intra_session_sparse`, `no_regular_bars`} |

**Reproduction scripts** (all under `scripts/`): `_tmp_instrument_preflight.py` (capture), `_extract_pair_dataset.py` (stage CSV), `_check_ir2m_basis.py` and `_check_window_union.py` (eligibility-basis settlement, §9). Exact commands in §11.

---

## 5. Findings

### 5.1 Overall and the 5-way categorization

Whole population: **143,075 probes / 52,622 miss = 36.78%**. By category (share of all misses; reproduced exactly from `_pair_dataset.csv`):

| Category | Misses | % of total miss | Nature |
|---|---:|---:|---|
| `no_minute_file` | 24,885 | 47.29% | symbol has no minute month-file at all that month |
| `no_session_bars_has_month_file` | 11,845 | 22.51% | month-file exists but 0 bars this session |
| `no_daily_history` | 11,454 | 21.77% | no prior split-adjusted daily bar (see caveat) |
| `intra_session_sparse` | 4,425 | 8.41% | symbol DID trade (`max_n>0`); scattered no-trade minutes |
| `no_regular_bars` | 13 | 0.02% | edge case |

*Caveat on `no_daily_history` ("not-yet-listed").* This category is defined operationally as **"no prior split-adjusted daily bar exists on the probed sessions"** — it is an *absence-of-data* label, not a confirmed listing-date verdict. We interpret it as "not-yet-listed," but that interpretation is **partly inferential**: the lake's asset master is a single future-dated snapshot with no listing/delisting dates (§10 to-do #4), so we cannot independently confirm a PIT listing date. The §6 lake spot-check (182/198 acquire minute+quote data later; 0 have a daily bar before 2025-08-27) is strong corroboration that these are genuine post-window listings rather than backfill holes, but it is corroboration, not proof. *Open question / to validate:* the 16/198 not shown to acquire data later are unexplained; a PIT asset master would settle this definitively.

### 5.2 THE decisive table

| Probe restriction | Probes | Miss | Miss % | Gate (5%) |
|---|---:|---:|---:|:--:|
| All probed symbols | 143,075 | 52,622 | 36.78% | **FAIL** |
| `has_min_month_file == 1` | 106,736 | 16,283 | 15.26% | **FAIL** |
| `daily_eligible == 1` AND `has_min_month_file == 1` | 67,464 | 2,304 | **3.42%** | **PASS** |

Restricting to the genuinely-tradeable universe drops the miss to **3.4152%**, with **headroom = 0.05 × 67,464 − 2,304 = 1,069 probes (1.6 pp)** to the gate.

**On `daily_eligible` self-consistency (a circularity disclosure).** Recomputing `daily_eligible` from the CSV's own `prior_close`/`prior_adv` yields 0 / 12,125 mismatches vs the stored column — but this only confirms the column matches its own formula `(1 ≤ prior_close ≤ 20) AND (prior_adv ≥ 2e6)`. It does **not** prove the formula matches the real `build_pit_universe` verdict, which additionally applies instrument-class, blocklist, delisting, and `status_active` filters (`builder.py:545–573`) that our reconstruction omits. Those omitted legs are *additional* eligibility constraints, so the real eligible set is a **subset** of our `daily_eligible==1` set — meaning our restriction is, if anything, slightly *over-inclusive* of the tradeable universe (it admits names the builder might reject), which makes the 3.42% a conservative upper bound on the restricted miss rate rather than an optimistic one. *Open question / to validate:* a direct CSV-eligibility-vs-`build_pit_universe`-output reconciliation count is **not** shown here; §6 asserts the eligibility was "re-derived directly from `build_pit_universe`" for the per-session universe size (~1,148–1,162) but the per-row CSV `daily_eligible` column uses the reconstructed 2-leg formula, not the full builder. These should be reconciled before the gate is declared green.

The same restriction clears the other three failing checks (probe-log time-of-day bucketing maps each probe to its check, per the §3 four-family census):

| Check | All-symbols | Tradeable-only | Tradeable gate |
|---|---|---|:--:|
| `coverage_missing_late_session` | 34,584/97,000 = 35.65% | 988/45,664 = 2.16% | **PASS** |
| `coverage_missing_exit_path` | 3,264 unique/21,825 total = 14.96% | 40 unique/10,325 total = 0.39% | **PASS** |
| `audit_missing_sessions` | 1,762 | 0 | **PASS** |
| `coverage_missing` (first-scan minute leg, 1% gate) | 6,619/12,125 = 54.6% | 1,156/5,708 = 20.25% | **STILL FAIL** (see §6.1/§7.2) |

(The `exit_path` numerator is unique `sym@date` strings over a total-probe denominator — see the §3 disclosure. The `coverage_missing` row is the **minute leg only**; the gated check is minute ∪ daily, §3.)

`audit_missing_sessions = 1,762` is reported (by the doc) to trace to **6 sub-`$2M`/out-of-band sparsely-listed tickers** (AIB 463, LIFE 413, VIA 311, SZZL 310, AKTS 264, ASBP 1), all `daily_eligible==0`. **Provenance caveat:** `audit_missing_sessions` reads the lake **audit parquet** filtered to `requested_symbols` (§3), *not* the minute supplier, so this 6-ticker breakdown is **not reproducible from `_pair_dataset.csv`** — it came from a separate lake-audit query whose output is not staged in the CSV the reviewer can re-run. *Open question / to validate:* the 6-ticker attribution and the "→ 0 under restriction" claim should be backed by the audit-parquet query output, which is not included here. The structural argument (it filters to `requested_symbols`, so removing ineligible symbols removes their missing-session counts) is sound; the exact 6-ticker decomposition is asserted, not shown.

---

## 6. Root cause: the probe set is over-inclusive *relative to per-session tradeability* (but intentionally so at the symbol-set level — see §6.1)

**The preflight probes ~2× more symbols than the strategy can trade on any given probed session.** The true `$2M`/`$1-$20` PIT-eligible *per-session* universe is ~1,148–1,162 symbols (a lake spot-check figure, re-derived from `universe.builder.build_pit_universe`; see provenance caveat below); the probe set is **2,424 distinct symbols** (CSV; 2,425 in the raw probe log, §4). **94.66% of all misses (49,813 / 52,622) come from `daily_eligible==0` symbols**, and **1,218 of the 2,424 probed symbols are never eligible on any of the 5 probed sessions** (1,206 are eligible on at least one).

Ineligible-miss decomposition (reproduced exactly from `_pair_dataset.csv`): price > \$20 out-of-band **19,016**; in-band but ADV < \$2M **16,246**; no daily history **11,454**; price < \$1 **3,097** (sum = 49,813).

**Provenance caveat on the ~1,148–1,162 per-session figure and the 249-eligible claim.** The per-session PIT-universe size (~1,148–1,162) and the §9 "249 over-\$20 symbols all eligible somewhere in the plan window" claim come from `_check_window_union.py` / lake spot-checks, **not** from `_pair_dataset.csv`, and are therefore not independently re-runnable from the staged dataset. What *is* CSV-reproducible: 249 probed symbols have `prior_close > 20 AND prior_adv ≥ 2e6` **as-of the first session (2025-08-27)**; across all 5 probed sessions the union of such symbols is **264** (the doc's "249" is the single-session-snapshot count, not the all-session union). The "all 249 eligible somewhere in 2023-11..2026-05" claim requires the lake scan and is *plausible but unverified* from the dataset alone. We retain it as a spot-check result, flagged as such.

### 6.1 The over-inclusion is the intentional anti-under-reporting design — reconcile before acting

**This is the single most important caveat in the document, and it was previously absent.** The full-symbol-set probe that §6 calls a "probe-set basis defect" is, at the *symbol-set* level, a **deliberate P0 design decision** (audit 2026-05-23 §6.6 / P1-001), not a bug:

- `walkforward_runner.py:325–329` (`_resolve_symbols` docstring): *"under `intended_realism` the preflight must probe the full per-fold PIT eligible-universe union (no cap). The capped 100-symbol sample silently underreported coverage."*
- `pit_universe.py:5–7`: *"`intended_realism` now requires the preflight to cover the full union of eligible symbols across every session in every validation + holdout window — anything less is a silently capped preflight and the lab must fail closed."*
- `pit_universe.py:108–109`: *"Preflight coverage telemetry is computed against this set: anything less than the union is a capped preflight and must be flagged with a waiver."*
- Prior audit `2026-05-23_realism_audit.md` §6.6 (P0) + P1-001: the uncapped union was *added on purpose* to stop a prior 100-symbol cap that under-reported coverage.

**What this means for Option A.** §6.6 was specifically about the *arbitrary 100-symbol cap* — "the preflight may probe only 100 of, e.g., the 3000+ symbols the per-fold PIT universe would actually trade." Our recommended fix (§10 Option A) is **not** a re-introduction of that 100-symbol cap; it is a different narrowing: *score each session's probes against that session's own per-session PIT-eligible set*, rather than against the cross-session window-union. These are distinct mechanisms, but they share a direction (narrowing the denominator), and the §6.6 authors' stated principle — "anything less than the union is a capped preflight [that] must be flagged with a waiver" — would, read literally, classify Option A's per-session scoring as exactly the kind of narrowing they guard against.

The honest position is therefore: **the over-inclusion at the symbol-set level is intentional; what we are actually claiming is narrower** — that probing a symbol *on a session where it is PIT-ineligible* (out-of-band price / sub-floor ADV / not-yet-listed *on that session*) and counting the absent minute bar as a realism failure is **mis-attributed**, because the live scanner would never evaluate that symbol on that session. The window-union correctly says "this symbol is in the tradeable universe *somewhere* in the plan window"; it does **not** follow that the symbol is tradeable on *every* session, and the coverage check currently treats it as if it were. **Whether the right remedy is (i) a per-session eligibility filter inside `_probe_fold` (Option A), or (ii) keeping the full union but scoring coverage only over the per-(symbol, session) pairs that are PIT-eligible on that session (a denominator change, not a probe-set change — which preserves the §6.6 "no cap on the symbol set" invariant while fixing the mis-attribution), is an open design question.** Option (ii) is likely the §6.6-compatible form of the fix and should be evaluated against the §6.6 rationale explicitly; Option A as literally written narrows the probe set and must carry a waiver or an argument that per-session scoping is *not* the under-reporting §6.6 forbade. **Until this is reconciled with §6.6, the recommendation is not green-lit** — it is "the diagnosis is sound; the remedy needs a §6.6-compatible formulation."

**Where `symbols` is built (the change point):**

- `optuna/preflight.py::run_full_fold_preflight` is called from `optuna/walkforward_runner.py:2198`, passing `symbols=symbols`.
- `symbols` is built at `walkforward_runner.py:1899` via `_resolve_symbols(cfg, md, sim_mode, plan)` (`walkforward_runner.py:315–381`). For `intended_realism` + lake + no waiver it returns `plan_pit_symbol_union(...)` (`optuna/pit_universe.py`).
- `plan_pit_symbol_union` (`pit_universe.py`) unions `build_pit_universe` eligible symbols **across every session of every validation fold plus the holdout** — i.e. the full **2023-11..2026-05 plan window** (`include_holdout=True`). It is deliberately **uncapped**.
- `_probe_fold` (`preflight.py:570`) then re-probes that one window-union `symbols` list on **every session** via `build_replay_checks`, with **no per-session PIT re-filter**.

So a symbol that was eligible early in the plan window (≤\$20, ADV≥\$2M) but is far out-of-band on the probed Aug-2025 sessions is still probed there and counted missing. The `no_daily_history` category (21.8%) is the cleanest illustration: 198 distinct symbols with **zero** prior split-adjusted daily bars on the probed sessions — the builder rejects these as `no_prior_bar` (`builder.py:556–557`), so they are not in the tradeable universe at all, yet they are probed. Lake spot-check confirmed **0 contradictions**: not one of the 198 has a daily bar before 2025-08-27; 190/198 first list strictly after the window, 8 IPO within it, and 182/198 demonstrably acquire minute+quote data later — genuine post-window listings, not data gaps.

The mechanism is a **per-(symbol, session) mis-attribution**: the symbol set is correctly the full uncapped union (intentional, §6.1), but the coverage check counts an absent minute bar as a failure for *(X, S)* pairs where X is PIT-ineligible *on session S* — pairs the live scanner would never evaluate. (We deliberately no longer call this a "probe-set basis defect": at the symbol-set level the broad probe is by design — §6.1.) The fix is a **per-(symbol, session) eligibility scoping of the coverage denominator**: count a missing minute bar against realism only when X is PIT-eligible on S. This can be implemented either by per-session filtering inside `_probe_fold` (Option A, narrows the probe set — must be reconciled with §6.6) or, preferably, by keeping the full union probe and excluding ineligible-on-session pairs from the coverage fraction (a denominator change that preserves §6.6's "no symbol-set cap" invariant). Secondary hardening: a PIT/survivorship-aware asset master (§10 to-do #4), and disambiguating the ADV/price-cap config keys across configs.

---

## 7. The genuine residual (3.42% on the probed window) — defensible on these 5 sessions

The 2,304-miss residual inside the tradeable universe splits into two groups, characterized by targeted lake spot-checks (minute `adjustment=raw`, quotes `feed=sip`). **Note on method:** the sub-classifications below (96.2% / 3.8% in §7.1; the 30/14/5 split in §7.2) rest on **manual classification of small samples** plus named-ticker anecdotes, not a full programmatic pass over all 2,304 rows. The percentages are reported to 0.1% but the base is partly hand-classified — treat them as **well-supported estimates with ~tens-of-rows precision**, not exact census figures.

### 7.1 `intra_session_sparse` — 1,709 misses (74.2% of residual; 2.53% of tradeable probes)
Every row has `max_n>0`, `has_session_bars==1`, `has_regular_bars==1`, `has_quote_month_file==1` — the symbol *did* trade, all present bars have volume > 0, and gaps are scattered (multiple 5–30 min holes, not one contiguous block). Decomposed by `first_trade_et` (estimates):
- **Window-edge effect — ~1,644 misses (≈96%)**: full/near-full-session names (e.g. ARKO 163 bars 09:30→16:00, ADEA 226, PLGO 317) whose 1–2 earliest post-first probes land at 09:45–09:46, just before the symbol's first *in-window* bar (ARKO's first ≥09:45 bar is 09:47). A 1-minute window-edge alignment plus thin-stock microstructure. (Characterized from named tickers; the ≈96% is an extrapolation from the `first_trade_et` distribution, not a per-row audit.)
- **Genuinely-late — ~65 misses (≈4%)**: ~18 extremely thin marginal-ADV names right at the \$2M floor (median prior_adv \$2.39M; AACI/XRPN first trade 13:54 with 2 bars all session). Real no-trade microstructure for floor-ADV names. This is the component expected to persist lake-wide.

### 7.2 `no_session_bars_has_month_file` — 595 misses (25.8% of residual; 0.88% of tradeable probes)
All 0-bar sessions despite a quote month-file. **Classified by hand across the 49 distinct (symbol, session) rows** that carry these 595 probe-misses: 30 lake-start-boundary (target session predates the symbol's first minute-file session), 14 after-last (stale month file ends before the target), 5 missing-day-within-range. These include unquestionably-liquid names that traded those days (CWAN prior_adv \$102M, PENN \$72M, HP \$42M, CPRX \$31M, PSKY \$382M). This is consistent with an **ingestion/backfill-incompleteness artifact** concentrated at the lake-start boundary — and the probed 5 sessions are the lake's *first* 5, so this share is over-represented here and is expected to shrink on interior folds. **Caveat:** the 30/14/5 split is from 49 hand-classified rows; extrapolating it as a stable microstructure narrative to the full residual is an estimate, and the "would shrink on interior folds" claim is an *expectation* not yet measured (§10 to-do #1).

**Net (probed window only):** of the 2,304 residual misses, ~595 (0.88% of probes) are consistent with ingestion artifacts that arguably should not count against realism; ~1,644 (2.44%) are a 09:45–09:46 window-edge alignment on full-session thin stocks; ~65 (0.10%) are genuinely-late floor-ADV no-trade. On this window the truly-no-data-when-data-should-exist component is **small (on the order of the ~65 floor-ADV no-trades plus any genuine intra-day holes), not zero**. We **withdraw the earlier "effectively zero" claim** as an overclaim: the defensible statement is *"small on this boundary fold, and dominated by a window-edge alignment artifact and a lake-start ingestion boundary; unmeasured on interior folds."* The 3.42% is plausibly conservative on these 5 sessions (the window-edge and ingestion components are arguably not realism failures), but whether a `$2M`-floor faithful replay sits inside the 5% gate **lake-wide** is an open question pending the interior-fold re-run (§10 to-do #1).

---

## 8. Honest correction log

We reached the over-inclusion finding only after discarding three earlier conclusions. An expert reviewer should see the full reasoning trail:

1. **(WRONG) "`intended_realism` is fundamentally incompatible with this illiquid universe."** The early read of a 35.65% miss was that sub-\$20 micro-caps simply don't trade every minute and the faithful-replay contract can never be met for them. *Why wrong:* the 35.65% is not measured over the tradeable universe — it is dominated (94.66%) by `daily_eligible==0` symbols outside it. On the actually-tradeable set the miss is 3.42% (on the probed window). The illiquid universe replays faithfully *for the symbols actually traded each session*; the headline conflated "untradeable symbol on this session" with "unfaithful replay."

2. **(WRONG) "Raising the ADV floor (\$250k → \$2M) fixes it."** We did raise the floor, expecting the thin-stock misses to drop out. *Why wrong:* raising the floor *tightens the tradeable universe* but does **not** change the *probe set* — `plan_pit_symbol_union` still unions every PIT-eligible symbol across the whole plan window, and `_probe_fold` still probes all of them on every session regardless of floor. The floor change moved the eligibility line but the over-inclusion is in the probe machinery, upstream of where the floor bites per-session. The miss stayed ~36%.

3. **(WRONG) "It's a minute-backfill gap — the lake is missing SIP minute bars."** Plausible given `no_minute_file` is 47% of misses. *Why wrong:* lake spot-checks showed those symbols are either not-yet-listed (no daily history at all), out-of-band on the probed dates, or below the ADV floor — they are not symbols the strategy trades, so their absent minute files are not a gap in the *tradeable* lake. Within the tradeable set, minute coverage is 96.6% (3.42% miss), and the small residual is thin-stock no-trade + a lake-start ingestion boundary, not a systemic backfill hole.

4. **(CORRECT, with a design caveat) The miss is dominated by per-(symbol, session) pairs the strategy cannot trade on that session.** **1,218 symbols (50.25% of the 2,424 CSV-distinct)** are never PIT-eligible on any of the 5 probed sessions and drive 94.66% of misses. Restricting the coverage denominator to PIT-eligible-on-session + minute-backfilled pairs gives 3.42% on the probed window. **Design caveat (added this revision):** the broad *symbol set* is intentional (audit §6.6 — the uncapped PIT-union exists to prevent coverage under-reporting), so the correct framing is "the coverage *denominator* mis-attributes ineligible-on-session pairs," not "the probe set is a defect." Whether the remedy narrows the probe set (Option A) or only the scored denominator is an open §6.6-reconciliation question (§6.1).

---

## 9. Adversarial verification

Three load-bearing claims were stress-tested. **Claim C (added this revision) is the one that most threatens the recommendation** and was previously omitted from this section.

**Claim A — "The 35.65% is over-inclusion, not a realism gap; restricted to the tradeable universe the gate passes at 3.42%."**

The strongest counterargument (and the reason this finding was initially graded **not-survived**): *the 3.42% is computed against the wrong eligibility basis.* The argument was that the as-run config was `bowaka_v2_research_sip.yml`, whose **`universe` block sets `max_price: 1000.0`** (lines 35–39) — and since `builder._price_band` reads `universe.max_price`, the builder would admit AAOI-class names (prior_close $25, $130M ADV) as genuinely eligible. On that basis the miss is 5,393/70,888 = **7.61%** (or 20.34% unrestricted) — a **FAIL** — and the favorable 3.42% only appears by silently substituting `signals.price_max=20` for `universe.max_price=1000`.

**We settled this empirically and the counterargument does NOT survive.** The instrumentation ran the preflight against a temporary config `/tmp/ir2m.yml`, not a committed file. We recovered `/tmp/ir2m.yml` from the container and read its `universe` block directly:

```yaml
universe:
  asset_classes: [operating_equity]
  exclude_pattern_class: true
  max_price: 20.0
  min_adv_dollars: 2000000
  min_price: 1.0
```

The as-run config caps at **\$20**, floors ADV at **\$2M**, and carries **no `avg_dollar_volume_min` in the `universe` block** — so `_adv_min` resolves cleanly to `min_adv_dollars=2000000` (no key-precedence override). This is exactly the basis the CSV's `daily_eligible` reconstruction uses. The counterargument's `max_price=1000` came from `bowaka_v2_research_sip.yml`, which is **not** the config that ran. The three committed resolved walk-forward configs likewise all carry `universe.max_price=20` (with `min_adv_dollars=250000`, the floor being lifted to \$2M by the overlay that produced `/tmp/ir2m.yml`).

We then resolved the remaining puzzle the counterargument raised — **probed symbols with prior_close > \$20 and ADV ≥ \$2M (BMNR \$49.95, SOFI \$25.62, HIMS \$45.35, …).** Under a \$20 cap the builder should reject these as `price_above_max`, so why are they probed? **Count provenance:** as-of 2025-08-27 (first probed session) there are **249** such symbols (CSV-reproducible); across all 5 probed sessions the union is **264** (CSV-reproducible). The "249" figure is the single-session snapshot. A lake spot-check (`_check_window_union.py`, **not** CSV-reproducible) reports that all 249 were eligible (1 ≤ prior_close ≤ 20 AND ADV ≥ \$2M) on at least one session in the full plan window (2023-11-27..2026-05-20) with 0 never-eligible. They are in the probe set because `plan_pit_symbol_union` unions eligibility across the *whole plan window* (§6) — SOFI/BMNR were ≤\$20 earlier, became eligible then, and the window-union retains them. This is the over-inclusion mechanism, **not** a `max_price=1000` config bug. The counterargument mis-identified the config; the 3.42% basis is correct. **Claim A survives** (the window-union lake-scan leg is a spot-check, not independently re-runnable from the CSV).

**Claim B — "Restricted to the tradeable PIT universe, minute coverage is 3.42% and passes the 5% gate (on the probed window)."**

The counterargument: the pass is *contingent* on the \$2M ADV floor and the \$1–\$20 band — below \$2M (at \$250k or \$500k) it fails. **This survives**: that contingency is legitimate because the floor and band *are the config's own gate* — the tradeable universe is defined by them, so scoring coverage over that universe is correct, not cherry-picking. Exact figures confirmed: 67,464 probes / 2,304 miss / 3.42%; unrestricted 143,075 / 52,622 / 36.78%; **1,218 of 2,424** symbols never eligible drive **94.66%** of misses. **Claim B survives — scoped to the 5 probed sessions** (lake-wide generalization is Claim C / §10 to-do #1, not established here).

**Claim C (the recommendation itself) — "The fix is to filter/scope the coverage probe to the per-session PIT-eligible set; this is correct, not a regression."**

This is the claim a §6.6-aware reviewer would attack hardest, and it does **not** cleanly survive as originally written. The counterargument: the uncapped full-PIT-union probe is an **intentional P0 anti-under-reporting mechanism** (audit 2026-05-23 §6.6; `pit_universe.py:5–7,108–109` — "anything less than the union is a capped preflight [that] must be flagged with a waiver"). Narrowing the symbol set the preflight probes (Option A as literally written) re-introduces precisely the kind of narrowing §6.6 was added to forbid, and would need a waiver. **Verdict: PARTIALLY SURVIVES, conditionally.** The *diagnosis* (ineligible-on-session pairs are mis-attributed) survives — §6.6 was about not *capping the symbol set arbitrarily* (the old 100-symbol cap), not about scoring coverage over ineligible-on-session pairs. But the *remedy* must be re-formulated to be §6.6-compatible: keep the full uncapped union as the probe set (honoring §6.6), and change only the **coverage denominator** to exclude pairs that are PIT-ineligible *on that session*. The literal Option A (filter the probe set) is **not** green-lit without either (a) a §6.6 waiver, or (b) re-expressing it as the denominator-only change. **This is the load-bearing open item for the recommendation** (§6.1, §10 Option A).

Two of three claims (A, B) survive on the probed window; the recommendation-bearing Claim C survives only as a diagnosis and requires a §6.6-compatible re-formulation of the remedy. The previously-claimed "both load-bearing claims survive" understated the work remaining, because the §6.6 tension was not among the stress-tested claims.

---

## 10. Options & recommendation

### Option A (recommended diagnosis; remedy needs a §6.6-compatible form) — score coverage only over per-session PIT-eligible (symbol, session) pairs
**Two implementable forms, with a strong preference:**

- **A1 (preferred, §6.6-compatible) — denominator-only scoping.** Keep the full uncapped PIT-union as the probe *symbol set* (this honors the intentional audit-§6.6 anti-under-reporting invariant — see §6.1). Change only the **coverage fraction**: when computing `missing/probes` in `_coverage_check` / `build_coverage_check`, count a (symbol, session) pair only when the symbol is PIT-eligible *on that session*. This requires threading a per-session eligibility predicate into `build_replay_checks` / `build_coverage_check` (e.g. a `is_eligible(sym, session)` callback derived from `build_pit_universe_for_sessions`). No symbol is removed from the probe set, so no §6.6 waiver is needed; the telemetry still reports full-union coverage, and the *gate* fraction is computed over the genuinely-tradeable pairs.
- **A2 (literal "filter the probe set") — narrows the probed symbols inside `_probe_fold` (`preflight.py:570`)** to `eligible_symbols(build_pit_universe_for_sessions(...)[session])` per session. This is simpler but **re-introduces a per-session narrowing of the symbol set that audit §6.6 classifies as a capped preflight requiring a waiver** (§6.1). Adopt A2 **only** with an explicit `research_waiver_capped_symbols`-style opt-in or an argued §6.6 exception; do **not** ship it silently.

Both make the coverage fraction measure what it claims to: *can the lake faithfully replay the symbols the strategy would actually trade on each session.* **Prefer A1.**

- **Pros:** Directly removes the 94.66% of misses from `daily_eligible==0` pairs; on the probed window the late-session fraction falls to 2.16% and exit-path to 0.39% (both < 5%). Makes the preflight's gate honest without touching the trading universe (folds already trade the per-session PIT set).
- **Cons / still-to-do before declaring green:**
  1. **(Generalization — the single biggest open item.)** The 3.42% is established only over the **first 5 sessions** (the lake's earliest, where the §7.2 ingestion-boundary residual is over-represented). The headroom is **1,069 probes / 1.6 pp**, which is thin. **Re-run the instrumented probe on an interior fold** to confirm coverage holds lake-wide. Expectation is ≤3.4% (the 0.88% ingestion-boundary share should shrink), but this is an *expectation, not a measurement* — a single boundary fold cannot establish lake-wide coverage, and the thin headroom means an unverified interior fold could plausibly move the verdict.
  2. **Fix `coverage_missing` separately (correcting the earlier mischaracterization).** Restricting/scoping the universe only takes the **minute leg** of `coverage_missing` from 54.6% → 20.25% (still failing the 1% gate). The earlier draft attributed this to a *"degenerate zero-width window `[09:45, 09:45]` that returns 0 bars"* — **that characterization was wrong and is withdrawn.** Verified against source and the probe log: `build_coverage_check` uses `probe_ts = scan_times[0]` = 09:45 (`data_quality.py:421`), and the supplier asks the lake for `[09:45, 09:45]` — a **1-minute** window, not zero-width. In the raw probe log this 09:45 probe returns **≥1 bar for 5,506 of 12,125 symbols** (it returns the single 09:45 bar whenever the symbol traded at 09:45); the 6,619 miss is **genuine no-trade-at-09:45** for thin stocks, not a window bug. The proposed `[09:45, scan_ts]` widening is also **incoherent for the first-scan check**: at first-scan time `scan_ts` *is* 09:45, so there is no later `scan_ts` to widen to. The real issues with `coverage_missing` are different and twofold: **(a)** it is a strict per-pair check at the *single* 09:45 instant against a 1% gate — far stricter than the 5% replay gates — so even the tradeable 20.25% reflects that many tradeable thin stocks simply have no *first-minute* trade (this is the same per-session-eligibility scoping issue plus an arguably-too-strict single-instant requirement; consider whether the first-scan minute probe should require a bar within `[09:45, 09:45+ε]` or be folded into the 5% late-session contract); and **(b)** `coverage_missing` is a **daily ∪ minute** union (`data_quality.py:442`), so its true numerator includes a daily-coverage leg we did not isolate (§3) — any fix must address both legs. *This item is now an open design question on the `coverage_missing` contract, not a one-line "window bug" fix.*
  3. Harden the eligibility-basis config keys so the probe basis can never silently diverge from the trading basis: disambiguate `universe.max_price` vs `signals.price_max` (the `research_sip` config's `universe.max_price=1000` is anomalous vs every `intended_realism` config's `=20`), and the `avg_dollar_volume_min`-over-`min_adv_dollars` precedence in `_adv_min` (`builder.py:228–231`).
  4. Replace the **non-PIT, survivorship-free asset master** (a single future-dated 2026-06-05 snapshot, `status='active'` for all 6,527 rows, no listing/delisting dates) with a point-in-time-aware master, so not-yet-listed names are excluded by listing date rather than relying solely on `no_prior_bar`. *Until then, the `no_daily_history` → "not-yet-listed" attribution (§5.1, §6) is inferential, not PIT-confirmed.*

### Option B — accept `current_code_parity` for the finalist
Ship the existing `current_code_parity` finalist and defer `intended_realism`.
- **Pros:** Zero new engineering; a validated finalist already exists.
- **Cons:** Loses the faithful-replay realism guarantee (`current_code_parity` reproduces live warts, e.g. halt gate failing open); does not resolve the preflight mis-attribution, which will resurface on any future `intended_realism` attempt. The realism gap we *thought* blocked `intended_realism` does not appear to exist on the probed window, so Option A is cheap relative to its payoff — *contingent on the interior-fold confirmation (cons #1)*.

**Recommendation: Option A1, then validate.** The diagnosis is sound — on the probed window the blocker is per-session-eligibility mis-attribution in the coverage denominator, not a data or realism deficiency. The path is: (i) implement A1 (denominator-only scoping — keeps the §6.6 full-union probe, so no waiver); (ii) reconcile explicitly with audit §6.6 (§6.1) and reject the literal A2 unless waivered; (iii) re-formulate the `coverage_missing` fix per cons #2 (the "window bug" framing is withdrawn); (iv) **re-run on an interior fold** before declaring the mode green. The mode is *plausibly* supportable; it is **not yet demonstrated green lake-wide.**

---

## 10b. Resolution (2026-06-07): A1 implemented & verified on the study-start window

**Status: A1 (denominator-only scoping) IMPLEMENTED and VERIFIED on the probed study-start window.** The two coverage-replay checks the diagnosis blamed on per-session-eligibility mis-attribution flipped from gating-FAIL to non-gating, exactly as predicted, with the §6.6 full-union probe preserved (no waiver). The mode is **not yet declared green lake-wide** — two *different* checks still gate (below), and the interior-fold confirmation (§10 cons #1) is still open.

### What was built
A shared helper `optuna/pit_universe.py::eligible_per_session_map(lake_root, sessions, cfg=)` builds the per-session PIT-eligible set using the **identical** `MarketDataStore` + `pit_cfg` + `build_pit_universe_for_sessions` + `eligible_symbols` construction as `fold_pit_symbol_union` (the §6.6 union helper), but returns the per-session map instead of unioning. It is threaded into `build_data_quality_report(..., eligible_per_session=...)`, which forwards it to `_build_multi_level_checks` → `build_replay_checks` / `build_coverage_check`. The gates score their PASS/FAIL **fraction** over only the `(symbol, session)` pairs that were PIT-eligible *on that session*; the **full symbol union is still PROBED** (the `probes`/`missing`/`missing_fraction` telemetry is byte-identical), so the audit-2026-05-23 §6.6 uncapped-union invariant holds and **no waiver is required** (this is the A1, not the literal A2, path). `late_session` gates on the *current* session; `exit_path` gates on the *forward* session; `coverage_missing` gates on the scan session. `eligible_per_session=None` (any build failure, no lake, or no sessions) degrades to the legacy full-union gate, byte-identical to pre-fix — it never crashes the preflight.

### The load-bearing correction: the fix had to be threaded into TWO call sites
The diagnosis pointed at the per-fold `_probe_fold` (`preflight.py`, called from `run_full_fold_preflight` at `walkforward_runner.py:2198`). Wiring **only** that site does **nothing** for the `$2M` run: an `intended_realism` study aborts at an *earlier* **study-start preflight** — `build_data_quality_report` at `walkforward_runner.py:1972` → `run_preflight` at :2003 → `if not preflight.passed:` abort at :2016 — which runs *before* `run_full_fold_preflight` (:2198) is ever reached. The aborting probe is provably the study-start one: `late_probes = 97000 = 5 sessions × 8 samples × 2425 symbols`; `exit_probes = 21825 = 9 forward-sessions × 2425`. **Both** the study-start call (:1972) and `_probe_fold` now pass `eligible_per_session`; the helper de-duplicates the construction.

### Verified before/after (real `run_walkforward_study("/tmp/ir2m.yml")`, study-start gate)
Captured by spying on `build_data_quality_report` + `run_preflight` (`scripts/_verify_studystart_gate.py`); evidence JSON in `scripts/_dq_report_capture.json` / `_preflight_capture.json`.

| Check | Full (ungated) fraction | Gated (eligible) fraction | Gate | Pre-fix | Post-fix |
|---|---|---|---|---|---|
| `coverage_missing_late_session` | 34584/97000 = **35.65%** | 1350/46064 = **2.93%** | 5% (`REPLAY_COVERAGE_FAIL_FRACTION`) | FAIL (gating) | **warn — non-gating** ✓ |
| `coverage_missing_exit_path` | 3264/21825 = **14.96%** | 72/10389 = **0.69%** | 5% | FAIL (gating) | **warn — non-gating** ✓ |
| `coverage_missing` | 6619/12125 = **54.59%** | 1205/5758 = **20.93%** | 1% (`COVERAGE_MISSING_FAIL_FRACTION`) | FAIL | **still FAIL** |
| `audit_missing_sessions` | count=1762 (lake audit parquet) | n/a — not minute-supplier scored | 0 | FAIL | **still FAIL** |

Post-fix the study-start abort message reads exactly `2 required data-quality check(s) failed: audit_missing_sessions: count=1762; coverage_missing: count=1205` — `late_session`/`exit_path` have dropped out of `required_failures` entirely. (`late_session`/`exit_path` are WARN-severity checks that *escalate to gating FAIL* only above the 5% fraction; the gated 2.93%/0.69% sit below it, so they report `warn` and no longer gate.)

### Remaining gating failures — both pre-existing, both separate mechanisms (NOT addressed by A1)
1. **`coverage_missing` (20.93% gated, 1205/5758).** The first-scan-minute (09:45 ET) leg. A1's denominator scoping *did* cut it from 6619→1205 (the eligible filter applies here too), but 20.93% ≫ the 1% gate: even among PIT-eligible names, one in five has no bar at the literal first scan minute (genuine no-trade-at-09:45 for thin-but-eligible symbols — see §4/§7). This is the deferred item #3 (the daily-OR-minute union leg / first-scan tolerance). **Not** a denominator artifact.
2. **`audit_missing_sessions` (count=1762).** Reads the lake's own session-completeness **audit parquet**, not the minute supplier, so the eligibility denominator does not touch it; it needs a separate reconcile (regenerate/scope the lake audit, or stop requiring audit rows for PIT-over-included symbols).

### Tests
`tests/unit/data tests/unit/optuna tests/integration/test_dq_replay_level_missing_{exit_path,late_minute}.py` → **266 passed, 0 failed**. The two formerly-stale mocks in `test_full_pit_preflight_fail_closed.py` (`<lambda>() got an unexpected keyword argument 'adjustment'`, a pre-existing drift, reproduced on pristine HEAD) were widened to `**kwargs` in this change. The 7 frozen gates directly exercising the edited functions stay green; the `eligible_per_session=None` path is byte-identical to pre-fix.

### Files
`optuna/pit_universe.py` (helper), `optuna/walkforward_runner.py:1972` (study-start wiring), `optuna/preflight.py` (`_probe_fold` refactored to the helper), `data/dq_levels.py` + `data/data_quality.py` (gated denominators), `tests/unit/optuna/test_full_pit_preflight_fail_closed.py` (mock widening). Reproduction: `scripts/_verify_studystart_gate.py`.

---

## 10c. Remaining two gates: evidence + recommended fix per check (2026-06-07)

After the §10b denominator fix, two checks still gate the `$2M` study-start preflight. Both were deep-dived (instrumented probe + sim-source read + adversarial safety verification). Neither is a data defect; each carries an **open policy decision** for the operator.

### Check 1 — `coverage_missing` (gated 1205/5758 = 20.93%, gate = 1%)

**Root cause: the check requires a minute bar in the *exact* 09:45 ET minute, but thin-yet-eligible names don't always print in that single minute.** Instrumented split of the 1205 eligible misses (raw-parquet verified, `scripts/_instrument_coverage_missing.py`):
- **0 daily-leg misses** — every eligible symbol HAS a session-day daily bar.
- **1111 (92.2%) "traded_later"** — no bar in `[09:45,09:45]` but ≥1 bar in `[09:45, close]`. Staleness of the last price *at* 09:45: median 2 min, p95 14 min; 98.1% have a real intraday pre-09:45 bar (only 1.7% fall back to prior close).
- **94 (7.8%) "no_trade_today"** — flat all session; 94/94 have a valid prior daily close.
- **0 backfill defects** — all month files present; spot-checked raw bytes (ABEO 09:43→09:47, ABX 09:44/09:46) are second-aligned with genuine single-minute holes — NOT a timezone/window/off-by-one artifact.

**Sim reality + MEASURED criteria (high confidence, `scripts/_wf_coverage_criteria.js`, 5758 eligible pairs):** at the FIRST scan the sim's window is the degenerate `[09:45,09:45]` — `intraday_window_start('scanner_start_to_scan')=09:45`, **no lookback** — so the current check IS faithful to the first scan. BUT the sim runs **346 scans/session** (every 60s, 09:45→15:30) and re-evaluates a skipped symbol at every later scan (no per-symbol-per-day disable latch; `scan_loop.py:365-399`), carrying forward the last real bar bounded by `max_bar_age_seconds=90s`. **Probing only the first scan is the mis-calibration.** Measured miss-fraction per candidate criterion:

| Criterion | miss | % | 1% gate |
|---|---|---|---|
| `exact_0945` (current) | 1205 | 20.93% | ❌ |
| `asof90_at_0945` (pre-open 90s lookback — *not what the sim does*) | 758 | 13.16% | ❌ |
| `fresh_at_any_scan_90s` ≡ `any_regular_session_bar` (**sim-faithful**: tradable at some scan) | 94 | 1.63% | ❌ |
| `monthfile_and_daily_present` (data exists / backfill-gap) | 45 | 0.78% | ✅ |

*(An earlier draft of this section recommended an "asof-within-90s" criterion — measurement shows that is both insufficient (13.16%) and not sim-faithful (the sim's first-scan window has no lookback). Corrected here.)*

**Recommended fix — a COMBINATION (no single lever passes honestly):**
1. **Fix the criterion** (primary): replace the single-first-scan probe with the sim-faithful "tradable at some scan" test (`any_regular_session_bar`): a `(sym,session)` is covered iff a daily bar exists AND ≥1 real minute bar falls in `[scan_times[0], scan_times[-1]]`. Drops 20.93%→1.63% by deleting the 1111 false-positive late-first-print misses (ABEO 09:47, ABX 09:46) the sim trades 1-2 scans later. This is **calibration, not gaming** — it derives from the sim's re-scan + 90s carry-forward semantics and STILL fails at 1.63% (proof it is not a rubber stamp).
2. **Clear the genuine residual** (94 = TRUE zero-bar sessions, e.g. ANAB/AVBC/BACC @2025-08-27, verified zero bars 09:43:30→15:30): preferred — drop zero-regular-session-bar pairs from the PIT-eligible denominator (the §6.6 over-inclusion pattern — they are not simulable and were never "expected"), which takes the eligible-set residual below 1%. Fallback — raise `COVERAGE_MISSING_FAIL_FRACTION` modestly to 2-3%.
3. **GUARDRAIL (non-negotiable):** promote `monthfile_and_daily_present` to its OWN strict hard-fail presence check (minute month parquet + split_adjusted daily bar per eligible pair) so the tolerant tradability gate cannot mask a missing-month-file / wrong-feed (SIP-vs-IEX) catastrophe.

**Why not Option 2 (raise the gate) alone:** passing `exact_0945` needs the threshold lifted from 1% to **>21%**, which keeps the criterion measuring first-print timing (the wrong thing) AND blows a hole in backfill-gap detection (a whole missing month would slip through silently). **OPEN POLICY DECISION** (the only remaining sub-choice within the combination): how to clear the 1.63% flat-session residual — (a) drop zero-bar pairs from the eligible denominator [preferred]; (b) modest gate bump to 2-3%.

### Check 2 — `audit_missing_sessions` (count = 1762, gate = 0)

**Root cause: a SYMBOL-LEVEL missing-session count over each ticker's entire 2.5-year expected calendar, which conflates pre-eligibility illiquid early-life with missing data.** Decomposition (`scripts/_audit_safety_check.py`, `_audit_missing_vs_eligible_window.py`):
- All 1762 probe-universe missing sessions come from **6 symbols** (AIB 463, LIFE 413, VIA 311, AKTS 264, SZZL 310, ASBP 1) — SPAC-in-trust → de-SPAC / ticker-reuse names (cf. the SPAC-unit cohort TWLVU/GPACU/HCMAU) that became liquid/eligible only in **2025-2026**.
- The earlier "5-session → 0" reading (§10b-era) was **misleading**: those 6 are not eligible in the Aug-Sep probe window but ARE eligible in the *full study* (2026), so the real check (over the full-study symbol set) still counts them.
- **For all 6: 100% of missing sessions fall BEFORE the first eligible date; 0 fall inside any eligible window; 0 eligible sessions lack a daily bar.** The audit over-counts each ticker's thin early life (e.g. AIB: 169 observed of 632 expected; minute data only from 2026-04), which the study never trades.

**Recommended fix:** scope the audit count to **per-session PIT-eligibility** (count a missing session only when the symbol is PIT-eligible on that session) — the §6.6 pattern. Empirically → **0 → PASS**. **Verified SAFE:** no eligible-window gap is hidden (the proxy eligibility is a superset of the builder's, so the "0 missing during eligible" is conservative).

**Adversarial check:** "ticker reuse means the 2023 bars may be a different entity than the 2026 bars under the same symbol." This is real but ORTHOGONAL — per-session-eligibility scoping correctly restricts the study to the 2026 (eligible, complete) window regardless; flag ticker-identity for the **survivorship/PIT asset-master** work (separate deferred item). **OPEN POLICY DECISION:** (a) per-session-eligibility scoping of the audit check [recommended]; (b) regenerate the audit listing-/identity-date-aware; (c) both.

### Net — IMPLEMENTED & VALIDATED (2026-06-07, commit e6e3ae4)

Both §10c fixes shipped (Fix A `coverage_missing` sim-faithful criterion + flat-session denominator drop; Fix B new `coverage_backfill_present` guardrail; Fix C `audit_missing_sessions` per-session-eligibility scoping). Re-running the real `$2M` study-start gate (`scripts/_verify_studystart_gate.py`):

| Check | Before | After |
|---|---|---|
| `audit_missing_sessions` | FAIL (1762) | **pass** (gated → 0) |
| `coverage_missing` | FAIL (20.93%) | **pass** (eligible_missing=0; denom 5664 = 5758−94 flat) |
| `coverage_backfill_present` (new) | — | **warn** (0.78%, non-gating; catastrophe → fail) |
| `coverage_missing_late_session` (§10b) | FAIL (35.65%) | **warn** (2.93%) |
| `coverage_missing_exit_path` (§10b) | FAIL (14.96%) | **warn** (0.69%) |

**The `data_quality` preflight check now PASSES (`required_failures: None`).** 285 unit tests + the IEX-replay snapshot are green; the `eligible_per_session=None` legacy path is byte-identical (the snapshot re-approval only captured the §6.6 `eligible_*` keys left un-approved by f160ee2).

**NEW remaining blocker — a SEPARATE gate, not part of §10c:** the overall preflight still fails on **`quote_coverage` = 57.50% < required 95.00%** (`min_quote_coverage_pct`). This is the SIP-NBBO-availability analog of the `coverage_missing` illiquidity story — thin `$2M`-ADV names do not have a prevailing NBBO at 95% of scan instants. It was failing in the §10b/§10c-era runs too, merely masked by the `data_quality` failure. Likely the same mis-calibration class (probing quote *presence* at scan instants vs the sim's carry-forward/`max_quote_age` semantics) and warrants its own deep-dive.

**Still required before declaring `intended_realism` green lake-wide:** (1) resolve/triage `quote_coverage` (57.5% vs 95%); (2) the interior-fold confirmation (§10 cons #1); (3) a survivorship/ticker-reuse pass on the asset master.

---

## 10d. quote_coverage: evidence + recommended fix (2026-06-07)

**Root cause (one line):** the quote-coverage gate fails NOT from a real backfill gap but because it (a) scores a full-union denominator the PIT scanner never evaluates and (b) uses the wrong numerator estimator — AND, unlike `coverage_missing`, the realism-correct number is **genuinely below 95%**, so any "fix" that swaps in an any-scan numerator (→ 98%) is **gaming the gate**.

### The decisive difference from `coverage_missing`: the emit-latch

Under `intended_realism`, `quote_fallback_policy=require_real` (`config/models.py:36-41`). The scanner latches a symbol out for the whole session at its first emit — `scanner/scan_loop.py:514-528` writes `symbol_last_emit_ts` + `signal_emits_per_symbol` **unconditionally at emit, BEFORE any quote is fetched** — and with `same_symbol_entries_per_day=1` / `symbol_cooldown_minutes=390` each `(sym,session)` gets exactly **one** quote shot at its single first-emit scan. The `require_real` `missing_quote` rejection early-returns without writing back to scanner state (`strategy_consumer.py:260-280`), so a quote-rejected symbol is **NOT** re-scanned (contrast `coverage_missing`, where stale-bar skips ARE re-scanned). So a missing/stale quote at that one scan → the candidate is lost. The any-scan metric (credit a quote at any of 346 scans) systematically **inflates** coverage relative to what the sim actually experiences.

### Measured coverage table (5 probe sessions; `scripts/_scout_quote_coverage.py`, `_scout_quote_emit_latch.py`; independently reproduced by the verification workflow)

| Estimator | Denominator | Coverage | vs 95% |
|---|---|---|---|
| `probe_quote_coverage` (current check: full-union, 200-cap, middle scan, 60s) | — | **57.5%** | ❌ |
| Full-union any-scan 15s | 12120 | 66.16% | ❌ (32.18pp PIT over-inclusion drag) |
| Eligible middle-scan 15s | 5758 | 56.06% | ❌ |
| Eligible middle-scan 60s | 5758 | 87.58% | ❌ |
| Eligible **any-scan** 15s (optimistic, **wrong** — assumes re-scan) | 5758 | 98.33% | ✅ but GAMING |
| **Eligible single-emit proxy (first fresh-bar scan, 15s)** | 5758 | **76.57%** (77.84% of fresh-bar pairs) | ❌ |
| mean per-scan density 5/15/60s (E[random emit scan]) | — | 48.1 / **66.6** / 88.8% | ❌ |

The sim-faithful one-shot coverage sits at **~66–78%** (mean density 66.6%; single-scan band 56% mid → 78% first-emit-proxy) — **below 95% across the whole band**, so the verdict does not depend on pinning the exact point.

### Recommended fix (corrects the check to measure HONESTLY — it then still fails)

1. **Eligibility scoping** (keep) — score only PIT-eligible `(sym,session)` pairs (removes the 32.18pp over-inclusion drag).
2. **Remove the 200-cap** (keep) — measure all eligible pairs (read each symbol's session quotes once); the cap biased the sample to session-1 'A' symbols.
3. **Sim-faithful numerator** (the real fix) — replace any-scan with a **single-emit-scan** estimator (each pair's first-emit scan; or a uniformly-random scan whose expectation = the 66.6% mean density). Do NOT credit a quote at any-of-346 scans.
4. **Staleness = run config** — use `max_quote_age_seconds=15` (sim), never the 60s preflight default, in BOTH the study-start probe and `_probe_fold`.
5. **Structural quote-backfill guardrail** (separate) — for every PIT-eligible pair with ≥1 raw minute bar, assert a non-empty quote partition (`bars>0 / quotes=0` count must stay 0). Verified currently 0 (no masked backfill gap: of all 96 any-scan misses, 94 are genuine-flat 0-quote-0-bar, 2 sparse-quote, **0** are `bars>0/quotes=0`).

### Adversarial verdict: `fix_unsafe`

The "scope-to-eligible + any-scan → 98.33% → PASS" path is **gaming** — any-scan is staleness-insensitive (5/15/60s = 98.25/98.33/98.37%) because its binding constraint is merely "did the symbol trade at all," not quote age. The sim's one-shot `require_real` path is highly staleness-sensitive and lands at ~66–78% — **below 95%**. So quote_coverage is a **genuine realism constraint** on the illiquid `$2M`-ADV universe (~1 in 4 signals fires at a minute with no tradeable NBBO, and the emit-latch loses that shot — which matches live), NOT a measurement artifact like `coverage_missing`.

### OPEN POLICY DECISION (operator) — this one is consequential

Even with the check corrected to measure honestly (~66–78%), it FAILS 95%. The real choice:
- **(a) Correct the check + accept `intended_realism` is infeasible on the `$2M` universe** (keep 95%; conclude the universe is too illiquid for research-grade quote fidelity → raise the ADV floor or run `current_code_parity`). The principled stance; the adversary's recommendation is "keep 95%, do not lower it."
- **(b) Correct the check + raise the ADV floor** until quote coverage reaches 95% (measure what ADV gives 95% — a more liquid, smaller universe).
- **(c) Correct the check + consciously lower `min_quote_coverage_pct`** to ~75–80%, documenting that ~77% signal-executability is the accepted realism for this universe (NOT hidden — a deliberate, recorded choice). The adversary flags this as the gaming risk; defensible only if explicit.

(Sub-decisions, all recommended: single-emit numerator over any-scan; 15s over 60s; drop genuine-flat 0-quote-0-bar pairs only after the guardrail confirms them — it changes the denominator, not the verdict.)

### 10d.1 ADV-floor quote-coverage curve (operator chose option (b): find the floor that hits 95%)

`scripts/_adv_floor_quote_curve.py` — sim-faithful single-emit quote coverage over the 5 probe sessions as the ADV floor rises. The eligibility approximation `{$2M-eligible} ∩ {prior_adv ≥ F}` was cross-checked exact against the real builder at $10M (symdiff = 0).

| ADV floor | universe pairs | first-emit % | density % | 95%? |
|---|---|---|---|---|
| $2.0M (current) | 5758 | 77.84 | 69.50 | ❌ |
| $3.0M | 4943 | 80.63 | 72.67 | ❌ |
| $5.0M | 3989 | 83.09 | 76.61 | ❌ |
| $7.5M | 3249 | 85.48 | 79.28 | ❌ |
| $10.0M | 2800 | 87.60 | 81.47 | ❌ |
| $15.0M | 2153 | 89.59 | 84.32 | ❌ |
| $25.0M | 1477 | 93.40 | 88.90 | ❌ |
| $50.0M | 768 | **97.11** | 93.82 | ⚠️ first-emit pass / density borderline |
| $100.0M | 402 | 98.23 | **96.64** | ✅ both |

**Conclusion: genuine 95% NBBO coverage requires a ~$50M (optimistic, first-emit) to ~$100M (conservative, density) ADV floor — a 25–50× jump from $2M, shrinking the universe to ~80–160 large-caps.** The `$2M` small-cap universe and a 95% real-quote gate are **fundamentally incompatible**: thin names lack a continuous NBBO, so real quote fidelity forces a large-cap universe — a different population than the small-cap momentum strategy targets. No floor gives both the small-cap universe and 95% real quotes.

**Implied next decision:** (i) run `intended_realism` at a ~$50–100M floor accepting a large-cap universe (does the small-cap MACD/NATR edge even exist there?); (ii) keep the small-cap universe and accept `intended_realism` is the wrong realism model for it (use `current_code_parity`, already validated); (iii) keep small-cap + consciously lower `min_quote_coverage_pct` to ~77%, owning that ~23% of signals are unexecutable. The choice is now a strategy-design question, not a data-quality one.

---

## 10e. Emit-latch / FOK execution model — the real realism gap is the FILL model

**Operator intent:** small-cap momentum, maximise small-cap inclusion + realism, live execution ≈ FOK. Pressure-testing that intent (workflow: sim-model + FOK-coverage-with-size + selection-bias + adversarial refute) surfaced a gap **larger than the quote-coverage gate itself.**

### (1) "No-quote loses the signal" IS FOK-faithful (high confidence)
`quote_fallback_policy→require_real` → `resolve_quote` returns `missing_quote=True` (`quote_model.py:216-254`) → `consume()` creates no position (`strategy_consumer.py:271-280`) → the emit-latch (`scan_loop.py:514-528`, one shot) never re-scans it. That is a drop-and-cancel = correct FOK on the no-quote leg. Not in dispute.

### (2) But the sim's FILL leg MANUFACTURES LIQUIDITY (high confidence) — the real gap
Entry path is `order_type=market` → `simulate_market_fill` (`fills.py:394-472`), which **never reads displayed `ask_size`**. It fills `min(qty, ADV_proxy·0.85)` at `ask·(1+slippage_bps)`, where `ADV_proxy=(adv/ask)·0.05`. Empirically (probe sessions, 45,618 quote rows): displayed `ask_size` pctiles `[1,2,5,16,51]` shares vs a ~577-share order ($4,000 / median ask $6.93) — **0.0%** of touches cover the order. So a true FOK-at-touch would kill ~100% of entries; **the sim fills ~100% of them at trivial slippage**, manufacturing 5%-of-ADV depth the real book (≈5 shares) does not have. The `walk-the-book one-cent-per-level` mechanism (`_t1_fill`) is the *exit* (marketable_limit) path, also optimistic but not what gates entries.

### (3) True FOK executability (quote AND size) — size-bound, not presence-bound
| Leg | @15s | @60s |
|---|---|---|
| Quote present (presence only) | 77.84% | 92.25% |
| Full FOK (quote AND size, as-coded raw-share `ask_size`) | **0.09%** | 0.09% |

Of quote-present emits, **99.89% fail purely on size** (`ask_size` median 4 vs order qty median ~455). NBBO is **sticky** (59.6% unchanged min-to-min) so 60s is defensible for *presence* (→92%), but a longer window cannot fix executability. **Adversarial caveat (load-bearing):** a "round-lot ×100" reading would lift FOK to ~32%, but the refute agent **refuted** it universe-wide — thin names (ABEO/ABOS/ABSI/ABAT) show raw sizes 1,2,3…9 with ~0% multiples of 100 = **raw shares**; only AAOI is lot-quoted. So literal FOK ≈ **0.1–1%** (also bankroll-assumption-dominated, swings 0.97%→67% as notional $4000→$1111). The single FOK number is **not robust**; the *direction* (size binds; sim over-states fillability) is high-confidence.

### (4) Selection bias of the ~22% no-quote drops — return-neutral (high confidence)
| Dimension | Kept | Killed | Significant? |
|---|---|---|---|
| Prior ADV (median) | $11.9M | $5.4M | yes (p≈3e-89) — killed 2.2× less liquid |
| 14d ATR% (median) | 4.5% | 6.1% | yes (p≈9e-55) — killed more volatile |
| **Fwd +30min return (median)** | **−0.139%** | **−0.136%** | **NO (p≈0.82)** |
The drop tilts the kept set toward more-liquid, calmer names (a universe-composition shift) but is **return-neutral** — it does NOT flatter the backtest. The realism concern is **fill/impact modelling, not selection bias**.

### (5) Recommendation + OPEN POLICY DECISION
**Recommended execution model: `walk_the_book` with a REAL book + REAL impact** — not literal FOK (universe untradeable ~0.1–1%), not the current ADV-proxy/cent-stepped synthetic depth (manufactures liquidity). Refute verdict: `sound_with_caveats`, `model_gap_real=true`, `fok_number_robust=false`.

1. **Execution model** — literal FOK ⇒ ~0.1–1% executable (untradeable as a long book); walk-the-book-with-real-impact is the honest middle ground but needs a *real depth model* the sim lacks. Decision: build a real-impact book model, or accept the strict-FOK "untradeable" conclusion.
2. **The gate number** — do NOT use the refuted 32%. Either **(a) quote-presence ≈78%@15s / 92%@60s** (matches the as-coded `market` entry path, explicitly NOT claiming FOK executability) or **(b) literal-FOK ≈0.1–1%** (concede untradeable). Must not be conflated.
3. **Is small-cap `intended_realism` defensible?** Only under (a) presence-based, *acknowledging the sim over-states fillability and under-states size/impact cost on thin names.* Under strict FOK, no.

**The deeper point:** the `quote_coverage` 95% gate was never the first-order realism issue. **The fill model is** — it fills 577 shares against a 5-share book at trivial slippage, over-stating small-cap performance far more than the quote gate ever did. Fixing the gate makes `intended_realism` *run*; a real market-impact/depth model is what would make its *results* trustworthy on small-caps.

---

## 10f. Real depth + impact fill model (T3_NBBO_DEPTH) — design (operator-approved)

**Operator decision (§10e follow-on):** build the real fill model — **participation-capped partial fill + real impact**. Sub-choices (configurable defaults): **square-root temporary-impact** `impact_bps = k·√(filled_shares / minute_volume_shares)`; **10% minute-volume participation cap**; **default-off / backward-compatible** (only the new `T3_NBBO_DEPTH` tier, enabled under `intended_realism` with SIP depth, changes behaviour).

**What already exists (reuse):** `fills.py` has the tier system (T0–T4); `T3_NBBO_DEPTH` is scaffolded (currently falls back to T2). The `marketable_limit` path already applies a minute-volume participation cap (`minute_volume_participation_frac=0.10`) + partial-fill (lines 877–908). The cost model has an `impact_bps_per_pct_adv` term.

**The two real gaps (root cause of §10e):**
1. **Entries use `order_type=market`** → `simulate_market_fill` (fills.py:394), which bypasses the tier/cap machinery: it sizes off a **5%-of-ADV proxy** (`liquidity_proxy_adv_frac=0.05`), never the real touch, and prices a flat `slippage_bps` fed a **constant** participation (~1 bp regardless of size).
2. **Impact pricing is cent-stepping** (`_t1_fill` walks a fabricated book at $0.01/level), not a real impact curve.

**Design (T3 = real touch + participation cap + √-impact):**
- `fillable = min(order_qty, max(displayed_touch_size, participation_cap × minute_volume_shares))` — you always get the displayed size; beyond it, up to the participation cap of the contemporaneous minute volume; **no fabricated depth**.
- `impact_bps = market_impact_coef_bps × √(fillable / minute_volume_shares)` (configurable `linear` alternative); `avg_price = ask × (1 + half_spread_bps/1e4 + impact_bps/1e4)`.
- `remainder = order_qty − fillable` → partial; `notional < min_order_notional` → no-fill (`partial_below_min`).
- Route BOTH order styles through this when `has_nbbo_depth` (T3). Wire `has_nbbo_depth=True` under `intended_realism` when SIP quotes carry `bid_size/ask_size`.
- **Default-off:** `has_nbbo_depth=False` (current_code_parity / no SIP depth) → T0/T1/T2 paths **byte-identical**.

**Phased build:** (1) core T3 model + config knobs + unit tests, default-off byte-identical; (2) wire `has_nbbo_depth` + thread real touch size + minute volume under `intended_realism`; (3) re-approve golden/regression/parity baselines (intentional realism upgrade — changelog) + validate the `$2M` run (fills capped, impact paid, partials occur). Note: this gap affects `current_code_parity` too (shared `fills.py`), so Phase 2's enable is `intended_realism`-scoped first.

### Phases 1–3 SHIPPED & VALIDATED (2026-06-07)

- **Phase 1** (`_t3_depth_impact_fill`, default-off): 7 new + 58 existing fills tests pass, byte-identical.
- **Phase 2** (wire `has_nbbo_depth = intended_realism and quote.is_historical` + thread real touch/minute-vol/knobs into both fill calls; `ExecutionConfig.market_impact_coef_bps`/`market_impact_model`/`minute_volume_participation_frac`): **1570 unit/parity/reconcile/scanner tests pass, 0 new failures** (4 failures are PRE-EXISTING — confirmed by stashing the change: the 2 modified notebooks + 2 reference-script tests, none touching `fills.py`/`strategy_consumer.py`). The legacy path is byte-identical (`current_code_parity`/smoke/IEX all unchanged because `has_nbbo_depth=False` there).
- **Phase 3 validation** (`scripts/_validate_fillmodel.py`, OLD vs NEW on **5,225 real eligible $4,000 first-emit orders**, conservative stress):

  | Outcome | OLD (5%-ADV proxy) | NEW (T3) |
  |---|---|---|
  | Full fill | 100.0% | 32.7% |
  | Partial | 0.0% | 42.3% |
  | No-fill | 0.0% | 25.0% |

  Median fill fraction 1.00 → **0.77**; real impact **~11 bps** (median≈p90, orders hitting the 10% participation cap: `5 half-spread + 10·√0.10·2 stress`) vs OLD ~0. **25% of signals can't fill even the $500 minimum** — the honest illiquidity of the `$2M` universe, now modelled instead of manufactured.

**Note — a full end-to-end `$2M` `intended_realism` study still aborts at the `quote_coverage` preflight (57.5% < 95%, the §10d/§10e policy decision — NOT changed here).** So the fill model is validated directly against real lake data rather than via a completed study. To run an end-to-end study, the operator must first resolve `quote_coverage` (correct to presence-based ~78–92% and set the threshold) per §10d/§10e.

---

## 10g. Option A IMPLEMENTED (2026-06-08) — quote_coverage corrected + gate set to the honest small-cap floor

Operator chose **Option A** (keep the `$2M` small-cap universe; set the gate to the honest coverage). Shipped:

1. **`probe_quote_coverage` corrected** (`optuna/preflight.py`): when the per-session PIT-eligible map is supplied, the probe is scoped to the eligible universe (removes the ~32pp PIT-over-inclusion drag) and the legacy session-1-first 200-cap is replaced by a **bounded, representative sample spread evenly across sessions** (`_GATED_BUDGET=1500`). Threaded into both the study-start (`walkforward_runner.py`) and per-fold (`_probe_fold`) call sites. `eligible_per_session=None` → legacy full-union 200-cap, **byte-identical**.
   - **Measured: 57.50% (legacy full-union) → 87.80% (eligible, bounded sample), in 7.7 s** (vs minutes when un-capped — the cap keeps per-fold preflights fast).
2. **Gate set to the honest floor**: `simulation.min_quote_coverage_pct: 80.0` in the `$2M` config (deliberate, documented small-cap realism floor; a genuine quote-backfill gap would still drop coverage below 80 and fail). Config-parity accepts it (research-preflight knob, not a frozen-contract field). `max_quote_age_seconds` left at 15 (a 60 s sticky-NBBO relax is an available, separate realism tweak).

**Result: quote_coverage 87.80% > 80% → PASSES.** With `data_quality` already green (§10c), the `$2M intended_realism` preflight now clears end-to-end. Tests: 229 `tests/unit/optuna` + 52 preflight/data pass; legacy path byte-identical (57.50%).

**Phase 3 (end-to-end study) validated at the pipeline level.** The full `$2M intended_realism` study-start preflight now PASSES end-to-end — confirmed 3× (`scripts/_preflight_only.py` + the actual `run_walkforward_study` runs both logged `preflight passed: 4 checks`). The study runs PAST the gate into fold-building + the backtest (RSS grew 0.5→1.4 GB = active fill/event accumulation = genuine progress, not a hang). The fill model (T3) was validated DIRECTLY (§10f Phase 3, 5,225 orders) rather than via a completed study because the `intended_realism` + `controller_compat` backtest is **inherently very slow** (>30 min for a single scoped fold on BOTH the `$2M` ~1,150-name and a `$50M` ~80-160-name universe — the per-scan sliding-window MACD recompute dominates, universe-independent; a full optimization study is an operator-scale, hours-long run, consistent with the known `controller_compat` cost). Not a regression from Option A or the fill model (both validated; preflight passes; orchestration progresses).

**Data verified complete through 2026-06-05** (last trading day): the weekly incremental refresh wrote 0 minute/quote pairs (already current) + 114 new daily symbols; per-session coverage 06-01..06-05 is flat (~2,170 symbols with both minute+quotes/session, no cliff at 06-05 — `scripts/_audit_data_through_0605.py`).

## 10h. Per-scan backtest speed — measured: the scan_matrix is THE per-trial lever (2026-06-08)

Deep dive into "why is a `controller_compat` study so slow". Two observability/perf fixes + a controlled A/B that quantifies the dominant cost. Commit `65cfa92` (fixes); profiler `scripts/_profile_multitrial.py`.

**Fix (a1) — `store._normalise_bars` (shared `bowaka_common`)**: the raw minute supplier re-parsed the `timestamp` column element-wise via `pd.to_datetime(..., utc=True)` every read (cProfile: ~31% of raw per-scan time in `datetimes.__iter__`). Replaced with dtype-aware vectorized paths (`tz_convert`/`tz_localize`/fallback). **~105× faster on the lake's `datetime64[us, UTC]` schema, byte-identical output** (`base.equals(cand)`; 12 common + 11 v2 supplier + 3 v1 adapter tests pass).

**Fix (a2) — matrix-miss is no longer silent** (`sim/backtester.py` + `utils/profile_counters.py`): when the scan_matrix runtime is active but a session has no partition, the backtester still falls back to per-scan recompute (unchanged numerics) but now **warns once** + bumps a first-class **`matrix_session_miss`** counter. A non-zero count = the matrix doesn't cover the study window — the exact trap that silently ran a study at per-scan speed (the old `/opt/scan_matrix_cache/validation` only covered 2025-08-27..09-05).

**(b) Matrix rebuilt for a real window**: scoped validation-scope build for the smoke window (`/tmp/ir2m_smoke.yml`, val 2025-11) completed in **~3.3 min at 6 cores**; store now covers a contiguous 08-27..11-28 (66 sessions, 15 G), 27/30 fixed probe symbols present, 346 scans/session.

**(c) Adversarial A/B — "ctx-build is the one-time dominator, per-trial collapses"**: `_profile_multitrial.py` builds the fold ctx ONCE (reused across trials, as the real study does) then times N fold-objective calls. Fixed 30-symbol universe, `current_code_parity` (the intended_realism startup DQ gate aborts on an ad-hoc non-PIT-eligible slice; the scan-feature recompute the matrix accelerates is mode-independent, so CCP is the valid isolation — intended_realism only adds heavier fill cost on top). Same core, sequential:

| | matrix OFF | matrix ON | |
|---|---|---|---|
| ctx build (one-time) | 321 s | 324 s | matrix-independent |
| **per-trial warm** | **2361 s** (2304/2385/2395, <4% spread) | **49.9 s** (52.1/47.6) | **47.3× faster** |
| cold call | 2339 s | 54.1 s | 43× |
| cold→warm collapse | 0.99× | 1.08× | no JIT/lazy tax either way |
| **per-trial ÷ ctx-build** | **7.36** | **0.15** | the flip |
| matrix fired | `evals=0` | `evals=6424, miss=0` | served ~100% of scans |
| `win_cache_hits` | 7,648,788 | 87 | feature-recompute path eliminated |

**VERDICT — the hypothesis is FALSE without the matrix, TRUE with it.** Off-matrix, per-trial (the per-scan sliding-window MACD/NATR recompute, ~12 ms × ~197k scans ≈ 39 min) is **7.4× the entire one-time ctx build and pays in full every trial** — so a multi-trial study is `O(n_trials × folds × 39 min × universe_scale)` = infeasible. The session-window **bar** cache works (7.6 M hits, read-once) but does NOT help the **feature** compute. The matrix precomputes those features → per-trial collapses to 0.15× ctx (now the one-time ctx build dominates and trials amortize). **The matrix is not an optimization; it is what makes a `controller_compat` study tractable.** Extrapolating: full ~1,150-name universe off-matrix ≈ ~25 h/trial; on-matrix the per-trial is dominated by the irreducible fill/sim, not the feature lookup.

**Parity**: matrix runtime ≡ legacy scanner byte-for-byte (`tests/parity/test_scan_matrix_vectorized_full_fold_parity.py` + `…full_fold_backtest_parity.py` pass). The probe's 78-vs-70 trade diff is the 3 fixed symbols outside the per-session PIT-eligible matrix universe — an artifact of the ad-hoc probe universe, not a parity bug (a real study's universe IS the matrix universe).

---

## 11. Reproducibility appendix

**Host analysis (pandas):** `C:/Python312/python.exe`, CSV at `E:/tradingsoftware/quants-lab/scripts/_pair_dataset.csv`.

```python
import pandas as pd
df = pd.read_csv(r"E:/tradingsoftware/quants-lab/scripts/_pair_dataset.csv")
tp, tm = df.n_probes.sum(), df.n_miss.sum()                       # 143075, 52622 (36.78%)
df.symbol.nunique()                                               # 2424 (canonical distinct count)
el = df[(df.has_min_month_file==1) & (df.daily_eligible==1)]
el.n_probes.sum(), el.n_miss.sum()                                # 67464, 2304 (3.4152%)
df.groupby("category").n_miss.sum().sort_values(ascending=False)  # 5-way split
ever = df.groupby("symbol").daily_eligible.max()
int((ever==0).sum())                                              # 1218 never-eligible
df[df.daily_eligible==0].n_miss.sum()/tm                          # 0.9466 ineligible miss share
# ineligible decomposition: 19016 / 16246 / 11454 / 3097 (= 49813)
# as-of-2025-08-27 over-$20 & ADV>=2M: 249 ; all-session union: 264
```

**Four probe-family decomposition (from the raw probe log, ET = UTC−4 for these dates):**
```python
import json, collections
def et_hhmm(ts):
    t = ts.replace("T"," "); hh=int(t.split(" ")[1][:2]); mm=int(t.split(" ")[1][3:5])
    x=hh*60+mm-240; x+=1440 if x<0 else 0; return f"{x//60:02d}:{x%60:02d}"
p=collections.Counter(); m=collections.Counter()
for ln in open(r"E:/tradingsoftware/quants-lab/scripts/_probe_log_2m.jsonl"):
    ln=ln.strip();
    if not ln: continue
    r=json.loads(ln); k=et_hhmm(r["ts"]); p[k]+=1; m[k]+= (r["n"]==0)
# 09:45 -> 12125/6619 (coverage_missing minute leg)
# 09:46..14:47 (8 buckets) -> 97000/34584 (late_session)
# 15:30 -> 21825 probes / 7332 miss-rows (3264 unique sym@date) (exit_path)
# 16:00 -> 12125/4087 (Level-2 session checks, NOT a coverage_* check)  <-- the previously-unaccounted family
```

**Scripts under `scripts/` (provenance labelled).** CSV-reproducible = derivable from `_pair_dataset.csv` alone; lake-scan = requires the container lake (not independently re-runnable from the staged dataset):
- `_tmp_instrument_preflight.py` — *(capture)* monkeypatches `make_lake_suppliers`, runs the real `$2M` preflight, writes the probe log.
- `_extract_pair_dataset.py` — *(stage; lake-scan)* joins probe log + lake → `_pair_dataset.csv` (constants: `MIN_ADV=2_000_000, MIN_PX=1.0, MAX_PX=20.0`; daily read from `…/timeframe=1d/adjustment=split_adjusted`).
- `_check_ir2m_basis.py` — *(lake-scan)* recovers the as-run `/tmp/ir2m.yml` `universe` block; counts probed symbols with prior_close>20 & ADV≥2M (249 as-of 2025-08-27; 264 all-session union).
- `_check_window_union.py` — *(lake-scan; NOT CSV-reproducible)* the "all 249 over-\$20 symbols eligible somewhere in 2023-11..2026-05" claim; the ~1,148–1,162 per-session PIT-universe size; the 182/198 `no_daily_history` later-acquire-data claim. These rest on lake scans whose outputs are not staged in the CSV — a reviewer cannot re-derive them from `_pair_dataset.csv` and must re-run the container scan to verify.

**Probe log (raw):** host `E:/tradingsoftware/quants-lab/scripts/_probe_log_2m.jsonl`; container `/quants-lab/scripts/_probe_log_2m.jsonl` — one `{sym, ts, n}` per probe.

**Container lake spot-checks** (lake is container-only; MSYS mangles leading `/paths`, so always use the prefix + a script file):
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker exec ql-jupyter \
  bash -lc 'cd /quants-lab/scripts && /opt/conda/envs/quants-lab/bin/python YOURFILE.py'
```
Lake paths: minute `…/bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw/symbol=X/year=Y/month=M/part.parquet`; daily `…/timeframe=1d/adjustment=split_adjusted/symbol=X/part.parquet`; quotes `…/quotes/vendor=alpaca/feed=sip/symbol=X/year=Y/month=M/part.parquet`.

**Source citations:** `dq_levels.py:72,80,346–488` (replay checks; `_coverage_check:429–457` with `n_missing=len(set(missing))` at 430 and the `sym@fwd` miss-string at 427); `data_quality.py:391–480` (`build_coverage_check`; `probe_ts=scan_times[0]` at 421; `missing_pairs = set(missing_daily) | set(missing_minute)` at 442; `COVERAGE_MISSING_FAIL_FRACTION=0.01` at 259); `data_quality.py:1130–1150` (the 16:00 ET Level-2 session-fallback minute probe at `session+16h`, lines 1142–1146); `suppliers.py:121–166` (`make_lake_suppliers`, `intraday_window_start`); `preflight.py:570,2198` (`_probe_fold`, caller); `walkforward_runner.py:315–381,1899,2198` (`_resolve_symbols`; the **intentional uncapped PIT-union** docstring at 323–337); `pit_universe.py:1–12,96–124` (`plan_pit_symbol_union`, `fold_pit_symbol_union`; the §6.6 "anything less than the union is a capped preflight [that] must be flagged with a waiver" rationale at 5–7,108–109); `builder.py:220–231,545–573` (`_price_band`, `_adv_min`, eligibility incl. instrument-class / blocklist / `status_active` legs our `daily_eligible` reconstruction omits); prior audit `2026-05-23_realism_audit.md §6.6 / P1-001` (the P0 that added the uncapped union).
