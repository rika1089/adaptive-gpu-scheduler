"""
tests/test_metrics.py — Tests for metrics collector and utility functions.
"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from adaptive_gpu.metrics.collector import MetricsCollector
from adaptive_gpu.metrics.utilization import jains_fairness_index
from adaptive_gpu.utils.types import AgentState, AllocationResult


def make_state(name, latency=100.0, throughput=1.0, sla=0.05, share=0.25, q=0):
    return AgentState(
        name=name, queue_length=q, arrival_rate=10.0,
        avg_latency_ms=latency, throughput=throughput,
        sla_violation_rate=sla, gpu_share=share,
    )


class TestMetricsCollector:

    def test_record_and_retrieve_snapshots(self):
        col = MetricsCollector("adaptive", "test")
        states = {
            "coord": make_state("coord"),
            "nlp":   make_state("nlp"),
        }
        col.record_snapshot(states, elapsed=5.0)
        assert len(col.snapshots) == 2

    def test_summary_keys_match_agents(self):
        col = MetricsCollector("adaptive", "test")
        agents = ["coord", "nlp", "vision", "reasoning"]
        for i in range(3):
            states = {a: make_state(a) for a in agents}
            col.record_snapshot(states, elapsed=float(i * 5))

        summary = col.summary()
        assert set(summary.keys()) == set(agents)

    def test_csv_export_creates_file(self, tmp_path):
        col = MetricsCollector("static", "test")
        states = {"coord": make_state("coord"), "nlp": make_state("nlp")}
        col.record_snapshot(states, elapsed=10.0)

        out = tmp_path / "metrics.csv"
        col.to_csv(str(out))
        assert out.exists()
        content = out.read_text()
        assert "coord" in content
        assert "avg_latency_ms" in content

    def test_allocation_recording(self):
        col = MetricsCollector("adaptive", "test")
        alloc = AllocationResult(
            shares={"coord": 0.4, "nlp": 0.3, "vision": 0.15, "reasoning": 0.15},
            policy="adaptive",
        )
        col.record_allocation(alloc)
        assert len(col.allocations) == 1
        assert col.allocations[0].policy == "adaptive"


class TestJainsFairnessIndex:

    def test_perfect_fairness(self):
        shares = {"a": 0.25, "b": 0.25, "c": 0.25, "d": 0.25}
        assert abs(jains_fairness_index(shares) - 1.0) < 1e-6

    def test_complete_unfairness(self):
        # One agent gets everything
        shares = {"a": 1.0, "b": 0.0, "c": 0.0, "d": 0.0}
        # J = 1^2 / (4 * 1^2) = 0.25 = 1/N
        assert abs(jains_fairness_index(shares) - 0.25) < 1e-6

    def test_partial_fairness(self):
        shares = {"a": 0.5, "b": 0.3, "c": 0.1, "d": 0.1}
        j = jains_fairness_index(shares)
        assert 0.25 < j < 1.0

    def test_empty_shares(self):
        assert jains_fairness_index({}) == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
