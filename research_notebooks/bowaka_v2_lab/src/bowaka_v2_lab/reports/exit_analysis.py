"""Exit-lifecycle analysis — Realism Phase 7 (audit P0-009, §11 Phase 7).

Builds the exit-analysis surfaces the run report and ``report.json`` carry:

* **exit-reason distribution** — counts + PnL per ``exit_reason``
  (``stop`` / ``target`` / ``time_stop`` / ``max_hold`` / ``signal_fade_hard``
  / ``signal_fade_critical`` / ``gap_stop`` / ``gap_target`` plus the
  ``ambiguous_stop_wins`` count).
* **exit-slippage-bps distribution** — count / mean / p50 / p95 / max of the
  per-trade ``exit_slippage_bps``.
* **per-trade MFE / MAE** — the maximum favourable / adverse excursion each
  closed lot reached over its held minute path.

Every helper accepts the per-trade dict list :meth:`Portfolio.closed_trades`
produces (Phase 7 enriches it with ``exit_timestamp`` / ``mfe_pct`` /
``mae_pct`` / ``exit_slippage_bps`` / ``halted``).
"""
from __future__ import annotations

from typing import Any, Iterable

#: The full canonical exit-reason vocabulary the report always reports a count
#: for (a 0 is meaningful — it says "no lot exited this way").
EXIT_REASONS: tuple[str, ...] = (
    "stop",
    "target",
    "time_stop",
    "max_hold",
    "signal_fade_hard",
    "signal_fade_critical",
    "gap_stop",
    "gap_target",
    "halt_resume_exit",
)


def exit_reason_distribution(trades: Iterable[dict]) -> dict[str, Any]:
    """Count + total PnL per exit reason, plus the ``ambiguous_stop_wins`` count.

    Returns a dict ``{"counts": {reason: n}, "pnl": {reason: total},
    "ambiguous_stop_wins": n, "n_trades": n}``. Every reason in
    :data:`EXIT_REASONS` is present in ``counts`` (0 when unused) so a downstream
    table never has missing rows.
    """
    counts: dict[str, int] = {r: 0 for r in EXIT_REASONS}
    pnl: dict[str, float] = {r: 0.0 for r in EXIT_REASONS}
    ambiguous_stop_wins = 0
    n = 0
    for t in trades:
        n += 1
        reason = str(t.get("exit_reason", "unknown"))
        counts[reason] = counts.get(reason, 0) + 1
        pnl[reason] = pnl.get(reason, 0.0) + float(t.get("pnl", 0.0) or 0.0)
        # A same-minute ambiguity resolved to the stop under the conservative
        # axis — surfaced as its own counter so reviewers see how often the
        # ambiguity mattered.
        if t.get("ambiguous_bar_resolved") and reason == "stop":
            ambiguous_stop_wins += 1
    return {
        "counts": counts,
        "pnl": {k: round(v, 4) for k, v in pnl.items()},
        "ambiguous_stop_wins": ambiguous_stop_wins,
        "n_trades": n,
    }


def _percentile(values: list[float], pct: float) -> float:
    """Linear-interpolated percentile (no numpy dependency in this helper)."""
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * pct
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    frac = k - lo
    return s[lo] + (s[hi] - s[lo]) * frac


def exit_slippage_distribution(trades: Iterable[dict]) -> dict[str, float]:
    """count / mean / p50 / p95 / max / min of the per-trade exit slippage (bps)."""
    vals = [
        float(t.get("exit_slippage_bps", 0.0) or 0.0)
        for t in trades
        if t.get("exit_slippage_bps") is not None
    ]
    if not vals:
        return {"count": 0, "mean": 0.0, "p50": 0.0, "p95": 0.0, "max": 0.0, "min": 0.0}
    return {
        "count": len(vals),
        "mean": round(sum(vals) / len(vals), 4),
        "p50": round(_percentile(vals, 0.50), 4),
        "p95": round(_percentile(vals, 0.95), 4),
        "max": round(max(vals), 4),
        "min": round(min(vals), 4),
    }


def mfe_mae_per_trade(trades: Iterable[dict]) -> list[dict]:
    """Per-trade MFE / MAE rows from the Phase-7-enriched trade records.

    Unlike ``reports.mfe_mae.mfe_mae_per_trade`` (which recomputes the excursion
    from daily bars), this reads the ``mfe_pct`` / ``mae_pct`` the minute-path
    exit walk already recorded on each trade — the excursion over the *actual
    minute path* the lot was held, not a daily approximation.
    """
    rows: list[dict] = []
    for t in trades:
        rows.append({
            "symbol": t.get("symbol"),
            "position_id": t.get("position_id"),
            "exit_reason": t.get("exit_reason"),
            "mfe_pct": float(t.get("mfe_pct", 0.0) or 0.0),
            "mae_pct": float(t.get("mae_pct", 0.0) or 0.0),
            "pnl": float(t.get("pnl", 0.0) or 0.0),
        })
    return rows


def build_exit_analysis(trades: Iterable[dict]) -> dict[str, Any]:
    """Bundle the three exit-analysis surfaces into one dict for the report.

    ``trades`` is consumed once into a list so callers may pass a generator.
    """
    tl = list(trades)
    return {
        "exit_reason_distribution": exit_reason_distribution(tl),
        "exit_slippage_bps": exit_slippage_distribution(tl),
        "mfe_mae_per_trade": mfe_mae_per_trade(tl),
    }


def render_exit_analysis_section(trades: Iterable[dict]) -> str:
    """Render the Markdown ``## Exit Analysis`` section for ``report.md``."""
    tl = list(trades)
    dist = exit_reason_distribution(tl)
    slip = exit_slippage_distribution(tl)
    mm = mfe_mae_per_trade(tl)

    lines = ["## Exit Analysis (Phase 7)", ""]
    lines.append(f"- trades closed: {dist['n_trades']}")
    lines.append(f"- ambiguous_stop_wins: {dist['ambiguous_stop_wins']}")
    lines.append("")
    lines.append("### Exit-reason distribution")
    lines.append("")
    lines.append("| exit_reason | count | total_pnl |")
    lines.append("|---|---:|---:|")
    for reason in EXIT_REASONS:
        lines.append(
            f"| {reason} | {dist['counts'][reason]} | {dist['pnl'][reason]} |"
        )
    lines.append("")
    lines.append("### Exit-slippage (bps)")
    lines.append("")
    lines.append(
        f"- count: {slip['count']} | mean: {slip['mean']} | p50: {slip['p50']} "
        f"| p95: {slip['p95']} | max: {slip['max']} | min: {slip['min']}"
    )
    lines.append("")
    lines.append("### MFE / MAE per trade")
    lines.append("")
    if mm:
        avg_mfe = round(sum(r["mfe_pct"] for r in mm) / len(mm), 5)
        avg_mae = round(sum(r["mae_pct"] for r in mm) / len(mm), 5)
        lines.append(f"- mean MFE: {avg_mfe} | mean MAE: {avg_mae} (fraction of entry)")
    else:
        lines.append("- Not available because: no trades closed in this run.")
    lines.append("")
    return "\n".join(lines)
