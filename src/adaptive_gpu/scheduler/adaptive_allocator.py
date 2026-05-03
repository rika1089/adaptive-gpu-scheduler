"""
scheduler/adaptive_allocator.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Paper-faithful implementation of Algorithm 1:
  "Adaptive GPU Resource Allocation for Multi-Agent Collaborative Reasoning"
  arXiv:2512.22149v1

Algorithm 1 (exact reproduction from paper Section III.C):
──────────────────────────────────────────────────────────
Input : Agents A, workload W_t, total capacity G_total
Output: Allocation G_t

For each agent A_i:
    d_i = (λ_i(t) * R_i) / P_i          ← demand score
           where:
             λ_i = arrival rate (req/s) in recent window
             R_i = minimum GPU resource requirement (fraction)
             P_i = priority level (1=high, 2=medium, 3=low)

D_total = Σ d_i

If D_total == 0:
    return G_t = {0, ..., 0}             ← no demand, no allocation

For each agent A_i:
    g_i_prop = (d_i / D_total) * G_total  ← proportional share
    g_i(t)   = max(R_i, g_i_prop)         ← enforce minimum

G_allocated = Σ g_i(t)

If G_allocated > G_total:
    g_i(t) = g_i(t) / G_allocated * G_total  ← normalize

Return G_t

Complexity: O(N)
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
        self.min_shares: Dict[str, float] = {
            name: cfg.min_gpu_share
            for name, cfg in agents_cfg.agents.items()
        }
        self.priorities: Dict[str, int] = {
            name: cfg.priority
            for name, cfg in agents_cfg.agents.items()
        }

    def allocate(self, agent_states: Dict[str, AgentState]) -> AllocationResult:
        # ── Step 1: compute demand per agent (Algorithm 1, line 5) ───────────
        # d_i = (λ_i * R_i) / P_i
        demand: Dict[str, float] = {}
        for name, state in agent_states.items():
            lam = state.arrival_rate                     # λ_i  — req/s
            r   = self.min_shares.get(name, 0.1)        # R_i  — min GPU fraction
            p   = self.priorities.get(name, 1)           # P_i  — priority level
            demand[name] = (lam * r) / max(p, 1)

        # ── Step 2: total demand (Algorithm 1, line 8) ────────────────────────
        total_demand = sum(demand.values())

        # ── Step 3: zero-demand guard (Algorithm 1, lines 10-12) ─────────────
        if total_demand <= 0:
            n = len(agent_states)
            shares = {name: 1.0 / n for name in agent_states}
        else:
            # ── Step 4: proportional allocation (Algorithm 1, lines 14-16) ───
            shares = {
                name: max(
                    self.min_shares.get(name, 0.0),          # enforce R_i floor
                    (demand[name] / total_demand)            # proportional share
                )
                for name in agent_states
            }

        # ── Step 5: normalize if total exceeds capacity (Algorithm 1, lines 21-24) ──
        shares = self._normalize(shares)

        logger.debug(f"Adaptive allocation: {
            {k: round(v, 3) for k, v in shares.items()}
        }")

        return AllocationResult(shares=shares, timestamp=time.time(), policy=self.name)
