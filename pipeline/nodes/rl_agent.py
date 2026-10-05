"""
pipeline/nodes/rl_agent.py — LangGraph node: run RL policy recommendation.
"""
from __future__ import annotations

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def rl_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the RL policy evaluation to generate a recommendation (Phase C).
    """
    import paths  # noqa: F401
    from core.rl.evaluate import evaluate

    industry = state.get("industry", "semiconductors")
    errors = list(state.get("errors", []))
    rl_results = None

    try:
        # Quick eval for pipeline
        rl_results = evaluate(industry=industry, n_episodes=10, top_k=8)
        logger.info("RL policy evaluation completed.")
    except Exception as exc:
        msg = f"rl_agent failed: {exc}"
        logger.warning(msg)
        errors.append(msg)

    return {"rl_results": rl_results}
