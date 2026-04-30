"""
scheduler/static_allocator.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Baseline 1 — Static Equal Allocation.

Every agent receives an equal fixed share (1/N) regardless of load.
This is the simplest baseline the paper compares against.
The allocation never changes during the experiment.
"""
from __future__ import annotations
import time
from typing import Dict

from adaptive_gpu.scheduler.policy_interface import AllocationPolicy
from adaptive_gpu.utils.types import AgentState, AllocationResult
from adaptive_gpu.utils.logging import get_logger

logger = get_logger("scheduler.static")


class StaticAllocator(AllocationPolicy):
    name = "static"

    def __init__(self, share_per_agent: float = 0.25):
        """
        Args:
            share_per_agent: fixed GPU fraction per agent (default 0.25 for 4 agents).
        """
        self.share_per_agent = share_per_agent

    def allocate(self, agent_states: Dict[str, AgentState]) -> AllocationResult:
        n = len(agent_states)
        share = 1.0 / n if n > 0 else self.share_per_agent
        shares = {name: share for name in agent_states}

        logger.debug(f"Static allocation: {share:.3f} per agent")
        return AllocationResult(shares=shares, timestamp=time.time(), policy=self.name)
