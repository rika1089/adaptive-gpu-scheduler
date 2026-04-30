"""
agents/base_agent.py — Abstract base for all simulated agents.

Each agent has:
  - A FIFO request queue
  - A service time distribution (Normal)
  - Priority and min GPU share from config
  - Methods to enqueue, process, and report state
"""
from __future__ import annotations
import time
import random
import threading
from collections import deque
from typing import List, Optional, Deque

from adaptive_gpu.utils.types import Request, AgentState
from adaptive_gpu.config.loader import AgentConfig
from adaptive_gpu.utils.logging import get_logger


class BaseAgent:
    def __init__(self, cfg: AgentConfig, sla_threshold_ms: float = 200.0):
        self.name = cfg.name
        self.priority = cfg.priority
        self.min_gpu_share = cfg.min_gpu_share
        self.service_time_mean_ms = cfg.service_time_mean_ms
        self.service_time_std_ms = cfg.service_time_std_ms
        self.sla_threshold_ms = sla_threshold_ms

        self._queue: Deque[Request] = deque()
        self._lock = threading.Lock()

        # Tracking
        self._arrival_times: List[float] = []
        self._completed: List[Request] = []
        self._sla_violations: int = 0
        self._gpu_share: float = 0.25   # initialised equally

        self.logger = get_logger(f"agent.{self.name}")

    # ── Queue ops ────────────────────────────────────────────────────────────

    def enqueue(self, request: Request) -> None:
        with self._lock:
            self._queue.append(request)
            self._arrival_times.append(request.arrival_time)

    def dequeue(self) -> Optional[Request]:
        with self._lock:
            if self._queue:
                req = self._queue.popleft()
                req.start_service_time = time.time()
                return req
        return None

    def queue_length(self) -> int:
        with self._lock:
            return len(self._queue)

    # ── Service simulation ────────────────────────────────────────────────────

    def simulate_service(self, request: Request) -> Request:
        """
        Simulate inference latency.
        GPU share increases capacity → service time scales inversely with share.
        Base service time is drawn from Normal(mean, std).
        """
        base_ms = max(1.0, random.gauss(
            self.service_time_mean_ms,
            self.service_time_std_ms
        ))
        # GPU share effect: higher share → lower service time (inverse scaling)
        effective_ms = base_ms / max(self._gpu_share, 0.05)
        time.sleep(effective_ms / 1000.0)

        request.completion_time = time.time()
        return request

    def complete(self, request: Request) -> None:
        lat = request.latency_ms or 0.0
        with self._lock:
            self._completed.append(request)
            if lat > self.sla_threshold_ms:
                self._sla_violations += 1

    # ── Metrics ──────────────────────────────────────────────────────────────

    def arrival_rate(self, window_seconds: float = 10.0) -> float:
        now = time.time()
        with self._lock:
            recent = [t for t in self._arrival_times if now - t < window_seconds]
        return len(recent) / window_seconds

    def avg_latency_ms(self) -> float:
        with self._lock:
            if not self._completed:
                return 0.0
            lats = [r.latency_ms for r in self._completed if r.latency_ms is not None]
        return sum(lats) / len(lats) if lats else 0.0

    def p95_latency_ms(self) -> float:
        with self._lock:
            lats = sorted(r.latency_ms for r in self._completed if r.latency_ms)
        if not lats:
            return 0.0
        idx = int(0.95 * len(lats))
        return lats[min(idx, len(lats) - 1)]

    def throughput(self, duration_seconds: float = 60.0) -> float:
        with self._lock:
            return len(self._completed) / max(duration_seconds, 1.0)

    def sla_violation_rate(self) -> float:
        with self._lock:
            total = len(self._completed)
            return self._sla_violations / total if total else 0.0

    def set_gpu_share(self, share: float) -> None:
        self._gpu_share = max(share, 0.01)

    def state_snapshot(self, elapsed_seconds: float = 60.0) -> AgentState:
        return AgentState(
            name=self.name,
            queue_length=self.queue_length(),
            arrival_rate=self.arrival_rate(),
            avg_latency_ms=self.avg_latency_ms(),
            throughput=self.throughput(elapsed_seconds),
            sla_violation_rate=self.sla_violation_rate(),
            gpu_share=self._gpu_share,
        )

    def reset_stats(self) -> None:
        with self._lock:
            self._arrival_times.clear()
            self._completed.clear()
            self._sla_violations = 0
