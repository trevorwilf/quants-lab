# Quarantined configs

Configs in this directory are **not valid** for any backtest, optimization, or
promotion run. They are kept only as forensic / historical artifacts.

## Quarantine policy

A config is quarantined when it is unsafe to run — typically because it claims a
`simulation.mode` (e.g. `current_code_parity`) that it does not actually honor,
or it materially diverges from the frozen live-strategy contract
(`reference/actual_bowaka_v2_contract.yaml`) without a declared parity sidecar.

Quarantine mechanics:

- The file is renamed with a `__DO_NOT_USE` suffix and moved into
  `configs/quarantined/`.
- A `# QUARANTINED <date> — <reason>` banner is prepended (it is a YAML comment,
  so `yaml.safe_load` still parses the body — tests may use it as a base).
- The standard config loader
  (`bowaka_v2_lab.config.loader.load_config`) **refuses to load any path under
  `configs/quarantined/`**, raising a `ValueError` with a "quarantined" message.
  This is the hard gate: a quarantined config cannot reach the backtester,
  the Optuna runner, or the CLI.
- The shipping-config test globs (`configs/bowaka_v2_*.yml`) are non-recursive,
  so a quarantined file is no longer discovered as a shipping config.

A quarantined config is **not** un-quarantined by editing it — it is superseded
by a freshly generated, contract-parity replacement (see the Realism
Remediation 2 plan, Phases 1 and 8).

## Current contents

| File | Quarantined | Reason |
|---|---|---|
| `bowaka_v2_walkforward_optuna__DO_NOT_USE.yml` | 2026-05-22 | Claimed `current_code_parity` while materially changing execution / sizing / risk / stop / target / hold period vs the live contract. See `docs/audits/2026-05-22_realism_audit.md` §P0-001. Replacement Optuna configs are generated in Realism Remediation 2 Phase 8. |
