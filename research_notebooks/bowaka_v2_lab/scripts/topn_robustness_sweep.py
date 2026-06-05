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
import copy
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
import yaml

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


def _agg_fold_metrics(fold_metrics: list[dict]) -> dict:
    """Aggregate a trial's per-fold metrics into the headline PnL / quant figures.

    PnL / averages → mean across folds; drawdown / worst-day → MAX (worst across
    folds); trades → sum. Per-fold values are kept for the detail section.
    """
    def _col(key):
        return [float(fm.get(key)) for fm in fold_metrics if fm.get(key) is not None]
    out: dict = {}
    for key, how in (
        ("net_return_pct", "mean"), ("win_rate", "mean"),
        ("avg_trade_return_pct", "mean"), ("median_trade_return_pct", "mean"),
        ("fill_rate", "mean"), ("frac_trades_ge_min_profit", "mean"),
        ("mtm_max_drawdown_pct", "max"), ("worst_day_loss_pct", "max"),
    ):
        vals = _col(key)
        if not vals:
            out[key] = None
        elif how == "mean":
            out[key] = sum(vals) / len(vals)
        else:  # max
            out[key] = max(vals)
    out["n_trades"] = int(sum(int(fm.get("n_trades", 0) or 0) for fm in fold_metrics))
    out["per_fold_net_return_pct"] = [fm.get("net_return_pct") for fm in fold_metrics]
    out["per_fold_max_dd_pct"] = [fm.get("mtm_max_drawdown_pct") for fm in fold_metrics]
    out["per_fold_win_rate"] = [fm.get("win_rate") for fm in fold_metrics]
    out["per_fold_n_trades"] = [fm.get("n_trades") for fm in fold_metrics]
    return out


def _export_yaml(base_cfg: dict, params: dict, out_path: Path, *, label: str,
                 trial_number, combined, dev_net_return) -> None:
    """Write the base config with ``params`` applied (the deployable config).

    ``wr.apply_trial_params`` resolves the gap/ratio search-space keys into the
    actual-strategy fields. A header comment records provenance.
    """
    deployable = wr.apply_trial_params(base_cfg, dict(params))
    # drop the optuna search/study block — it is irrelevant to a deployed config
    deployable = copy.deepcopy(deployable)
    deployable.pop("optuna", None)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"# {label} — trial #{trial_number}\n"
        f"# combined_score={combined}  dev_net_return_pct(mean)={dev_net_return}\n"
        f"# base config with the trial's tuned params applied (optuna block stripped).\n"
        f"# generated by scripts/topn_robustness_sweep.py\n"
    )
    out_path.write_text(header + yaml.safe_dump(deployable, sort_keys=False),
                        encoding="utf-8")


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


def _pct(x, signed=True):
    """Decimal-return / fraction → percent string (e.g. 0.1947 → +19.47%)."""
    if x is None:
        return "—"
    s = "+" if signed and float(x) >= 0 else ""
    return f"{s}{float(x) * 100:.2f}%"


def _dm(r, key):
    return (r.get("dev_metrics") or {}).get(key)


