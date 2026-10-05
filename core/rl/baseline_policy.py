"""
core/rl/baseline_policy.py — Heuristic baseline policy for the SupplyChainEnv.

Policy: diversify the node with the lowest health when any node health < threshold.
If all nodes healthy, take the wait action.
"""
from __future__ import annotations

import numpy as np
from typing import Optional


class BaselinePolicy:
    """
    Heuristic policy: diversify the weakest node when health < threshold.

    Parameters
    ----------
    K         : int   number of nodes tracked (env.K)
    threshold : float health level below which the policy intervenes (default 0.6)
    """

    def __init__(self, K: int, threshold: float = 0.6):
        self.K = K
        self.threshold = threshold

    def predict(self, obs: np.ndarray, deterministic: bool = True):
        """
        Return action given observation array.

        Observation layout: health[:K] | geo_risk[K:2K] | buffer | step_frac
        """
        health = obs[:self.K]
        min_health_idx = int(np.argmin(health))
        min_health_val = float(health[min_health_idx])

        if min_health_val < self.threshold:
            action = 1 + min_health_idx  # diversify weakest node
        else:
            action = 0  # wait

        return action, None  # mimic SB3 policy.predict() return signature
