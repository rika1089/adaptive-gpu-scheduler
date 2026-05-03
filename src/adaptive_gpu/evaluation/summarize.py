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

# Formal names for agents to match paper
AGENT_DISPLAY_NAMES = {
    "coord": "Coordinator",
    "nlp": "Specialist (NLP)",
    "vision": "Specialist (Vision)",
    "reasoning": "Specialist (Reasoning)"
}

def format_latency(ms: float) -> str:
    if ms >= 1000:
        return f"{ms/1000:.1f}s"
    return f"{ms:.0f}ms"

# ── Console table ─────────────────────────────────────────────────────────────

def print_comparison_table(comparison: Dict[str, Dict]) -> None:
    agents = [k for k in next(iter(comparison.values())).keys() if not k.startswith("_")]
    policies = list(comparison.keys())

    header_width = 16
    col_width = 12

    def hr():
        print("-" * (header_width + col_width * len(policies) + len(policies) + 1))

    print()
    print("=" * (header_width + col_width * len(policies) + len(policies) + 1))
    print("  POLICY COMPARISON RESULTS (ALIGNED WITH PAPER)")
    print("=" * (header_width + col_width * len(policies) + len(policies) + 1))

    # Header row
    header = f"{'':>{header_width}}" + "".join(f" {p:>{col_width}}" for p in policies)
    print(header)
    hr()

    metrics_to_show = [
        ("avg_latency_ms",    "Avg Latency"),
        ("avg_throughput",    "Throughput (r/s)"),
        ("avg_sla_violation", "SLA Violation %"),
        ("avg_gpu_share",     "Avg GPU Share"),
    ]

    for agent in agents:
        disp_name = AGENT_DISPLAY_NAMES.get(agent, agent.upper())
        print(f"\n  Agent: {disp_name}")
        for metric_key, metric_label in metrics_to_show:
            row = f"  {metric_label:>{header_width - 2}}"
            for policy in policies:
                val = comparison[policy].get(agent, {}).get(metric_key, 0)
                if metric_key == "avg_sla_violation":
                    row += f" {val * 100:>{col_width}.1f}%"
                elif metric_key == "avg_latency_ms":
                    row += f" {format_latency(val):>{col_width}}"
                else:
                    row += f" {val:>{col_width}.3f}"
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
    # STRICT PAPER ORDER for Figure 2 Parity
    PAPER_ORDER = ["static", "round_robin", "adaptive"]
    policies = [p for p in PAPER_ORDER if p in comparison]
    
    x = np.arange(len(agents))
    width = 0.25
    colors_map = {"adaptive": "#2E7D32", "static": "#1565C0", "round_robin": "#EF6C00"} # Aligned with paper colors
    
    agent_labels = [AGENT_DISPLAY_NAMES.get(a, a.upper()) for a in agents]

    # ── Latency bar chart ────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Check if we should use seconds instead of ms
    all_lats = [comparison[p].get(a, {}).get("avg_latency_ms", 0) for p in policies for a in agents]
    use_seconds = any(l > 1000 for l in all_lats)
    unit_scale = 1000 if use_seconds else 1
    ylabel = "Avg Latency (s)" if use_seconds else "Avg Latency (ms)"
    
    # Map internal names to paper legend labels
    LEGEND_LABELS = {
        "adaptive": "Adaptive (Proposed)",
        "static": "Static Equal",
        "round_robin": "Round Robin"
    }

    for i, policy in enumerate(policies):
        vals = [comparison[policy].get(a, {}).get("avg_latency_ms", 0) / unit_scale for a in agents]
        bars = ax.bar(x + i * width, vals, width, 
                      label=LEGEND_LABELS.get(policy.lower(), policy.upper()),
                      color=colors_map.get(policy.lower(), "#9E9E9E"), alpha=0.85)
        ax.bar_label(bars, fmt="%.1f", fontsize=8, padding=3)

    ax.set_xlabel("Agent")
    ax.set_ylabel(ylabel)
    ax.set_title("(a) Average Latency by Agent", loc='center')
    ax.set_xticks(x + width)
    ax.set_xticklabels([a.lower() for a in agents], rotation=45)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    out = Path(figures_dir) / "latency_comparison.png"
    plt.savefig(out, dpi=200)
    plt.close()
    logger.info(f"Plot → {out}")

    # ── Throughput bar chart ─────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, policy in enumerate(policies):
        vals = [comparison[policy].get(a, {}).get("avg_throughput", 0) for a in agents]
        bars = ax.bar(x + i * width, vals, width, 
                      label=LEGEND_LABELS.get(policy.lower(), policy.upper()),
                      color=colors_map.get(policy.lower(), "#9E9E9E"), alpha=0.85)
        ax.bar_label(bars, fmt="%.1f", fontsize=8, padding=3)

    ax.set_xlabel("Agent")
    ax.set_ylabel("Throughput (req/s)")
    ax.set_title("(b) Average Throughput by Agent", loc='center')
    ax.set_xticks(x + width)
    ax.set_xticklabels([a.lower() for a in agents], rotation=45)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    out = Path(figures_dir) / "throughput_comparison.png"
    plt.savefig(out, dpi=200)
    plt.close()
    logger.info(f"Plot → {out}")

    # ── SLA violation chart ──────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, policy in enumerate(policies):
        vals = [comparison[policy].get(a, {}).get("avg_sla_violation", 0) * 100 for a in agents]
        bars = ax.bar(x + i * width, vals, width, label=policy.upper(),
                      color=colors_map.get(policy, "#9E9E9E"), alpha=0.85)
        ax.bar_label(bars, fmt="%.1f%%", fontsize=8, padding=3)

    ax.set_xlabel("Agent Server Type")
    ax.set_ylabel("SLA Violation Rate (%)")
    ax.set_title("SLA Violations (Threshold: 200ms)")
    ax.set_xticks(x + width)
    ax.set_xticklabels(agent_labels, rotation=15)
    ax.legend()
    ax.set_ylim(0, 110)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    out = Path(figures_dir) / "sla_comparison.png"
    plt.savefig(out, dpi=200)
    plt.close()
    logger.info(f"Plot → {out}")

    # ── Fairness bar ─────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))
    fair_vals = [comparison[p].get("_fairness", 0) for p in policies]
    bars = ax.bar([p.upper() for p in policies], fair_vals,
                  color=[colors_map.get(p, "#9E9E9E") for p in policies], alpha=0.85)
    ax.bar_label(bars, fmt="%.3f", fontsize=10, padding=3)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Jain's Fairness Index")
    ax.set_title("Resource Allocation Fairness")
    ax.axhline(1.0, color="gray", linestyle="--", linewidth=0.8)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    out = Path(figures_dir) / "fairness_comparison.png"
    plt.savefig(out, dpi=200)
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

    fig, ax = plt.subplots(figsize=(11, 6))
    for agent in agents:
        vals = [a.shares.get(agent, 0) for a in allocs]
        label = AGENT_DISPLAY_NAMES.get(agent, agent.upper())
        ax.plot(times, vals, label=label, linewidth=2.0,
                color=colors_a.get(agent, None))

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("GPU Share Fraction")
    ax.set_title(f"Dynamic GPU Allocation Over Time (Policy: {collector.policy_name.upper()})")
    ax.legend(loc='upper right')
    ax.set_ylim(0, 0.7)
    ax.grid(linestyle="--", alpha=0.3)
    plt.tight_layout()
    out = Path(figures_dir) / f"allocation_over_time_{collector.policy_name}.png"
    plt.savefig(out, dpi=200)
    plt.close()
    logger.info(f"Plot → {out}")