def _build_markdown(study_name, cfg_path, results, winner, study_best, plan,
                    n_neighbours, ts, yaml_paths) -> str:
    md: list[str] = []
    md += [f"# Top-N robustness + holdout sweep — `{study_name}`", ""]
    md += [
        f"- generated: {ts}",
        f"- config: `{cfg_path}`",
        f"- finalists: {len(results)}  ·  neighbours/finalist: {n_neighbours} (±10%)",
        f"- holdout window: {plan.final_holdout_start} … {plan.final_holdout_end}",
        "",
        "> **Reading the numbers:** *Objective* is the tuned v2 score (log-return "
        "**minus edge/turnover/fill penalties**) — it can be **negative even when "
        "PnL is positive**. So judge profitability from **Net return** / win rate / "
        "drawdown, and judge *what was optimised* from Objective. *Robustness* = how "
        "far the ±10% parameter neighbours fall below the candidate (a flat plateau "
        "vs a fragile spike).",
        "",
    ]
    ho_errs = [r for r in results if r.get("holdout_error")]
    if ho_errs:
        why = str(ho_errs[0]["holdout_error"]).splitlines()[0][:160]
        md += [
            f"> **Holdout not evaluated** for {len(ho_errs)}/{len(results)} finalists — "
            f"{why}. The combined score uses **dev objective + neighbour mean only**; "
            f"the Holdout columns show `—`. Build + verify the holdout-scope scan-matrix, "
            f"then re-run, to add the out-of-sample column.",
            "",
        ]
    # ---- winners ----------------------------------------------------------
    md += ["## Recommended configs", ""]
    if winner is not None:
        md += [
            f"- **Robustness winner (combined): trial #{winner['number']}** — "
            f"combined {_fmt(winner.get('combined_score'))} · "
            f"net return {_pct(_dm(winner, 'net_return_pct'))} · "
            f"max DD {_pct(_dm(winner, 'mtm_max_drawdown_pct'), signed=False)} · "
            f"win {_pct(_dm(winner, 'win_rate'), signed=False)} · "
            f"robust **{_fmt(winner.get('robust_ok'))}**",
        ]
    if study_best is not None and (winner is None or study_best['number'] != winner['number']):
        md += [
            f"- **Study #1 by objective: trial #{study_best['number']}** — "
            f"objective {_fmt(study_best.get('median_fold_score'))} · "
            f"net return {_pct(_dm(study_best, 'net_return_pct'))} · "
            f"robust {_fmt(study_best.get('robust_ok'))}",
        ]
    elif study_best is not None:
        md += ["  - (study #1 by objective is the same trial)"]
    for key, label in (("winner", "robustness winner"), ("study_best", "study #1")):
        if yaml_paths.get(key):
            md += [f"- exported YAML ({label}): `{yaml_paths[key]}`"]
    md += [
        "",
        "> Auto-pick = highest **combined** (mean of dev objective, neighbour mean, "
        "holdout) among finalists passing the robustness + no-holdout-collapse gates. "
        "Every metric is below — override the pick on PnL / drawdown / your own weights.",
        "",
    ]
    # ---- comparison table (PnL-led) --------------------------------------
    headers = ["Rank", "Trial", "Net ret%", "Max DD%", "Win%", "Trades", "Avg trade%",
               "Objective", "FoldVar", "NbObj min", "Robust?", "Holdout net%", "Combined"]
    rows = []
    for i, r in enumerate(results, 1):
        star = " ★" if (study_best and r["number"] == study_best["number"]) else ""
        hm = r.get("holdout_metrics") or {}
        rows.append([
            i, f"{r['number']}{star}",
            _pct(_dm(r, "net_return_pct")), _pct(_dm(r, "mtm_max_drawdown_pct"), signed=False),
            _pct(_dm(r, "win_rate"), signed=False), _dm(r, "n_trades"),
            _pct(_dm(r, "avg_trade_return_pct")),
            _fmt(r.get("median_fold_score")), _fmt(r.get("fold_variance")),
            _fmt(r.get("neighbour_min")), _fmt(r.get("robust_ok")),
            _pct(hm.get("net_return_pct")) if not r.get("holdout_error") else "—",
            _fmt(r.get("combined_score")),
        ])
    md += ["## Finalist comparison (ranked by combined score · ★ = study #1 by objective)", ""]
    md += _md_table(headers, rows, align_right_from=2)
    md += [""]
    # ---- per-finalist detail ---------------------------------------------
    md += ["## Per-finalist detail", ""]
    for i, r in enumerate(results, 1):
        tag = "  [study #1 by objective]" if (study_best and r["number"] == study_best["number"]) else ""
        md += [f"### #{i} — trial {r['number']}{tag}  (combined {_fmt(r.get('combined_score'))})", ""]
        # PnL / quant block
        md += [
            f"- **PnL (validation):** net return {_pct(_dm(r, 'net_return_pct'))} (mean of folds) · "
            f"max drawdown {_pct(_dm(r, 'mtm_max_drawdown_pct'), signed=False)} (worst fold) · "
            f"worst-day loss {_pct(_dm(r, 'worst_day_loss_pct'), signed=False)}",
            f"  - win rate {_pct(_dm(r, 'win_rate'), signed=False)} · "
            f"avg trade {_pct(_dm(r, 'avg_trade_return_pct'))} · "
            f"median trade {_pct(_dm(r, 'median_trade_return_pct'))} · "
            f"# trades {_dm(r, 'n_trades')} · fill {_pct(_dm(r, 'fill_rate'), signed=False)} · "
            f"≥min-profit {_pct(_dm(r, 'frac_trades_ge_min_profit'), signed=False)}",
            f"  - per-fold net return: {[_pct(x) for x in (_dm(r, 'per_fold_net_return_pct') or [])]}",
            f"  - per-fold max DD: {[_pct(x, signed=False) for x in (_dm(r, 'per_fold_max_dd_pct') or [])]}"
            f" · per-fold trades: {_dm(r, 'per_fold_n_trades')}",
            f"- **Objective:** dev value {_fmt(r.get('dev_value'))} · median {_fmt(r.get('median_fold_score'))} "
            f"· fold variance {_fmt(r.get('fold_variance'))} · per-fold {[_fmt(s) for s in (r.get('fold_scores') or [])]}",
            f"- **Robustness (±10%, {n_neighbours} neighbours):** objective "
            f"{[_fmt(s) for s in (r.get('neighbour_scores') or [])]} → min {_fmt(r.get('neighbour_min'))} / "
            f"mean {_fmt(r.get('neighbour_mean'))} / max {_fmt(r.get('neighbour_max'))} · "
            f"dev−neighbour drop {_fmt(r.get('dev_minus_neighbour_mean'))} · robust {_fmt(r.get('robust_ok'))}",
        ]
        hm = r.get("holdout_metrics") or {}
        if r.get("holdout_error"):
            md += [f"- **Holdout:** not evaluated — {str(r['holdout_error']).splitlines()[0][:140]}"]
        else:
            md += [
                f"- **Holdout (out-of-sample):** objective {_fmt(r.get('holdout_score'))} · "
                f"net return {_pct(hm.get('net_return_pct'))} · "
                f"max DD {_pct(hm.get('max_drawdown_pct'), signed=False)} · "
                f"trades {hm.get('n_trades', '—')} · collapse {_fmt(r.get('holdout_collapse'))}",
            ]
        params = r.get("params") or {}
        ptxt = ", ".join(f"`{k}`={_fmt(v, 5) if isinstance(v, float) else v}"
                         for k, v in sorted(params.items()))
        md += [f"- **Params:** {ptxt}", ""]
    md += [
        "## Methodology", "",
        f"- **Neighbours:** {n_neighbours} parameter sets, each numeric param perturbed "
        "±10% of its search range (deterministic seed), re-scored on the validation folds.",
        "- **Combined score:** mean of the available {dev objective median, neighbour mean, "
        "holdout objective}.",
        "- **Robust?** worst neighbour objective within 50% of the candidate's dev objective.",
        "- **PnL aggregation:** net return / win rate / trade returns = mean across folds; "
        "max drawdown / worst-day = worst fold; trades = sum.",
        "- **Holdout:** scored on the reserved final-holdout window when its scan-matrix is "
        "available; otherwise blank (the validation matrix does not cover it).",
        "",
    ]
    return "\n".join(md)


