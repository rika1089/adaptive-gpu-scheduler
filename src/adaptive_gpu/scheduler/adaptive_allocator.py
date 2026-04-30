"""
scheduler/adaptive_allocator.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Paper-faithful implementation of Algorithm 1:
  "Adaptive GPU Resource Allocation for Multi-Agent Collaborative Reasoning"

Algorithm 1 (reproduced):
─────────────────────────
Input : agent states {λ_i, Q_i, P_i, R_i}  for i in agents
Output: GPU share allocation {s_i}

1. For each agent i:
       demand_i = (λ_i + α * Q_i) / P_i
          where:
            λ_i = arrival rate (req/s) in recent window
            Q_i = current queue backlog
            α   = queue weight (default 0.5)
            P_i = priority (lower = more important)

2. total_demand = Σ demand_i

3. If total_demand == 0:
       s_i = 1/N  for all i   (equal fallback)
   Else:
       s_i = demand_i / total_demand   (proportional)

4. Enforce minimum share:
       s_i = max(s_i, R_i)

5. Re-normalise so Σ s_i = 1.0

6. Return {s_i}
"""
from __future__ import annotations
import time
from typing import Dict

from adaptive_gpu.scheduler.policy_interface import AllocationPolicy
from adaptive_gpu.utils.types import AgentState, AllocationResult
from adaptive_gpu.config.loader import AgentsConfig, PoliciesConfig
from adaptive_gpu.utils.logging import get_logger

logger = get_logger("scheduler.adaptive")


class AdaptiveAllocator(AllocationPolicy):
    name = "adaptive"

    def __init__(self, agents_cfg: AgentsConfig, policies_cfg: PoliciesConfig):
        policy = policies_cfg.get("adaptive")
        self.alpha = policy.queue_weight_alpha          # queue backlog weight
        self.min_shares: Dict[str, float] = {
            name: cfg.min_gpu_share
            for name, cfg in agents_cfg.agents.items()
        }
        self.priorities: Dict[str, int] = {
            name: cfg.priority
            for name, cfg in agents_cfg.agents.items()
        }

    def allocate(self, agent_states: Dict[str, AgentState]) -> AllocationResult:
        # ── Step 1: compute demand per agent ──────────────────────────────
        demand: Dict[str, float] = {}
        for name, state in agent_states.items():
            lam = state.arrival_rate                     # λ_i
            q   = state.queue_length                     # Q_i
            p   = self.priorities.get(name, 1)           # P_i  (lower = higher priority)
            demand[name] = (lam + self.alpha * q) / max(p, 1)

        # ── Step 2: total demand ──────────────────────────────────────────
        total_demand = sum(demand.values())

        # ── Step 3: proportional allocation or equal fallback ─────────────
        if total_demand <= 0:
            n = len(agent_states)
            shares = {name: 1.0 / n for name in agent_states}
        else:
            shares = {name: demand[name] / total_demand for name in agent_states}

        # ── Step 4: enforce minimum share ─────────────────────────────────
        for name in shares:
            shares[name] = max(shares[name], self.min_shares.get(name, 0.0))

        # ── Step 5: re-normalise ──────────────────────────────────────────
        shares = self._normalize(shares)

        logger.debug(f"Adaptive allocation: {
            {k: round(v, 3) for k, v in shares.items()}
        }")

        return AllocationResult(shares=shares, timestamp=time.time(), policy=self.name)
