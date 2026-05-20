"""Walk-forward Optuna search infrastructure (Phase 6)."""
from .search_space import suggest_params, SEARCH_SPACE_SPEC
from .objective import compute_objective, ObjectiveResult, fold_score
from .walkforward import WalkForwardPlan, WalkForwardSplit, build_walkforward_splits
from .holdout_guard import HoldoutGuard, HoldoutGuardError
from .stability import top_k_cluster_stability
from .dispatcher import OptunaStudy, build_study_name

__all__ = [
    "suggest_params", "SEARCH_SPACE_SPEC",
    "compute_objective", "ObjectiveResult", "fold_score",
    "WalkForwardPlan", "WalkForwardSplit", "build_walkforward_splits",
    "HoldoutGuard", "HoldoutGuardError",
    "top_k_cluster_stability",
    "OptunaStudy", "build_study_name",
]
