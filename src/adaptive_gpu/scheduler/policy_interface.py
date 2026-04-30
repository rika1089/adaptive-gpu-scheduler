"""
scheduler/policy_interface.py — Abstract base class for all allocation policies.

Every policy must implement:
  allocate(agent_states) -> AllocationResult
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict

from adaptive_gpu.utils.types import AgentState, AllocationResult


class AllocationPolicy(ABC):
    name: str = "base"

    @abstractmethod
    def allocate(self, agent_states: Dict[str, AgentState]) -> AllocationResult:
        """
        Given a snapshot of all agent states, compute GPU share allocations.

        Args:
            agent_states: dict of agent_name -> AgentState

        Returns:
            AllocationResult with shares summing to ~1.0
        """
        ...

    def _normalize(self, shares: Dict[str, float]) -> Dict[str, float]:
        total = sum(shares.values())
        if total <= 0:
            n = len(shares)
            return {k: 1.0 / n for k in shares}
        return {k: v / total for k, v in shares.items()}
