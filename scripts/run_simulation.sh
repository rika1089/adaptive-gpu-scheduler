#!/bin/bash
# scripts/run_simulation.sh
# Run the full simulation comparison experiment.
# Usage: bash scripts/run_simulation.sh [--quick]

set -e
cd "$(dirname "$0")/.."   # always run from project root

echo "==================================================="
echo "  Adaptive GPU Scheduler — Simulation Experiment"
echo "==================================================="

# Activate venv if present
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

ARGS=""
if [[ "$1" == "--quick" ]]; then
    ARGS="--quick"
    echo "  Mode: QUICK (30s per policy, 1 repeat)"
else
    echo "  Mode: FULL  (300s per policy, 3 repeats)"
fi

mkdir -p output/metrics output/figures output/logs output/reports

python experiments/exp_static_vs_rr_vs_adaptive.py $ARGS

echo ""
echo "Results:"
echo "  Metrics  → output/metrics/"
echo "  Figures  → output/figures/"
echo "  Reports  → output/reports/"
