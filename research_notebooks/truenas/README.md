# `truenas/` — local mirror of the TrueNAS Gluetun Jupyter environment

> **Note to Claude Code (read this first, every time you touch this folder).**
> This file exists to remind you what this folder is and how to work in it.
> Read it before creating or editing anything under `research_notebooks/truenas/`.

## What this folder is

A **local staging copy** of the Jupyter Lab environment that runs **inside the
Gluetun VPN container on the TrueNAS server**. The real environment lives on the
server here:

```
\\192.168.1.54\apps\hummingbot\jupyter\notebooks
```

(`192.168.1.54` is `TRUENAS_LAN_IP`. That Jupyter Lab is where the labs actually
run — inside Gluetun, on the Trading Pod.) The local `notebooks/` subfolder here
mirrors the server's `notebooks/` directory.

## Why it exists — the access gap

Claude Code **cannot reach the server's Jupyter environment directly**, so it
can't help edit or run things in place. This folder bridges that gap:

1. **You (Trevor) and I author / edit files here**, in this local folder, where I
   have full read/write and can run tooling.
2. **You copy the finished files up** to
   `\\192.168.1.54\apps\hummingbot\jupyter\notebooks` (the Gluetun Jupyter share).
3. **You run the labs there**, inside the VPN'd Jupyter Lab.
4. When useful, **you copy results/outputs back down** into this folder so I can
   read logs, artifacts, and outputs and help iterate.

Think of this folder as "the desk where we prepare and review the work," and the
TrueNAS Jupyter share as "the lab bench where it actually runs."

## Current access status (probed 2026-07-13)

- The host `192.168.1.54` **is up** (ping OK) and SMB **does** work to it —
  `\\192.168.1.54\trevorshare` is already mapped as drive `Z:`.
- The **`apps` share is NOT reachable** from my environment. `\\192.168.1.54\apps`
  and `\\192.168.1.54\apps\hummingbot\jupyter\notebooks` both fail `Test-Path` and
  don't enumerate — the `apps` share isn't permitted to this session, even though
  the box and other shares are fine.
- **Bottom line:** today the only bridge is **manual copy** (steps above).
- **If that ever changes** — i.e. the `apps` share is permitted for this account
  or mapped to a drive letter — I could read/write the Jupyter files directly, and
  the manual copy step could be dropped. Re-test with:
  `Test-Path '\\192.168.1.54\apps\hummingbot\jupyter\notebooks'`.

## What's in here now (snapshot copied 2026-07-13)

The full server tree was dropped in — **~514 MB, ~6,400 files**. Most of it is
bulk data and run output that is git-ignored (see below). The parts that matter:

> **Base-dir cleanup (2026-07-13).** The base `notebooks/` directory used to hold
> an older oscillator-finder lab (KRAKEN/NONKYC finder notebooks v1–v11 + a
> duplicate `ladder_lab*.py` engine + caches/artifacts). That whole line was
> **removed** — it had already diverged from and been superseded by
> `range_ladder/`, which is self-contained. Its design-notes markdown was moved
> into `range_ladder/`. The base dir now holds just the ladder lab
> (`range_ladder/`), the doc scraper, the API-validation notebooks, and `_private/`.

### 1. `notebooks/range_ladder/` — the ladder / oscillator finder lab ⭐ (canonical, only copy)
The active body of work: the `range_inventory_ladder` engine registered in
`pmm_lab`. Fully self-contained — the notebooks use plain `import ladder_lab*`
which resolves to the copies **inside** `range_ladder/`, and all file I/O stays
local to that folder.

- **Engine (import chain):** `ladder_lab.py` (adapters) → `ladder_lab_recycle.py`
  (v10) → `ladder_lab_recycle_v11.py` (v11). Plus `ladder_lab_robust.py`.
  **All must stay together, unchanged** — v11 imports v10 and the adapters and
  asserts bit-for-bit v10 parity on every run.
- **Tests:** `test_recycle_v11.py` — *run this first on the server after any engine edit.*
- **Notebooks:** `KRAKEN_Crypto_oscillator_finder_v9.ipynb`,
  `NONKYC_Crypto_oscillator_finder_v11.ipynb`, `Ladder_backtest.ipynb`.
- **Notes (design docs):** `LadderLab_v11_notes_claude_code.md` is the current,
  best single explainer of the engine (true holdout, clean-block gating,
  volume-capped partial fills, order-book-depth truth, model-free `grid_harvest`
  pair ranking). Also `LadderLab_v10_recycle_notes_claude_code.md`,
  `robust_ladder_notebook_upgrade_report.md`, and
  `LadderLab_v11_notes_claude_code_base_older.md` (the superseded base-dir v11 notes,
  kept for history — the un-suffixed one is authoritative).
