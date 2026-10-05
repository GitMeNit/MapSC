#!/usr/bin/env python
"""
scripts/run_rl.py — Phase C done-when script.

Usage
-----
    python scripts/run_rl.py --industry semiconductors --timesteps 100000
    python scripts/run_rl.py --industry ev-battery-minerals --timesteps 50000
"""
from __future__ import annotations

import sys
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and evaluate RL disruption-response agent.")
    parser.add_argument("--industry",   required=True)
    parser.add_argument("--timesteps",  type=int, default=100_000)
    parser.add_argument("--top-k",      type=int, default=8)
    parser.add_argument("--eval-only",  action="store_true",
                        help="Skip training, only run evaluation (uses cached model if present)")
    args = parser.parse_args()

    industry   = args.industry
    timesteps  = args.timesteps
    top_k      = args.top_k

    # ── Training ──────────────────────────────────────────────────────────────
    if not args.eval_only:
        print(f"\n[RL] Training PPO for '{industry}' ({timesteps:,} timesteps) …\n")
        try:
            from core.rl.train import train_ppo
            model_path = train_ppo(
                industry=industry,
                total_timesteps=timesteps,
                top_k=top_k,
                verbose=1,
            )
            print(f"\n[RL] Model saved: {model_path}")
        except ImportError as e:
            print(f"\n[RL] Training skipped (dependency missing): {e}")
            print("[RL] Continuing with evaluation (baseline only).")

    # ── Evaluation ────────────────────────────────────────────────────────────
    print(f"\n[RL] Evaluating policies for '{industry}' (100 episodes) …\n")
    from core.rl.evaluate import evaluate
    results = evaluate(industry=industry, n_episodes=100, top_k=top_k)

    # ── Print table ───────────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  Industry : {industry}   Top-K: {top_k}")
    print(f"{'='*65}")
    header = f"{'Policy':<12}  {'Mean Reward':>12}  {'Std':>8}  {'Win Rate':>10}"
    print(header)
    print("-" * len(header))
    for policy_name, stats in results["policies"].items():
        wr = stats.get("win_rate_vs_baseline", "   —")
        wr_str = f"{wr:.2%}" if isinstance(wr, float) else str(wr)
        print(f"{policy_name:<12}  {stats['mean_reward']:>12.4f}  "
              f"{stats['std_reward']:>8.4f}  {wr_str:>10}")

    ppo_beats = results.get("ppo_beats_baseline")
    if ppo_beats is None:
        print("\n[Note] PPO model not found; only baseline and random evaluated.")
    elif ppo_beats:
        print("\n[Result] PPO beats the heuristic baseline (win rate > 50%).")
    else:
        print("\n[Result] PPO does NOT beat the heuristic baseline "
              "(reported honestly — no tuning).")

    print(f"\n{'='*65}")
    print("  Phase C — DONE")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()
