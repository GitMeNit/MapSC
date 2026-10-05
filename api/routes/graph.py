"""
api/routes/graph.py — Endpoint for Cytoscape.js frontend.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
import networkx as nx
from api.dependencies import get_graph

router = APIRouter()

@router.get("/{industry}/cytoscape")
def get_cytoscape_graph(industry: str, graph: nx.DiGraph = Depends(get_graph)):
    """
    Returns graph data formatted for Cytoscape.js.
    """
    elements = []
    
    # Nodes
    for node_id, data in graph.nodes(data=True):
        elements.append({
            "data": {
                "id": str(node_id),
                "label": str(node_id),
                "type": data.get("node_type", "Unknown"),
                **{k: v for k, v in data.items() if k != "node_type"}
            }
        })
        
    # Edges
    for u, v, data in graph.edges(data=True):
        elements.append({
            "data": {
                "source": str(u),
                "target": str(v),
                "label": data.get("edge_type", ""),
                **data
            }
        })
        
    return {"elements": elements}
