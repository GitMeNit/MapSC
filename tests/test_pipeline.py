"""
tests/test_pipeline.py — Tests for the new pipeline and optimizers.
"""
from __future__ import annotations

import pytest
from core.optimizer.problem import Candidate, Problem
from core.optimizer.baseline import greedy_baseline

def test_problem_initialization():
    candidates = [
        Candidate(id="A", region="AA", resilience_gain=0.1, lead_time=0.5, cost=0.1),
        Candidate(id="B", region="BB", resilience_gain=0.2, lead_time=0.5, cost=0.3),
    ]
    prob = Problem(candidates, max_budget=0.5)
    assert prob.n() == 2
    assert prob.max_budget == 0.5

def test_greedy_baseline():
    candidates = [
        Candidate(id="A", region="AA", resilience_gain=0.1, lead_time=0.5, cost=0.2), # efficiency 0.5
        Candidate(id="B", region="BB", resilience_gain=0.2, lead_time=0.5, cost=0.1), # efficiency 2.0 (chosen first)
    ]
    prob = Problem(candidates, max_budget=0.25)
    mask, score, _ = greedy_baseline(prob)
    
    # B should be selected, A should not because budget is 0.25 and B takes 0.1, leaving 0.15 (not enough for A's 0.2)
    assert mask[0] == 0.0
    assert mask[1] == 1.0
    assert score == 20.0
