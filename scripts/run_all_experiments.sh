#!/bin/bash
# scripts/run_all_experiments.sh
# Run ALL experiments in sequence: main comparison + ablation.

set -e
cd "$(dirname "$0")/.."

if [ -f ".venv/bin/activate" ]; then source .venv/bin/activate; fi

mkdir -p output/{metrics,figures,logs,reports}

echo "============================================"
echo "  Step 1: Main policy comparison"
echo "============================================"
bash scripts/run_simulation.sh "$@"

echo ""
echo "============================================"
echo "  Step 2: Priority ablation study"
echo "============================================"
python experiments/exp_ablation_priority.py

echo ""
echo "All experiments complete."
echo "Check output/ directory for all results."
