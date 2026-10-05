"""
pipeline/state.py — Shared state TypedDict for the LangGraph pipeline.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class PipelineState(TypedDict, total=False):
    # Input
    industry:   str                    # e.g. "semiconductors"
    config:     Dict[str, Any]         # loaded industry YAML config

    # Ingestion
    graph_path: str                    # path to node-link JSON on disk
    raw_docs:   List[Dict[str, Any]]   # GDELT article dicts

    # Extraction
    extracted:  Dict[str, Any]         # LLM/keyword extraction output
                                       # keys: entities, materials, relations, confidence

    # Risk
    risk_table: Dict[str, Any]         # serialised risk DataFrame
                                       # keys: columns, rows

    # Optimizer
    optimizer_results: Optional[Dict[str, Any]]   # from run_optimizer_suite()

    # RL
    rl_results: Optional[Dict[str, Any]]          # from evaluate()

    # Simulation
    sim_results: Optional[Dict[str, Any]]         # from simulate_removal()

    # Report
    report: str                        # final markdown report

    # Control
    approved:   bool                   # human-review gate
    errors:     List[str]              # non-fatal error messages accumulated
    retry_count: int                   # extraction retry counter
