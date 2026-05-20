#!/usr/bin/env bash
# Phase 9 final smoke: env-check + run a smoke backtest end-to-end, then leave a
# run_dir for the promotion gate to inspect.
#
# Usage (from repo root):
#   bash research_notebooks/bowaka_v2_lab/scripts/run_final_smoke.sh
set -eu

LAB_DIR="research_notebooks/bowaka_v2_lab"
SMOKE_CFG="$LAB_DIR/configs/bowaka_v2_backtest_smoke.yml"

if [ ! -f "$SMOKE_CFG" ]; then
  echo "FATAL: $SMOKE_CFG not found"
  exit 1
fi

echo "[1/2] env-check"
python -m bowaka_v2_lab.cli env-check --config "$SMOKE_CFG"

echo "[2/2] dev smoke backtest"
python -m bowaka_v2_lab.devtools.smoke_backtester --synth --n-trades 5
echo "Final smoke complete."
