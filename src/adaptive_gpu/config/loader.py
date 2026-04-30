"""
config/loader.py — Load and validate YAML configuration files.
"""
from __future__ import annotations
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Optional


CONFIG_DIR = Path(__file__).resolve().parents[3] / "configs"


def _load_yaml(path: Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


# ─── Agent Config ────────────────────────────────────────────────────────────

@dataclass
class AgentConfig:
    name: str
    priority: int
    min_gpu_share: float
    service_time_mean_ms: float
    service_time_std_ms: float
    description: str = ""


@dataclass
class AgentsConfig:
    agents: Dict[str, AgentConfig]
    sla_threshold_ms: float = 200.0

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "AgentsConfig":
        path = path or (CONFIG_DIR / "agents.yaml")
        raw = _load_yaml(path)
        agents = {
            name: AgentConfig(name=name, **cfg)
            for name, cfg in raw["agents"].items()
        }
        return cls(agents=agents, sla_threshold_ms=raw.get("sla_threshold_ms", 200.0))


# ─── Workload Config ─────────────────────────────────────────────────────────

@dataclass
class WorkloadConfig:
    name: str
    description: str
    duration_seconds: int
    arrival_rates: Dict[str, float]   # agent_name -> requests/sec


@dataclass
class WorkloadsConfig:
    workloads: Dict[str, WorkloadConfig]

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "WorkloadsConfig":
        path = path or (CONFIG_DIR / "workloads.yaml")
        raw = _load_yaml(path)
        workloads = {
            name: WorkloadConfig(name=name, **cfg)
            for name, cfg in raw["workloads"].items()
        }
        return cls(workloads=workloads)

    def get(self, name: str) -> WorkloadConfig:
        if name not in self.workloads:
            raise KeyError(f"Workload '{name}' not found. Available: {list(self.workloads)}")
        return self.workloads[name]


# ─── Policy Config ────────────────────────────────────────────────────────────

@dataclass
class PolicyConfig:
    name: str
    description: str = ""
    update_interval_seconds: float = 5.0
    arrival_rate_window_seconds: float = 10.0
    queue_weight_alpha: float = 0.5
    min_share_enforcement: bool = True
    renormalize: bool = True
    share_per_agent: float = 0.25


@dataclass
class PoliciesConfig:
    policies: Dict[str, PolicyConfig]

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "PoliciesConfig":
        path = path or (CONFIG_DIR / "policies.yaml")
        raw = _load_yaml(path)
        policies = {
            name: PolicyConfig(name=name, **{k: v for k, v in cfg.items() if k != "name"})
            for name, cfg in raw["policies"].items()
        }
        return cls(policies=policies)

    def get(self, name: str) -> PolicyConfig:
        if name not in self.policies:
            raise KeyError(f"Policy '{name}' not found. Available: {list(self.policies)}")
        return self.policies[name]


# ─── Experiment Config ────────────────────────────────────────────────────────

@dataclass
class ExperimentConfig:
    name: str
    description: str
    workload: str
    policies: list
    repeats: int = 3
    random_seed: int = 42
    output_dir: str = "output/metrics"
    figures_dir: str = "output/figures"
    log_dir: str = "output/logs"
    metrics_interval_seconds: float = 5.0

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "ExperimentConfig":
        path = path or (CONFIG_DIR / "experiment_default.yaml")
        raw = _load_yaml(path)
        return cls(**raw["experiment"])


# ─── Convenience loader ───────────────────────────────────────────────────────

def load_all(
    agents_path: Optional[Path] = None,
    workloads_path: Optional[Path] = None,
    policies_path: Optional[Path] = None,
    experiment_path: Optional[Path] = None,
):
    return (
        AgentsConfig.load(agents_path),
        WorkloadsConfig.load(workloads_path),
        PoliciesConfig.load(policies_path),
        ExperimentConfig.load(experiment_path),
    )
