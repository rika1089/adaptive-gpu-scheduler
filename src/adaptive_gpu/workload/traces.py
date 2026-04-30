"""
workload/traces.py — Replay a pre-recorded request trace from CSV.

CSV format: timestamp_sec,agent_name,query_type,payload
"""
from __future__ import annotations
import csv
import time
import threading
import uuid
from pathlib import Path
from typing import Callable, Dict

from adaptive_gpu.utils.types import Request
from adaptive_gpu.utils.logging import get_logger

logger = get_logger("workload.traces")


class TraceReplayer:
    def __init__(self, trace_path: str, speed: float = 1.0):
        self.trace_path = Path(trace_path)
        self.speed = speed       # >1.0 = faster replay
        self._callbacks: Dict[str, Callable[[Request], None]] = {}
        self._stop_event = threading.Event()

    def register(self, agent_name: str, callback: Callable[[Request], None]) -> None:
        self._callbacks[agent_name] = callback

    def _run(self) -> None:
        with open(self.trace_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            logger.warning("Empty trace file.")
            return

        t0_trace = float(rows[0]["timestamp_sec"])
        t0_wall = time.time()

        for row in rows:
            if self._stop_event.is_set():
                break
            delta = (float(row["timestamp_sec"]) - t0_trace) / self.speed
            target = t0_wall + delta
            wait = target - time.time()
            if wait > 0:
                self._stop_event.wait(timeout=wait)

            agent = row["agent_name"]
            req = Request(
                request_id=str(uuid.uuid4())[:8],
                agent_name=agent,
                query_type=row.get("query_type", "text"),
                payload=row.get("payload", ""),
            )
            cb = self._callbacks.get(agent)
            if cb:
                cb(req)

        logger.info("Trace replay completed.")

    def start(self) -> None:
        self._stop_event.clear()
        t = threading.Thread(target=self._run, daemon=True, name="trace-replayer")
        t.start()

    def stop(self) -> None:
        self._stop_event.set()
