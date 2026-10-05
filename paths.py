"""
paths.py — Add repo root and core/engine to sys.path so that:
  - top-level packages (adapters, configs, pipeline, api, …) are importable
  - `from graph_engine.loader import …` works (matching the import style used in core/engine/graph_engine/)
Import this module FIRST in any entry-point script or conftest.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent          # <repo>/
GRAPH_ENGINE_PARENT = REPO_ROOT / "core" / "engine"  # gives `import graph_engine.*`

for p in (str(REPO_ROOT), str(GRAPH_ENGINE_PARENT)):
    if p not in sys.path:
        sys.path.insert(0, p)
