"""
api/routes/simulation.py — Endpoint for the Failure Simulator.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
import networkx as nx
from api.dependencies import get_graph
from graph_engine.simulator import CascadingFailureSimulator

router = APIRouter()

@router.post("/{industry}/remove")
def simulate_removal(industry: str, target_node: str, graph: nx.DiGraph = Depends(get_graph)):
    """
    Simulate the removal of a specific node and return the impact.
    """
    try:
        simulator = CascadingFailureSimulator(graph)
        result = simulator.simulate_removal(target_node)
        return {
            "target_node": target_node,
            "systemic_impact_pct": result["impact_percentage"] / 100,
            "downstream_nodes_affected": result["downstream_affected_count"]
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
