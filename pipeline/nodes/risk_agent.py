"""
pipeline/nodes/risk_agent.py — LangGraph node: run existing risk engine.
"""
from __future__ import annotations

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def risk_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute risk scores using the existing Risk Engine.
    """
    import paths  # noqa: F401
    
    graph_path = state.get("graph_path")
    errors = list(state.get("errors", []))
    risk_table = {}

    if not graph_path:
        return state

    try:
        import json
        from pathlib import Path
        import networkx as nx
        from networkx.readwrite import json_graph
        from graph_engine.risk_scores import SupplyChainRiskEngine
        
        with Path(graph_path).open("r", encoding="utf-8") as f:
            data = json.load(f)
        graph = json_graph.node_link_graph(data)
        
        if graph.number_of_nodes() > 0:
            engine = SupplyChainRiskEngine(graph)
            df = engine.compute_composite_risk_scores()
            risk_table = {
                "columns": list(df.columns),
                "rows": df.to_dict(orient="records")
            }
            logger.info("Risk table computed.")
        else:
            logger.warning("Graph is empty, skipping risk scores.")
    except Exception as exc:
        msg = f"risk_agent failed: {exc}"
        logger.warning(msg)
        errors.append(msg)

    return {**state, "risk_table": risk_table, "errors": errors}
