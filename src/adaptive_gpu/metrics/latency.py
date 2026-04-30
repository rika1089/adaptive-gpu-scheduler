"""
metrics/latency.py — Latency statistics computed from collector snapshots.
"""
from __future__ import annotations
from typing import Dict, List
from adaptive_gpu.metrics.collector import MetricsCollector


def avg_latency_per_agent(collector: MetricsCollector) -> Dict[str, float]:
    """Return mean avg_latency_ms per agent across all snapshots."""
    from collections import defaultdict
    buckets = defaultdict(list)
    for row in collector.snapshots:
        if row.avg_latency_ms > 0:
            buckets[row.agent].append(row.avg_latency_ms)
    return {
        agent: round(sum(vals) / len(vals), 2)
        for agent, vals in buckets.items()
    }


def latency_over_time(collector: MetricsCollector, agent: str) -> List[tuple]:
    """Return list of (elapsed_s, avg_latency_ms) for a single agent."""
    return [
        (row.elapsed_s, row.avg_latency_ms)
        for row in collector.snapshots
        if row.agent == agent and row.avg_latency_ms > 0
    ]
