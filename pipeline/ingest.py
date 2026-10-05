"""
pipeline/ingest.py — Phase A: build_graph(industry, use_cache) -> nx.DiGraph

Calls all real adapters driven by the industry YAML config.
On any adapter failure: log and continue (never crash the whole pipeline).
Output is cached to data/processed/<industry>_graph.json (NetworkX node-link format).
"""
from __future__ import annotations

import sys
import json
import logging
import datetime
from pathlib import Path
from typing import List, Dict, Any

# ── ensure repo root + core/engine are on sys.path ───────────────────────────
import paths  # noqa: F401

import networkx as nx
from networkx.readwrite import json_graph

from adapters.base import RawRecord
from graph_engine.loader import GenericGraphLoader
from industry import load_industry

logger = logging.getLogger(__name__)

# ── constants ─────────────────────────────────────────────────────────────────
_PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# OGD resource IDs for data.gov.in (DGFT + IBM datasets)
_DGFT_RESOURCE_ID = "6d6d5b25-d8a0-4b0e-a32c-c3b11e4f3985"
_IBM_RESOURCE_ID  = "4c60e1f4-9d39-4a5c-8c0a-2c4e2b5e8a1d"


# ─────────────────────────────────────────────────────────────────────────────
# Helper: safe adapter call
# ─────────────────────────────────────────────────────────────────────────────

def _safe_fetch(adapter_name: str, adapter, params: Dict[str, Any]) -> List[RawRecord]:
    """Call adapter.fetch(); on any exception return [] and log the error."""
    try:
        records = adapter.fetch(params)
        logger.info("[%s] fetched %d records", adapter_name, len(records))
        return records
    except Exception as exc:
        logger.warning("[%s] failed (%s: %s) — skipping", adapter_name, type(exc).__name__, exc)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Helper: convert adapter records -> loader-compatible pattern-1 RawRecords
# ─────────────────────────────────────────────────────────────────────────────

def _records_from_mines(records: List[RawRecord]) -> List[RawRecord]:
    """
    IBM Mines raw_data keys: mineral_name, location, district, state,
    estimated_reserves, ore_type, reporting_agency, auction_status, reporting_year

    Maps to:
      Material node (mineral_name)
      Facility node (location)  -- mine site
      Country node (India)
      edges: Facility -produces-> Material, Facility -located_in-> Country
    """
    out = []
    for rec in records:
        d = rec.raw_data
        mineral  = d.get("mineral_name", "Unknown_Mineral")
        location = d.get("location", "Unknown_Location")
        state    = d.get("state", "India")

        out.append(RawRecord(
            source_name=rec.source_name,
            raw_data={
                "nodes": [
                    {"id": mineral,  "type": "Material",
                     "attributes": {
                         "ore_type":    d.get("ore_type", ""),
                         "reserves":    d.get("estimated_reserves", ""),
                         "source":      "ibm_mines",
                     }},
                    {"id": location, "type": "Facility",
                     "attributes": {
                         "district":      d.get("district", ""),
                         "state":         state,
                         "auction_status": d.get("auction_status", ""),
                         "source":        "ibm_mines",
                     }},
                    {"id": "India", "type": "Country", "attributes": {}},
                ],
                "edges": [
                    {"source": location, "target": mineral,
                     "type": "produces", "attributes": {}},
                    {"source": location, "target": "India",
                     "type": "located_in", "attributes": {}},
                ],
            },
            timestamp=rec.timestamp,
        ))
    return out


def _records_from_dgft(records: List[RawRecord]) -> List[RawRecord]:
    """
    DGFT raw_data keys: title, entity, iec_code, status, order_date,
    category, notification_number, restriction_type, jurisdiction

    Maps to:
      Company node (entity)
      Country node (India)
      edge: Company -located_in-> Country   (with compliance metadata)
    """
    out = []
    for rec in records:
        d = rec.raw_data
        entity = d.get("entity", "Unknown_Entity")
        out.append(RawRecord(
            source_name=rec.source_name,
            raw_data={
                "nodes": [
                    {"id": entity, "type": "Company",
                     "attributes": {
                         "iec_code":          d.get("iec_code", ""),
                         "compliance_status":  d.get("status", ""),
                         "restriction_type":   d.get("restriction_type", ""),
                         "category":           d.get("category", ""),
                         "source":             "dgft",
                     }},
                    {"id": "India", "type": "Country", "attributes": {}},
                ],
                "edges": [
                    {"source": entity, "target": "India",
                     "type": "located_in",
                     "attributes": {
                         "compliance_flag": d.get("status", ""),
                     }},
                ],
            },
            timestamp=rec.timestamp,
        ))
    return out


