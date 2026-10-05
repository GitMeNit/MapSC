"""
pipeline/nodes/optimizer_agent.py — LangGraph node: run diversification optimizer.
"""
from __future__ import annotations

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def optimizer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the sourcing diversification optimizer (Phase B).
    """
    import paths  # noqa: F401
    from scripts.run_optimizer import run_optimizer_suite

    industry = state.get("industry", "semiconductors")
    risk_table = state.get("risk_table", {})
    errors = list(state.get("errors", []))
    opt_results = None

    rows = risk_table.get("rows", [])
    if not rows:
        return state

    top_node = rows[0].get("Node_ID")
    if not top_node:
        return state

    try:
        opt_results = run_optimizer_suite(
            industry=industry,
            chokepoint=top_node,
            budget=0.5,
            n_runs=3,  # quick runs for pipeline
        )
        logger.info("Optimizer completed.")
    except Exception as exc:
        msg = f"optimizer_agent failed: {exc}"
        logger.warning(msg)
        errors.append(msg)

    return {"optimizer_results": opt_results}
