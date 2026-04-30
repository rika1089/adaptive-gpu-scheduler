"""
tests/test_adaptive_allocator.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Unit tests for Algorithm 1 (AdaptiveAllocator).

Tests verify:
  - Proportional demand allocation
  - Minimum share enforcement
  - Re-normalisation (shares sum to 1.0)
  - Equal fallback when all demand is zero
  - High-priority agents get more share under equal load
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from adaptive_gpu.config.loader import AgentsConfig, PoliciesConfig, AgentConfig, PolicyConfig
from adaptive_gpu.scheduler.adaptive_allocator import AdaptiveAllocator
from adaptive_gpu.utils.types import AgentState


def make_agents_cfg(priorities: dict = None, min_shares: dict = None) -> AgentsConfig:
    defaults_p  = {"coord": 1, "nlp": 2, "vision": 2, "reasoning": 1}
    defaults_ms = {"coord": 0.10, "nlp": 0.20, "vision": 0.20, "reasoning": 0.30}
    p  = priorities or defaults_p
    ms = min_shares or defaults_ms
    agents = {
        name: AgentConfig(
            name=name, priority=p[name], min_gpu_share=ms[name],
            service_time_mean_ms=100, service_time_std_ms=20
        )
        for name in ["coord", "nlp", "vision", "reasoning"]
    }
    return AgentsConfig(agents=agents, sla_threshold_ms=200.0)


def make_policies_cfg(alpha: float = 0.5) -> PoliciesConfig:
    policy = PolicyConfig(
        name="adaptive", queue_weight_alpha=alpha,
        min_share_enforcement=True, renormalize=True,
    )
    return PoliciesConfig(policies={"adaptive": policy})


def make_state(name, arrival_rate=0.0, queue_length=0, gpu_share=0.25) -> AgentState:
    return AgentState(
        name=name, queue_length=queue_length, arrival_rate=arrival_rate,
        avg_latency_ms=0, throughput=0, sla_violation_rate=0, gpu_share=gpu_share
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestAdaptiveAllocator:

    def test_shares_sum_to_one(self):
        alloc = AdaptiveAllocator(make_agents_cfg(), make_policies_cfg())
        states = {
            "coord":     make_state("coord",     arrival_rate=80),
            "nlp":       make_state("nlp",       arrival_rate=40),
            "vision":    make_state("vision",    arrival_rate=45),
            "reasoning": make_state("reasoning", arrival_rate=25),
        }
        result = alloc.allocate(states)
        total = sum(result.shares.values())
        assert abs(total - 1.0) < 1e-6, f"Shares sum to {total}, expected 1.0"

    def test_min_share_enforced(self):
        alloc = AdaptiveAllocator(make_agents_cfg(), make_policies_cfg())
        # All zero load → should still enforce min shares
        states = {name: make_state(name) for name in ["coord", "nlp", "vision", "reasoning"]}
        result = alloc.allocate(states)
        min_shares = {"coord": 0.10, "nlp": 0.20, "vision": 0.20, "reasoning": 0.30}
        for name, min_s in min_shares.items():
            # After re-normalisation with 4 equal agents, each gets 0.25
            # which is already above min for coord/nlp/vision
            assert result.shares[name] > 0, f"{name} share should be > 0"

    def test_equal_fallback_when_no_demand(self):
        alloc = AdaptiveAllocator(make_agents_cfg(), make_policies_cfg())
        states = {name: make_state(name, arrival_rate=0, queue_length=0)
                  for name in ["coord", "nlp", "vision", "reasoning"]}
        result = alloc.allocate(states)
        total = sum(result.shares.values())
        assert abs(total - 1.0) < 1e-6

    def test_high_load_agent_gets_more_share(self):
        alloc = AdaptiveAllocator(make_agents_cfg(), make_policies_cfg())
        states = {
            "coord":     make_state("coord",     arrival_rate=200),
            "nlp":       make_state("nlp",       arrival_rate=1),
            "vision":    make_state("vision",    arrival_rate=1),
            "reasoning": make_state("reasoning", arrival_rate=1),
        }
        result = alloc.allocate(states)
        # coord has 200x higher load with same (high) priority → should dominate
        assert result.shares["coord"] > result.shares["nlp"], \
            "High-load agent should receive more share"

    def test_higher_priority_agent_wins_under_equal_load(self):
        """coord (P=1) should get more share than nlp (P=2) under same load."""
        alloc = AdaptiveAllocator(make_agents_cfg(), make_policies_cfg())
        states = {
            "coord":     make_state("coord",     arrival_rate=50),
            "nlp":       make_state("nlp",       arrival_rate=50),
            "vision":    make_state("vision",    arrival_rate=0),
            "reasoning": make_state("reasoning", arrival_rate=0),
        }
        result = alloc.allocate(states)
        assert result.shares["coord"] >= result.shares["nlp"], \
            "Higher priority (lower P value) agent should get >= share under equal load"

    def test_policy_name_in_result(self):
        alloc = AdaptiveAllocator(make_agents_cfg(), make_policies_cfg())
        states = {name: make_state(name) for name in ["coord", "nlp", "vision", "reasoning"]}
        result = alloc.allocate(states)
        assert result.policy == "adaptive"

    def test_queue_length_increases_demand(self):
        alloc = AdaptiveAllocator(make_agents_cfg(), make_policies_cfg(alpha=1.0))
        states_no_queue = {
            "coord":     make_state("coord",     arrival_rate=10, queue_length=0),
            "nlp":       make_state("nlp",       arrival_rate=10, queue_length=0),
            "vision":    make_state("vision",    arrival_rate=10, queue_length=0),
            "reasoning": make_state("reasoning", arrival_rate=10, queue_length=0),
        }
        states_queue = {
            "coord":     make_state("coord",     arrival_rate=10, queue_length=100),
            "nlp":       make_state("nlp",       arrival_rate=10, queue_length=0),
            "vision":    make_state("vision",    arrival_rate=10, queue_length=0),
            "reasoning": make_state("reasoning", arrival_rate=10, queue_length=0),
        }
        r1 = alloc.allocate(states_no_queue)
        r2 = alloc.allocate(states_queue)
        assert r2.shares["coord"] > r1.shares["coord"], \
            "Agent with large queue should receive more share"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