def _records_from_patents(records: List[RawRecord]) -> List[RawRecord]:
    """
    Patents BQ raw_data keys: publication_number, assignee_harmonized, filing_date, title

    Maps to: Company node with patent_count attribute (incremented).
    We emit one pattern-1 record per patent with a Company node carrying the pub number.
    The final graph merge will accumulate patent_count via loader.add_node attribute update.
    """
    # Group by first assignee name to accumulate count
    from collections import defaultdict
    counts: Dict[str, int] = defaultdict(int)
    for rec in records:
        d = rec.raw_data
        assignees = d.get("assignee_harmonized", [])
        if assignees and isinstance(assignees[0], dict):
            name = assignees[0].get("name", "Unknown_Assignee")
        elif isinstance(assignees, list) and assignees:
            name = str(assignees[0])
        else:
            name = "Unknown_Assignee"
        counts[name] += 1

    out = []
    for name, cnt in counts.items():
        out.append(RawRecord(
            source_name="google_patents_bq_in",
            raw_data={
                "nodes": [
                    {"id": name, "type": "Company",
                     "attributes": {"patent_count": cnt, "source": "ip_india"}},
                    {"id": "India", "type": "Country", "attributes": {}},
                ],
                "edges": [
                    {"source": name, "target": "India",
                     "type": "located_in", "attributes": {}},
                ],
            },
            timestamp=datetime.datetime.now().isoformat(),
        ))
    return out


def _apply_gdelt_attributes(graph: nx.DiGraph, gdelt_records: List[RawRecord],
                             keywords: List[str]) -> None:
    """
    Annotate existing Country/Company nodes with GDELT geo_risk / event_count.
    raw_data keys: url, title, seendate, domain, language, sourcecountry
    We bump event_count on every Country node whose name appears in a GDELT article title.
    """
    for rec in gdelt_records:
        title   = rec.raw_data.get("title", "").lower()
        src_cty = rec.raw_data.get("sourcecountry", "")

        for node, data in graph.nodes(data=True):
            node_lower = str(node).lower()
            if node_lower in title or (src_cty and src_cty.lower() in node_lower):
                data["event_count"] = data.get("event_count", 0) + 1
                data["geo_risk"]    = min(1.0,
                    data.get("geo_risk", 0.0) + 0.05)  # incremental risk proxy


def _apply_market_attributes(graph: nx.DiGraph,
                              market_records: List[RawRecord]) -> None:
    """
    Add market-data attributes to Company nodes that match NSE symbols.
    raw_data keys vary by nselib version; we store whatever arrives as market_data.
    """
    for rec in market_records:
        d      = rec.raw_data
        symbol = str(d.get("symbol", d.get("Symbol", ""))).upper()
        for node in graph.nodes:
            if symbol and symbol in str(node).upper():
                graph.nodes[node]["market_data"] = d
                break


def _records_from_seed_entities(cfg: Dict[str, Any]) -> List[RawRecord]:
    """
    Always add seed entities as Company nodes so the graph is never empty.
    Each entity: located_in India; produces each key_material.
    """
    sector      = cfg.get("sector_name", "")
    entities    = cfg.get("seed_entities", [])
    materials   = cfg.get("key_materials", [])
    records: List[RawRecord] = []

    for entity in entities:
        nodes = [
            {"id": entity,  "type": "Company",
             "attributes": {"sector": sector, "source": "config"}},
            {"id": "India", "type": "Country", "attributes": {}},
        ]
        edges = [
            {"source": entity, "target": "India",
             "type": "located_in", "attributes": {}},
        ]
        for mat in materials:
            nodes.append({"id": mat, "type": "Material",
                          "attributes": {"sector": sector}})
            edges.append({"source": entity, "target": mat,
                          "type": "produces", "attributes": {}})

        records.append(RawRecord(
            source_name="pipeline_config",
            raw_data={"nodes": nodes, "edges": edges},
            timestamp=datetime.datetime.now().isoformat(),
        ))
    return records


# ─────────────────────────────────────────────────────────────────────────────
# Main public API
# ─────────────────────────────────────────────────────────────────────────────

