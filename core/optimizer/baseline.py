"""
core/optimizer/baseline.py — Greedy baseline: select candidates by resilience-per-cost.

Returns (best_mask, best_score, history) matching the interface of PSO/ACO.
"""
from __future__ import annotations

from typing import Tuple, List
import numpy as np
from .problem import Problem


def greedy_baseline(problem: Problem, seed: int = 42) -> Tuple[np.ndarray, float, List[float]]:
    """
    Greedy selection by descending resilience_gain / cost ratio.

    Steps
    -----
    1. Sort candidates by resilience_gain / (cost + 1e-9) descending.
    2. Add each candidate greedily while the cumulative cost stays ≤ budget.
    3. Evaluate the final mask.

    Returns
    -------
    best_mask  : np.ndarray  binary, shape (n_candidates,)
    best_score : float
    history    : List[float]  single-element list (no iterations)
    """
    n = problem.n()
    candidates = problem.candidates

    ratio = np.array(
        [c.resilience_gain / (c.cost + 1e-9) for c in candidates], dtype=float
    )
    order = np.argsort(-ratio)  # descending

    mask = np.zeros(n, dtype=float)
    cum_cost = 0.0
    for idx in order:
        c = candidates[idx]
        if cum_cost + c.cost <= problem.budget:
            mask[idx] = 1.0
            cum_cost += c.cost

    score = problem.evaluate(mask)
    return mask, score, [score]
