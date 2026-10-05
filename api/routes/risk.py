"""
api/routes/risk.py — Endpoint for the Risk Engine.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
import networkx as nx
from api.dependencies import get_graph
from graph_engine.risk_scores import SupplyChainRiskEngine

router = APIRouter()

@router.get("/{industry}/scores")
def get_risk_scores(industry: str, graph: nx.DiGraph = Depends(get_graph)):
    """
    Compute and return composite risk scores.
    """
    try:
        engine = SupplyChainRiskEngine(graph)
        df = engine.compute_composite_risk_scores()
        return df.to_dict(orient="records")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