def build_graph(industry: str, use_cache: bool = True) -> nx.DiGraph:
    """
    Build the supply-chain knowledge graph for *industry*.

    Parameters
    ----------
    industry : str   e.g. "semiconductors" or "ev-battery-minerals"
    use_cache : bool  if True, load from data/processed/<industry>_graph.json when present

    Returns
    -------
    nx.DiGraph  with node attrs: node_type, source, …; edge attrs: edge_type, weight, …
    """
    cache_path = _PROCESSED_DIR / f"{industry}_graph.json"

    if use_cache and cache_path.exists():
        logger.info("Loading cached graph from %s", cache_path)
        with cache_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return json_graph.node_link_graph(data)

    cfg = load_industry(industry)

    # ── lazy adapter imports (wrapped so missing optional packages don't crash) ──
    import settings

    # Comtrade
    try:
        from adapters.comtrade import ComtradeIndiaAdapter
        comtrade = ComtradeIndiaAdapter(api_key=settings.COMTRADE_API_KEY)
    except Exception as e:
        logger.warning("Comtrade adapter unavailable: %s", e); comtrade = None

    # GDELT (no key needed)
    try:
        from adapters.gdelt import GdeltAdapter
        gdelt = GdeltAdapter()
    except Exception as e:
        logger.warning("GDELT adapter unavailable: %s", e); gdelt = None

    # DGFT
    try:
        from adapters.dgft import DgftOgdAdapter
        dgft = DgftOgdAdapter(api_key=settings.TRADE_GOV_API_KEY
                              or getattr(settings, "DATA_GOV_IN_API_KEY", ""))
    except Exception as e:
        logger.warning("DGFT adapter unavailable: %s", e); dgft = None

    # IBM Mines
    try:
        from adapters.ibm_mines import MinistryOfMinesOgdAdapter
        ibm_mines = MinistryOfMinesOgdAdapter(
            api_key=getattr(settings, "DATA_GOV_IN_API_KEY", "") or settings.USGS_API_KEY)
    except Exception as e:
        logger.warning("Mines adapter unavailable: %s", e); ibm_mines = None

    # BSE/NSE (optional — nselib may not be installed)
    bse_nse = None
    try:
        from adapters.bse_nse import BseNseAdapter
        bse_nse = BseNseAdapter()
    except Exception as e:
        logger.warning("BSE/NSE adapter unavailable: %s", e)

    # Google Patents / BigQuery (optional)
    patents = None
    try:
        from adapters.ip_india import GooglePatentsBigQueryAdapter
        gcp_pid = getattr(settings, "GCP_PROJECT_ID",
                          __import__("os").getenv("GCP_PROJECT_ID", ""))
        if gcp_pid:
            patents = GooglePatentsBigQueryAdapter(project_id=gcp_pid)
    except Exception as e:
        logger.warning("Patents adapter unavailable: %s", e)

    # ── Fetch ─────────────────────────────────────────────────────────────────

    all_loader_records: List[RawRecord] = []

    # 1. Seed entities from config (always succeeds)
    seed_records = _records_from_seed_entities(cfg)
    all_loader_records.extend(seed_records)

    # 2. Comtrade trade flows (pattern 2 — loader handles natively)
    if comtrade:
        current_year = datetime.datetime.now().year
        ct_records = _safe_fetch("comtrade", comtrade, {
            "hs_codes": cfg["hs_codes"],
            "years": [current_year - 1, current_year - 2],
        })
        all_loader_records.extend(ct_records)  # pattern 2 handled by loader directly

    # 3. GDELT articles (stored separately; applied as attributes after graph build)
    gdelt_records: List[RawRecord] = []
    if gdelt and cfg.get("search_keywords"):
        gdelt_records = _safe_fetch("gdelt", gdelt, {
            "keywords": cfg["search_keywords"][:5],  # cap to 5 to keep URL short
        })

    # 4. DGFT compliance
    if dgft:
        for entity in cfg["seed_entities"][:3]:  # limit API calls
            recs = _safe_fetch("dgft", dgft, {
                "resource_id": _DGFT_RESOURCE_ID,
                "search_query": entity,
            })
            all_loader_records.extend(_records_from_dgft(recs))

    # 5. IBM Mines mineral data
    if ibm_mines and cfg["key_materials"]:
        mine_recs = _safe_fetch("ibm_mines", ibm_mines, {
            "resource_id": _IBM_RESOURCE_ID,
            "materials": cfg["key_materials"],
        })
        all_loader_records.extend(_records_from_mines(mine_recs))

    # 6. Google Patents
    if patents and cfg["seed_entities"]:
        pat_recs = _safe_fetch("patents", patents, {
            "seed_entities": cfg["seed_entities"],
        })
        all_loader_records.extend(_records_from_patents(pat_recs))

    # 7. BSE/NSE market data
    market_records: List[RawRecord] = []
    if bse_nse and cfg["seed_entities"]:
        # Use only the first tokens of entity names as NSE symbols (best-effort)
        symbols = [e.split()[0].upper() for e in cfg["seed_entities"]]
        market_records = _safe_fetch("bse_nse", bse_nse, {"symbols": symbols})

    # ── Build graph ───────────────────────────────────────────────────────────
    loader = GenericGraphLoader()
    graph  = loader.load_from_records(all_loader_records)

    # ── Post-process attribute overlays ──────────────────────────────────────
    if gdelt_records:
        _apply_gdelt_attributes(graph, gdelt_records, cfg["search_keywords"])
    if market_records:
        _apply_market_attributes(graph, market_records)

    # ── Persist to cache ──────────────────────────────────────────────────────
    data = json_graph.node_link_data(graph)
    with cache_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, default=str)
    logger.info("Graph cached to %s", cache_path)

    return graph
