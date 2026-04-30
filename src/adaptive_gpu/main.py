"""
main.py — CLI entry point for running experiments.

Usage examples:
    # Run full comparison (all 3 policies, paper workload)
    python -m adaptive_gpu.main

    # Run a single policy
    python -m adaptive_gpu.main --policy adaptive --workload paper_default

    # Quick smoke-test (short duration)
    python -m adaptive_gpu.main --workload low_load --duration 30 --repeats 1

    # With custom config dir
    python -m adaptive_gpu.main --config-dir /path/to/configs
"""
from __future__ import annotations
import argparse
import sys
import time
from pathlib import Path

# Ensure src is on path when running directly
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from adaptive_gpu.config.loader import load_all, ExperimentConfig
from adaptive_gpu.evaluation.compare_policies import run_comparison
from adaptive_gpu.evaluation.summarize import (
    print_comparison_table,
    save_json,
    plot_bar_comparison,
    plot_allocation_over_time,
)
from adaptive_gpu.simulation.event_loop import run_single
from adaptive_gpu.utils.logging import get_logger

logger = get_logger("main")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Adaptive GPU Resource Allocation — Experiment Runner"
    )
    p.add_argument("--policy", default=None,
                   choices=["adaptive", "static", "round_robin"],
                   help="Run a single policy instead of all three.")
    p.add_argument("--workload", default="paper_default",
                   help="Workload name from workloads.yaml (default: paper_default)")
    p.add_argument("--duration", type=int, default=None,
                   help="Override workload duration in seconds")
    p.add_argument("--repeats", type=int, default=None,
                   help="Override number of repeats per policy")
    p.add_argument("--output-dir", default="output/metrics",
                   help="Directory for CSV outputs")
    p.add_argument("--figures-dir", default="output/figures",
                   help="Directory for plot outputs")
    p.add_argument("--no-plots", action="store_true",
                   help="Skip matplotlib plot generation")
    p.add_argument("--config-dir", default=None,
                   help="Path to configs directory (default: ./configs)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # ── Load configs ────────────────────────────────────────────────────────
    config_dir = Path(args.config_dir) if args.config_dir else None
    agents_cfg, workloads_cfg, policies_cfg, exp_cfg = load_all(
        agents_path=config_dir / "agents.yaml" if config_dir else None,
        workloads_path=config_dir / "workloads.yaml" if config_dir else None,
        policies_path=config_dir / "policies.yaml" if config_dir else None,
        experiment_path=config_dir / "experiment_default.yaml" if config_dir else None,
    )

    # ── Apply CLI overrides ─────────────────────────────────────────────────
    workload_cfg = workloads_cfg.get(args.workload)
    if args.duration:
        workload_cfg.duration_seconds = args.duration
    if args.repeats:
        exp_cfg.repeats = args.repeats
    if args.output_dir:
        exp_cfg.output_dir = args.output_dir
    if args.figures_dir:
        exp_cfg.figures_dir = args.figures_dir

    # Override policies list if single policy requested
    if args.policy:
        exp_cfg.policies = [args.policy]

    # ── Print experiment banner ─────────────────────────────────────────────
    print()
    print("+--------------------------------------------------------------+")
    print("|   Adaptive GPU Resource Allocation — Multi-Agent Scheduler   |")
    print("+--------------------------------------------------------------+")
    print(f"  Workload : {workload_cfg.name}")
    print(f"  Duration : {workload_cfg.duration_seconds}s per run")
    print(f"  Policies : {exp_cfg.policies}")
    print(f"  Repeats  : {exp_cfg.repeats}")
    print(f"  Agents   : {list(agents_cfg.agents.keys())}")
    print(f"  Rates    : {workload_cfg.arrival_rates}")
    print()

    t_start = time.time()

    # ── Run comparison ──────────────────────────────────────────────────────
    comparison = run_comparison(
        agents_cfg=agents_cfg,
        workload_cfg=workload_cfg,
        policies_cfg=policies_cfg,
        exp_cfg=exp_cfg,
        output_dir=exp_cfg.output_dir,
    )

    # ── Print results table ─────────────────────────────────────────────────
    print_comparison_table(comparison)

    # ── Save JSON summary ───────────────────────────────────────────────────
    json_path = Path(exp_cfg.output_dir) / "comparison_summary.json"
    save_json(comparison, str(json_path))

    # ── Generate plots ──────────────────────────────────────────────────────
    if not args.no_plots:
        plot_bar_comparison(comparison, figures_dir=exp_cfg.figures_dir)

    total_time = time.time() - t_start
    print(f"\n  Total experiment time: {total_time:.1f}s")
    print(f"  Results saved to: {exp_cfg.output_dir}/")
    print(f"  Figures saved to: {exp_cfg.figures_dir}/")
    print()


if __name__ == "__main__":
    main()
