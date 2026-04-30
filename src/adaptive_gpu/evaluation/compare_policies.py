"""
evaluation/compare_policies.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Runs all requested policies on the same workload and returns
a structured comparison dict ready for summarize.py and plotting.
"""
from __future__ import annotations
import random
from typing import Dict, List

from adaptive_gpu.simulation.event_loop import run_single
from adaptive_gpu.metrics.collector import MetricsCollector
from adaptive_gpu.metrics import (
    avg_latency_per_agent,
    avg_throughput_per_agent,
    avg_gpu_share_per_agent,
    sla_violation_rate_per_agent,
    avg_fairness,
)
from adaptive_gpu.config.loader import (
    AgentsConfig, WorkloadConfig, PoliciesConfig, ExperimentConfig
)
from adaptive_gpu.utils.logging import get_logger

logger = get_logger("evaluation.compare")


def run_comparison(
    agents_cfg: AgentsConfig,
    workload_cfg: WorkloadConfig,
    policies_cfg: PoliciesConfig,
    exp_cfg: ExperimentConfig,
    output_dir: str = "output/metrics",
) -> Dict[str, Dict]:
    """
    Run each policy `exp_cfg.repeats` times, average results, return comparison.

    Returns:
        {
          "adaptive": { "coord": {...}, "nlp": {...}, ... , "_fairness": 0.95 },
          "static":   { ... },
          "round_robin": { ... },
        }
    """
    from pathlib import Path
    from collections import defaultdict

    results: Dict[str, List[MetricsCollector]] = {}

    base_seed = exp_cfg.random_seed

    for policy_name in exp_cfg.policies:
        logger.info(f"> Policy: {policy_name} ({exp_cfg.repeats} repeat(s))")
        collectors = []

        for repeat in range(exp_cfg.repeats):
            seed = base_seed + repeat
            random.seed(seed)

            collector = run_single(
                policy_name=policy_name,
                agents_cfg=agents_cfg,
                workload_cfg=workload_cfg,
                policies_cfg=policies_cfg,
                exp_cfg=exp_cfg,
                seed=seed,
            )
            collectors.append(collector)

            # Save raw CSVs
            out = Path(output_dir)
            collector.to_csv(str(out / f"{policy_name}_repeat{repeat}_metrics.csv"))
            collector.allocation_to_csv(
                str(out / f"{policy_name}_repeat{repeat}_allocations.csv")
            )

        results[policy_name] = collectors

    # Average across repeats
    comparison: Dict[str, Dict] = {}

    for policy_name, collectors in results.items():
        agent_names = list(agents_cfg.agents.keys())
        agg: Dict[str, Dict] = {a: defaultdict(list) for a in agent_names}
        fairness_vals = []

        for collector in collectors:
            lats  = avg_latency_per_agent(collector)
            thrs  = avg_throughput_per_agent(collector)
            shares = avg_gpu_share_per_agent(collector)
            slas  = sla_violation_rate_per_agent(collector)
            fairness_vals.append(avg_fairness(collector))

            for a in agent_names:
                agg[a]["avg_latency_ms"].append(lats.get(a, 0))
                agg[a]["avg_throughput"].append(thrs.get(a, 0))
                agg[a]["avg_gpu_share"].append(shares.get(a, 0))
                agg[a]["avg_sla_violation"].append(slas.get(a, 0))

        policy_result = {}
        for a in agent_names:
            policy_result[a] = {
                k: round(sum(v) / len(v), 4)
                for k, v in agg[a].items()
            }
        policy_result["_fairness"] = round(
            sum(fairness_vals) / len(fairness_vals), 4
        )
        comparison[policy_name] = policy_result

    return comparison
