"""
metrics/collector.py
━━━━━━━━━━━━━━━━━━━━
Central metrics store. Records:
  - Per-agent state snapshots (latency, throughput, SLA, queue, GPU share)
  - Allocation decisions over time
  - Exports to CSV and produces summary dicts for comparison
"""
from __future__ import annotations
import csv
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from adaptive_gpu.utils.types import AgentState, AllocationResult
from adaptive_gpu.utils.logging import get_logger

logger = get_logger("metrics.collector")


@dataclass
class SnapshotRow:
    elapsed_s: float
    policy: str
    workload: str
    agent: str
    queue_length: int
    arrival_rate: float
    avg_latency_ms: float
    throughput: float
    sla_violation_rate: float
    gpu_share: float
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    def __init__(self, policy_name: str, workload_name: str):
        self.policy_name = policy_name
        self.workload_name = workload_name
        self._snapshots: List[SnapshotRow] = []
        self._allocations: List[AllocationResult] = []
        self._start_time = time.time()

    # ── Recording ─────────────────────────────────────────────────────────

    def record_snapshot(
        self,
        states: Dict[str, AgentState],
        elapsed: float,
    ) -> None:
        for name, state in states.items():
            row = SnapshotRow(
                elapsed_s=round(elapsed, 2),
                policy=self.policy_name,
                workload=self.workload_name,
                agent=name,
                queue_length=state.queue_length,
                arrival_rate=round(state.arrival_rate, 3),
                avg_latency_ms=round(state.avg_latency_ms, 2),
                throughput=round(state.throughput, 3),
                sla_violation_rate=round(state.sla_violation_rate, 4),
                gpu_share=round(state.gpu_share, 4),
            )
            self._snapshots.append(row)

    def record_allocation(self, result: AllocationResult) -> None:
        self._allocations.append(result)

    # ── Export ────────────────────────────────────────────────────────────

    def to_csv(self, path: str) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "elapsed_s", "policy", "workload", "agent",
            "queue_length", "arrival_rate", "avg_latency_ms",
            "throughput", "sla_violation_rate", "gpu_share", "timestamp",
        ]
        with open(out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in self._snapshots:
                writer.writerow(row.__dict__)

        logger.info(f"Metrics saved -> {out} ({len(self._snapshots)} rows)")
        return out

    def allocation_to_csv(self, path: str) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        if not self._allocations:
            return out

        agents = list(self._allocations[0].shares.keys())
        fieldnames = ["timestamp", "policy"] + agents

        with open(out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for alloc in self._allocations:
                row = {"timestamp": round(alloc.timestamp, 3), "policy": alloc.policy}
                row.update({k: round(v, 4) for k, v in alloc.shares.items()})
                writer.writerow(row)

        logger.info(f"Allocations saved -> {out} ({len(self._allocations)} rows)")
        return out

    # ── Summary ───────────────────────────────────────────────────────────

    def summary(self) -> Dict:
        """Return per-agent average metrics over the full run."""
        from collections import defaultdict
        buckets: Dict[str, List[SnapshotRow]] = defaultdict(list)
        for row in self._snapshots:
            buckets[row.agent].append(row)

        result = {}
        for agent, rows in buckets.items():
            result[agent] = {
                "avg_latency_ms":       round(sum(r.avg_latency_ms for r in rows) / len(rows), 2),
                "avg_throughput":       round(sum(r.throughput for r in rows) / len(rows), 3),
                "avg_sla_violation":    round(sum(r.sla_violation_rate for r in rows) / len(rows), 4),
                "avg_gpu_share":        round(sum(r.gpu_share for r in rows) / len(rows), 4),
                "avg_queue_length":     round(sum(r.queue_length for r in rows) / len(rows), 2),
                "snapshots":            len(rows),
            }
        return result

    @property
    def snapshots(self) -> List[SnapshotRow]:
        return list(self._snapshots)

    @property
    def allocations(self) -> List[AllocationResult]:
        return list(self._allocations)
