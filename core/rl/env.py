"""
core/rl/env.py — Gymnasium environment for supply-chain disruption response.

State
-----
    Per-node health ∈ [0, 1] for the top-K risk nodes,
    a global buffer level ∈ [0, 1], and the current step index (normalised).
    Observation shape: (K + K + 1 + 1,) = (2K + 2,)
      [:K]   node health vector
      [K:2K] node geo_risk vector (static, from graph attributes)
      [2K]   buffer level
      [2K+1] step / max_steps (progress indicator)

Actions  — Discrete(1 + 2K)
-----------
    0          : wait (no action; incurs no cost)
    1 … K      : diversify node k-1  (add alternate supplier; reduces HHI for that node)
    K+1 … 2K   : stockpile node k-1  (build buffer inventory; costs more, protects longer)

Rewards
-------
    r_t = −action_cost − weighted_health_loss

    where:
        action_cost  = 0 (wait), 0.05 (diversify), 0.10 (stockpile)
        weighted_health_loss = Σ_k (Risk_Score_k / Σ Risk_Score) * (1 − health_k)

Episode
-------
    max_steps = 50
    Each step:
      1. Apply action → health / buffer update.
      2. Random shocks: each node damaged with probability proportional to its Risk_Score
         (boosted by geo_risk). Damage = Uniform(0.1, 0.4).
      3. Cascading: nodes whose health < 0.3 propagate 50% of their damage to
         direct successors in the graph (simple neighbour-propagation proxy for the
         existing simulator logic which requires full graph copies).
      4. Clamp all health to [0, 1]; clamp buffer to [0, 1].
      5. Compute reward.
    Truncation at max_steps; termination if all nodes health < 0.05.
"""
from __future__ import annotations

import sys
from pathlib import Path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
import paths  # noqa: F401

from typing import Optional, Tuple, Dict, Any, List
import numpy as np
import networkx as nx
import gymnasium as gym
from gymnasium import spaces


