"""
core/optimizer/aco.py — Ant Colony Optimisation for supplier subset selection.

Algorithm
---------
Each ant builds a binary selection by visiting every candidate and probabilistically
including it based on pheromone τ and heuristic η (resilience_gain / cost).

Pheromone update: elitist (best-of-iteration ant deposits; global evaporation).

Parameters
----------
n_ants   : int   colony size
n_iters  : int   maximum iterations
alpha    : float pheromone exponent
beta     : float heuristic exponent
rho      : float evaporation rate ∈ (0, 1)
q        : float pheromone deposit scaling factor
seed     : int   RNG seed

Returns
-------
best_mask  : np.ndarray  binary shape (n_candidates,)
best_score : float
history    : List[float] best score per iteration
"""
from __future__ import annotations

from typing import Tuple, List
import numpy as np
from .problem import Problem


def ant_colony(
    problem: Problem,
    n_ants: int = 30,
    n_iters: int = 100,
    alpha: float = 1.0,
    beta: float = 2.0,
    rho: float = 0.1,
    q: float = 1.0,
    seed: int = 42,
) -> Tuple[np.ndarray, float, List[float]]:
    """ACO for combinatorial supplier subset selection."""
    rng = np.random.default_rng(seed)
    n   = problem.n()

    # Heuristic: resilience_gain / (cost + eps)
    eta = np.array(
        [c.resilience_gain / (c.cost + 1e-9) for c in problem.candidates], dtype=float
    )
    eta_norm = eta / (eta.max() + 1e-9)  # normalise to [0,1]

    # Pheromone initialisation
    tau = np.ones(n, dtype=float) * 0.5

    best_mask  = np.zeros(n, dtype=float)
    best_score = -np.inf
    history: List[float] = []

    for _ in range(n_iters):
        iteration_masks  = []
        iteration_scores = []

        for _ in range(n_ants):
            # Probability of selecting each candidate independently
            prob = (tau ** alpha) * (eta_norm ** beta)
            prob = np.clip(prob, 1e-12, None)
            prob = prob / prob.sum()

            # Stochastic binary selection per candidate
            mask = (rng.random(n) < prob).astype(float)
            score = problem.evaluate(mask)
            iteration_masks.append(mask)
            iteration_scores.append(score)

        # Evaporate
        tau *= (1.0 - rho)

        # Elitist deposit: best ant this iteration
        best_iter_idx   = int(np.argmax(iteration_scores))
        best_iter_mask  = iteration_masks[best_iter_idx]
        best_iter_score = iteration_scores[best_iter_idx]
        deposit = q * max(best_iter_score, 0.0)  # only positive contributions
        tau += deposit * best_iter_mask

        # Update global best
        if best_iter_score > best_score:
            best_score = best_iter_score
            best_mask  = best_iter_mask.copy()

        history.append(best_score)

    return best_mask, best_score, history
