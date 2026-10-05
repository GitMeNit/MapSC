"""
api/main.py — FastAPI application entrypoint.
"""
from __future__ import annotations

import sys
from pathlib import Path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
import paths  # noqa: F401

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import graph, risk, optimizer, simulation

app = FastAPI(
    title="MapSC Supply Chain API",
    description="Backend for the supply chain resilience analysis tool.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graph.router, prefix="/api/v1/graph", tags=["Graph"])
app.include_router(risk.router, prefix="/api/v1/risk", tags=["Risk Engine"])
app.include_router(optimizer.router, prefix="/api/v1/optimizer", tags=["Optimizer"])
app.include_router(simulation.router, prefix="/api/v1/simulation", tags=["Simulation"])

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