- `controllers/` — hand-authored live deployment YAMLs (kraken + nonkyc). Small,
  source-like, **tracked**.
- `artifacts/`, `diagnostics/`, `_ladder_cache/` — run outputs, live JSONL logs,
  and OHLCV cache. Large and regenerated — **git-ignored**.

### 2. `notebooks/getdocumentation/` — exchange API-doc scraper (separate sub-project)
Scrapes + validates MEXC spot/futures and NonKYC API docs into an offline bundle.
Entry points: `scrape_exchange_docs.py`, `scrape_websites.py`; see
`README_exchange_docs_engineering_reference.md`. **Its redaction is incomplete** —
it strips IDs/addresses but leaves real trade prices/quantities — so the raw
private response dumps and the generated docs that embed them
(`mexc_spot_v3.md`, `mexc_futures.md`, `nonkyc.md`, `observed_schemas.md`,
`validation_report.md`) were **quarantined into `_private/`** (see below). What
stays here is public: `sources/`, `webscrape/`, the scraper scripts, and the meta
reports. The private docs regenerate by re-running the scraper on the server.

### 3. API / WS validation notebooks — `notebooks/`
`mexc_api_ws_validation_notebook.ipynb`, `nonkyc_api_ws_validation_notebook.ipynb`,
`nonkyc_mexc_APISTUB.ipynb`. Credentials come from `os.environ` (no hardcoded keys).

### 4. `notebooks/_private/` — quarantined personal / bulk data (git-ignored)
Everything with personal-financial-holdings info or bulk regenerable data was moved
here on 2026-07-13 (see `_private/README.txt`): crypto-tax backups, wallet
histories, a balances notebook, `db_backup.ipynb`, ~100 MB of raw CSV extracts, and
the getdocumentation private dumps + generated docs. **Never commit this.** Originals
live on the server.

## Git hygiene — IMPORTANT

This folder has its own **`.gitignore`**. The rule: **track only source** — engine
`.py`, notebooks, `.md` notes, and small hand-authored configs (`controllers/*.yml`)
and report CSVs. Everything bulky, regenerated, or personal is ignored. After the
ignore rules + the 2026-07-13 cleanup, the trackable set is **~4.7 MB / ~99 files**
(down from 514 MB; ~374 MB still on disk, almost all git-ignored `.Trash-0/` and
`_private/`).

Ignored here (in addition to the repo-root's `__pycache__/`,
`.ipynb_checkpoints`, `.Trash-0/`):

- `notebooks/_private/` — the personal / bulk quarantine folder
- `_ladder_cache/` + `*.npz` — OHLCV cache
- raw per-pair CSV extracts (`ETH-USDT_*.csv`, `SOL-USDT_*.csv`, `xmr_usdt_*.csv`)
- `artifacts/`, `diagnostics/` — regenerated run output
- `*.zip`, `*.gz` — archives / compressed dumps
- `logs/backup/`, `*.xlsx` — **personal financial data, must never be committed**

If you add a new kind of bulk/personal file, extend `.gitignore` before committing.
**Never `git add -A` this tree blindly** — always confirm what would be staged
(`git status`, `git ls-files --others --exclude-standard research_notebooks/truenas/`).

## Working here — checklist for Claude Code

- **Author and edit locally.** Do the real work in this folder; don't try to run
  it — the actual run happens on the server after Trevor copies it up.
- **The ladder lab lives only in `range_ladder/`** now — edit the engine/notebooks
  there. (The old base-dir duplicate was removed 2026-07-13.)
- **Be copy-friendly.** Files here get hand-carried to the server, so keep paths,
  imports, and relative references sane for the *server* side (Jupyter runs with
  the `notebooks/` tree as its root; scripts reference `/notebooks/...`).
- **State the copy step.** When you finish something meant to run on the server,
  remind Trevor which file(s) to copy up to
  `\\192.168.1.54\apps\hummingbot\jupyter\notebooks`.
- **Ask for pulled-back outputs.** If you need to see how a run went, ask Trevor to
  copy the relevant logs/artifacts back down into this folder.

## Don't confuse this with other Jupyters

There is also a **local desktop Jupyter** from `quantslab_desktop_compose.yaml`
(the `ql-jupyter` container) used for the `pmm_dynamic` / `bowaka_v2` work. That is
a *different* environment. **This folder is specifically about the TrueNAS Gluetun
Jupyter share** at the path above — the one running inside the VPN on the Trading
Pod.
