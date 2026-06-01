# Shared Market-Data Lake — Operator Runbook

> **Provenance.** Extracted verbatim from the "Operator Runbook" section of the Claude
> Code prompt `bowaka_shared_marketdata_lake_claude_code_prompt.md` (now archived at
> `docs/old_cc_prompts/`, gitignored). See `_marketdata_implementation_summary.md` for
> what the automated phases delivered. These steps are **manual** — they move the real
> ~301k-file dataset and were intentionally left out of any automated phase.

---

## Operator Runbook (manual — run after Phase 5 is merged)

The lake lives in-repo at `research_notebooks/market_data/`, already visible inside `ql-jupyter` (the repo is mounted at `/quants-lab`) — **no Docker mount or restart is needed.** These steps move the real data and are not part of any automated phase.

1. **Migrate the data** — run inside `ql-jupyter` (it has pyarrow):
   ```bash
   docker exec ql-jupyter bash -lc 'cd /quants-lab && python scripts/migrate_market_data.py \
     --source research_notebooks/bowaka_lab/db_tools/bowaka_data/parquet \
     --dest research_notebooks/market_data --verify-only'   # dry inspection first
   # then drop --verify-only for the real run
   ```
   Review `research_notebooks/market_data/_ingestion/migration_report.json` — counts and hashes must match.
2. **Smoke-test both labs on real data.** Run a v2 notebook with an IEX research config; run a v1 backtest. Confirm bars load from the lake.
3. **Reclaim space.** Once verified, delete `research_notebooks/bowaka_lab/db_tools/bowaka_data/` (the old duplicate). Keep a backup until fully confident.
4. **Relocate later (optional).** To move the lake off-repo (e.g. a shared drive for other projects), set `MARKET_DATA_ROOT` in the repo-root `.env` to the new path and move the directory — no code change.
5. **Future re-backfills** go straight to the lake via `bowaka_common.marketdata.backfill`; the v1 `bowaka_backfill.ipynb` still works (it shims through).

> **Note on `.gitignore`.** The two lines ignoring
> `research_notebooks/bowaka_lab/db_tools/bowaka_data/parquet/{bars,assets}/*` are kept
> until step 3 above is done (the legacy ~301k-file tree still exists on disk; removing
> the ignore early would expose 301k untracked files). Remove those two lines once that
> directory is deleted.
