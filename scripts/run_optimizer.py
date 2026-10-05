#!/usr/bin/env python
"""
scripts/run_optimizer.py — Phase B done-when script.

Usage
-----
    python scripts/run_optimizer.py --industry semiconductors --budget 0.5 --runs 5
    python scripts/run_optimizer.py --industry ev-battery-minerals --node auto --budget 0.6 --runs 10
"""
from __future__ import annotations

import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import paths  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)

import numpy as np
from pipeline.ingest import build_graph
from graph_engine.risk_scores import SupplyChainRiskEngine
from core.optimizer.problem import build_problem_from_graph
from core.optimizer.baseline import greedy_baseline
from core.optimizer.pso import binary_pso
from core.optimizer.aco import ant_colony

_RESULTS_DIR = _REPO_ROOT / "data" / "processed" / "results"
_RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_optimizer_suite(
    industry: str,
    chokepoint: str,
    budget: float,
    n_runs: int,
) -> Dict[str, Any]:
    """Run Baseline / PSO / ACO over *n_runs* seeds, return aggregated stats."""

    graph = build_graph(industry, use_cache=True)
    problem = build_problem_from_graph(graph, chokepoint, budget=budget)

    if problem.n() == 0:
        raise RuntimeError(f"No candidates generated for chokepoint '{chokepoint}'")

    results: Dict[str, Any] = {
        "industry":   industry,
        "chokepoint": chokepoint,
        "budget":     budget,
        "n_candidates": problem.n(),
        "n_runs":     n_runs,
        "algorithms": {},
    }

    all_scores: Dict[str, List[float]] = {"baseline": [], "pso": [], "aco": []}
    all_histories: Dict[str, List[List[float]]] = {"pso": [], "aco": []}

    for seed in range(n_runs):
        b_mask, b_score, _   = greedy_baseline(problem, seed=seed)
        p_mask, p_score, p_h = binary_pso(problem, seed=seed, n_iters=80)
        a_mask, a_score, a_h = ant_colony(problem,  seed=seed, n_iters=80)

        all_scores["baseline"].append(b_score)
        all_scores["pso"].append(p_score)
        all_scores["aco"].append(a_score)
        all_histories["pso"].append(p_h)
        all_histories["aco"].append(a_h)

    b_mean = float(np.mean(all_scores["baseline"]))

    for algo, scores in all_scores.items():
        arr = np.array(scores)
        mean, std = float(arr.mean()), float(arr.std())
        improvement = ((mean - b_mean) / (abs(b_mean) + 1e-9)) * 100 if algo != "baseline" else 0.0
        entry: Dict[str, Any] = {
            "mean_score": round(mean, 6),
            "std_score":  round(std,  6),
            "improvement_vs_baseline_pct": round(improvement, 2),
        }
        if algo in all_histories:
            # Average convergence curve across seeds
            histories = all_histories[algo]
            min_len = min(len(h) for h in histories)
            avg_curve = np.mean([h[:min_len] for h in histories], axis=0).tolist()
            entry["convergence_history"] = [round(v, 6) for v in avg_curve]
        results["algorithms"][algo] = entry

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run supplier diversification optimisers.")
    parser.add_argument("--industry", required=True)
    parser.add_argument("--node", default="auto",
                        help="Chokepoint node ID, or 'auto' (top-risk node)")
    parser.add_argument("--budget", type=float, default=0.5)
    parser.add_argument("--runs",   type=int,   default=5)
    args = parser.parse_args()

    # Resolve 'auto' node
    chokepoint = args.node
    if chokepoint == "auto":
        graph = build_graph(args.industry, use_cache=True)
        engine = SupplyChainRiskEngine(graph)
        risk_df = engine.compute_composite_risk_scores()
        chokepoint = str(risk_df.iloc[0]["Node_ID"])
        print(f"[Auto] Selected chokepoint: '{chokepoint}' (top-risk node)")

    results = run_optimizer_suite(
        industry=args.industry,
        chokepoint=chokepoint,
        budget=args.budget,
        n_runs=args.runs,
    )

    # ── Print comparison table ────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  Industry  : {args.industry}")
    print(f"  Chokepoint: {chokepoint}")
    print(f"  Budget    : {args.budget}  |  Runs: {args.runs}")
    print(f"  Candidates: {results['n_candidates']}")
    print(f"{'='*65}")
    header = f"{'Algorithm':<12}  {'Mean Score':>12}  {'Std':>8}  {'vs Baseline':>12}"
    print(header)
    print("-" * len(header))
    for algo, stats in results["algorithms"].items():
        impr = stats["improvement_vs_baseline_pct"]
        impr_str = f"{impr:+.2f}%" if algo != "baseline" else "    baseline"
        print(f"{algo:<12}  {stats['mean_score']:>12.6f}  {stats['std_score']:>8.6f}  {impr_str:>12}")
    print(f"{'='*65}\n")

    # ── Save JSON ─────────────────────────────────────────────────────────────
    out_path = _RESULTS_DIR / f"optimizer_{args.industry}.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print(f"[Saved] {out_path}")

    # ── Convergence plot ──────────────────────────────────────────────────────
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(9, 5))
        colors = {"pso": "#4C72B0", "aco": "#DD8452"}
        for algo, stats in results["algorithms"].items():
            if "convergence_history" in stats:
                ax.plot(stats["convergence_history"],
                        label=algo.upper(), color=colors.get(algo, "grey"), linewidth=2)
        ax.set_title(f"Optimiser Convergence — {args.industry}")
        ax.set_xlabel("Iteration")
        ax.set_ylabel("Best Score")
        ax.legend()
        ax.grid(alpha=0.3)
        fig.tight_layout()
        png_path = _RESULTS_DIR / f"optimizer_{args.industry}_convergence.png"
        fig.savefig(png_path, dpi=120)
        plt.close(fig)
        print(f"[Saved] {png_path}")
    except ImportError:
        print("[Skip] matplotlib not installed — convergence plot skipped.")

    print("\n  Phase B — DONE\n")


if __name__ == "__main__":
    main()
