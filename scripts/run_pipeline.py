#!/usr/bin/env python
"""
scripts/run_pipeline.py — Phase D done-when script.

Usage
-----
    python scripts/run_pipeline.py --industry semiconductors --auto-approve
"""
from __future__ import annotations

import sys
import json
import argparse
import logging
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
import paths  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)

_RESULTS_DIR = _REPO_ROOT / "data" / "processed" / "results"
_RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LangGraph multi-agent pipeline.")
    parser.add_argument("--industry", required=True)
    parser.add_argument("--auto-approve", action="store_true", help="Bypass human review")
    args = parser.parse_args()

    from pipeline.graph import build_pipeline
    
    print(f"\n{'='*65}")
    print(f"  Running Pipeline : {args.industry}")
    print(f"  Auto-Approve     : {args.auto_approve}")
    print(f"{'='*65}\n")

    app = build_pipeline()
    
    thread = {"configurable": {"thread_id": f"pipeline_{args.industry}"}}
    initial_state = {
        "industry": args.industry,
        "approved": args.auto_approve,
        "retry_count": 0,
        "errors": []
    }
    
    # 1. Run until interrupt (human_review)
    print("\n[Pipeline] Starting run...")
    for event in app.stream(initial_state, thread):
        for node, state in event.items():
            print(f"[Pipeline] Finished node: {node}")
            
    # Check if we are paused at human_review
    state_snap = app.get_state(thread)
    if state_snap.next and state_snap.next[0] == "human_review":
        if args.auto_approve:
            print("\n[Pipeline] Auto-approving human review step...")
            # Continue execution
            for event in app.stream(None, thread):
                for node, state in event.items():
                    print(f"[Pipeline] Finished node: {node}")
        else:
            print("\n[Pipeline] PAUSED. Waiting for human approval at 'human_review'.")
            print("Run with --auto-approve to bypass.")
            return

    # Final state
    final_state = app.get_state(thread).values
    
    report_md = final_state.get("report", "No report generated.")
    
    # ── Save Report ─────────────────────────────────────────────────────────────
    out_path = _RESULTS_DIR / f"report_{args.industry}.md"
    with out_path.open("w", encoding="utf-8") as fh:
        fh.write(report_md)
        
    print(f"\n[Saved] {out_path}")
    print(f"\n{'='*65}")
    print("  Phase D — DONE")
    print(f"{'='*65}\n")

if __name__ == "__main__":
    main()
