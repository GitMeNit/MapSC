"""
core/metrics.py — System-wide metrics collector.
"""
from __future__ import annotations

import time
import json
from pathlib import Path
from typing import Dict, Any

_METRICS_FILE = Path(__file__).resolve().parent.parent / "data" / "processed" / "system_metrics.json"

class MetricsCollector:
    def __init__(self):
        self.metrics: Dict[str, Any] = self._load()
        self.metrics.setdefault("runs", 0)
        self.metrics.setdefault("total_execution_time_s", 0.0)

    def _load(self) -> Dict[str, Any]:
        if _METRICS_FILE.exists():
            try:
                with _METRICS_FILE.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save(self):
        _METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _METRICS_FILE.open("w", encoding="utf-8") as f:
            json.dump(self.metrics, f, indent=2)

    def record_run(self, execution_time: float, industry: str, success: bool):
        self.metrics["runs"] += 1
        self.metrics["total_execution_time_s"] += execution_time
        
        ind_stats = self.metrics.setdefault("industries", {}).setdefault(industry, {"runs": 0, "successes": 0})
        ind_stats["runs"] += 1
        if success:
            ind_stats["successes"] += 1
            
        self._save()
