"""Phase 3 (audit 2026-05-29 §14.1) — ensemble best = highest-median group."""
from __future__ import annotations

from bowaka_v2_lab.optuna.multi_seed import SeedResult, select_ensemble_best


def _sr(seed, params, value):
    return SeedResult(seed, f"s{seed}", dict(params), dict(params), value, [value])


def test_highest_median_group_wins() -> None:
    group_a = [_sr(1, {"x": 0.025}, 0.05), _sr(2, {"x": 0.025}, 0.07),
               _sr(3, {"x": 0.025}, 0.10)]          # median 0.07
    group_b = [_sr(4, {"x": 0.05}, 0.08), _sr(5, {"x": 0.05}, 0.08)]  # median 0.08
    eb = select_ensemble_best(group_a + group_b)
    assert eb.params_internal == {"x": 0.05}
    assert abs(eb.median_score - 0.08) < 1e-9
    assert eb.contributing_seeds == [4, 5]


def test_tie_on_median_breaks_to_lowest_std() -> None:
    high_std = [_sr(1, {"x": 0.01}, 0.05), _sr(2, {"x": 0.01}, 0.07), _sr(3, {"x": 0.01}, 0.09)]
    low_std = [_sr(4, {"x": 0.02}, 0.07), _sr(5, {"x": 0.02}, 0.07), _sr(6, {"x": 0.02}, 0.07)]
    eb = select_ensemble_best(high_std + low_std)
    assert eb.params_internal == {"x": 0.02}  # both median 0.07; lower std wins
    assert eb.score_std_across_seeds == 0.0
