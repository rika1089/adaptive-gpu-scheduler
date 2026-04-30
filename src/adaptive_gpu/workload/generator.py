"""
workload/generator.py — Synthetic workload generator.

Generates requests per agent at configurable Poisson arrival rates,
matching the paper's workload model (Table 1: 80/40/45/25 req/s).
"""
from __future__ import annotations
import time
import random
import threading
import uuid
from typing import Dict, Callable, Optional

from adaptive_gpu.utils.types import Request
from adaptive_gpu.config.loader import WorkloadConfig
from adaptive_gpu.utils.logging import get_logger

logger = get_logger("workload.generator")

QUERY_TYPE_MAP = {
    "coord": "text",
    "nlp": "text",
    "vision": "vision",
    "reasoning": "logic",
}

SAMPLE_QUERIES = {
    "text":   ["Summarise climate change", "Explain transformer architecture",
               "What is reinforcement learning?", "Describe photosynthesis"],
    "vision": ["Describe this image", "What objects are visible?",
               "Identify the scene", "Caption this photo"],
    "logic":  ["If A implies B and B implies C, does A imply C?",
               "Solve: 3x + 5 = 20", "Find the next term: 2 4 8 16 ...",
               "What has keys but no locks?"],
}


class WorkloadGenerator:
    """
    Launches one thread per agent. Each thread sleeps for an
    exponentially-distributed inter-arrival time (Poisson process)
    then calls the registered callback with a new Request.
    """

    def __init__(self, workload_cfg: WorkloadConfig, seed: int = 42):
        self.cfg = workload_cfg
        self._threads: Dict[str, threading.Thread] = {}
        self._stop_event = threading.Event()
        self._callbacks: Dict[str, Callable[[Request], None]] = {}
        random.seed(seed)

    def register(self, agent_name: str, callback: Callable[[Request], None]) -> None:
        """Register a function to be called when a new request arrives for agent_name."""
        self._callbacks[agent_name] = callback

    def _generate_for_agent(self, agent_name: str, rate: float) -> None:
        """Thread target: continuously generate requests at `rate` req/s."""
        if rate <= 0:
            return
        mean_interval = 1.0 / rate
        qtype = QUERY_TYPE_MAP.get(agent_name, "text")
        callback = self._callbacks.get(agent_name)

        while not self._stop_event.is_set():
            interval = random.expovariate(rate)   # Poisson inter-arrival
            self._stop_event.wait(timeout=interval)
            if self._stop_event.is_set():
                break

            req = Request(
                request_id=str(uuid.uuid4())[:8],
                agent_name=agent_name,
                query_type=qtype,
                payload=random.choice(SAMPLE_QUERIES[qtype]),
            )
            if callback:
                callback(req)

    def start(self) -> None:
        self._stop_event.clear()
        for agent, rate in self.cfg.arrival_rates.items():
            t = threading.Thread(
                target=self._generate_for_agent,
                args=(agent, rate),
                daemon=True,
                name=f"gen-{agent}",
            )
            self._threads[agent] = t
            t.start()
        logger.info(f"Workload '{self.cfg.name}' started - rates: {self.cfg.arrival_rates}")

    def stop(self) -> None:
        self._stop_event.set()
        for t in self._threads.values():
            t.join(timeout=2.0)
        logger.info("Workload generator stopped.")

    def is_running(self) -> bool:
        return not self._stop_event.is_set()
