"""
experiments/exp_ablation_priority.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ablation study: vary the priority values for each agent
and measure the impact on latency and SLA for high-priority agents.

Tests three priority configurations:
  1. uniform   — all agents priority=1 (no differentiation)
  2. paper     — coord=1, nlp=2, vision=2, reasoning=1  (paper default)
  3. aggressive — coord=1, nlp=3, vision=3, reasoning=1 (stronger differentiation)

Run from project root:
    python experiments/exp_ablation_priority.py
"""
from __future__ import annotations
import sys
import copy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adaptive_gpu.config.loader import load_all
from adaptive_gpu.evaluation.compare_policies import run_comparison
from adaptive_gpu.evaluation.summarize import print_comparison_table, save_json
from adaptive_gpu.utils.logging import get_logger

logger = get_logger("exp.ablation_priority")

PRIORITY_CONFIGS = {
    "uniform":    {"coord": 1, "nlp": 1, "vision": 1, "reasoning": 1},
    "paper":      {"coord": 1, "nlp": 2, "vision": 2, "reasoning": 1},
    "aggressive": {"coord": 1, "nlp": 3, "vision": 3, "reasoning": 1},
}


def main() -> None:
    agents_cfg, workloads_cfg, policies_cfg, exp_cfg = load_all()
    workload_cfg = workloads_cfg.get("paper_default")
    exp_cfg.policies = ["adaptive"]
    exp_cfg.repeats = 1
    workload_cfg.duration_seconds = 60   # shorter for ablation

    all_results = {}

    for config_name, priorities in PRIORITY_CONFIGS.items():
        logger.info(f"Running priority config: {config_name} — {priorities}")

        # Patch agent priorities
        patched_cfg = copy.deepcopy(agents_cfg)
        for agent_name, pval in priorities.items():
            if agent_name in patched_cfg.agents:
                patched_cfg.agents[agent_name].priority = pval

        comparison = run_comparison(
            agents_cfg=patched_cfg,
            workload_cfg=workload_cfg,
            policies_cfg=policies_cfg,
            exp_cfg=exp_cfg,
            output_dir=f"output/metrics/ablation_{config_name}",
        )
        all_results[config_name] = comparison.get("adaptive", {})

    # Print summary
    print("\n" + "=" * 60)
    print("  ABLATION: Priority Weight Sensitivity")
    print("=" * 60)
    agents = list(agents_cfg.agents.keys())
    for config_name, result in all_results.items():
        print(f"\n  Config: {config_name.upper()}  priorities={PRIORITY_CONFIGS[config_name]}")
        for agent in agents:
            lat = result.get(agent, {}).get("avg_latency_ms", 0)
            sla = result.get(agent, {}).get("avg_sla_violation", 0) * 100
            share = result.get(agent, {}).get("avg_gpu_share", 0)
            print(f"    {agent:>10}: latency={lat:7.2f}ms  SLA={sla:5.2f}%  share={share:.3f}")

    save_json(all_results, "output/reports/ablation_priority.json")
    print("\nAblation complete. Results → output/reports/ablation_priority.json\n")


if __name__ == "__main__":
    main()