class SupplyChainEnv(gym.Env):
    """
    Gymnasium environment for supply-chain disruption response.

    Parameters
    ----------
    graph      : nx.DiGraph  built by pipeline.ingest.build_graph
    risk_df    : pd.DataFrame  output of SupplyChainRiskEngine.compute_composite_risk_scores()
    top_k      : int  number of high-risk nodes to track (default 8, capped to graph size)
    seed       : Optional[int]
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        graph: nx.DiGraph,
        risk_df,          # pd.DataFrame — imported lazily to avoid hard dep at class level
        top_k: int = 8,
        render_mode: Optional[str] = None,
    ):
        super().__init__()

        self.graph   = graph
        self.render_mode = render_mode

        # ── Select top-K nodes ────────────────────────────────────────────────
        import pandas as pd
        if not isinstance(risk_df, pd.DataFrame):
            raise TypeError("risk_df must be a pandas DataFrame")

        actual_k = min(top_k, len(risk_df))
        top_rows = risk_df.head(actual_k)
        self.node_ids: List[str] = list(top_rows["Node_ID"])
        self.K = len(self.node_ids)

        # Risk weights (normalised) used for reward computation
        raw_scores = top_rows["Risk_Score"].values.astype(float)
        total = raw_scores.sum()
        self.risk_weights = raw_scores / (total + 1e-9)

        # Shock probability per node = Risk_Score (0-100) / 100, capped at 0.9
        self.shock_prob = np.clip(raw_scores / 100.0, 0.01, 0.90)

        # Static geo_risk overlay from graph attributes
        self.geo_risk = np.array([
            float(graph.nodes[nid].get("geo_risk", 0.0))
            for nid in self.node_ids
        ], dtype=np.float32)

        # Build adjacency index (within top-K) for cascading propagation
        node_idx = {n: i for i, n in enumerate(self.node_ids)}
        self._adj: List[List[int]] = [[] for _ in range(self.K)]
        for u, v in graph.edges():
            if u in node_idx and v in node_idx:
                self._adj[node_idx[u]].append(node_idx[v])

        # ── Spaces ────────────────────────────────────────────────────────────
        obs_dim = 2 * self.K + 2
        self.observation_space = spaces.Box(
            low=0.0, high=1.0,
            shape=(obs_dim,), dtype=np.float32,
        )
        self.action_space = spaces.Discrete(1 + 2 * self.K)

        # ── Episode state ─────────────────────────────────────────────────────
        self.max_steps = 50
        self._health: np.ndarray = np.ones(self.K, dtype=np.float32)
        self._buffer: float = 0.5
        self._step:   int   = 0

        # ── Action costs ──────────────────────────────────────────────────────
        self._action_cost = {
            "wait":       0.00,
            "diversify":  0.05,
            "stockpile":  0.10,
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_obs(self) -> np.ndarray:
        return np.concatenate([
            self._health,
            self.geo_risk,
            [np.float32(self._buffer)],
            [np.float32(self._step / self.max_steps)],
        ]).astype(np.float32)

    def _apply_action(self, action: int) -> float:
        """Apply action, return cost incurred."""
        if action == 0:
            return self._action_cost["wait"]
        elif 1 <= action <= self.K:
            k = action - 1
            # Diversify: partially restore health + reduce shock probability
            self._health[k] = min(1.0, self._health[k] + 0.15)
            self.shock_prob[k] = max(0.01, self.shock_prob[k] * 0.85)
            return self._action_cost["diversify"]
        else:
            k = action - self.K - 1
            # Stockpile: draw from buffer to restore node health
            draw = min(self._buffer, 0.20)
            self._buffer   = max(0.0, self._buffer - draw)
            self._health[k] = min(1.0, self._health[k] + draw)
            return self._action_cost["stockpile"]

    def _apply_shocks(self, rng: np.random.Generator) -> None:
        """Random shocks scaled by shock probability + geo_risk."""
        for k in range(self.K):
            effective_prob = np.clip(
                self.shock_prob[k] + 0.5 * self.geo_risk[k], 0, 0.95
            )
            if rng.random() < effective_prob:
                damage = rng.uniform(0.1, 0.4)
                self._health[k] = max(0.0, self._health[k] - damage)

    def _apply_cascade(self) -> None:
        """Propagate 50% of damage from critically unhealthy nodes to successors."""
        for k in range(self.K):
            if self._health[k] < 0.3:
                cascade_damage = (0.3 - self._health[k]) * 0.5
                for j in self._adj[k]:
                    self._health[j] = max(0.0, self._health[j] - cascade_damage)

    def _compute_reward(self, action_cost: float) -> float:
        health_loss = float(np.dot(self.risk_weights, 1.0 - self._health))
        return -(action_cost + health_loss)

    # ── Gymnasium API ─────────────────────────────────────────────────────────

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        self._health[:] = 1.0
        self._buffer    = 0.5
        self._step      = 0
        # Reset shock probs from original risk_weights (they mutate during episode)
        self.shock_prob = np.clip(self.risk_weights * 2.0 + 0.01, 0.01, 0.90)
        return self._get_obs(), {}

    def step(
        self, action: int
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        # 1. Action
        cost = self._apply_action(int(action))

        # 2. Shocks
        self._apply_shocks(self.np_random)

        # 3. Cascade
        self._apply_cascade()

        # 4. Reward
        reward = self._compute_reward(cost)

        # 5. Termination
        self._step += 1
        terminated = bool(np.all(self._health < 0.05))
        truncated  = self._step >= self.max_steps

        info = {
            "health": self._health.copy(),
            "buffer": self._buffer,
            "step":   self._step,
        }
        return self._get_obs(), reward, terminated, truncated, info

    def render(self) -> None:
        pass  # no visual render


# ─────────────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────────────

def make_env(industry: str, top_k: int = 8) -> SupplyChainEnv:
    """Build the SupplyChainEnv for *industry* using the cached graph."""
    from pipeline.ingest import build_graph
    from graph_engine.risk_scores import SupplyChainRiskEngine

    graph = build_graph(industry, use_cache=True)
    engine = SupplyChainRiskEngine(graph)
    risk_df = engine.compute_composite_risk_scores()
    return SupplyChainEnv(graph=graph, risk_df=risk_df, top_k=top_k)
