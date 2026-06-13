"""P5 — finalist rank-shift report: legacy fill model vs the honest fill contract.

The production finalist (#3155) was selected under the LEGACY fill model
(manufactured liquidity + zero-cost exits). P1-P5 make the fill model honest
(PIT no-look-ahead, displayed-touch cap, spread-paying stops, tape-condition
eligibility, odd-lot filter, realistic participation). This tool measures how the
finalist RANKING moves under the honest contract — the headline P5 deliverable.

PURE CORE (host-testable): :func:`compute_rank_shift` / :func:`render_markdown`
diff two pre-scored finalist sets and emit the old-vs-new rank table + metric
deltas. No lake / study needed.

OPERATOR RUN (needs the completed study + the real SIP tape, in-container): score
the study's top-K finalists under each contract, then diff. Procedure:

    # 1. Legacy contract (how #3155 was scored): the study's own config.
    bowaka-v2 evaluate-finalists --config <search.yml> --top-k 15 \
        --out artifacts/rank_shift/legacy_finalists.json
    # 2. Honest contract: tape-replay validation (derive_validation_config).
    python -c "from bowaka_v2_lab.optuna.autoconfig import derive_validation_config; \
        derive_validation_config('<search.yml>', enable_tape_replay=True, out_path='val_tape.yml')"
    bowaka-v2 evaluate-finalists --config val_tape.yml --top-k 15 \
        --out artifacts/rank_shift/honest_finalists.json
    # 3. Diff -> the committed rank-shift report.
    python scripts/p5_rank_shift_report.py \
        artifacts/rank_shift/legacy_finalists.json \
        artifacts/rank_shift/honest_finalists.json \
        --out artifacts/rank_shift/rank_shift_report

Input schema (either a list, or ``{"finalists": [...]}``): each entry is
``{"trial": <int|str>, "score": <float>, "metrics": {<name>: <float>, ...}}``.
``trial`` is the stable join key across the two contracts (e.g. 3155).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence


def _coerce_finalists(raw: Any) -> list[dict]:
    """Accept a bare list or a ``{"finalists": [...]}`` wrapper (the
    evaluate-finalists artifact shape) and normalise to a list of dicts."""
    if isinstance(raw, Mapping):
        raw = raw.get("finalists", raw.get("ranked", []))
    if not isinstance(raw, (list, tuple)):
        raise ValueError("finalist scores must be a list (or {'finalists': [...]})")
    out: list[dict] = []
    for e in raw:
        if not isinstance(e, Mapping):
            raise ValueError(f"finalist entry not a mapping: {e!r}")
        if "trial" not in e or "score" not in e:
            raise ValueError(f"finalist entry needs 'trial' and 'score': {e!r}")
        out.append({"trial": str(e["trial"]), "score": float(e["score"]),
                    "metrics": dict(e.get("metrics") or {})})
    return out


def _ranked(finalists: Sequence[Mapping]) -> dict[str, int]:
    """Rank by score DESC (1 = best). Ties broken by trial id for determinism."""
    order = sorted(finalists, key=lambda f: (-float(f["score"]), str(f["trial"])))
    return {str(f["trial"]): i + 1 for i, f in enumerate(order)}


def compute_rank_shift(
    legacy: Sequence[Mapping], honest: Sequence[Mapping]
) -> dict:
    """Pure rank-shift: how each finalist's rank moves from the legacy fill model
    to the honest fill contract. Joined on ``trial``.

    Returns ``{"rows": [...], "summary": {...}}``. Each row carries the trial, both
    ranks, ``rank_delta`` (legacy_rank - honest_rank; positive = improved under the
    honest contract), both scores, ``score_delta``, and per-metric deltas. Finalists
    present in only one contract get ``None`` for the missing side.
    """
    leg = {str(f["trial"]): f for f in legacy}
    hon = {str(f["trial"]): f for f in honest}
    leg_rank, hon_rank = _ranked(legacy), _ranked(honest)
    trials = sorted(set(leg) | set(hon))

    rows: list[dict] = []
    for t in trials:
        lf, hf = leg.get(t), hon.get(t)
        lr, hr = leg_rank.get(t), hon_rank.get(t)
        ls = float(lf["score"]) if lf else None
        hs = float(hf["score"]) if hf else None
        metric_deltas: dict[str, Optional[float]] = {}
        if lf and hf:
            for m in sorted(set(lf.get("metrics", {})) | set(hf.get("metrics", {}))):
                lv, hv = lf["metrics"].get(m), hf["metrics"].get(m)
                metric_deltas[m] = (
                    round(float(hv) - float(lv), 6) if lv is not None and hv is not None else None
                )
        rows.append({
            "trial": t,
            "legacy_rank": lr, "honest_rank": hr,
            "rank_delta": (lr - hr) if (lr is not None and hr is not None) else None,
            "legacy_score": ls, "honest_score": hs,
            "score_delta": round(hs - ls, 6) if (ls is not None and hs is not None) else None,
            "metric_deltas": metric_deltas,
            "dropped_under_honest": hf is None,
            "new_under_honest": lf is None,
        })

    legacy_top = min(leg_rank, key=leg_rank.get) if leg_rank else None
    honest_top = min(hon_rank, key=hon_rank.get) if hon_rank else None
    both = [r for r in rows if r["rank_delta"] is not None]
    summary = {
        "n_legacy": len(legacy), "n_honest": len(honest),
        "legacy_winner": legacy_top, "honest_winner": honest_top,
        "winner_changed": legacy_top != honest_top,
        "max_abs_rank_move": max((abs(r["rank_delta"]) for r in both), default=0),
        # Finalists that looked positive under the legacy model but go non-positive
        # under the honest contract — the headline "selection was an artifact" signal.
        "flipped_positive_to_nonpositive": sorted(
            r["trial"] for r in rows
            if r["legacy_score"] is not None and r["honest_score"] is not None
            and r["legacy_score"] > 0 and r["honest_score"] <= 0
        ),
        "dropped_under_honest": sorted(r["trial"] for r in rows if r["dropped_under_honest"]),
    }
    return {"rows": rows, "summary": summary}


def render_markdown(report: Mapping, *, title: str = "P5 — finalist rank-shift") -> str:
    s = report["summary"]
    lines = [
        f"# {title}",
        "",
        "Legacy fill model (how the production finalist was selected) vs the honest "
        "fill contract (P1-P5: PIT, displayed-touch cap, spread-paying stops, tape "
        "eligibility, odd-lot filter, realistic participation).",
        "",
        f"- Legacy winner: **{s['legacy_winner']}** | Honest winner: **{s['honest_winner']}** "
        f"({'CHANGED' if s['winner_changed'] else 'unchanged'})",
        f"- Finalists scored: legacy {s['n_legacy']}, honest {s['n_honest']}",
        f"- Max rank movement: {s['max_abs_rank_move']}",
        f"- Positive→non-positive under honest contract: "
        f"{', '.join(s['flipped_positive_to_nonpositive']) or 'none'}",
        f"- Dropped under honest contract: {', '.join(s['dropped_under_honest']) or 'none'}",
        "",
        "| trial | legacy rank | honest rank | Δrank | legacy score | honest score | Δscore |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in sorted(report["rows"], key=lambda x: (x["honest_rank"] is None, x["honest_rank"] or 1e9)):
        def _f(v): return "—" if v is None else (f"{v:+.4f}" if isinstance(v, float) else str(v))
        lines.append(
            f"| {r['trial']} | {r['legacy_rank'] or '—'} | {r['honest_rank'] or '—'} | "
            f"{_f(r['rank_delta'])} | {_f(r['legacy_score'])} | {_f(r['honest_score'])} | "
            f"{_f(r['score_delta'])} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="P5 finalist rank-shift report (legacy vs honest fill).")
    ap.add_argument("legacy_json", help="finalist scores under the LEGACY fill model")
    ap.add_argument("honest_json", help="finalist scores under the HONEST fill contract")
    ap.add_argument("--out", default="artifacts/rank_shift/rank_shift_report",
                    help="output path stem (.md + .json are written)")
    ns = ap.parse_args(argv)

    legacy = _coerce_finalists(json.loads(Path(ns.legacy_json).read_text(encoding="utf-8")))
    honest = _coerce_finalists(json.loads(Path(ns.honest_json).read_text(encoding="utf-8")))
    report = compute_rank_shift(legacy, honest)

    out = Path(ns.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    out.with_suffix(".md").write_text(render_markdown(report), encoding="utf-8")
    print(f"rank-shift report -> {out.with_suffix('.md')}", flush=True)
    print(render_markdown(report), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
