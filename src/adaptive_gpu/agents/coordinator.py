"""
agents/coordinator.py — Coordinator agent (priority 1, lightweight orchestration).
"""
from adaptive_gpu.agents.base_agent import BaseAgent
from adaptive_gpu.config.loader import AgentConfig


class CoordinatorAgent(BaseAgent):
    """Routes and orchestrates; fast service time, high priority."""
    pass
