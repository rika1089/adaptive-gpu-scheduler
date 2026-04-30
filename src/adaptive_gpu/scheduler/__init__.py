"""scheduler package — policy factory."""
from adaptive_gpu.scheduler.policy_interface import AllocationPolicy
from adaptive_gpu.scheduler.adaptive_allocator import AdaptiveAllocator
from adaptive_gpu.scheduler.static_allocator import StaticAllocator
from adaptive_gpu.scheduler.round_robin import RoundRobinAllocator
from adaptive_gpu.config.loader import AgentsConfig, PoliciesConfig


def build_policy(name: str, agents_cfg: AgentsConfig, policies_cfg: PoliciesConfig) -> AllocationPolicy:
    if name == "adaptive":
        return AdaptiveAllocator(agents_cfg, policies_cfg)
    elif name == "static":
        p = policies_cfg.get("static")
        return StaticAllocator(share_per_agent=p.share_per_agent)
    elif name == "round_robin":
        return RoundRobinAllocator()
    else:
        raise ValueError(f"Unknown policy: '{name}'. Choose: adaptive, static, round_robin")
