#!/bin/bash
# scripts/run_baselines.sh
# Run each baseline policy individually with the paper workload.
# Useful for debugging individual policies before the full comparison.

set -e
cd "$(dirname "$0")/.."

if [ -f ".venv/bin/activate" ]; then source .venv/bin/activate; fi

mkdir -p output/metrics output/figures

echo "Running STATIC baseline..."
python -m adaptive_gpu.main --policy static --workload paper_default \
    --duration 60 --repeats 1 --no-plots

echo ""
echo "Running ROUND-ROBIN baseline..."
python -m adaptive_gpu.main --policy round_robin --workload paper_default \
    --duration 60 --repeats 1 --no-plots

echo ""
echo "Running ADAPTIVE policy..."
python -m adaptive_gpu.main --policy adaptive --workload paper_default \
    --duration 60 --repeats 1 --no-plots

echo ""
echo "All baselines complete. See output/metrics/"
