"""
tests/test_workload_generator.py — Tests for the Poisson workload generator.
"""
import sys
import time
import threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from adaptive_gpu.config.loader import WorkloadConfig
from adaptive_gpu.workload.generator import WorkloadGenerator
from adaptive_gpu.utils.types import Request


def make_workload(rates: dict = None, duration: int = 10) -> WorkloadConfig:
    return WorkloadConfig(
        name="test",
        description="test workload",
        duration_seconds=duration,
        arrival_rates=rates or {"coord": 5, "nlp": 5, "vision": 5, "reasoning": 5},
    )


class TestWorkloadGenerator:

    def test_requests_are_generated(self):
        """Verify generator produces requests at configured rates."""
        received = {"coord": [], "nlp": []}
        workload = make_workload(rates={"coord": 10, "nlp": 10})

        gen = WorkloadGenerator(workload, seed=42)
        gen.register("coord", lambda r: received["coord"].append(r))
        gen.register("nlp",   lambda r: received["nlp"].append(r))

        gen.start()
        time.sleep(0.5)   # 500ms → expect ~5 requests per agent
        gen.stop()

        # At 10 req/s for 0.5s we expect roughly 3-7 (Poisson variation)
        assert len(received["coord"]) > 0, "No requests generated for coord"
        assert len(received["nlp"])   > 0, "No requests generated for nlp"

    def test_request_fields_populated(self):
        """Verify Request objects have required fields."""
        received = []
        workload = make_workload(rates={"coord": 20})

        gen = WorkloadGenerator(workload, seed=1)
        gen.register("coord", lambda r: received.append(r))

        gen.start()
        time.sleep(0.2)
        gen.stop()

        assert len(received) > 0
        r = received[0]
        assert isinstance(r, Request)
        assert r.agent_name == "coord"
        assert r.request_id != ""
        assert r.payload != ""
        assert r.arrival_time > 0

    def test_stop_halts_generation(self):
        workload = make_workload(rates={"coord": 50})
        received = []

        gen = WorkloadGenerator(workload, seed=99)
        gen.register("coord", lambda r: received.append(r))

        gen.start()
        time.sleep(0.1)
        gen.stop()
        count_at_stop = len(received)

        time.sleep(0.3)   # wait more — should NOT receive additional requests
        assert len(received) == count_at_stop, "Generator kept sending after stop()"

    def test_zero_rate_agent_sends_nothing(self):
        workload = make_workload(rates={"coord": 0, "nlp": 20})
        received_coord = []

        gen = WorkloadGenerator(workload, seed=7)
        gen.register("coord", lambda r: received_coord.append(r))

        gen.start()
        time.sleep(0.3)
        gen.stop()

        assert len(received_coord) == 0, "Zero-rate agent should produce no requests"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
