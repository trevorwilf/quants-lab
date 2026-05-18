"""Markdown report assembler.

Implements the 17-section structure from ``[Report §20.1]``:

  1. Run metadata
  2. Data source and feed limitations
  3. Universe mode and survivorship-bias warning
  4. Config hash and dataset hashes
  5. Prefilter funnel
  6. Candidate rank diagnostics
  7. Trade performance summary
  8. Exit reason summary
  9. MFE/MAE analysis
  10. Entry timing counterfactuals
  11. Exit surface counterfactuals
  12. Signal-fade threshold comparison
  13. Liquidity bucket analysis
  14. Paper-vs-backtest reconciliation, if available
  15. Known limitations
  16. Stop-ship / research-only status
  17. Exact next actions

Disclaimers (per §20.2):
- IEX-feed runs include the §20.2 IEX disclaimer verbatim.
- Paper-reconciliation runs include the §20.2 paper-trading disclaimer verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from tabulate import tabulate


IEX_DISCLAIMER = (
    "This report uses Alpaca IEX data. IEX is a single-exchange feed and is not "
    "consolidated SIP data. Results are exploratory and should not be treated as "
    "final evidence of live profitability, especially for volume, RVOL, VWAP, "
    "spread, quote-age, and liquidity-dependent decisions."
)

PAPER_DISCLAIMER = (
    "Paper-trading fills are simulated and do not account for market impact, "
    "information leakage, latency slippage, queue position, price improvement, "
    "regulatory fees, or dividends. Paper fills can be useful for software "
    "behavior validation but are not proof of live execution quality."
)


SECTION_HEADERS: list[str] = [
    "1. Run metadata",
    "2. Data source and feed limitations",
    "3. Universe mode and survivorship-bias warning",
    "4. Config hash and dataset hashes",
    "5. Prefilter funnel",
    "6. Candidate rank diagnostics",
    "7. Trade performance summary",
    "8. Exit reason summary",
    "9. MFE/MAE analysis",
    "10. Entry timing counterfactuals",
    "11. Exit surface counterfactuals",
    "12. Signal-fade threshold comparison",
    "13. Liquidity bucket analysis",
    "14. Walk-forward optimization (Optuna)",
    "15. Paper-vs-backtest reconciliation",
    "16. Known limitations",
    "17. Stop-ship / research-only status",
    "18. Exact next actions",
]


@dataclass
class ReportInputs:
    run_id: str
    config_hash: str
    dataset_hashes: dict[str, str] = field(default_factory=dict)
    data_vendor: str = "alpaca"
    data_feed: str = "iex"
    adjustment: str = "raw"
    universe_mode: str = "alpaca_current_assets"
    prefilter_metadata: dict[str, Any] = field(default_factory=dict)
    #: Optional aggregated funnel from
    #: ``bowaka_lab.features.prefilter.aggregate_prefilter_funnel``. When set,
    #: Section 5 reads from this dict (unprefixed keys); otherwise it falls
    #: back to ``prefilter_metadata`` (which uses ``n_`` prefixes from a
    #: single-session ``CandidateSet``).
    prefilter_funnel: dict[str, Any] | None = None
    candidate_rank_distribution: pd.DataFrame | None = None
    trades: pd.DataFrame = field(default_factory=pd.DataFrame)
    counterfactuals: pd.DataFrame = field(default_factory=pd.DataFrame)
    reconciliation: pd.DataFrame | None = None
    #: Per-trade signal-fade evaluations from notebook 07. When provided,
    #: Section 12 renders a bucket distribution from this frame instead of the
    #: variant-threshold view derived from ``counterfactuals``.
    signal_fade: pd.DataFrame | None = None
    #: Tidy liquidity-bucket summary from notebook 08
    #: (e.g. ``bucket, trades, win_rate, median_pnl_pct, stop_gap_rate``).
    #: When provided, Section 13 renders this directly instead of
    #: re-bucketing from ``trades``.
    liquidity: pd.DataFrame | None = None
    #: ``optuna_best.json`` payload from notebook 10. When non-empty, Section 14
    #: renders the study summary and Section 17's ``walk_forward_not_run`` flag
    #: clears. Operators can also set :attr:`has_walk_forward` explicitly.
    optuna_best: dict[str, Any] | None = None
    #: Per-trial table from notebook 10 (``optuna_trials.parquet``). When
    #: present, Section 14 also renders the top-N trials by objective value.
    optuna_trials: pd.DataFrame | None = None
    has_walk_forward: bool = False
    known_limitations: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)

    def __post_init__(self):
        # Derive has_walk_forward from optuna_best when caller didn't set it.
        if not self.has_walk_forward and self.optuna_best:
            n_trials = int(self.optuna_best.get("n_trials") or 0)
            best = self.optuna_best.get("best_value")
            if n_trials > 0 and best is not None:
                self.has_walk_forward = True


def _md_table(df: pd.DataFrame, *, max_rows: int | None = None) -> str:
    if df is None or df.empty:
        return "_no data_"
    out = df if max_rows is None else df.head(max_rows)
    return tabulate(out, headers="keys", tablefmt="github", showindex=False)


def research_status_flags(inputs: ReportInputs) -> list[str]:
    flags: list[str] = []
    if inputs.data_feed == "iex":
        flags.append("iex_feed_exploratory")
    if inputs.universe_mode == "alpaca_current_assets":
        flags.append("current_universe_survivorship_biased")
    if not inputs.has_walk_forward:
        flags.append("walk_forward_not_run")
    if inputs.reconciliation is not None and "implementation_mismatch" in set(inputs.reconciliation.get("classification", pd.Series([], dtype=str))):
        flags.append("paper_implementation_mismatch_unresolved")
    return flags


def build_markdown(inputs: ReportInputs) -> str:
    parts: list[str] = []
    parts.append("# Bowaka Backtest Report\n")
    parts.append(f"**Run ID:** {inputs.run_id}  ")
    parts.append("**Status:** RESEARCH_ONLY  ")
    parts.append(f"**Data vendor/feed:** {inputs.data_vendor.title()} / {inputs.data_feed.upper()}  ")
    parts.append(f"**Universe mode:** {inputs.universe_mode}  ")
    parts.append(f"**Config hash:** `{inputs.config_hash}`  ")
    if inputs.dataset_hashes:
        parts.append("**Dataset hashes:**")
        for k, v in inputs.dataset_hashes.items():
            parts.append(f"- {k}: `{v}`")
    parts.append("\n> This report is exploratory. It does not establish live-trading readiness.\n")

    if inputs.data_feed == "iex":
        parts.append(f"\n> {IEX_DISCLAIMER}\n")
    if inputs.reconciliation is not None and not inputs.reconciliation.empty:
        parts.append(f"\n> {PAPER_DISCLAIMER}\n")

    parts.append(f"\n## {SECTION_HEADERS[0]}\n")
    parts.append(f"- Generated at: {datetime.now(timezone.utc).isoformat()}")
    parts.append(f"- Run ID: `{inputs.run_id}`")
    parts.append(f"- Config hash: `{inputs.config_hash}`\n")

    parts.append(f"\n## {SECTION_HEADERS[1]}\n")
    parts.append(f"- Vendor: {inputs.data_vendor}")
    parts.append(f"- Feed: {inputs.data_feed}")
    parts.append(f"- Adjustment: {inputs.adjustment}")
    parts.append("- Limitations: " + ("IEX-only exploratory data" if inputs.data_feed == "iex" else "Consolidated SIP data"))

    parts.append(f"\n## {SECTION_HEADERS[2]}\n")
    if inputs.universe_mode == "alpaca_current_assets":
        parts.append("- Universe: current Alpaca active/tradable assets.")
        parts.append("- Bias: **survivorship-biased**. Historical delisted/inactive names may be missing.")
    else:
        parts.append(f"- Universe mode: {inputs.universe_mode}")

    parts.append(f"\n## {SECTION_HEADERS[3]}\n")
    parts.append(f"- Config hash: `{inputs.config_hash}`")
    if inputs.dataset_hashes:
        for k, v in inputs.dataset_hashes.items():
            parts.append(f"- {k}: `{v}`")
    else:
        parts.append("- _no dataset hashes provided_")

    parts.append(f"\n## {SECTION_HEADERS[4]}\n")
    from bowaka_lab.reports.tables import candidate_funnel

    funnel_source = inputs.prefilter_funnel if inputs.prefilter_funnel else inputs.prefilter_metadata
    parts.append(_md_table(candidate_funnel(funnel_source)))

    parts.append(f"\n## {SECTION_HEADERS[5]}\n")
    if inputs.candidate_rank_distribution is not None and not inputs.candidate_rank_distribution.empty:
        parts.append(_md_table(inputs.candidate_rank_distribution))
    else:
        parts.append("_not provided_")

    parts.append(f"\n## {SECTION_HEADERS[6]}\n")
    from bowaka_lab.reports.tables import trade_summary

    parts.append(_md_table(trade_summary(inputs.trades)))

    parts.append(f"\n## {SECTION_HEADERS[7]}\n")
    from bowaka_lab.reports.tables import exit_reasons

    parts.append(_md_table(exit_reasons(inputs.trades)))

    parts.append(f"\n## {SECTION_HEADERS[8]}\n")
    from bowaka_lab.reports.tables import mfe_mae_buckets

    parts.append(_md_table(mfe_mae_buckets(inputs.trades)))

    parts.append(f"\n## {SECTION_HEADERS[9]}\n")
    from bowaka_lab.reports.tables import entry_counterfactual_grid

    parts.append(_md_table(entry_counterfactual_grid(inputs.counterfactuals)))

    parts.append(f"\n## {SECTION_HEADERS[10]}\n")
    from bowaka_lab.reports.tables import exit_counterfactual_grid

    parts.append(_md_table(exit_counterfactual_grid(inputs.counterfactuals)))

    parts.append(f"\n## {SECTION_HEADERS[11]}\n")
    if inputs.signal_fade is not None and not inputs.signal_fade.empty:
        from bowaka_lab.reports.tables import signal_fade_bucket_distribution

        parts.append(_md_table(signal_fade_bucket_distribution(inputs.signal_fade)))
    else:
        from bowaka_lab.reports.tables import signal_fade_thresholds

        parts.append(_md_table(signal_fade_thresholds(inputs.counterfactuals)))

    parts.append(f"\n## {SECTION_HEADERS[12]}\n")
    if inputs.liquidity is not None and not inputs.liquidity.empty:
        parts.append(_md_table(inputs.liquidity))
    else:
        from bowaka_lab.reports.tables import liquidity_buckets

        parts.append(_md_table(liquidity_buckets(inputs.trades)))

    parts.append(f"\n## {SECTION_HEADERS[13]}\n")
    if inputs.optuna_best:
        ob = inputs.optuna_best
        study_name = ob.get("study_name", "_unknown_")
        n_trials = ob.get("n_trials", 0)
        best_value = ob.get("best_value")
        best_params = ob.get("best_params") or {}
        parts.append(f"- **Study:** `{study_name}`")
        parts.append(f"- **Trials:** {n_trials}")
        if best_value is not None:
            parts.append(f"- **Best objective:** {best_value:.6f}")
        else:
            parts.append("- **Best objective:** _no completed trials_")
        if best_params:
            parts.append("- **Best parameters:**")
            for k, v in sorted(best_params.items()):
                parts.append(f"  - `{k}` = `{v}`")
        if inputs.optuna_trials is not None and not inputs.optuna_trials.empty:
            from bowaka_lab.reports.tables import optuna_top_trials

            parts.append("\n**Top trials by objective value:**")
            parts.append(_md_table(optuna_top_trials(inputs.optuna_trials, n=10)))
    else:
        parts.append("_no walk-forward optimization run; set Section 14 by running notebook 10 in production mode_")

    parts.append(f"\n## {SECTION_HEADERS[14]}\n")
    if inputs.reconciliation is None or inputs.reconciliation.empty:
        parts.append("_no paper reconciliation provided_")
    else:
        from bowaka_lab.reports.tables import paper_vs_backtest_summary

        parts.append(_md_table(paper_vs_backtest_summary(inputs.reconciliation)))

    parts.append(f"\n## {SECTION_HEADERS[15]}\n")
    if inputs.known_limitations:
        for lim in inputs.known_limitations:
            parts.append(f"- {lim}")
    else:
        parts.append("- IEX-only exploratory feed" if inputs.data_feed == "iex" else "- None recorded")

    flags = research_status_flags(inputs)
    parts.append(f"\n## {SECTION_HEADERS[16]}\n")
    if flags:
        parts.append("**Research status:** `research-grade exploratory evidence` (not live-trading approved).")
        parts.append("Flags:")
        for f in flags:
            parts.append(f"- `{f}`")
    else:
        parts.append("All known stop-ship flags pass. Status: `paper_validation_candidate`.")

    parts.append(f"\n## {SECTION_HEADERS[17]}\n")
    if inputs.next_actions:
        for action in inputs.next_actions:
            parts.append(f"- {action}")
    else:
        parts.append("- Add walk-forward validation.")
        parts.append("- Replace IEX feed with SIP for liquidity-sensitive claims.")
        parts.append("- Resolve any outstanding paper-vs-backtest implementation_mismatch incidents.")

    parts.append("\n---\n")
    parts.append("**Research status footer:** This run is classified as `research-grade exploratory evidence`. Live-trading approval requires SIP data + point-in-time universe + walk-forward validation per Report §31.\n")

    return "\n".join(parts)
