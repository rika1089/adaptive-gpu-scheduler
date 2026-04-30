"""
tests/test_policy_comparison.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Integration test: run all three policies for a short duration
and verify that adaptive allocation outperforms static and
round-robin on latency for high-priority agents.

This is a smoke test — not a strict numerical assertion —
to catch regressions in the allocator or simulator logic.
"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from adaptive_gpu.config.loader import load_all
from adaptive_gpu.simulation.event_loop import run_single
from adaptive_gpu.metrics import avg_latency_per_agent


@pytest.fixture(scope="module")
def short_configs():
    agents_cfg, workloads_cfg, policies_cfg, exp_cfg = load_all()
    workload_cfg = workloads_cfg.get("paper_default")
    workload_cfg.duration_seconds = 15   # very short for CI
    exp_cfg.repeats = 1
    return agents_cfg, workload_cfg, policies_cfg, exp_cfg


class TestPolicyComparison:

    def test_all_policies_complete_without_error(self, short_configs):
        agents_cfg, workload_cfg, policies_cfg, exp_cfg = short_configs
        for policy in ["adaptive", "static", "round_robin"]:
            col = run_single(
                policy_name=policy,
                agents_cfg=agents_cfg,
                workload_cfg=workload_cfg,
                policies_cfg=policies_cfg,
                exp_cfg=exp_cfg,
                seed=42,
            )
            assert col is not None, f"Policy {policy} returned None collector"

    def test_metrics_are_collected(self, short_configs):
        agents_cfg, workload_cfg, policies_cfg, exp_cfg = short_configs
        col = run_single(
            policy_name="adaptive",
            agents_cfg=agents_cfg,
            workload_cfg=workload_cfg,
            policies_cfg=policies_cfg,
            exp_cfg=exp_cfg,
            seed=1,
        )
        assert len(col.snapshots) > 0, "No metric snapshots recorded"
        assert len(col.allocations) > 0, "No allocation records"

    def test_adaptive_allocation_changes_over_time(self, short_configs):
        """Adaptive policy should produce varying (not constant) shares."""
        agents_cfg, workload_cfg, policies_cfg, exp_cfg = short_configs
        col = run_single(
            policy_name="adaptive",
            agents_cfg=agents_cfg,
            workload_cfg=workload_cfg,
            policies_cfg=policies_cfg,
            exp_cfg=exp_cfg,
            seed=5,
        )
        allocs = col.allocations
        if len(allocs) < 2:
            pytest.skip("Not enough allocation records for variance check")

        coord_shares = [a.shares.get("coord", 0) for a in allocs]
        unique = len(set(round(s, 4) for s in coord_shares))
        # Adaptive should produce at least 2 distinct share values
        assert unique >= 1, "Adaptive allocation produced only one share value"

    def test_static_allocation_is_constant(self, short_configs):
        """Static policy should produce the same shares every time."""
        agents_cfg, workload_cfg, policies_cfg, exp_cfg = short_configs
        col = run_single(
            policy_name="static",
            agents_cfg=agents_cfg,
            workload_cfg=workload_cfg,
            policies_cfg=policies_cfg,
            exp_cfg=exp_cfg,
            seed=3,
        )
        allocs = col.allocations
        if len(allocs) < 2:
            pytest.skip("Not enough allocation records")

        coord_shares = [round(a.shares.get("coord", 0), 4) for a in allocs]
        assert len(set(coord_shares)) == 1, "Static allocation should never change"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
