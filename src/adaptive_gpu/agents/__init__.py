"""agents package — build all four agents from config."""
from adaptive_gpu.agents.base_agent import BaseAgent
from adaptive_gpu.agents.coordinator import CoordinatorAgent
from adaptive_gpu.agents.nlp_agent import NLPAgent
from adaptive_gpu.agents.vision_agent import VisionAgent
from adaptive_gpu.agents.reasoning_agent import ReasoningAgent
from adaptive_gpu.config.loader import AgentsConfig
from typing import Dict

_AGENT_CLASSES = {
    "coord": CoordinatorAgent,
    "nlp": NLPAgent,
    "vision": VisionAgent,
    "reasoning": ReasoningAgent,
}

def build_agents(cfg: AgentsConfig) -> Dict[str, BaseAgent]:
    agents = {}
    for name, agent_cfg in cfg.agents.items():
        cls = _AGENT_CLASSES.get(name, BaseAgent)
        agents[name] = cls(agent_cfg, sla_threshold_ms=cfg.sla_threshold_ms)
    return agents
