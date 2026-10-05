#!/usr/bin/env python
"""
scripts/run_graph.py — Phase A done-when script.

Usage
-----
    python scripts/run_graph.py --industry semiconductors
    python scripts/run_graph.py --industry ev-battery-minerals
    python scripts/run_graph.py --industry semiconductors --no-cache
"""
from __future__ import annotations

import sys
import argparse
import logging
from pathlib import Path

# Add repo root to sys.path so 'paths' module is importable regardless of cwd
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import paths  # noqa: F401  (now resolvable; sets up all other path entries)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)

from pipeline.ingest import build_graph
from graph_engine.risk_scores import SupplyChainRiskEngine
from graph_engine.simulator import CascadingFailureSimulator


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and analyse a supply-chain graph.")
    parser.add_argument("--industry", required=True,
                        help="Industry name: 'semiconductors' or 'ev-battery-minerals'")
    parser.add_argument("--no-cache", action="store_true",
                        help="Ignore cached graph and re-fetch from adapters")
    args = parser.parse_args()

    use_cache = not args.no_cache

    print(f"\n{'='*60}")
    print(f"  Industry : {args.industry}")
    print(f"  Cache    : {'off (fresh fetch)' if not use_cache else 'on'}")
    print(f"{'='*60}\n")

    # ── 1. Build graph ────────────────────────────────────────────────────────
    graph = build_graph(args.industry, use_cache=use_cache)

    print(f"[Graph]  Nodes : {graph.number_of_nodes()}")
    print(f"[Graph]  Edges : {graph.number_of_edges()}")

    # Node-type breakdown
    from collections import Counter
    type_counts = Counter(
        data.get("node_type", "Unknown")
        for _, data in graph.nodes(data=True)
    )
    print("\n[Graph]  Node-type breakdown:")
    for ntype, cnt in sorted(type_counts.items()):
        print(f"           {ntype:<20} {cnt}")

    # ── 2. Risk scores ────────────────────────────────────────────────────────
    if graph.number_of_nodes() == 0:
        print("\n[WARNING] Graph is empty — no risk scores to compute.")
        return

    engine = SupplyChainRiskEngine(graph)
    risk_df = engine.compute_composite_risk_scores()

    print("\n[Risk]   Top-10 risky nodes:")
    print(risk_df.to_string(index=False))

    # ── 3. Cascading failure simulation ───────────────────────────────────────
    if risk_df.empty:
        print("\n[Sim]    No nodes to simulate.")
        return

    top_node = risk_df.iloc[0]["Node_ID"]
    print(f"\n[Sim]    Removing top-risk node: '{top_node}'")

    simulator = CascadingFailureSimulator(graph)
    result    = simulator.simulate_removal(top_node)

    print(f"[Sim]    Systemic impact : {result['impact_percentage']}% of network")
    print(f"[Sim]    Downstream nodes affected : {result['downstream_affected_count']}")
    if result["affected_node_list"]:
        print(f"[Sim]    Sample affected : {result['affected_node_list'][:5]}")

    print(f"\n{'='*60}")
    print("  Phase A — DONE")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
