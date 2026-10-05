"""
api/routes/optimizer.py — Endpoint for Phase B optimizers.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from scripts.run_optimizer import run_optimizer_suite

router = APIRouter()

@router.get("/{industry}/run")
def run_optimizers(industry: str, chokepoint: str, budget: float = 0.5, runs: int = 1):
    """
    Run PSO and ACO optimisers to find diverse suppliers.
    """
    try:
        results = run_optimizer_suite(
            industry=industry,
            chokepoint=chokepoint,
            budget=budget,
            n_runs=runs,
        )
        return results
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
