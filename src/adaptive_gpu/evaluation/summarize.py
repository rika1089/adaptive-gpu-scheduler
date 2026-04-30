"""
evaluation/summarize.py
━━━━━━━━━━━━━━━━━━━━━━━
Produces:
  1. A printed comparison table (console)
  2. Bar charts: latency, throughput, SLA per policy (matplotlib)
  3. GPU share over time line chart
  4. A JSON summary file
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict

from adaptive_gpu.utils.logging import get_logger

logger = get_logger("evaluation.summarize")


# ── Console table ─────────────────────────────────────────────────────────────

def print_comparison_table(comparison: Dict[str, Dict]) -> None:
    agents = [k for k in next(iter(comparison.values())).keys() if not k.startswith("_")]
    policies = list(comparison.keys())

    header_width = 14
    col_width = 12

    def hr():
        print("-" * (header_width + col_width * len(policies) + len(policies) + 1))

    print()
    print("=" * (header_width + col_width * len(policies) + len(policies) + 1))
    print("  POLICY COMPARISON RESULTS")
    print("=" * (header_width + col_width * len(policies) + len(policies) + 1))

    # Header row
    header = f"{'':>{header_width}}" + "".join(f" {p:>{col_width}}" for p in policies)
    print(header)
    hr()

    metrics_to_show = [
        ("avg_latency_ms",    "Avg Latency (ms)"),
        ("avg_throughput",    "Throughput (r/s)"),
        ("avg_sla_violation", "SLA Violation %"),
        ("avg_gpu_share",     "Avg GPU Share"),
    ]

    for agent in agents:
        print(f"\n  Agent: {agent.upper()}")
        for metric_key, metric_label in metrics_to_show:
            row = f"  {metric_label:>{header_width - 2}}"
            for policy in policies:
                val = comparison[policy].get(agent, {}).get(metric_key, 0)
                if metric_key == "avg_sla_violation":
                    row += f" {val * 100:>{col_width}.2f}%"[:-1]
                else:
                    row += f" {val:>{col_width}.4f}"
            print(row)

    hr()
    print(f"  {'Jain Fairness':>{header_width - 2}}", end="")
    for policy in policies:
        val = comparison[policy].get("_fairness", 0)
        print(f" {val:>{col_width}.4f}", end="")
    print()
    print("=" * (header_width + col_width * len(policies) + len(policies) + 1))


# ── JSON export ────────────────────────────────────────────────────────────────

def save_json(comparison: Dict, path: str) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(comparison, f, indent=2)
    logger.info(f"Summary JSON → {out}")
    return out


# ── Matplotlib plots ───────────────────────────────────────────────────────────

def plot_bar_comparison(comparison: Dict, figures_dir: str = "output/figures") -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        logger.warning("matplotlib not installed — skipping plots. Run: pip install matplotlib")
        return

    Path(figures_dir).mkdir(parents=True, exist_ok=True)
    agents = [k for k in next(iter(comparison.values())).keys() if not k.startswith("_")]
    policies = list(comparison.keys())
    x = np.arange(len(agents))
    width = 0.25
    colors_map = {"adaptive": "#2196F3", "static": "#FF9800", "round_robin": "#4CAF50"}

    # ── Latency bar chart ────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, policy in enumerate(policies):
        vals = [comparison[policy].get(a, {}).get("avg_latency_ms", 0) for a in agents]
        bars = ax.bar(x + i * width, vals, width, label=policy,
                      color=colors_map.get(policy, "#9E9E9E"), alpha=0.85)
        ax.bar_label(bars, fmt="%.1f", fontsize=7, padding=2)

    ax.set_xlabel("Agent")
    ax.set_ylabel("Avg Latency (ms)")
    ax.set_title("Average End-to-End Latency per Agent × Policy")
    ax.set_xticks(x + width)
    ax.set_xticklabels([a.upper() for a in agents])
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    out = Path(figures_dir) / "latency_comparison.png"
    plt.savefig(out, dpi=150)
    plt.close()
    logger.info(f"Plot → {out}")

    # ── Throughput bar chart ─────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, policy in enumerate(policies):
        vals = [comparison[policy].get(a, {}).get("avg_throughput", 0) for a in agents]
        bars = ax.bar(x + i * width, vals, width, label=policy,
                      color=colors_map.get(policy, "#9E9E9E"), alpha=0.85)
        ax.bar_label(bars, fmt="%.3f", fontsize=7, padding=2)

    ax.set_xlabel("Agent")
    ax.set_ylabel("Throughput (req/s)")
    ax.set_title("Average Throughput per Agent × Policy")
    ax.set_xticks(x + width)
    ax.set_xticklabels([a.upper() for a in agents])
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    out = Path(figures_dir) / "throughput_comparison.png"
    plt.savefig(out, dpi=150)
    plt.close()
    logger.info(f"Plot → {out}")

    # ── SLA violation chart ──────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, policy in enumerate(policies):
        vals = [comparison[policy].get(a, {}).get("avg_sla_violation", 0) * 100 for a in agents]
        bars = ax.bar(x + i * width, vals, width, label=policy,
                      color=colors_map.get(policy, "#9E9E9E"), alpha=0.85)
        ax.bar_label(bars, fmt="%.1f%%", fontsize=7, padding=2)

    ax.set_xlabel("Agent")
    ax.set_ylabel("SLA Violation Rate (%)")
    ax.set_title("SLA Violation Rate per Agent × Policy")
    ax.set_xticks(x + width)
    ax.set_xticklabels([a.upper() for a in agents])
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    out = Path(figures_dir) / "sla_comparison.png"
    plt.savefig(out, dpi=150)
    plt.close()
    logger.info(f"Plot → {out}")

    # ── Fairness bar ─────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(6, 4))
    fair_vals = [comparison[p].get("_fairness", 0) for p in policies]
    bars = ax.bar(policies, fair_vals,
                  color=[colors_map.get(p, "#9E9E9E") for p in policies], alpha=0.85)
    ax.bar_label(bars, fmt="%.4f", fontsize=9, padding=2)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Jain's Fairness Index")
    ax.set_title("GPU Allocation Fairness (Jain's Index)")
    ax.axhline(1.0, color="gray", linestyle="--", linewidth=0.8)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    out = Path(figures_dir) / "fairness_comparison.png"
    plt.savefig(out, dpi=150)
    plt.close()
    logger.info(f"Plot → {out}")


def plot_allocation_over_time(collector, figures_dir: str = "output/figures") -> None:
    """Line chart of GPU share per agent over time for a single policy run."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from collections import defaultdict
    except ImportError:
        return

    Path(figures_dir).mkdir(parents=True, exist_ok=True)
    allocs = collector.allocations
    if not allocs:
        return

    agents = list(allocs[0].shares.keys())
    t0 = allocs[0].timestamp
    times = [(a.timestamp - t0) for a in allocs]
    colors_a = {"coord": "#1565C0", "nlp": "#2E7D32", "vision": "#E65100", "reasoning": "#6A1B9A"}

    fig, ax = plt.subplots(figsize=(10, 5))
    for agent in agents:
        vals = [a.shares.get(agent, 0) for a in allocs]
        ax.plot(times, vals, label=agent.upper(), linewidth=1.8,
                color=colors_a.get(agent, None))

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("GPU Share Fraction")
    ax.set_title(f"GPU Allocation Over Time - Policy: {collector.policy_name.upper()}")
    ax.legend()
    ax.set_ylim(0, 0.7)
    ax.grid(linestyle="--", alpha=0.5)
    plt.tight_layout()
    out = Path(figures_dir) / f"allocation_over_time_{collector.policy_name}.png"
    plt.savefig(out, dpi=150)
    plt.close()
    logger.info(f"Plot → {out}")
