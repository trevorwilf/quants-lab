#!/usr/bin/env bash
# Deterministic CI driver for the bowaka_v2_lab test matrix.
#
# Runs each non-live test segment with its own timeout, captures JUnit XML and a
# full pytest log per segment under artifacts/test-runs/<utc-iso>/, and prints
# the versions of the tools that determine reproducibility (python / pytest /
# pyarrow / optuna). Addresses docs/audits/2026-05-22_realism_audit.md §P1-007.
#
# Usage (from the lab dir, or anywhere — it cd's to its own repo location):
#   bash scripts/run_full_test_matrix.sh            # run the full matrix
#   bash scripts/run_full_test_matrix.sh --dry-run  # print the plan and exit 0
#
# Environment:
#   PYTHON      python interpreter to use (default: python)
#   In the ql-jupyter container, invoke with:
#     PYTHON=/opt/conda/envs/quants-lab/bin/python bash scripts/run_full_test_matrix.sh
#
# --dry-run is intentionally hermetic: it prints the planned segments and exits 0
# WITHOUT importing anything or invoking pytest, so it is callable from a test.
set -u

# --- Locate the lab dir (this script lives in <lab>/scripts/) -----------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMMON_DIR="$(cd "$LAB_DIR/.." && pwd)/bowaka_common"

# --- Test segments: name | paths | extra pytest args --------------------------
# Each segment runs with the comprehensive non-live marker filter. The default
# per-test timeout (60s) comes from pyproject.toml; segments that exercise real
# backtests raise it to 120s explicitly.
NOT_LIVE='not live_alpaca and not slow and not live_paper and not live_mongo'

SEG_NAMES=(
  "unit_parity"
  "integration_reconcile"
  "bowaka_common"
)
SEG_DESCS=(
  "lab unit + parity tests (default 60s/test timeout)"
  "lab integration + reconcile tests (120s/test timeout)"
  "bowaka_common shared-package tests"
)

DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "run_full_test_matrix.sh: unknown argument '$arg'" >&2
      echo "run with --help for usage" >&2
      exit 2
      ;;
  esac
done

# --- Dry-run: print the plan and exit 0 (no imports, no pytest) ---------------
if [ "$DRY_RUN" -eq 1 ]; then
  echo "run_full_test_matrix.sh --dry-run"
  echo "lab_dir: $LAB_DIR"
  echo "planned test segments:"
  for i in "${!SEG_NAMES[@]}"; do
    echo "  [$((i + 1))/${#SEG_NAMES[@]}] ${SEG_NAMES[$i]} — ${SEG_DESCS[$i]}"
  done
  echo "marker filter: $NOT_LIVE"
  echo "dry-run complete; no tests executed."
  exit 0
fi

# --- Real run -----------------------------------------------------------------
PYTHON="${PYTHON:-python}"
export PYTHONPATH="src:../bowaka_common/src${PYTHONPATH:+:$PYTHONPATH}"

RUN_TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
RUN_DIR="$LAB_DIR/artifacts/test-runs/$RUN_TS"
mkdir -p "$RUN_DIR"

echo "=============================================================="
echo "bowaka_v2_lab full test matrix — $RUN_TS"
echo "run dir: $RUN_DIR"
echo "=============================================================="
echo "--- tool versions ---"
"$PYTHON" --version 2>&1 | sed 's/^/python:  /'
"$PYTHON" -m pytest --version 2>&1 | head -1 | sed 's/^/pytest:  /'
"$PYTHON" -c 'import pyarrow; print("pyarrow:", pyarrow.__version__)' 2>&1 || echo "pyarrow:  <not importable>"
"$PYTHON" -c 'import optuna; print("optuna:", optuna.__version__)' 2>&1 || echo "optuna:   <not importable>"
{
  "$PYTHON" --version 2>&1
  "$PYTHON" -m pytest --version 2>&1 | head -1
  "$PYTHON" -c 'import pyarrow; print("pyarrow", pyarrow.__version__)' 2>&1
  "$PYTHON" -c 'import optuna; print("optuna", optuna.__version__)' 2>&1
} > "$RUN_DIR/versions.txt"
echo "----------------------"

OVERALL_RC=0

run_segment() {
  # $1 = segment name, remaining args = pytest args
  local name="$1"; shift
  local log="$RUN_DIR/${name}.log"
  local junit="$RUN_DIR/${name}.junit.xml"
  echo ""
  echo ">>> segment: $name"
  ( cd "$LAB_DIR" && "$PYTHON" -m pytest "$@" \
      -q --tb=short \
      --junitxml="$junit" \
      -m "$NOT_LIVE" ) 2>&1 | tee "$log"
  local rc=${PIPESTATUS[0]}
  echo "<<< segment $name exit=$rc (log: $log)"
  if [ "$rc" -gt "$OVERALL_RC" ]; then
    OVERALL_RC=$rc
  fi
}

# Segment 1: lab unit + parity — default 60s/test timeout from pyproject.toml.
run_segment "unit_parity" tests/unit tests/parity

# Segment 2: lab integration + reconcile — 120s/test budget for real backtests.
run_segment "integration_reconcile" tests/integration tests/reconcile \
  --timeout=120 --timeout-method=thread

# Segment 3: bowaka_common shared-package tests (run from its own dir).
echo ""
echo ">>> segment: bowaka_common"
COMMON_LOG="$RUN_DIR/bowaka_common.log"
COMMON_JUNIT="$RUN_DIR/bowaka_common.junit.xml"
( cd "$COMMON_DIR" && PYTHONPATH="src" "$PYTHON" -m pytest \
    -q --tb=short \
    --junitxml="$COMMON_JUNIT" \
    -m "$NOT_LIVE" ) 2>&1 | tee "$COMMON_LOG"
COMMON_RC=${PIPESTATUS[0]}
echo "<<< segment bowaka_common exit=$COMMON_RC (log: $COMMON_LOG)"
if [ "$COMMON_RC" -gt "$OVERALL_RC" ]; then
  OVERALL_RC=$COMMON_RC
fi

echo ""
echo "=============================================================="
echo "test matrix complete — overall exit=$OVERALL_RC"
echo "artifacts: $RUN_DIR"
echo "=============================================================="
exit "$OVERALL_RC"
