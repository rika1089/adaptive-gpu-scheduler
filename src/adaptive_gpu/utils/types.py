"""
utils/types.py — Shared dataclasses used across the entire codebase.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional
import time


@dataclass
class Request:
    """A single inference request routed to an agent."""
    request_id: str
    agent_name: str
    query_type: str          # "text", "vision", "logic"
    payload: str
    arrival_time: float = field(default_factory=time.time)
    start_service_time: Optional[float] = None
    completion_time: Optional[float] = None

    @property
    def latency_ms(self) -> Optional[float]:
        if self.arrival_time and self.completion_time:
            return (self.completion_time - self.arrival_time) * 1000
        return None

    @property
    def service_time_ms(self) -> Optional[float]:
        if self.start_service_time and self.completion_time:
            return (self.completion_time - self.start_service_time) * 1000
        return None


@dataclass
class AgentState:
    """Live snapshot of one agent's state — input to allocator."""
    name: str
    queue_length: int
    arrival_rate: float        # requests/sec in recent window
    avg_latency_ms: float
    throughput: float          # completed requests/sec
    sla_violation_rate: float  # 0.0–1.0
    gpu_share: float           # current allocation 0.0–1.0


@dataclass
class AllocationResult:
    """Output of one allocator pass."""
    shares: Dict[str, float]   # agent_name -> GPU share fraction
    timestamp: float = field(default_factory=time.time)
    policy: str = "unknown"
