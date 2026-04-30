"""
deployment/dgx_runner.py
━━━━━━━━━━━━━━━━━━━━━━━━
DGX-specific runner: launches vLLM directly as Python processes
(not Docker) using CUDA_VISIBLE_DEVICES, mirroring launch_all.sh.

This is the preferred mode on DGX where Docker GPU access can
be finicky. Each agent runs as a separate subprocess.
"""
from __future__ import annotations
import subprocess
import os
import time
import signal
import requests
from typing import Dict, List, Optional
from pathlib import Path
from adaptive_gpu.utils.logging import get_logger

logger = get_logger("deployment.dgx_runner")

MODELS_ROOT = "/nfsshare/users/sreekar/models"
LOGS_DIR = Path("output/logs/dgx")

AGENT_CONFIG = {
    "coord":     {"gpu": 5, "port": 8001, "model": "phi3"},
    "nlp":       {"gpu": 6, "port": 8002, "model": "qwen"},
    "vision":    {"gpu": 7, "port": 8003, "model": "tinyllama"},
    "reasoning": {"gpu": 5, "port": 8004, "model": "phi3"},
}


class DGXRunner:
    def __init__(
        self,
        agents: Optional[List[str]] = None,
        gpu_memory_utilization: float = 0.40,
        max_model_len: int = 2048,
    ):
        self.agents = agents or list(AGENT_CONFIG.keys())
        self.gpu_memory_utilization = gpu_memory_utilization
        self.max_model_len = max_model_len
        self._processes: Dict[str, subprocess.Popen] = {}

    def _launch_one(self, name: str) -> subprocess.Popen:
        cfg = AGENT_CONFIG[name]
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOGS_DIR / f"{name}.log"
        model_path = f"{MODELS_ROOT}/{cfg['model']}"

        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = str(cfg["gpu"])

        cmd = [
            "python", "-m", "vllm.entrypoints.openai.api_server",
            "--model", model_path,
            "--port", str(cfg["port"]),
            "--max-model-len", str(self.max_model_len),
            "--gpu-memory-utilization", str(self.gpu_memory_utilization),
        ]

        logger.info(f"Starting {name} on GPU {cfg['gpu']}, port {cfg['port']}")
        with open(log_path, "w") as log_f:
            proc = subprocess.Popen(
                cmd,
                env=env,
                stdout=log_f,
                stderr=subprocess.STDOUT,
            )
        return proc

    def start_all(self) -> None:
        for name in self.agents:
            proc = self._launch_one(name)
            self._processes[name] = proc
            time.sleep(3)   # brief stagger to avoid GPU memory contention

        logger.info(f"All agents launched: {self.agents}")
        logger.info("Waiting for readiness (this can take 60–120s)...")
        self._wait_all_ready()

    def _wait_all_ready(self, timeout: int = 180) -> None:
        for name in self.agents:
            port = AGENT_CONFIG[name]["port"]
            ready = False
            for i in range(timeout):
                try:
                    r = requests.get(f"http://localhost:{port}/v1/models", timeout=2)
                    if r.status_code == 200:
                        logger.info(f"  ✓ {name} ready (port {port})")
                        ready = True
                        break
                except Exception:
                    pass
                time.sleep(1)
            if not ready:
                logger.error(f"  ✗ {name} NOT ready after {timeout}s — check {LOGS_DIR}/{name}.log")

    def stop_all(self) -> None:
        for name, proc in self._processes.items():
            logger.info(f"Stopping {name} (PID {proc.pid})")
            proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        self._processes.clear()

    def health_check(self) -> Dict[str, bool]:
        status = {}
        for name in self.agents:
            port = AGENT_CONFIG[name]["port"]
            try:
                r = requests.get(f"http://localhost:{port}/v1/models", timeout=2)
                status[name] = r.status_code == 200
            except Exception:
                status[name] = False
        return status
