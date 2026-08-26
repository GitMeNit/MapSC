"""Smoke test: verify core dependencies import and run cleanly."""

from __future__ import annotations

import sys


def main() -> None:
    print(f"Python {sys.version.split()[0]}")

    import langchain
    import langgraph
    import networkx as nx
    import stable_baselines3
    import gymnasium as gym
    import fastapi
    import requests

    print(f"langchain       {langchain.__version__}")
    print(f"langgraph       {getattr(langgraph, '__version__', 'installed')}")
    print(f"networkx        {nx.__version__}")
    print(f"stable-baselines3 {stable_baselines3.__version__}")
    print(f"gymnasium       {gym.__version__}")
    print(f"fastapi         {fastapi.__version__}")
    print(f"requests        {requests.__version__}")

    # Minimal functional checks
    g = nx.Graph()
    g.add_edge("a", "b")
    assert len(g) == 2

    app = fastapi.FastAPI()

    @app.get("/")
    def root():
        return {"status": "ok"}

    assert app.title == "FastAPI"

    env = gym.make("CartPole-v1")
    obs, _info = env.reset()
    assert obs.shape == (4,)
    env.close()

    print("Hello, MapSC - all dependencies OK.")


if __name__ == "__main__":
    main()
