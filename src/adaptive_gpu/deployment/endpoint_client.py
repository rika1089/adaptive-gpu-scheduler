"""
deployment/endpoint_client.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Replaces simulation service with real HTTP calls to vLLM
OpenAI-compatible endpoints.

Usage (drop-in for BaseAgent.simulate_service):
    client = EndpointClient(port=8001, model_path="/models/phi3")
    response = client.infer("Explain climate change")
"""
from __future__ import annotations
import time
import requests
from typing import Optional
from adaptive_gpu.utils.logging import get_logger

logger = get_logger("deployment.endpoint_client")


class EndpointClient:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8001,
        model_path: str = "/models/phi3",
        timeout: float = 10.0,
        max_tokens: int = 64,
    ):
        self.base_url = f"http://{host}:{port}"
        self.model_path = model_path
        self.timeout = timeout
        self.max_tokens = max_tokens

    def is_alive(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/v1/models", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def infer(self, prompt: str) -> Optional[str]:
        """
        Send a chat completion request. Returns response text or None on failure.
        Records latency internally.
        """
        payload = {
            "model": self.model_path,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
        }
        t0 = time.time()
        try:
            r = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=self.timeout,
            )
            latency_ms = (time.time() - t0) * 1000
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"]
                logger.debug(f"Inference OK: {latency_ms:.1f}ms — {content[:60]}")
                return content
            else:
                logger.warning(f"Endpoint returned {r.status_code}: {r.text[:100]}")
                return None
        except requests.exceptions.Timeout:
            logger.error(f"Timeout after {self.timeout}s for port {self.base_url}")
            return None
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return None


# ── Agent-to-port mapping (matches launch_all.sh) ────────────────────────────
DGX_ENDPOINTS = {
    "coord":     {"port": 8001, "model_path": "/models/phi3"},
    "nlp":       {"port": 8002, "model_path": "/models/qwen"},
    "vision":    {"port": 8003, "model_path": "/models/tinyllama"},
    "reasoning": {"port": 8004, "model_path": "/models/phi3"},
}


def build_clients(host: str = "localhost") -> dict:
    """Build a dict of agent_name -> EndpointClient for all DGX agents."""
    return {
        name: EndpointClient(host=host, **cfg)
        for name, cfg in DGX_ENDPOINTS.items()
    }
