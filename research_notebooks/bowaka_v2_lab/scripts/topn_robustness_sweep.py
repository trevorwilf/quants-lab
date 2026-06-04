#!/usr/bin/env python
"""Top-N robustness + holdout sweep for a finished bowaka_v2 walk-forward study.

Post-hoc analysis tool (no re-running the study). Loads the completed Optuna
study, ranks the valid completed trials, takes the top N finalists, and for EACH
finalist runs:

  * a **neighbour / robustness sweep** — re-scores ``--neighbours`` parameter
    sets perturbed +/-10% around the finalist on the validation folds (does the
    score sit on a robust plateau or a fragile spike?); and
  * a **final-holdout evaluation** — scores the finalist once on the reserved
    holdout window (does it generalise out-of-sample, or collapse vs its dev
    score?).

It then ranks the finalists by a combined score (dev median + neighbour mean +
holdout), names the winner, and writes a markdown report comparing all N so YOU
can evaluate and override. A JSON sidecar carries the full numbers.

Parallelism: the fold contexts (validation + holdout) are built ONCE in the
parent and the worker processes inherit them copy-on-write (Linux fork) — no
per-worker rebuild. Each worker scores one finalist's sweep + holdout.

    cd research_notebooks/bowaka_v2_lab
    PYTHONPATH=src:../bowaka_common/src python scripts/topn_robustness_sweep.py \
        --config configs/_local_container_matrix.yml \
        --top-n 12 --neighbours 7 --jobs 12 \
        --out artifacts/topn_robustness.md
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import logging
import multiprocessing as mp
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Optional

import optuna

import bowaka_v2_lab.optuna.walkforward_runner as wr
from bowaka_v2_lab.config import BowakaV2Paths, SimulationConfig, load_config
from bowaka_v2_lab.data.lineage import resolve_lake_root
from bowaka_v2_lab.optuna.fold_context import build_fold_contexts, build_holdout_context
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard
from bowaka_v2_lab.optuna.objective import (
    compute_objective,
    fold_result_from_backtest_result,
)
from bowaka_v2_lab.optuna.search_space import resolve_search_space
from bowaka_v2_lab.optuna.storage_path import resolve_storage_uri
from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits
from bowaka_v2_lab.reports.render_run_report import _md_table

_FAILED = -1.0e9
_LOG = logging.getLogger("topn_sweep")

# Parent-process globals inherited (copy-on-write) by forked workers.
_G: dict[str, Any] = {}


# --------------------------------------------------------------------------
# Setup
# --------------------------------------------------------------------------
def _setup(config_path: str):
    cfg = load_config(config_path)
    paths = BowakaV2Paths.from_config(cfg, repo_root=wr._REPO_ROOT)
    optuna_cfg = cfg.get("optuna", {}) or {}
    wf = optuna_cfg.get("walkforward", {}) or {}
    bt = cfg.get("backtest", {}) or {}
    md = cfg.get("market_data", {}) or {}
    sim_cfg = SimulationConfig.model_validate(cfg.get("simulation") or {})
    plan = build_walkforward_splits(
        full_start=wr._to_date(bt["start_date"]), full_end=wr._to_date(bt["end_date"]),
        train_months=int(wf.get("train_months", 6)), val_months=int(wf.get("val_months", 1)),
        final_holdout_months=int(wf.get("final_holdout_months", 1)),
    )
    feed = str(md.get("feed", "iex"))
    lake_root = resolve_lake_root(cfg)
    symbols = wr._resolve_symbols(cfg, md, sim_mode=sim_cfg.mode, plan=plan)
    cached_suppliers = bool(optuna_cfg.get("cached_suppliers", False))
    spec = resolve_search_space(dict(optuna_cfg.get("search_space_overrides") or {}))
    storage_uri = resolve_storage_uri(
        optuna_cfg.get("storage") or "sqlite:///artifacts/optuna/local.db", paths=paths,
    )
    return dict(
        cfg=cfg, paths=paths, plan=plan, feed=feed, lake_root=lake_root,
        symbols=symbols, cached_suppliers=cached_suppliers, spec=spec,
        storage_uri=storage_uri,
    )


def _pick_study_name(storage_uri: str, explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    summaries = optuna.get_all_study_summaries(storage=storage_uri)
    cands = [s for s in summaries if "walkforward" in s.study_name]
    if not cands:
        raise SystemExit("no walk-forward study found in storage; pass --study-name")
    cands.sort(key=lambda s: (s.datetime_start or 0, s.study_name), reverse=True)
    return cands[0].study_name


def _is_valid(t, n_splits: int) -> bool:
    if t.value is None or float(t.value) <= _FAILED / 2:
        return False
    fs = t.user_attrs.get("fold_scores") or []
    fm = t.user_attrs.get("fold_metrics") or []
    if len(fs) != n_splits or len(fm) != n_splits:
        return False
    statuses = t.user_attrs.get("fold_statuses") or ["ok"] * n_splits
    return all(s == "ok" for s in statuses)


def _rank_score(t, w_var: float) -> float:
    med = t.user_attrs.get("median_fold_score")
    var = t.user_attrs.get("fold_variance")
    if med is None:
        return float(t.value) if t.value is not None else _FAILED
    v = float(med)
    if var is not None:
        v -= w_var * float(var)
    return v


# --------------------------------------------------------------------------
# Per-finalist evaluation (runs in a forked worker; reads inherited _G)
# --------------------------------------------------------------------------
def _eval_finalist(cand: dict) -> dict:
    cfg = _G["cfg"]; plan = _G["plan"]; feed = _G["feed"]; lake_root = _G["lake_root"]
    symbols = _G["symbols"]; paths = _G["paths"]; spec = _G["spec"]
    val_ctx = _G["val_contexts"]; holdout_ctx = _G["holdout_ctx"]
    n_neighbours = _G["n_neighbours"]
    guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
    log = logging.getLogger("topn_worker")
    params = cand["params"]
    out = dict(cand)

    # ---- neighbour / robustness sweep (validation folds, objective_minimal) --
    neighbours = wr._neighbour_param_sets(params, spec, n_neighbours=n_neighbours)
    nb_scores: list[Optional[float]] = []
    for nb in neighbours:
        try:
            folds = wr._run_validation_folds(
                wr.apply_trial_params(cfg, nb), plan,
                lake_root=lake_root, feed=feed, symbols=symbols, paths=paths,
                holdout_guard=guard, log=log,
                objective_artifact_mode="objective_minimal", fold_contexts=val_ctx,
            )
            nb_scores.append(float(compute_objective(folds).objective))
        except Exception as exc:  # noqa: BLE001
            log.warning("neighbour failed: %s", exc)
            nb_scores.append(None)
    valid_nb = [s for s in nb_scores if s is not None]
    out["neighbour_scores"] = nb_scores
    out["neighbour_min"] = min(valid_nb) if valid_nb else None
    out["neighbour_max"] = max(valid_nb) if valid_nb else None
    out["neighbour_mean"] = (sum(valid_nb) / len(valid_nb)) if valid_nb else None
    med = cand.get("median_fold_score")
    out["dev_minus_neighbour_mean"] = (
        (med - out["neighbour_mean"]) if (med is not None and out["neighbour_mean"] is not None) else None
    )

    # ---- final-holdout evaluation (objective_minimal, holdout context) -------
    out["holdout_score"] = None
    out["holdout_metrics"] = {}
    out["holdout_error"] = None
    try:
        guard.enter_final_eval()
        res = wr._run_fold_backtest_objective(
            wr.apply_trial_params(cfg, params),
            val_start=plan.final_holdout_start, val_end=plan.final_holdout_end,
            lake_root=lake_root, feed=feed, symbols=symbols, paths=paths,
            ctx=holdout_ctx,
        )
        guard.exit_final_eval()
        if res is not None:
            hf = fold_result_from_backtest_result("holdout", res)
            out["holdout_score"] = float(compute_objective([hf]).objective)
            out["holdout_metrics"] = {
                "net_return_pct": hf.net_return, "max_drawdown_pct": hf.max_drawdown,
                "worst_day_loss_pct": hf.worst_day_loss, "n_trades": hf.n_trades,
                "fill_rate": hf.fill_rate,
            }
    except Exception as exc:  # noqa: BLE001
        out["holdout_error"] = str(exc)

    return _finalize_verdict(out)


def _finalize_verdict(out: dict) -> dict:
    """Combined score + advisory robustness/holdout flags from the raw numbers.

    Pure function of the recorded fields, so it is applied both after a live
    sweep and when regenerating the report from a saved JSON (``--from-json``).
    """
    med = out.get("median_fold_score")
    dev = med if med is not None else out.get("dev_value")
    nb_mean = out.get("neighbour_mean")
    nb_min = out.get("neighbour_min")
    hs = out.get("holdout_score")
    parts = [v for v in (med, nb_mean, hs) if v is not None]
    out["combined_score"] = (sum(parts) / len(parts)) if parts else None
    out["robust_ok"] = (
        nb_min is not None and dev is not None and nb_min >= dev - abs(dev) * 0.5
    )
    if hs is None:
        # Holdout not evaluated (e.g. no holdout-scope matrix) — NOT a collapse;
        # leave it unknown so a missing holdout never disqualifies a candidate.
        out["holdout_collapse"] = None
    else:
        out["holdout_collapse"] = bool(
            (dev is not None and dev > 0 and hs < dev * 0.4)
            or (hs < 0 <= (dev or 0.0))
        )
    return out


# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------
def _fmt(x, nd=4):
    if x is None:
        return "—"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, (int,)):
        return str(x)
    return f"{float(x):.{nd}f}"


def _build_markdown(study_name, cfg_path, results, winner, plan, n_neighbours, ts) -> str:
    md: list[str] = []
    md += [f"# Top-N robustness + holdout sweep — `{study_name}`", ""]
    md += [
        f"- generated: {ts}",
        f"- config: `{cfg_path}`",
        f"- finalists: {len(results)}  ·  neighbours/finalist: {n_neighbours} (±10%)",
        f"- holdout window: {plan.final_holdout_start} … {plan.final_holdout_end}",
        "",
    ]
    ho_errs = [r for r in results if r.get("holdout_error")]
    if ho_errs:
        why = str(ho_errs[0]["holdout_error"]).splitlines()[0][:160]
        md += [
            f"> **Holdout not evaluated** for {len(ho_errs)}/{len(results)} finalists — "
            f"{why}. The combined score therefore uses **dev median + neighbour mean only**; "
            f"the Holdout / HO-collapse columns show `—`. Build + verify the holdout-scope "
            f"scan-matrix, then re-run, to add the out-of-sample column.",
            "",
        ]
    if winner is not None:
        md += [
            f"## Winner: trial #{winner['number']}  (combined {_fmt(winner['combined_score'])})",
            f"- robust under perturbation: **{_fmt(winner['robust_ok'])}**  ·  "
            f"holdout collapse: **{_fmt(winner['holdout_collapse'])}**",
            f"- dev median {_fmt(winner.get('median_fold_score'))}  ·  "
            f"neighbour mean {_fmt(winner.get('neighbour_mean'))}  ·  "
            f"holdout {_fmt(winner.get('holdout_score'))}",
            "",
            "> The winner is the highest **combined** score (mean of dev-median, "
            "neighbour-mean, holdout) among finalists passing both the robustness "
            "and no-holdout-collapse gates; if none pass both, the highest combined "
            "overall (flagged). All numbers below — judge for yourself.",
            "",
        ]
    # comparison table
    headers = ["Rank", "Trial", "Dev median", "Fold var", "Nb min", "Nb mean",
               "Dev−Nb", "Robust?", "Holdout", "HO collapse?", "Combined"]
    rows = []
    for i, r in enumerate(results, 1):
        rows.append([
            i, r["number"], _fmt(r.get("median_fold_score")), _fmt(r.get("fold_variance")),
            _fmt(r.get("neighbour_min")), _fmt(r.get("neighbour_mean")),
            _fmt(r.get("dev_minus_neighbour_mean")), _fmt(r.get("robust_ok")),
            _fmt(r.get("holdout_score")), _fmt(r.get("holdout_collapse")),
            _fmt(r.get("combined_score")),
        ])
    md += ["## Finalist comparison (ranked by combined score)", ""]
    md += _md_table(headers, rows, align_right_from=2)
    md += [""]
    # per-finalist detail
    md += ["## Per-finalist detail", ""]
    for i, r in enumerate(results, 1):
        md += [f"### #{i} — trial {r['number']}  (combined {_fmt(r.get('combined_score'))})", ""]
        md += [
            f"- dev value {_fmt(r.get('dev_value'))} · median {_fmt(r.get('median_fold_score'))} "
            f"· fold variance {_fmt(r.get('fold_variance'))}",
            f"- per-fold dev scores: {[_fmt(s) for s in (r.get('fold_scores') or [])]}",
            f"- neighbour scores (±10%): {[_fmt(s) for s in (r.get('neighbour_scores') or [])]}"
            f"  → min {_fmt(r.get('neighbour_min'))} / mean {_fmt(r.get('neighbour_mean'))} "
            f"/ max {_fmt(r.get('neighbour_max'))}",
        ]
        hm = r.get("holdout_metrics") or {}
        if r.get("holdout_error"):
            md += [f"- holdout: ERROR — {r['holdout_error']}"]
        else:
            md += [
                f"- holdout score {_fmt(r.get('holdout_score'))} · "
                f"net_return {_fmt(hm.get('net_return_pct'))} · "
                f"max_dd {_fmt(hm.get('max_drawdown_pct'))} · "
                f"trades {hm.get('n_trades', '—')} · fill {_fmt(hm.get('fill_rate'))}",
            ]
        params = r.get("params") or {}
        ptxt = ", ".join(f"`{k}`={_fmt(v, 5) if isinstance(v, float) else v}"
                         for k, v in sorted(params.items()))
        md += [f"- params: {ptxt}", ""]
    return "\n".join(md)


# --------------------------------------------------------------------------
# Emit (shared by the live sweep and --from-json)
# --------------------------------------------------------------------------
def _emit(results, study_name, cfg_path, plan, n_neighbours, ts, out_path: Path) -> int:
    for r in results:
        _finalize_verdict(r)

    def _ckey(r):
        cs = r.get("combined_score")
        return (cs is not None, cs if cs is not None else _FAILED)

    results.sort(key=_ckey, reverse=True)
    eligible = [r for r in results if r.get("robust_ok") and not r.get("holdout_collapse")]
    winner = eligible[0] if eligible else (results[0] if results else None)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    md = _build_markdown(study_name, cfg_path, results, winner, plan, n_neighbours, ts)
    out_path.write_text(md, encoding="utf-8")
    json_path = out_path.with_suffix(".json")
    json_path.write_text(json.dumps(
        {"study": study_name, "winner_trial": (winner or {}).get("number"),
         "finalists": results}, indent=2, default=str), encoding="utf-8")
    print(f"\nwinner: trial #{(winner or {}).get('number')}  "
          f"(combined {_fmt((winner or {}).get('combined_score'))})")
    print(f"markdown: {out_path}\njson: {json_path}")
    return 0


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main(argv=None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(message)s")
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", required=True)
    p.add_argument("--study-name", default=None, help="default: latest walk-forward study in storage")
    p.add_argument("--top-n", type=int, default=12)
    p.add_argument("--neighbours", type=int, default=7)
    p.add_argument("--jobs", type=int, default=None, help="parallel workers (default min(top-n, cpu-2))")
    p.add_argument("--out", default=None, help="markdown path (default artifacts/optuna/topn_robustness_<study>.md)")
    p.add_argument("--dry-run", action="store_true",
                   help="rank + render the table from stored trial attrs only; SKIP backtests")
    p.add_argument("--from-json", default=None,
                   help="regenerate the markdown from a prior sweep's JSON (no backtests); "
                        "re-applies the verdict logic")
    args = p.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    cfg_path = args.config

    if args.from_json:
        doc = json.loads(Path(args.from_json).read_text(encoding="utf-8"))
        results = doc.get("finalists") or []
        s = _setup(cfg_path)  # cheap: config + plan only (no study / lake load)
        study_name = doc.get("study") or args.study_name or "unknown_study"
        out_path = Path(args.out) if args.out else Path(args.from_json).with_suffix(".md")
        return _emit(results, study_name, cfg_path, s["plan"], args.neighbours,
                     time.strftime("%Y-%m-%d %H:%M:%S"), out_path)
    s = _setup(cfg_path)
    study_name = _pick_study_name(s["storage_uri"], args.study_name)
    study = optuna.load_study(study_name=study_name, storage=s["storage_uri"])
    n_splits = len(s["plan"].splits)
    w_var = float(wr.DEFAULT_PENALTY_WEIGHTS.fold_variance)

    completed = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    valid = [t for t in completed if _is_valid(t, n_splits)]
    ranked = sorted(valid, key=lambda t: _rank_score(t, w_var), reverse=True)
    top = ranked[: args.top_n]
    print(f"study={study_name}  completed={len(completed)}  valid={len(valid)}  "
          f"finalists={len(top)}  n_splits={n_splits}", flush=True)
    if not top:
        raise SystemExit("no valid finalists to evaluate")

    finalists = [
        dict(
            number=t.number, params=dict(t.params), dev_value=float(t.value),
            median_fold_score=t.user_attrs.get("median_fold_score"),
            fold_variance=t.user_attrs.get("fold_variance"),
            fold_scores=list(t.user_attrs.get("fold_scores") or []),
            rank_score=_rank_score(t, w_var),
        )
        for t in top
    ]

    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    if args.dry_run:
        for f in finalists:
            f.update(neighbour_scores=[], neighbour_min=None, neighbour_max=None,
                     neighbour_mean=None, dev_minus_neighbour_mean=None,
                     holdout_score=None, holdout_metrics={}, holdout_error="dry-run",
                     combined_score=f.get("median_fold_score"), robust_ok=None,
                     holdout_collapse=None)
        results = finalists
    else:
        plan = s["plan"]
        print("building validation + holdout fold contexts (once; workers inherit)...", flush=True)
        t0 = time.perf_counter()
        guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)
        val_contexts = build_fold_contexts(
            s["cfg"], plan, lake_root=s["lake_root"], feed=s["feed"], symbols=s["symbols"],
            paths=s["paths"], holdout_guard=guard, cached_suppliers=s["cached_suppliers"],
        )
        holdout_ctx = build_holdout_context(
            s["cfg"], plan, lake_root=s["lake_root"], feed=s["feed"], symbols=s["symbols"],
            paths=s["paths"], holdout_guard=guard, cached_suppliers=s["cached_suppliers"],
        )
        print(f"contexts built in {time.perf_counter() - t0:.0f}s", flush=True)
        _G.update(s); _G["val_contexts"] = val_contexts
        _G["holdout_ctx"] = holdout_ctx; _G["n_neighbours"] = args.neighbours

        n_jobs = args.jobs or min(len(finalists), max(1, (os.cpu_count() or 4) - 2))
        print(f"sweeping {len(finalists)} finalists × {args.neighbours} neighbours "
              f"on {n_jobs} workers...", flush=True)
        ctx = mp.get_context("fork")
        results = []
        with cf.ProcessPoolExecutor(max_workers=n_jobs, mp_context=ctx) as ex:
            futs = {ex.submit(_eval_finalist, f): f["number"] for f in finalists}
            for fut in cf.as_completed(futs):
                try:
                    results.append(fut.result())
                    print(f"  finalist trial {futs[fut]} done ({len(results)}/{len(finalists)})", flush=True)
                except Exception as exc:  # noqa: BLE001
                    print(f"  finalist trial {futs[fut]} FAILED: {exc}", flush=True)

    out_path = Path(args.out) if args.out else (
        Path(s["paths"].artifact_root) / "optuna" / f"topn_robustness_{study_name}.md"
    )
    return _emit(results, study_name, cfg_path, s["plan"], args.neighbours, ts, out_path)


if __name__ == "__main__":
    raise SystemExit(main())
