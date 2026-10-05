"""
pipeline/graph.py — LangGraph wiring for the pipeline.
"""
from __future__ import annotations

import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from pipeline.state import PipelineState
from pipeline.nodes.ingestion_agent import ingestion_agent
from pipeline.nodes.extraction_agent import extraction_agent
from pipeline.nodes.graph_update_agent import graph_update_agent
from pipeline.nodes.risk_agent import risk_agent
from pipeline.nodes.optimizer_agent import optimizer_agent
from pipeline.nodes.rl_agent import rl_agent
from pipeline.nodes.report_agent import report_agent
from pipeline.nodes.human_review import human_review
from pipeline.nodes.extraction_agent import _CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)


def route_extraction(state: PipelineState) -> str:
    """
    Conditional routing: if extraction confidence is low, retry once.
    If errors exist, skip to report.
    """
    extracted = state.get("extracted", {})
    method = extracted.get("method")
    
    if state.get("errors") and method == "error_fallback":
        return "report"
        
    if method == "no_docs":
        return "graph_update"
        
    conf = extracted.get("confidence", 0.0)
    retries = state.get("retry_count", 0)
    
    # We incremented retry_count in extraction_agent. So 1 means first try, 2 means second try.
    if conf < _CONFIDENCE_THRESHOLD and retries < 2:
        return "extraction"
        
    return "graph_update"


def build_pipeline() -> StateGraph:
    """Build the LangGraph pipeline."""
    workflow = StateGraph(PipelineState)

    # Add nodes
    workflow.add_node("ingestion", ingestion_agent)
    workflow.add_node("extraction", extraction_agent)
    workflow.add_node("graph_update", graph_update_agent)
    workflow.add_node("human_review", human_review)
    workflow.add_node("risk", risk_agent)
    workflow.add_node("optimizer", optimizer_agent)
    workflow.add_node("rl", rl_agent)
    workflow.add_node("report", report_agent)

    # Build edges
    workflow.add_edge(START, "ingestion")
    workflow.add_edge("ingestion", "extraction")
    
    # Conditional edge from extraction
    workflow.add_conditional_edges(
        "extraction",
        route_extraction,
        {
            "extraction": "extraction",
            "graph_update": "graph_update",
            "report": "report"
        }
    )
    
    workflow.add_edge("graph_update", "human_review")
    workflow.add_edge("human_review", "risk")
    
    # Risk fans out to Optimizer and RL
    workflow.add_edge("risk", "optimizer")
    workflow.add_edge("risk", "rl")
    
    # Both fan in to Report
    workflow.add_edge("optimizer", "report")
    workflow.add_edge("rl", "report")
    
    workflow.add_edge("report", END)

    # Compile with memory (for human_review interrupt)
    memory = MemorySaver()
    app = workflow.compile(
        checkpointer=memory,
        interrupt_before=["human_review"]
    )
    
    return app
