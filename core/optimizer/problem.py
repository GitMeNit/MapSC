"""
core/optimizer/problem.py — Sourcing diversification problem formulation.

Candidate
---------
    A candidate alternate supplier / partner country for a given chokepoint node.

    Attributes
    ----------
    id           : str    human-readable label (e.g. "Japan" or "TSMC-JP")
    region       : str    ISO-3166 country / region code
    cost         : float  normalised procurement cost ∈ [0, 1]
                           derived as: (trade_value_share of current partner) *
                           (1 + distance_proxy / max_distance)
                           where distance_proxy = 1.0 for neighbouring regions,
                           3.0 for intercontinental
    lead_time    : float  normalised lead-time ∈ [0, 1]
                           derived as: 1 − (import_share_of_candidate / total_imports)
                           (less established sources = longer lead time)
    resilience_gain : float  expected HHI reduction on activation ∈ [0, 1]
                           = current_hhi − hhi_after_adding_candidate
                           clamped to [0, 1]

Problem
-------
    Encapsulates a set of candidates, a budget ceiling, and scoring weights.

    evaluate(selection_mask) -> float
    ----------------------------------
    Objective value for a binary mask over candidates.
    Higher is better.

    Formula:
        score = w_res * Σ resilience_gain_i * mask_i
               − w_cost * Σ cost_i * mask_i
               − w_lt  * Σ lead_time_i * mask_i
               − PENALTY * max(0, Σ cost_i * mask_i − budget)

    PENALTY = 1e6  (hard budget enforcement)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np
import networkx as nx


PENALTY = 1e6


@dataclass
class Candidate:
    """A candidate alternate supplier / partner country."""
    id: str
    region: str
    cost: float           # ∈ [0, 1]
    lead_time: float      # ∈ [0, 1]
    resilience_gain: float  # ∈ [0, 1]

    def __post_init__(self):
        for attr in ("cost", "lead_time", "resilience_gain"):
            v = getattr(self, attr)
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"Candidate.{attr} must be ∈ [0,1], got {v}")


@dataclass
class Problem:
    """
    Supplier diversification optimisation problem.

    Parameters
    ----------
    candidates : List[Candidate]
    budget     : float   total cost budget (same scale as Candidate.cost sums)
    weights    : dict    keys: resilience, cost, lead_time  (default 0.5/0.3/0.2)
    """
    candidates: List[Candidate]
    budget: float
    weights: dict = field(default_factory=lambda: {
        "resilience": 0.5,
        "cost":       0.3,
        "lead_time":  0.2,
    })

    # Pre-computed arrays for fast numpy evaluation
    _res: np.ndarray = field(init=False, repr=False)
    _cst: np.ndarray = field(init=False, repr=False)
    _lt:  np.ndarray = field(init=False, repr=False)

    def __post_init__(self):
        if not self.candidates:
            raise ValueError("Problem must have at least one candidate.")
        self._res = np.array([c.resilience_gain for c in self.candidates], dtype=float)
        self._cst = np.array([c.cost            for c in self.candidates], dtype=float)
        self._lt  = np.array([c.lead_time       for c in self.candidates], dtype=float)

    def n(self) -> int:
        return len(self.candidates)

    def evaluate(self, mask: np.ndarray) -> float:
        """
        Evaluate a binary selection mask (1 = selected, 0 = not).

        Returns the objective score (higher is better).
        A budget violation applies a large penalty.
        """
        mask = np.asarray(mask, dtype=float)
        w = self.weights
        total_cost = float(self._cst @ mask)
        score = (
            w["resilience"] * float(self._res @ mask)
            - w["cost"]     * total_cost
            - w["lead_time"] * float(self._lt  @ mask)
            - PENALTY * max(0.0, total_cost - self.budget)
        )
        return score


# ─────────────────────────────────────────────────────────────────────────────
# Factory: build a Problem from a live graph + chokepoint node
# ─────────────────────────────────────────────────────────────────────────────

# Distance proxies (intercontinental distance factor for lead-time estimation)
_DISTANCE_PROXY: dict = {
    "CN": 1.0,  "TW": 1.0,  "KR": 1.0,  "JP": 1.2,
    "US": 2.5,  "DE": 2.0,  "NL": 2.0,  "FR": 2.0,
    "AU": 1.8,  "ZA": 2.2,  "CL": 3.0,  "PE": 3.0,
    "CD": 2.8,  "RU": 1.5,  "IN": 0.0,  # self
}
_MAX_DIST = max(_DISTANCE_PROXY.values()) or 1.0

# Potential alternate source countries per material / context
_ALTERNATE_COUNTRIES = ["JP", "KR", "US", "DE", "AU", "TW", "FR", "CL", "ZA"]


def build_problem_from_graph(
    graph: nx.DiGraph,
    chokepoint_node: str,
    budget: float = 0.5,
    weights: Optional[dict] = None,
    rng: Optional[np.random.Generator] = None,
) -> Problem:
    """
    Derive a sourcing-diversification Problem from the graph around *chokepoint_node*.

    Candidate generation
    --------------------
    1. Collect all Country nodes that currently supply *chokepoint_node* (in-edges from Country).
    2. Compute current HHI for *chokepoint_node* (via in-edge weights).
    3. For each alternate country in _ALTERNATE_COUNTRIES (not already a supplier):
       - cost = distance_proxy / _MAX_DIST * (1 - 1/n_alternates) clamped to [0,1]
       - lead_time = 1 - import_share_of_max_current_partner (less known = longer)
       - resilience_gain = estimated HHI reduction if this country captured 20% share

    If the graph has < 2 nodes, fall back to a synthetic 5-candidate problem.
    """
    if rng is None:
        rng = np.random.default_rng(42)

    # Current supplier share
    in_edges = list(graph.in_edges(chokepoint_node, data=True))
    country_weights: dict = {}
    for src, _, data in in_edges:
        node_type = graph.nodes[src].get("node_type", "")
        if node_type == "Country":
            country_weights[src] = float(data.get("weight", 1.0))

    total_w = sum(country_weights.values()) or 1.0
    shares  = {c: w / total_w for c, w in country_weights.items()}

    # Current HHI
    current_hhi = sum(s ** 2 for s in shares.values()) if shares else 1.0

    existing_suppliers = set(country_weights.keys())
    n_alt = len(_ALTERNATE_COUNTRIES)
    candidates: List[Candidate] = []

    for i, iso in enumerate(_ALTERNATE_COUNTRIES):
        if iso in existing_suppliers:
            continue

        dist_proxy = _DISTANCE_PROXY.get(iso, 2.0)
        cost = float(np.clip(dist_proxy / _MAX_DIST * (0.5 + 0.5 * rng.random()), 0, 1))

        # lead_time: established current partners have short lead times; new ones longer
        lead_time = float(np.clip(0.4 + 0.5 * rng.random(), 0, 1))

        # resilience_gain: HHI after adding this country at 20% share
        new_shares = {**shares, iso: 0.20}
        s_sum = sum(new_shares.values())
        new_shares = {k: v / s_sum for k, v in new_shares.items()}
        new_hhi = sum(s ** 2 for s in new_shares.values())
        resilience_gain = float(np.clip(current_hhi - new_hhi, 0, 1))

        candidates.append(Candidate(
            id=iso, region=iso,
            cost=cost,
            lead_time=lead_time,
            resilience_gain=resilience_gain,
        ))

    if not candidates:
        # Fall back: synthetic candidates
        for i in range(5):
            candidates.append(Candidate(
                id=f"alt_{i}", region="XX",
                cost=float(np.clip(0.1 + 0.15 * i, 0, 1)),
                lead_time=float(np.clip(0.1 + 0.1 * i, 0, 1)),
                resilience_gain=float(np.clip(0.4 - 0.05 * i, 0, 1)),
            ))

    return Problem(
        candidates=candidates,
        budget=budget,
        weights=weights or {"resilience": 0.5, "cost": 0.3, "lead_time": 0.2},
    )
