"""
metrics/utilization.py — GPU utilization and fairness metrics.
"""
from __future__ import annotations
from typing import Dict
from adaptive_gpu.metrics.collector import MetricsCollector


def jains_fairness_index(shares: Dict[str, float]) -> float:
    """
    Jain's Fairness Index: J = (Σx_i)^2 / (N * Σx_i^2)
    Returns 1.0 for perfectly fair allocation, 1/N for completely unfair.
    """
    values = list(shares.values())
    n = len(values)
    if n == 0:
        return 0.0
    numerator = sum(values) ** 2
    denominator = n * sum(v ** 2 for v in values)
    return numerator / denominator if denominator > 0 else 0.0


def avg_gpu_share_per_agent(collector: MetricsCollector) -> Dict[str, float]:
    from collections import defaultdict
    buckets = defaultdict(list)
    for row in collector.snapshots:
        buckets[row.agent].append(row.gpu_share)
    return {
        agent: round(sum(vals) / len(vals), 4)
        for agent, vals in buckets.items()
    }


def avg_fairness(collector: MetricsCollector) -> float:
    """Mean Jain's fairness index over all allocation snapshots."""
    scores = []
    for alloc in collector.allocations:
        scores.append(jains_fairness_index(alloc.shares))
    return round(sum(scores) / len(scores), 4) if scores else 0.0


def sla_violation_rate_per_agent(collector: MetricsCollector) -> Dict[str, float]:
    from collections import defaultdict
    buckets = defaultdict(list)
    for row in collector.snapshots:
        buckets[row.agent].append(row.sla_violation_rate)
    return {
        agent: round(sum(vals) / len(vals), 4)
        for agent, vals in buckets.items()
    }
