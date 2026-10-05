"""
pipeline/nodes/human_review.py — LangGraph node: interrupt for human approval.
"""
from __future__ import annotations

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def human_review(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Passthrough node. The LangGraph interrupter will pause before this node.
    It reads 'approved' from the state which can be injected by a human (or auto-approve flag).
    """
    logger.info(f"Human review node reached. Approved: {state.get('approved', False)}")
    return state
