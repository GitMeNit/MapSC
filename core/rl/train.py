"""
core/rl/train.py — PPO training for SupplyChainEnv via Stable-Baselines3.

Saves model to models/ppo_<industry>.zip.
"""
from __future__ import annotations

import sys
import logging
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
import paths  # noqa: F401

logger = logging.getLogger(__name__)

_MODELS_DIR = _REPO_ROOT / "models"
_MODELS_DIR.mkdir(parents=True, exist_ok=True)


def train_ppo(
    industry: str,
    total_timesteps: int = 100_000,
    top_k: int = 8,
    seed: int = 42,
    verbose: int = 1,
) -> str:
    """
    Train a PPO agent on SupplyChainEnv for *industry*.

    Returns
    -------
    str  path to the saved .zip model file
    """
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.env_checker import check_env
    except ImportError:
        raise ImportError(
            "stable-baselines3 is required. Install with: pip install stable-baselines3"
        )

    from core.rl.env import make_env

    env = make_env(industry, top_k=top_k)

    # Verify env is gymnasium-compatible
    logger.info("Checking env with gymnasium env_checker …")
    check_env(env, warn=True)

    model = PPO(
        "MlpPolicy",
        env,
        n_steps=256,
        batch_size=64,
        n_epochs=10,
        learning_rate=3e-4,
        gamma=0.99,
        seed=seed,
        verbose=verbose,
    )

    logger.info("Starting PPO training for '%s' (%d timesteps) …", industry, total_timesteps)
    model.learn(total_timesteps=total_timesteps)

    out_path = str(_MODELS_DIR / f"ppo_{industry}.zip")
    model.save(out_path)
    logger.info("Model saved to %s", out_path)
    return out_path
