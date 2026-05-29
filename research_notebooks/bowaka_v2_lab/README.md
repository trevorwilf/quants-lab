# Bowaka v2 Lab — Research-Only QuantsLab Integration

> ⚠️ **Research and backtesting only.** This package does NOT promote any
> strategy variant to paper or live trading. Promotion to higher tiers
> (paper / live) requires SIP-validated walk-forward results and paper-vs-sim
> reconciliation, neither of which can be produced from this lab in isolation.

## Active audit blockers (2026-05-23)

A third realism audit
([`docs/audits/2026-05-23_realism_audit.md`](docs/audits/2026-05-23_realism_audit.md))
re-tested the lab after the prior two remediations and found the defects below
still live in code. Remediation 3 (this branch series) closes every code-
addressable P0/P1/P2 finding; the lake-ingestion / paper-recon work is
explicitly out of scope and tracked in the audit itself.

- **P0-001** — an all-sentinel Optuna study (every trial scored
  ``_FAILED_TRIAL_SCORE``) used to complete with ``status: "ok"`` and a
  non-empty ``best_params``. After Phase 0 the runner validates the completed
  trial set and raises ``OptunaStudyInvalidError`` when zero valid trials
  exist.
- **P0-002** — ``HoldoutGuard`` used closed-interval semantics; the walk-
  forward planner uses half-open ``[start, end)``. Boundary-equal folds were
  rejected by the guard, then swallowed by the objective. The guard is now
  half-open.
- **P0-003** — preflight DQ / quote-coverage probes failed open under
  ``intended_realism``. They now fail closed: a ``None`` DQ report or a probe
  exception fails the run.
- **§6.6** — preflight under ``intended_realism`` used a 100-symbol cap. Phase 1
  expands it to the full per-fold PIT eligible-universe union (or fails closed
  on a missing waiver).
- **P0-004 / P0-005** — Phase 1 adds the ``bowaka-v2-lab verify-lake`` CLI; the
  ingestion itself is operator-owned and out of scope.
- **P1-002** — the frozen contract now hashes the strategy/scanner/features/
  schemas/backtest source files via a ``source_manifest`` (Phase 2).
- **P1-003** — generated optuna configs now expose every live ``scanner:`` key
  (Phase 2); ``StrategyConsumer`` reads ``same_symbol_entries_per_day`` from
  the scanner block, not from risk.
- **P1-004** — risk-control parameters stay in the Optuna search space, but a
  promotion-gate refusal caps the effective tier at ``research_only`` when the
  candidate moves any risk control beyond epsilon from the incumbent (Phase 3).
- **P1-006** — ``OPTUNA_STORAGE=sqlite:///…`` relative paths are now resolved
  against the lab root, not the launch CWD (Phase 3).
- **P2-001** — stale ``config/models.py`` defaults removed / aligned (Phase 3).
- **P2-002** — new ``optuna_smoke`` / ``paper_reconcile`` pytest markers (Phase 3).

P1-005 (fill calibration) and P1-009 (paper reconciliation) require real paper
logs and stay deferred. The promotion checklist (audit §12) is the gate for
``main`` and is **not** closed by remediation 3.

## Active audit blockers (2026-05-22)

A second realism audit
([`docs/audits/2026-05-22_realism_audit.md`](docs/audits/2026-05-22_realism_audit.md))
found that the lab can still **optimize the wrong strategy**: the prior
`configs/bowaka_v2_walkforward_optuna.yml` claimed `current_code_parity` while
materially changing execution, sizing, risk, stop/target and hold period
(audit §5 P0-001). That config is now **quarantined** under
[`configs/quarantined/`](configs/quarantined/README.md) and the standard config
loader refuses to load it. Until the "Realism Remediation 2" phases land, treat
the lab as research-only simulator infrastructure under development — see the
audit for the full P0/P1 finding list.

**Strategy identifier:** `bowaka_v2`

**Feed policy:** the IEX feed is acceptable for research / methodology checks
but cannot support any promotion claim. Configurations explicitly select
`market_data.feed` between `iex` and `sip`; any configuration using `iex`
is automatically capped at the `research_only` suitability tier by the
promotion gate.

## Installation

```bash
cd research_notebooks/bowaka_v2_lab
pip install -e .[dev]
```

## Environment variables

Copy `.env.example` to `.env` and populate. Required:

- `MONGO_URI` — MongoDB connection string (auth source `admin`).
- `BOWAKA_V2_SOURCE_ROOT` — absolute path to the read-only v2 archive.

Optional:

- `BOWAKA_V2_PAPER_LOGS_ROOT` — absolute path to paper-trading log root used by
  Phase 7 reconciliation tests.
- `ALPACA_API_KEY_ID` / `ALPACA_API_SECRET_KEY` / `ALPACA_PAPER` /
  `BOWAKA_V2_ALPACA_FEED` — only required by tests marked `live_alpaca`.
- `MARKET_DATA_ROOT` — override the shared market-data lake root (unset →
  `research_notebooks/market_data`).

## Quick start

```bash
# 1. Verify environment + config
python -m bowaka_v2_lab.cli env-check --config configs/bowaka_v2_backtest_smoke.yml

# 2. Run unit tests
python -m pytest tests -q --tb=short -m "not live_alpaca and not slow"
```

## Linked reference

The companion design document is `bowaka_v2_quants_lab_integration_plan_revised.md`
(supplied by the operator). All cross-references in source are written as
`[Report §X.Y]`.

## Architecture (one paragraph)

`bowaka_v2_lab` is the strategy lab; `bowaka_common` (sibling package) is the
strategy-neutral data / artifact / research infrastructure. Both labs
(`bowaka_lab` for v1, `bowaka_v2_lab` for v2) consume `bowaka_common`. No
cross-strategy imports are permitted; tests under `tests/repo/` enforce this
at the repository level.

## Shared market-data lake

v2 reads real Alpaca data from the shared lake (`bowaka_common.marketdata`)
rather than a v2-private store. Set `market_data.minute_bar_source` /
`daily_bar_source` to `alpaca` in a config and `bowaka_v2_lab.data.loaders`
delegates to `MarketDataStore`; `market_data.shared_root` (or the
`MARKET_DATA_ROOT` env var) selects the lake root, defaulting to
`research_notebooks/market_data/`. The `bowaka_v2_lab.data.suppliers` helpers
(`make_lake_suppliers`, `build_daily_cache_from_lake`) feed the backtester, and
notebooks switch between the synthetic fixture path and the lake based on the
config. The smoke config keeps `*_source: fixture`. The lake root is **not**
routed through `BowakaV2Paths`, so strategy isolation is unaffected.

## Bayesian-optimization fix verification

After the audit 2026-05-29 Phases 0-3 remediation (fail-closed study-validity
gates, daily-adjustment threading + current-code-parity full-fold preflight,
incumbent mapping + search-space v3, structured promotion evidence, resolved-
config persistence + debug escalation), run the verification CLI to emit the
operator-pasteable PASS/FAIL report:

```bash
cd research_notebooks/bowaka_v2_lab
python -m bowaka_v2_lab.cli verify-bayesian-fix \
    --config configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml \
    --n-trials 3
# Prints `VERIFICATION_REPORT: <path>` and `OVERALL: PASS|FAIL`, and writes a
# Markdown report under artifacts/verification/. Copy the report and send it to
# the planner agent for sign-off before unblocking Phases 4-7. Add
# `--skip-short-run` to emit only the (fast, deterministic) P0 PASS/FAIL grid
# without the 3-trial study short-run.
```

A single FAIL anywhere blocks promotion to Phases 4-7.
