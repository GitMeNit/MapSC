"""
core/optimizer/pso.py — Binary Particle Swarm Optimisation for subset selection.

Algorithm: S-shaped sigmoid transfer function maps continuous velocity/position to
binary decisions (Kennedy & Eberhart 1997 discrete PSO).

Parameters
----------
n_particles : int   swarm size
n_iters     : int   maximum iterations
w           : float inertia weight
c1          : float cognitive acceleration (personal best)
c2          : float social acceleration (global best)
v_max       : float velocity clamp
seed        : int   RNG seed for reproducibility

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


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def binary_pso(
    problem: Problem,
    n_particles: int = 30,
    n_iters: int = 100,
    w: float = 0.7,
    c1: float = 1.5,
    c2: float = 1.5,
    v_max: float = 4.0,
    seed: int = 42,
) -> Tuple[np.ndarray, float, List[float]]:
    """Binary PSO for combinatorial supplier selection."""
    rng = np.random.default_rng(seed)
    n = problem.n()

    # Initialise positions (random binary) and velocities
    pos = rng.integers(0, 2, size=(n_particles, n)).astype(float)
    vel = rng.uniform(-v_max, v_max, size=(n_particles, n))

    # Personal bests
    p_best_pos   = pos.copy()
    p_best_score = np.array([problem.evaluate(pos[i]) for i in range(n_particles)])

    # Global best
    g_best_idx   = int(np.argmax(p_best_score))
    g_best_pos   = p_best_pos[g_best_idx].copy()
    g_best_score = float(p_best_score[g_best_idx])

    history: List[float] = []

    for _ in range(n_iters):
        r1 = rng.random(size=(n_particles, n))
        r2 = rng.random(size=(n_particles, n))

        # Velocity update
        vel = (w * vel
               + c1 * r1 * (p_best_pos - pos)
               + c2 * r2 * (g_best_pos  - pos))
        vel = np.clip(vel, -v_max, v_max)

        # Binary transfer: flip to 1 with probability sigmoid(v)
        prob = _sigmoid(vel)
        rand = rng.random(size=(n_particles, n))
        pos  = (rand < prob).astype(float)

        # Evaluate and update personal / global bests
        scores = np.array([problem.evaluate(pos[i]) for i in range(n_particles)])
        improved = scores > p_best_score
        p_best_pos[improved]   = pos[improved]
        p_best_score[improved] = scores[improved]

        new_best_idx = int(np.argmax(p_best_score))
        if p_best_score[new_best_idx] > g_best_score:
            g_best_score = float(p_best_score[new_best_idx])
            g_best_pos   = p_best_pos[new_best_idx].copy()

        history.append(g_best_score)

    return g_best_pos, g_best_score, history
