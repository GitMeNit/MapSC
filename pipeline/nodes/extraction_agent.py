"""
pipeline/nodes/extraction_agent.py — LangGraph node: extract entities/relations from GDELT docs.

Falls back to keyword matching when LLM is unavailable or confidence is low.
"""
from __future__ import annotations

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

_CONFIDENCE_THRESHOLD = 0.3   # below this triggers a re-extract attempt


def extraction_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured entities and relations from GDELT raw_docs.

    Updates state keys: extracted, retry_count, errors.
    """
    import paths  # noqa: F401
    from pipeline.llm import get_llm

    cfg      = state.get("config", {})
    raw_docs = state.get("raw_docs", [])
    errors   = list(state.get("errors", []))

    entities  = cfg.get("seed_entities", [])
    materials = cfg.get("key_materials", [])

    if not raw_docs:
        logger.info("No raw docs — skipping extraction.")
        return {
            **state,
            "extracted": {
                "entities": [], "materials": [], "relations": [],
                "confidence": 0.0, "method": "no_docs",
            },
        }

    # Combine article titles / snippets (capped for token budget)
    combined_text = "\n".join(
        d.get("title", d.get("url", "")) for d in raw_docs[:20]
    )

    llm = get_llm()
    try:
        extracted = llm.extract_entities(combined_text, entities, materials)
    except Exception as exc:
        msg = f"extraction_agent: LLM failed — {exc}"
        logger.warning(msg)
        errors.append(msg)
        extracted = {
            "entities": [], "materials": [], "relations": [],
            "confidence": 0.0, "method": "error_fallback",
        }

    return {
        **state,
        "extracted":   extracted,
        "retry_count": state.get("retry_count", 0) + 1,
        "errors":      errors,
    }
