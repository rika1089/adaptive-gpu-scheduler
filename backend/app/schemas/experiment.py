from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class PolicyName(str, Enum):
    adaptive = "adaptive"
    static = "static"
    round_robin = "round_robin"


class WorkloadName(str, Enum):
    paper_default = "paper_default"
    low_load = "low_load"
    burst_nlp = "burst_nlp"
    high_reasoning = "high_reasoning"
    uniform = "uniform"


class ExperimentRequest(BaseModel):
    policies: List[PolicyName] = Field(default=[PolicyName.adaptive, PolicyName.static, PolicyName.round_robin])
    workload: WorkloadName = Field(default=WorkloadName.paper_default)
    duration_seconds: int = Field(default=60, ge=10, le=600)
    repeats: int = Field(default=1, ge=1, le=5)
    random_seed: int = Field(default=42)
    run_name: Optional[str] = None


class RunStatus(str, Enum):
    idle = "idle"
    running = "running"
    completed = "completed"
    failed = "failed"
    stopped = "stopped"


class ExperimentStatus(BaseModel):
    run_id: str
    status: RunStatus
    current_policy: Optional[str] = None
    current_repeat: int = 0
    total_repeats: int = 0
    elapsed_seconds: float = 0.0
    estimated_remaining: float = 0.0
    progress_pct: float = 0.0
    started_at: Optional[str] = None
    message: str = ""
