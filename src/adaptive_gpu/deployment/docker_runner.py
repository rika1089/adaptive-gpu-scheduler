"""
deployment/docker_runner.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Launches vLLM containers via Docker subprocess calls.
Mirrors the paper's deployment but uses subprocess.run (not os.system)
to avoid shell-quoting issues.

Only used in Week 3+ after simulation is validated.
"""
from __future__ import annotations
import subprocess
import time
import os
import requests
from typing import Dict, Optional
from adaptive_gpu.utils.logging import get_logger

logger = get_logger("deployment.docker_runner")

# Default model → GPU mapping (edit to match your DGX GPU assignments)
DEFAULT_GPU_MAP = {
    "coord":     5,
    "nlp":       6,
    "vision":    7,
    "reasoning": 5,   # shares GPU 5 with coord (different port)
}

DEFAULT_PORTS = {
    "coord":     8001,
    "nlp":       8002,
    "vision":    8003,
    "reasoning": 8004,
}

DEFAULT_MODELS = {
    "coord":     "/models/phi3",
    "nlp":       "/models/qwen",
    "vision":    "/models/tinyllama",
    "reasoning": "/models/phi3",
}

NFS_MOUNT = "/nfsshare/users/sreekar/models"


def remove_container(name: str) -> None:
    subprocess.run(
        ["docker", "rm", "-f", name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def launch_agent(
    agent_name: str,
    gpu_id: int,
    port: int,
    model_path: str,
    gpu_memory_utilization: float = 0.40,
    max_model_len: int = 2048,
    nfs_mount: str = NFS_MOUNT,
) -> subprocess.CompletedProcess:
    container_name = f"{agent_name}_server"
    remove_container(container_name)

    logger.info(f"Launching {agent_name} → GPU {gpu_id}, port {port}, model {model_path}")
    return subprocess.run([
        "docker", "run", "-d",
        "--gpus", f"device={gpu_id}",
        "--ipc=host",
        "-p", f"{port}:8000",
        "-v", f"{nfs_mount}:/models",
        "--name", container_name,
        "vllm/vllm-openai",
        model_path,
        "--max-model-len", str(max_model_len),
        "--gpu-memory-utilization", str(round(gpu_memory_utilization, 2)),
    ])


def wait_until_ready(port: int, timeout: int = 120) -> bool:
    logger.info(f"Waiting for port {port} to become ready...")
    for i in range(timeout):
        try:
            r = requests.get(f"http://localhost:{port}/v1/models", timeout=2)
            if r.status_code == 200:
                logger.info(f"Port {port} ready after {i}s")
                return True
        except Exception:
            pass
        time.sleep(1)
    logger.error(f"Port {port} not ready after {timeout}s")
    return False


def launch_all(
    agents: Optional[list] = None,
    gpu_memory_utilization: float = 0.40,
) -> Dict[str, bool]:
    """
    Launch all agents (or a subset) and wait for readiness.

    Returns dict of agent_name -> ready (bool).
    """
    if agents is None:
        agents = list(DEFAULT_PORTS.keys())

    results = {}
    for name in agents:
        launch_agent(
            agent_name=name,
            gpu_id=DEFAULT_GPU_MAP[name],
            port=DEFAULT_PORTS[name],
            model_path=DEFAULT_MODELS[name],
            gpu_memory_utilization=gpu_memory_utilization,
        )
        ready = wait_until_ready(DEFAULT_PORTS[name])
        results[name] = ready
        if not ready:
            logger.warning(
                f"{name} failed to start — check: docker logs {name}_server"
            )

    return results
