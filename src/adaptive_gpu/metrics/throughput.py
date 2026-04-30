"""
metrics/throughput.py — Throughput statistics from collector snapshots.
"""
from __future__ import annotations
from typing import Dict, List
from adaptive_gpu.metrics.collector import MetricsCollector


def avg_throughput_per_agent(collector: MetricsCollector) -> Dict[str, float]:
    from collections import defaultdict
    buckets = defaultdict(list)
    for row in collector.snapshots:
        buckets[row.agent].append(row.throughput)
    return {
        agent: round(sum(vals) / len(vals), 4)
        for agent, vals in buckets.items()
    }


def throughput_over_time(collector: MetricsCollector, agent: str) -> List[tuple]:
    return [
        (row.elapsed_s, row.throughput)
        for row in collector.snapshots
        if row.agent == agent
    ]
