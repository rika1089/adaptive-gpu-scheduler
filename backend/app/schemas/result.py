from pydantic import BaseModel
from typing import Dict, List, Optional, Any


class AgentMetrics(BaseModel):
    avg_latency_ms: float
    avg_throughput: float
    avg_gpu_share: float
    avg_sla_violation: float


class PolicyResult(BaseModel):
    agents: Dict[str, AgentMetrics]
    fairness: float


class ComparisonSummary(BaseModel):
    run_id: str
    policies: Dict[str, PolicyResult]
    generated_at: str


class MetricRow(BaseModel):
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
    timestamp: float


class AllocationRow(BaseModel):
    timestamp: float
    policy: str
    coord: float
    nlp: float
    vision: float
    reasoning: float


class RunHistoryEntry(BaseModel):
    run_id: str
    run_name: str
    started_at: str
    duration_seconds: int
    policies: List[str]
    workload: str
    repeats: int
    status: str
    has_results: bool
    summary_preview: Optional[Dict[str, Any]] = None
