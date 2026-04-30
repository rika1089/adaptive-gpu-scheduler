"""
simulation/environment.py
━━━━━━━━━━━━━━━━━━━━━━━━━
Ties together agents, workload generator, allocator, and metrics.

Responsibilities:
  1. Accept incoming requests from the workload generator.
  2. Route each request to the correct agent queue.
  3. Spin up worker threads that pull from each queue and simulate service.
  4. Periodically call the allocator and push new GPU shares to agents.
  5. Log metrics snapshots at a configurable interval.
"""
from __future__ import annotations
import time
import random
import threading
from typing import Dict

from adaptive_gpu.agents.base_agent import BaseAgent
from adaptive_gpu.scheduler.policy_interface import AllocationPolicy
from adaptive_gpu.simulation.gpu_model import GPUModel
from adaptive_gpu.metrics.collector import MetricsCollector
from adaptive_gpu.utils.types import Request
from adaptive_gpu.utils.logging import get_logger

logger = get_logger("simulation.environment")


class SimulationEnvironment:
    def __init__(
        self,
        agents: Dict[str, BaseAgent],
        policy: AllocationPolicy,
        metrics_collector: MetricsCollector,
        allocation_interval_s: float = 5.0,
        metrics_interval_s: float = 5.0,
        n_workers_per_agent: int = 4,
    ):
        self.agents = agents
        self.policy = policy
        self.collector = metrics_collector
        self.allocation_interval = allocation_interval_s
        self.metrics_interval = metrics_interval_s
        self.n_workers = n_workers_per_agent

        self.gpu_model = GPUModel()
        self._stop_event = threading.Event()
        self._worker_threads: list = []
        self._alloc_thread: threading.Thread = None
        self._metrics_thread: threading.Thread = None
        self._start_time: float = 0.0
        self._elapsed: float = 1.0

    # ── Request ingestion ──────────────────────────────────────────────────

    def receive_request(self, request: Request) -> None:
        """Called by workload generator; routes to agent queue."""
        agent = self.agents.get(request.agent_name)
        if agent:
            agent.enqueue(request)
        else:
            logger.warning(f"Unknown agent '{request.agent_name}' — dropping request")

    # ── Worker threads (one per agent, N workers each) ─────────────────────

    def _worker_loop(self, agent: BaseAgent) -> None:
        while not self._stop_event.is_set():
            req = agent.dequeue()
            if req is None:
                self._stop_event.wait(timeout=0.001)
                continue

            # GPU-aware service time
            base_ms = max(1.0, random.gauss(
                agent.service_time_mean_ms,
                agent.service_time_std_ms,
            ))
            effective_ms = self.gpu_model.effective_service_time_ms(
                base_ms,
                agent._gpu_share,
                n_agents=len(self.agents),
            )
            self._stop_event.wait(timeout=effective_ms / 1000.0)
            if self._stop_event.is_set():
                break

            req.completion_time = time.time()
            agent.complete(req)

    # ── Allocation control loop ─────────────────────────────────────────────

    def _allocation_loop(self) -> None:
        while not self._stop_event.is_set():
            self._stop_event.wait(timeout=self.allocation_interval)
            if self._stop_event.is_set():
                break

            states = {
                name: agent.state_snapshot(self._elapsed)
                for name, agent in self.agents.items()
            }
            result = self.policy.allocate(states)

            for name, share in result.shares.items():
                if name in self.agents:
                    self.agents[name].set_gpu_share(share)

            self.collector.record_allocation(result)
            logger.debug(f"[{self.policy.name}] New shares: {
                {k: round(v, 3) for k, v in result.shares.items()}
            }")

    # ── Metrics snapshot loop ───────────────────────────────────────────────

    def _metrics_loop(self) -> None:
        while not self._stop_event.is_set():
            self._stop_event.wait(timeout=self.metrics_interval)
            if self._stop_event.is_set():
                break

            self._elapsed = time.time() - self._start_time + 1.0
            states = {
                name: agent.state_snapshot(self._elapsed)
                for name, agent in self.agents.items()
            }
            self.collector.record_snapshot(states, elapsed=self._elapsed)

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def start(self) -> None:
        self._stop_event.clear()
        self._start_time = time.time()

        # Start worker threads for each agent
        for agent in self.agents.values():
            for _ in range(self.n_workers):
                t = threading.Thread(
                    target=self._worker_loop,
                    args=(agent,),
                    daemon=True,
                    name=f"worker-{agent.name}",
                )
                self._worker_threads.append(t)
                t.start()

        # Start allocation control loop
        self._alloc_thread = threading.Thread(
            target=self._allocation_loop, daemon=True, name="allocator"
        )
        self._alloc_thread.start()

        # Start metrics snapshot loop
        self._metrics_thread = threading.Thread(
            target=self._metrics_loop, daemon=True, name="metrics"
        )
        self._metrics_thread.start()

        logger.info(f"Simulation started - policy={self.policy.name}, "
                    f"agents={list(self.agents.keys())}")

    def stop(self) -> None:
        self._stop_event.set()
        for t in self._worker_threads:
            t.join(timeout=2.0)
        if self._alloc_thread:
            self._alloc_thread.join(timeout=2.0)
        if self._metrics_thread:
            self._metrics_thread.join(timeout=2.0)
        logger.info("Simulation stopped.")
