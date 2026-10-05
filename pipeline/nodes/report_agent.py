"""
pipeline/nodes/report_agent.py — LangGraph node: summarize all findings.
"""
from __future__ import annotations

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def report_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate markdown report via LLM.
    """
    import paths  # noqa: F401
    from pipeline.llm import get_llm

    llm = get_llm()
    errors = list(state.get("errors", []))
    
    try:
        report = llm.summarise(state)
        logger.info("Report generated.")
    except Exception as exc:
        msg = f"report_agent failed: {exc}"
        logger.warning(msg)
        errors.append(msg)
        report = f"# Error Generating Report\n\n{msg}"

    return {**state, "report": report, "errors": errors}
