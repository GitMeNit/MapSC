"""
api/dependencies.py — Shared dependencies for FastAPI routes.
"""
from __future__ import annotations

from typing import Dict, Any
from fastapi import HTTPException
from pipeline.ingest import build_graph

_GRAPH_CACHE: Dict[str, Any] = {}

def get_graph(industry: str):
    """
    Dependency to load and cache the networkx graph in memory for the API.
    Uses the pipeline.ingest cache layer under the hood, but holds the nx.DiGraph
    object to avoid deserialisation overhead on every request.
    """
    if industry not in _GRAPH_CACHE:
        try:
            g = build_graph(industry, use_cache=True)
            _GRAPH_CACHE[industry] = g
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to load graph: {exc}")
    
    return _GRAPH_CACHE[industry]