# --------------------------------------------------------------------------
# Emit (shared by the live sweep and --from-json)
# --------------------------------------------------------------------------
def _emit(results, study_name, cfg_path, plan, n_neighbours, ts, out_path: Path,
          base_cfg: Optional[dict] = None) -> int:
    for r in results:
        _finalize_verdict(r)

    def _ckey(r):
        cs = r.get("combined_score")
        return (cs is not None, cs if cs is not None else _FAILED)

    results.sort(key=_ckey, reverse=True)
    eligible = [r for r in results if r.get("robust_ok") and not r.get("holdout_collapse")]
    winner = eligible[0] if eligible else (results[0] if results else None)
    # study #1 = the highest rank_score (median fold score − variance penalty)
    study_best = (max(results, key=lambda r: (r.get("rank_score") is not None,
                  r.get("rank_score") if r.get("rank_score") is not None else _FAILED))
                  if results else None)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ---- both single-best YAMLs (robustness winner + study #1 by objective) --
    yaml_paths: dict[str, str] = {}
    if base_cfg is not None:
        for key, r, label in (
            ("winner", winner, "top-N robustness WINNER"),
            ("study_best", study_best, "study #1 by objective"),
        ):
            if r is None:
                continue
            yp = out_path.with_name(f"{out_path.stem}_{key}.yml")
            _export_yaml(base_cfg, r["params"], yp, label=label,
                         trial_number=r["number"], combined=r.get("combined_score"),
                         dev_net_return=(r.get("dev_metrics") or {}).get("net_return_pct"))
            yaml_paths[key] = str(yp)

    md = _build_markdown(study_name, cfg_path, results, winner, study_best, plan,
                         n_neighbours, ts, yaml_paths)
    out_path.write_text(md, encoding="utf-8")
    json_path = out_path.with_suffix(".json")
    json_path.write_text(json.dumps(
        {"study": study_name, "winner_trial": (winner or {}).get("number"),
         "study_best_trial": (study_best or {}).get("number"),
         "yaml_paths": yaml_paths, "finalists": results},
        indent=2, default=str), encoding="utf-8")
    print(f"\nwinner (combined): trial #{(winner or {}).get('number')}  "
          f"(combined {_fmt((winner or {}).get('combined_score'))})")
    print(f"study #1 (objective): trial #{(study_best or {}).get('number')}")
    print(f"markdown: {out_path}\njson: {json_path}")
    for k, v in yaml_paths.items():
        print(f"yaml ({k}): {v}")
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
                     time.strftime("%Y-%m-%d %H:%M:%S"), out_path, base_cfg=s["cfg"])
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

    finalists = []
    for t in top:
        finalists.append(dict(
            number=t.number, params=dict(t.params), dev_value=float(t.value),
            median_fold_score=t.user_attrs.get("median_fold_score"),
            fold_variance=t.user_attrs.get("fold_variance"),
            fold_scores=list(t.user_attrs.get("fold_scores") or []),
            rank_score=_rank_score(t, w_var),
            # PnL + quant metrics from the trial's stored per-fold metrics (no
            # re-run needed for the candidate's own dev numbers).
            dev_metrics=_agg_fold_metrics(list(t.user_attrs.get("fold_metrics") or [])),
        ))

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
    return _emit(results, study_name, cfg_path, s["plan"], args.neighbours, ts, out_path,
                 base_cfg=s["cfg"])


if __name__ == "__main__":
    raise SystemExit(main())
