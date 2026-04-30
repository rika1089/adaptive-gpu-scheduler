"""
experiments/exp_static_vs_rr_vs_adaptive.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Main experiment: reproduce the paper's core comparison.

Runs all three policies (static, round_robin, adaptive) on the
paper's default workload (80/40/45/25 req/s) and outputs:
  - output/metrics/  → per-policy CSV files
  - output/figures/  → latency, throughput, SLA, fairness bar charts
  - output/reports/  → JSON summary + printed table

Run from project root:
    python experiments/exp_static_vs_rr_vs_adaptive.py
    python experiments/exp_static_vs_rr_vs_adaptive.py --quick   # 30s runs
"""
from __future__ import annotations
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adaptive_gpu.config.loader import load_all
from adaptive_gpu.evaluation.compare_policies import run_comparison
from adaptive_gpu.evaluation.summarize import (
    print_comparison_table,
    save_json,
    plot_bar_comparison,
    plot_allocation_over_time,
)
from adaptive_gpu.simulation.event_loop import run_single
from adaptive_gpu.utils.logging import get_logger

logger = get_logger("exp.main_comparison")


def main(quick: bool = False) -> None:
    agents_cfg, workloads_cfg, policies_cfg, exp_cfg = load_all()

    workload_cfg = workloads_cfg.get("paper_default")
    if quick:
        workload_cfg.duration_seconds = 30
        exp_cfg.repeats = 1
        logger.info("Quick mode: 30s runs, 1 repeat")

    exp_cfg.policies = ["adaptive", "static", "round_robin"]

    print()
    print("=" * 60)
    print("  EXPERIMENT: Static vs Round-Robin vs Adaptive")
    print(f"  Workload: {workload_cfg.name}")
    print(f"  Duration: {workload_cfg.duration_seconds}s × {exp_cfg.repeats} repeats")
    print(f"  Arrival rates: {workload_cfg.arrival_rates}")
    print("=" * 60)

    # ── Full comparison ────────────────────────────────────────────────────
    comparison = run_comparison(
        agents_cfg=agents_cfg,
        workload_cfg=workload_cfg,
        policies_cfg=policies_cfg,
        exp_cfg=exp_cfg,
        output_dir="output/metrics",
    )

    # ── Results ────────────────────────────────────────────────────────────
    print_comparison_table(comparison)
    save_json(comparison, "output/reports/main_comparison.json")
    plot_bar_comparison(comparison, figures_dir="output/figures")

    # ── Also plot allocation-over-time for adaptive only ───────────────────
    logger.info("Running single adaptive pass for allocation-over-time plot...")
    adaptive_collector = run_single(
        policy_name="adaptive",
        agents_cfg=agents_cfg,
        workload_cfg=workload_cfg,
        policies_cfg=policies_cfg,
        exp_cfg=exp_cfg,
        seed=exp_cfg.random_seed,
    )
    plot_allocation_over_time(adaptive_collector, figures_dir="output/figures")

    print("\nExperiment complete. Check output/ for results.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true",
                        help="Run 30s short version for testing")
    args = parser.parse_args()
    main(quick=args.quick)
