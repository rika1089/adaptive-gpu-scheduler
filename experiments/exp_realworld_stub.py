"""
experiments/exp_realworld_stub.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Week 3+ experiment: run the adaptive allocator against real
vLLM endpoints on DGX instead of the simulator.

Prerequisites:
  1. All vLLM containers are running (run scripts/launch_all.sh first)
  2. All ports (8001-8004) return 200 on /v1/models

The structure is identical to the simulation experiment, but
the BaseAgent.simulate_service() is monkey-patched to call
the real endpoint instead of sleeping.

Run from project root:
    bash scripts/launch_all.sh          # start vLLM servers
    python experiments/exp_realworld_stub.py
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adaptive_gpu.config.loader import load_all
from adaptive_gpu.deployment.endpoint_client import build_clients, EndpointClient
from adaptive_gpu.deployment.dgx_runner import DGXRunner
from adaptive_gpu.utils.logging import get_logger

logger = get_logger("exp.realworld")


def check_endpoints(clients: dict) -> bool:
    """Verify all endpoints are alive before starting."""
    all_ok = True
    for name, client in clients.items():
        alive = client.is_alive()
        status = "✓ UP" if alive else "✗ DOWN"
        logger.info(f"  {name:>12}: {status} (port {client.base_url})")
        if not alive:
            all_ok = False
    return all_ok


def main() -> None:
    agents_cfg, workloads_cfg, policies_cfg, exp_cfg = load_all()
    workload_cfg = workloads_cfg.get("paper_default")

    # ── Check DGX endpoints ────────────────────────────────────────────────
    logger.info("Checking DGX vLLM endpoints...")
    clients = build_clients(host="localhost")

    if not check_endpoints(clients):
        logger.error(
            "One or more endpoints are DOWN.\n"
            "Run:  bash scripts/launch_all.sh\n"
            "Then wait for 'Application startup complete' in logs."
        )
        sys.exit(1)

    logger.info("All endpoints UP. Starting real-world experiment...")

    # ── Monkey-patch BaseAgent to use real inference ───────────────────────
    from adaptive_gpu.agents.base_agent import BaseAgent
    import time as _time

    def real_simulate_service(self, request):
        """Replace simulated sleep with real vLLM HTTP call."""
        client: EndpointClient = clients.get(self.name)
        if client is None:
            logger.warning(f"No client for agent '{self.name}', falling back to sim")
            import random
            base_ms = max(1.0, random.gauss(self.service_time_mean_ms, self.service_time_std_ms))
            _time.sleep(base_ms / 1000.0)
        else:
            # Real inference
            client.infer(request.payload)

        request.completion_time = _time.time()
        return request

    BaseAgent.simulate_service = real_simulate_service
    logger.info("BaseAgent patched to use real vLLM endpoints.")

    # ── Run experiment (adaptive only for real-world demo) ─────────────────
    from adaptive_gpu.simulation.event_loop import run_single
    from adaptive_gpu.evaluation.summarize import print_comparison_table, plot_allocation_over_time

    exp_cfg.policies = ["adaptive"]
    exp_cfg.repeats = 1
    workload_cfg.duration_seconds = 120   # 2-minute real run

    collector = run_single(
        policy_name="adaptive",
        agents_cfg=agents_cfg,
        workload_cfg=workload_cfg,
        policies_cfg=policies_cfg,
        exp_cfg=exp_cfg,
        seed=42,
    )

    collector.to_csv("output/metrics/realworld_adaptive.csv")
    collector.allocation_to_csv("output/metrics/realworld_allocations.csv")
    plot_allocation_over_time(collector, figures_dir="output/figures")

    summary = collector.summary()
    print("\n  REAL-WORLD EXPERIMENT RESULTS")
    print("  " + "─" * 50)
    for agent, stats in summary.items():
        print(f"  {agent:>12}: latency={stats['avg_latency_ms']:7.2f}ms  "
              f"throughput={stats['avg_throughput']:.4f}  "
              f"SLA={stats['avg_sla_violation']*100:.2f}%  "
              f"share={stats['avg_gpu_share']:.3f}")
    print()


if __name__ == "__main__":
    main()
