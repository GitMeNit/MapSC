"""
pipeline/nodes/graph_update_agent.py — LangGraph node: update graph with extracted facts.
"""
from __future__ import annotations

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def graph_update_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge validated facts into the main graph.
    Only allows VALID_NODE_TYPES and VALID_EDGE_TYPES.
    """
    import paths  # noqa: F401
    import networkx as nx
    from networkx.readwrite import json_graph
    from graph_engine.loader import VALID_NODE_TYPES, VALID_EDGE_TYPES

    extracted = state.get("extracted", {})
    graph_path = state.get("graph_path")
    errors = list(state.get("errors", []))

    if not graph_path:
        return state

    try:
        import json
        from pathlib import Path
        
        with Path(graph_path).open("r", encoding="utf-8") as f:
            data = json.load(f)
        graph = json_graph.node_link_graph(data)
        
        # Add extracted entities as Companies (if not exist)
        for ent in extracted.get("entities", []):
            if not graph.has_node(ent):
                graph.add_node(ent, node_type="Company", source="llm_extraction")
                
        # Add extracted materials
        for mat in extracted.get("materials", []):
            if not graph.has_node(mat):
                graph.add_node(mat, node_type="Material", source="llm_extraction")
                
        # Add relations (only if types match schema)
        for rel in extracted.get("relations", []):
            src = rel.get("source")
            tgt = rel.get("target")
            rtype = rel.get("relation")
            
            if rtype in VALID_EDGE_TYPES and src and tgt:
                if graph.has_node(src) and graph.has_node(tgt):
                    graph.add_edge(src, tgt, edge_type=rtype, source="llm_extraction")
                    
        # Save updated graph
        out_data = json_graph.node_link_data(graph)
        with Path(graph_path).open("w", encoding="utf-8") as f:
            json.dump(out_data, f, default=str)
            
        logger.info("Graph updated with extracted facts.")
    except Exception as exc:
        msg = f"graph_update_agent failed: {exc}"
        logger.warning(msg)
        errors.append(msg)

    return {**state, "errors": errors}
