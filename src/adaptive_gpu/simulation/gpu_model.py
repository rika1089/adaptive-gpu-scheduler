"""
simulation/gpu_model.py
━━━━━━━━━━━━━━━━━━━━━━━
Models the relationship between GPU share and agent service capacity.

Key insight from the paper:
  Higher GPU share → lower service time → lower latency → higher throughput.

Model used here (inverse-linear scaling):
  effective_service_time = base_service_time / gpu_share

This is a simplified but realistic approximation: doubling the GPU share
roughly halves the time per request (up to hardware limits).

The model also enforces a minimum share floor to avoid division-by-zero
and a maximum speedup cap (the GPU cannot go faster than hardware allows).
"""
from __future__ import annotations


class GPUModel:
    def __init__(
        self,
        min_share: float = 0.05,
        max_speedup: float = 5.0,
    ):
        """
        Args:
            min_share:   floor for GPU share to prevent divide-by-zero.
            max_speedup: cap on how much faster max share makes service
                         vs equal share (1/N). Prevents unrealistic speedups.
        """
        self.min_share = min_share
        self.max_speedup = max_speedup

    def effective_service_time_ms(
        self,
        base_ms: float,
        gpu_share: float,
        n_agents: int = 4,
    ) -> float:
        """
        Compute effective service time given a GPU share allocation.

        Args:
            base_ms:   base (equal-share) service time in milliseconds.
            gpu_share: allocated GPU fraction [0, 1].
            n_agents:  total number of agents (used to compute equal-share baseline).

        Returns:
            Effective service time in milliseconds.
        """
        equal_share = 1.0 / max(n_agents, 1)
        share = max(gpu_share, self.min_share)

        # Speedup relative to equal-share baseline
        speedup = share / equal_share
        speedup = min(speedup, self.max_speedup)

        return base_ms / speedup

    def throughput_multiplier(self, gpu_share: float, n_agents: int = 4) -> float:
        """How much throughput scales vs equal-share baseline."""
        equal_share = 1.0 / max(n_agents, 1)
        share = max(gpu_share, self.min_share)
        return min(share / equal_share, self.max_speedup)
