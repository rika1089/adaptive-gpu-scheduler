"""
simulation/event_loop.py
━━━━━━━━━━━━━━━━━━━━━━━━
Runs one complete experiment: start generator + environment, wait for
duration, stop everything, return collected metrics.
"""
from __future__ import annotations
import time
from typing import Dict, Any

from adaptive_gpu.agents import build_agents
from adaptive_gpu.scheduler import build_policy
from adaptive_gpu.workload.generator import WorkloadGenerator
from adaptive_gpu.simulation.environment import SimulationEnvironment
from adaptive_gpu.metrics.collector import MetricsCollector
from adaptive_gpu.config.loader import (
    AgentsConfig, WorkloadConfig, PoliciesConfig, ExperimentConfig
)
from adaptive_gpu.utils.logging import get_logger

logger = get_logger("simulation.event_loop")


def run_single(
    policy_name: str,
    agents_cfg: AgentsConfig,
    workload_cfg: WorkloadConfig,
    policies_cfg: PoliciesConfig,
    exp_cfg: ExperimentConfig,
    seed: int = 42,
) -> MetricsCollector:
    """
    Run one full simulation for a single policy.

    Returns a MetricsCollector containing all recorded snapshots
    and allocation history ready for analysis.
    """
    logger.info(f"== Starting run: policy={policy_name}, "
                f"workload={workload_cfg.name}, "
                f"duration={workload_cfg.duration_seconds}s ==")

    # Build fresh agents and policy for each run
    agents = build_agents(agents_cfg)
    policy = build_policy(policy_name, agents_cfg, policies_cfg)
    collector = MetricsCollector(
        policy_name=policy_name,
        workload_name=workload_cfg.name,
    )

    # Build environment
    p_cfg = policies_cfg.get(policy_name) if policy_name in policies_cfg.policies else None
    alloc_interval = p_cfg.update_interval_seconds if p_cfg else 5.0
    alloc_interval = min(alloc_interval, workload_cfg.duration_seconds)

    env = SimulationEnvironment(
        agents=agents,
        policy=policy,
        metrics_collector=collector,
        allocation_interval_s=alloc_interval,
        metrics_interval_s=exp_cfg.metrics_interval_seconds,
    )

    # Build workload generator and wire to env
    gen = WorkloadGenerator(workload_cfg, seed=seed)
    for agent_name in agents:
        gen.register(agent_name, env.receive_request)

    # Run
        # Run
    env.start()
    gen.start()

    start_time = time.time()
    total_seconds = int(workload_cfg.duration_seconds)

    try:
        for elapsed_sec in range(total_seconds):
            time.sleep(1)

            running = elapsed_sec + 1
            remaining = total_seconds - running

            mins_run, secs_run = divmod(running, 60)
            mins_left, secs_left = divmod(remaining, 60)

            progress = (running / total_seconds) * 100

            print(
                f"\r[policy={policy_name}] "
                f"{progress:6.2f}% | "
                f"Running: {mins_run:02d}:{secs_run:02d} | "
                f"Remaining: {mins_left:02d}:{secs_left:02d}",
                end="",
                flush=True,
            )

        total_wall = time.time() - start_time
        print(
            f"\r[policy={policy_name}] "
            f"Running: {total_seconds//60:02d}:{total_seconds%60:02d} | "
            f"Remaining: 00:00 | "
            f"Wall time: {total_wall:.1f}s"
        )

    except KeyboardInterrupt:
        print()
        logger.warning("Run interrupted by user.")
    finally:
        gen.stop()
        env.stop()

    logger.info(f"== Run complete: policy={policy_name} ==")
    return collector
