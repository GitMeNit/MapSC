"""
industry.py — Industry configuration helpers.

Usage
-----
    from industry import load_industry, list_industries

    cfg = load_industry("semiconductors")
    # cfg keys: sector_name, hs_codes, seed_entities, key_materials,
    #           chokepoint_definitions, search_keywords
"""
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Dict, Any, List

_CONFIGS_DIR = Path(__file__).resolve().parent / "configs"

# Mapping: short name -> yaml filename (without extension)
_INDUSTRY_MAP: Dict[str, str] = {
    "semiconductors":       "semiconductors",
    "ev-battery-minerals":  "ev-battery-minerals",
    "ev_battery_minerals":  "ev-battery-minerals",  # underscore alias
}


def list_industries() -> List[str]:
    """Return canonical short names for all available industry configs."""
    return sorted(_INDUSTRY_MAP.keys())


def load_industry(name: str) -> Dict[str, Any]:
    """
    Load an industry YAML config by short name.

    Parameters
    ----------
    name : str
        One of the keys returned by :func:`list_industries`, e.g. ``"semiconductors"``.

    Returns
    -------
    dict
        Parsed YAML with keys: sector_name, hs_codes, seed_entities,
        key_materials, chokepoint_definitions, search_keywords.

    Raises
    ------
    KeyError
        If *name* is not a known industry.
    FileNotFoundError
        If the YAML file is missing from configs/.
    """
    canonical = _INDUSTRY_MAP.get(name)
    if canonical is None:
        raise KeyError(
            f"Unknown industry '{name}'. Available: {sorted(set(_INDUSTRY_MAP.values()))}"
        )

    yaml_path = _CONFIGS_DIR / f"{canonical}.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"Config file not found: {yaml_path}")

    with yaml_path.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    # Guarantee all expected keys exist (empty lists if absent)
    for key in ("hs_codes", "seed_entities", "key_materials",
                "chokepoint_definitions", "search_keywords"):
        cfg.setdefault(key, [])

    return cfg
