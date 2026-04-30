"""
scheduler/round_robin.py
━━━━━━━━━━━━━━━━━━━━━━━━
Baseline 2 — Round-Robin Allocation.

Rotates a "bonus" GPU share across agents on each update cycle.
One agent gets a boosted share; the rest share what remains equally.

This mimics the paper's round-robin policy where GPU priority
cycles through agents regardless of their actual load.

Allocation at time t for N agents:
  - Active agent (index t % N): gets boost_share
  - All others: split (1 - boost_share) / (N-1) equally
"""
from __future__ import annotations
import time
from typing import Dict, List

from adaptive_gpu.scheduler.policy_interface import AllocationPolicy
from adaptive_gpu.utils.types import AgentState, AllocationResult
from adaptive_gpu.utils.logging import get_logger

logger = get_logger("scheduler.round_robin")


class RoundRobinAllocator(AllocationPolicy):
    name = "round_robin"

    def __init__(self, boost_share: float = 0.55):
        """
        Args:
            boost_share: GPU fraction given to the currently active agent.
                         Remaining (1 - boost_share) is split equally.
        """
        self.boost_share = boost_share
        self._agent_order: List[str] = []
        self._index: int = 0

    def allocate(self, agent_states: Dict[str, AgentState]) -> AllocationResult:
        agents = list(agent_states.keys())

        # Initialise or refresh order on first call / agent change
        if set(agents) != set(self._agent_order):
            self._agent_order = sorted(agents)
            self._index = 0

        n = len(agents)
        if n == 0:
            return AllocationResult(shares={}, timestamp=time.time(), policy=self.name)

        active = self._agent_order[self._index % n]
        self._index += 1

        if n == 1:
            shares = {active: 1.0}
        else:
            remainder = (1.0 - self.boost_share) / (n - 1)
            shares = {
                name: self.boost_share if name == active else remainder
                for name in agents
            }

        logger.debug(f"Round-robin: active={active}, shares={
            {k: round(v, 3) for k, v in shares.items()}
        }")
        return AllocationResult(shares=shares, timestamp=time.time(), policy=self.name)
