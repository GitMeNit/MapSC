"""
core/rl/evaluate.py — Evaluate PPO vs Baseline vs Random on 100 held-out episodes.

Writes:
  data/processed/results/rl_<industry>.json
  data/processed/results/rl_<industry>_curve.png  (if matplotlib available)
"""
from __future__ import annotations

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
import paths  # noqa: F401

import numpy as np

logger = logging.getLogger(__name__)

_RESULTS_DIR = _REPO_ROOT / "data" / "processed" / "results"
_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
_MODELS_DIR  = _REPO_ROOT / "models"


def _run_episodes(policy, env, n_episodes: int, seed_offset: int = 0) -> List[float]:
    """Run *n_episodes* and return list of total episode rewards."""
    ep_rewards = []
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed_offset + ep)
        total = 0.0
        done = False
        while not done:
            action, _ = policy.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, _ = env.step(action)
            total += reward
            done = terminated or truncated
        ep_rewards.append(total)
    return ep_rewards


def _random_policy_predict(obs, env):
    action = env.action_space.sample()
    return action, None


class _RandomWrapper:
    def __init__(self, env):
        self._env = env
    def predict(self, obs, deterministic=True):
        return self._env.action_space.sample(), None


def evaluate(
    industry: str,
    n_episodes: int = 100,
    top_k: int = 8,
) -> Dict[str, Any]:
    """
    Evaluate three policies on *n_episodes* held-out episodes.

    Returns dict with per-policy stats; also writes JSON + optional PNG.
    """
    from core.rl.env import make_env
    from core.rl.baseline_policy import BaselinePolicy

    env = make_env(industry, top_k=top_k)

    # ── PPO (load if exists) ──────────────────────────────────────────────────
    model_path = _MODELS_DIR / f"ppo_{industry}.zip"
    ppo_policy = None
    if model_path.exists():
        try:
            from stable_baselines3 import PPO
            ppo_policy = PPO.load(str(model_path), env=env)
            logger.info("Loaded PPO model from %s", model_path)
        except Exception as exc:
            logger.warning("Could not load PPO model: %s — using baseline only.", exc)
    else:
        logger.warning("No PPO model found at %s — skipping PPO eval.", model_path)

    baseline_policy = BaselinePolicy(K=env.K)
    random_policy   = _RandomWrapper(env)

    policies = {
        "baseline": baseline_policy,
        "random":   random_policy,
    }
    if ppo_policy is not None:
        policies["ppo"] = ppo_policy

    results: Dict[str, Any] = {
        "industry":   industry,
        "n_episodes": n_episodes,
        "top_k":      top_k,
        "policies":   {},
    }

    all_rewards: Dict[str, List[float]] = {}
    for name, policy in policies.items():
        ep_rewards = _run_episodes(policy, env, n_episodes, seed_offset=1000)
        all_rewards[name] = ep_rewards
        arr = np.array(ep_rewards)
        results["policies"][name] = {
            "mean_reward": round(float(arr.mean()), 4),
            "std_reward":  round(float(arr.std()),  4),
            "min_reward":  round(float(arr.min()),  4),
            "max_reward":  round(float(arr.max()),  4),
        }

    # Win rate: % episodes where PPO > baseline
    if "ppo" in all_rewards:
        ppo_arr = np.array(all_rewards["ppo"])
        base_arr = np.array(all_rewards["baseline"])
        win_rate = float((ppo_arr > base_arr).mean())
        results["policies"]["ppo"]["win_rate_vs_baseline"] = round(win_rate, 4)
        results["ppo_beats_baseline"] = win_rate > 0.5
    else:
        results["ppo_beats_baseline"] = None

    # ── Save JSON ─────────────────────────────────────────────────────────────
    out_path = _RESULTS_DIR / f"rl_{industry}.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    logger.info("RL results saved to %s", out_path)

    # ── Plot ──────────────────────────────────────────────────────────────────
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(9, 5))
        colours = {"ppo": "#4C72B0", "baseline": "#DD8452", "random": "#aaa"}
        for name, rewards in all_rewards.items():
            # Smooth with a window
            arr = np.array(rewards)
            win = min(10, len(arr))
            smooth = np.convolve(arr, np.ones(win)/win, mode='valid')
            ax.plot(smooth, label=name.upper(), color=colours.get(name, "grey"), linewidth=2)
        ax.set_title(f"RL Policy Comparison — {industry}")
        ax.set_xlabel("Episode")
        ax.set_ylabel("Total Reward")
        ax.legend()
        ax.grid(alpha=0.3)
        fig.tight_layout()
        png_path = _RESULTS_DIR / f"rl_{industry}_curve.png"
        fig.savefig(png_path, dpi=120)
        plt.close(fig)
        logger.info("RL curve saved to %s", png_path)
    except ImportError:
        pass

    return results
