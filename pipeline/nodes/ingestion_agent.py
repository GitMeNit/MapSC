"""
pipeline/nodes/ingestion_agent.py — LangGraph node: ingest graph + GDELT docs.
"""
from __future__ import annotations

import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


def ingestion_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build / load the supply-chain graph and collect GDELT documents.

    Updates state keys: graph_path, raw_docs, errors.
    """
    import paths  # noqa: F401
    from industry import load_industry
    from pipeline.ingest import build_graph

    industry = state.get("industry", "semiconductors")
    errors   = list(state.get("errors", []))
    cfg      = state.get("config") or load_industry(industry)

    # ── Build / load graph ────────────────────────────────────────────────────
    try:
        graph = build_graph(industry, use_cache=True)
        from pathlib import Path
        graph_path = str(
            Path(__file__).resolve().parent.parent.parent
            / "data" / "processed" / f"{industry}_graph.json"
        )
        logger.info("Graph loaded: %d nodes, %d edges", graph.number_of_nodes(), graph.number_of_edges())
    except Exception as exc:
        msg = f"ingestion_agent: graph build failed — {exc}"
        logger.error(msg)
        errors.append(msg)
        graph_path = ""

    # ── Fetch GDELT docs ──────────────────────────────────────────────────────
    raw_docs = []
    try:
        from adapters.gdelt import GdeltAdapter
        from adapters.cache import BaseAPIClient  # installs cache  # noqa
        adapter = GdeltAdapter()
        keywords = cfg.get("search_keywords", [])[:4]
        if keywords:
            records = adapter.fetch({"keywords": keywords})
            raw_docs = [r.raw_data for r in records]
            logger.info("GDELT: fetched %d articles", len(raw_docs))
    except Exception as exc:
        msg = f"ingestion_agent: GDELT fetch failed — {exc}"
        logger.warning(msg)
        errors.append(msg)

    return {
        **state,
        "config":     cfg,
        "graph_path": graph_path,
        "raw_docs":   raw_docs,
        "errors":     errors,
    }
