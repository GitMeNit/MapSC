"""
pipeline/llm.py — LLM provider switch.

Priority:
  1. ANTHROPIC_API_KEY → Claude (claude-3-haiku-20240307)
  2. GOOGLE_API_KEY    → Gemini (gemini-1.5-flash)
  3. None             → Deterministic rule-based fallback (no API call)
"""
from __future__ import annotations

import os
import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class FallbackLLM:
    """
    Deterministic rule-based 'LLM' that works without any API key.
    Used as fallback so the pipeline always runs.
    """

    def extract_entities(
        self, text: str, config_entities: List[str], config_materials: List[str]
    ) -> Dict[str, Any]:
        """
        Keyword-match entities and materials mentioned in *text*.
        Returns structured JSON-compatible dict.
        """
        text_lower = text.lower()
        matched_entities  = [e for e in config_entities  if e.lower() in text_lower]
        matched_materials = [m for m in config_materials if m.lower() in text_lower]

        # Confidence proxy: fraction of config entities found
        total = len(config_entities) + len(config_materials)
        found = len(matched_entities) + len(matched_materials)
        confidence = found / max(total, 1)

        return {
            "entities":   matched_entities,
            "materials":  matched_materials,
            "relations":  [],           # fallback produces no relation triples
            "confidence": round(confidence, 3),
            "method":     "keyword_fallback",
        }

    def summarise(self, data: Dict[str, Any]) -> str:
        """Generate a simple markdown summary without an LLM."""
        lines = ["# Supply Chain Risk Report (auto-generated)\n"]

        industry = data.get("industry", "Unknown")
        lines.append(f"**Industry:** {industry}\n")

        rt = data.get("risk_table", {})
        if rt:
            lines.append("## Top Risk Nodes\n")
            for row in rt.get("rows", [])[:5]:
                lines.append(
                    f"- **{row.get('Node_ID', '?')}** "
                    f"({row.get('Node_Type', '?')}) — "
                    f"Risk Score: {row.get('Risk_Score', '?')}"
                )
            lines.append("")

        opt = data.get("optimizer_results", {})
        if opt:
            lines.append("## Optimizer Results\n")
            for algo, stats in opt.get("algorithms", {}).items():
                lines.append(
                    f"- **{algo.upper()}**: mean={stats.get('mean_score','?'):.4f}, "
                    f"improvement={stats.get('improvement_vs_baseline_pct','?')}%"
                )
            lines.append("")

        rl = data.get("rl_results", {})
        if rl:
            lines.append("## RL Policy Evaluation\n")
            for pol, stats in rl.get("policies", {}).items():
                lines.append(
                    f"- **{pol.upper()}**: mean reward={stats.get('mean_reward','?'):.4f}"
                )
            lines.append("")

        errors = data.get("errors", [])
        if errors:
            lines.append("## Errors / Warnings\n")
            for e in errors:
                lines.append(f"- {e}")

        return "\n".join(lines)


def get_llm() -> Any:
    """
    Return a unified LLM object with .extract_entities() and .summarise() methods.
    Falls back to FallbackLLM when no API key is present.
    """
    # 1. Try Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if anthropic_key:
        try:
            from langchain_anthropic import ChatAnthropic
            logger.info("Using Anthropic Claude (claude-3-haiku-20240307)")
            return _LangChainWrapper(
                ChatAnthropic(model="claude-3-haiku-20240307", api_key=anthropic_key)
            )
        except ImportError:
            logger.warning("langchain_anthropic not installed — falling back.")

    # 2. Try Google Gemini
    google_key = os.getenv("GOOGLE_API_KEY", "")
    if google_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            logger.info("Using Google Gemini (gemini-1.5-flash)")
            return _LangChainWrapper(
                ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=google_key)
            )
        except ImportError:
            logger.warning("langchain_google_genai not installed — falling back.")

    # 3. Deterministic fallback
    logger.info("No LLM API key found — using deterministic keyword-fallback.")
    return FallbackLLM()


class _LangChainWrapper:
    """Thin adapter around a LangChain chat model to expose our API."""

    def __init__(self, lc_model):
        self._model = lc_model

    def extract_entities(
        self, text: str, config_entities: List[str], config_materials: List[str]
    ) -> Dict[str, Any]:
        prompt = (
            "You are a supply-chain analyst. Extract structured information from the "
            "following news article. Return ONLY valid JSON with keys: "
            "'entities' (list of company/country names found), "
            "'materials' (list of materials/minerals mentioned), "
            "'relations' (list of {source, relation, target} triples), "
            "'confidence' (0-1 float).\n\n"
            f"Known entities: {config_entities}\n"
            f"Known materials: {config_materials}\n\n"
            f"Article:\n{text[:3000]}"
        )
        try:
            response = self._model.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            # Strip markdown fences if present
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            result = json.loads(content)
            result.setdefault("method", "llm")
            return result
        except Exception as exc:
            logger.warning("LLM extraction failed: %s — using fallback.", exc)
            fallback = FallbackLLM()
            return fallback.extract_entities(text, config_entities, config_materials)

    def summarise(self, data: Dict[str, Any]) -> str:
        prompt = (
            "You are a supply-chain risk analyst. Write a concise markdown report "
            "summarising the following analysis results. Include: top risk nodes, "
            "optimizer improvements, and RL policy comparison. Be factual.\n\n"
            f"Data: {json.dumps(data, indent=2)[:4000]}"
        )
        try:
            response = self._model.invoke(prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as exc:
            logger.warning("LLM summarise failed: %s — using fallback.", exc)
            fallback = FallbackLLM()
            return fallback.summarise(data)
