# KNOWN_ISSUES.md

## Notes — Adapter Contracts (read from source, do not guess)

### adapters/base.py
- `RawRecord(source_name:str, raw_data:dict, timestamp:str)` — plain dataclass, no validation.
- `DataSourceAdapter.fetch(params:dict) -> List[RawRecord]` — abstract.

### adapters/cache.py
- `requests_cache.install_cache('supply_chain_cache', expire_after=86400)` is called at **import time**. Any module importing this installs the cache globally. No option to disable.
- `BaseAPIClient.get(url, params=None, headers=None, timeout=None)` — rate-limited (5/s). Returns `requests.Response`. Raises on non-2xx.

### adapters/comtrade.py — `ComtradeIndiaAdapter(api_key:str)`
- `fetch(params)` params: `hs_codes:List[str]`, `years:List[int]`, optionally `reporter_code`, `flow_code`, `partner_code`.
- `raw_data` shape: standard UN Comtrade object — keys include `reporterDesc`, `partnerDesc`, `cmdCode`, `primaryValue`, `period`, `flowCode`.
- Loader pattern 2 matches directly on `reporterCode`/`cmdCode` keys.

### adapters/gdelt.py — `GdeltAdapter()`
- `fetch(params)` params: `keywords:List[str]`.
- `raw_data` shape: GDELT article dict — keys include `url`, `title`, `seendate`, `domain`, `language`, `sourcecountry`.

### adapters/dgft.py — `DgftOgdAdapter(api_key:str)`
- `fetch(params)` params: `resource_id:str`, `search_query:str` (optional).
- Falls back to `data/dgft_reference.json` on timeout/no records.
- `raw_data` shape: `{title, entity, iec_code, status, order_date, category, notification_number, restriction_type, jurisdiction}`.

### adapters/ibm_mines.py — `MinistryOfMinesOgdAdapter(api_key:str)`
- `fetch(params)` params: `resource_id:str`, `materials:List[str]`.
- Falls back to `data/mines_reference.json` on timeout/no records.
- `raw_data` shape: `{mineral_name, location, district, state, estimated_reserves, ore_type, reporting_agency, auction_status, reporting_year}`.

### adapters/bse_nse.py — `BseNseAdapter()`
- Requires `nselib` (not in `requirements.txt`). Import will fail if not installed.
- `fetch(params)` params: `symbols:List[str]`.
- `raw_data` shape: one row from NSE price/delivery DataFrame — keys include `symbol`, `subject`, `date` (varies by nselib version).

### adapters/ip_india.py — `GooglePatentsBigQueryAdapter(project_id:str)`
- Requires `google-cloud-bigquery`. Import fails if not installed.
- `fetch(params)` params: `seed_entities:List[str]`.
- `raw_data` shape: BigQuery row dict — keys: `publication_number`, `assignee_harmonized` (list of dicts), `filing_date`, `title`.

### core/engine/graph_engine/loader.py — `GenericGraphLoader`
- `VALID_NODE_TYPES = {Company, Facility, Material, Product, Country}` — anything else raises `ValueError`.
- `VALID_EDGE_TYPES = {supplies_to, depends_on, located_in, produces}` — anything else raises `ValueError`.
- Pattern 1: `raw_data = {"nodes":[{id,type,attributes}], "edges":[{source,target,type,attributes}]}`.
- Pattern 2 (Comtrade): keys `reporterCode` or `cmdCode` trigger automatic Country/Material node creation.

### core/engine/graph_engine/main.py
- **DO NOT IMPORT OR RUN.** Uses stale config filenames and `from graph_engine.*` (not `core.engine.graph_engine.*`). Requires `core/engine` on `sys.path`.

### core/engine/graph_engine/risk_scores.py — `SupplyChainRiskEngine(graph)`
- `compute_composite_risk_scores()` returns `pd.DataFrame` with columns: `Node_ID`, `Node_Type`, `Betweenness_Centrality`, `Supply_HHI`, `Is_Articulation_Point`, `Risk_Score`. **Top 10 only.**

### core/engine/graph_engine/simulator.py — `CascadingFailureSimulator(graph)`
- `simulate_removal(target_node:str) -> dict` keys: `removed_node`, `total_graph_nodes`, `downstream_affected_count`, `impact_percentage`, `affected_node_list`.

---

## Known Issues & Workarounds

| File | Symptom | Workaround |
|------|---------|------------|
| `adapters/bse_nse.py` | `import nselib` fails if package absent | Wrap import in try/except in `pipeline/ingest.py`; skip BSE/NSE silently |
| `adapters/ip_india.py` | `from google.cloud import bigquery` fails if package absent | Wrap import in try/except in `pipeline/ingest.py`; skip BigQuery silently |
| `core/engine/graph_engine/main.py` | Stale import paths and config filenames | Never import; use `paths.py` to wire `sys.path`, import submodules directly |
| `adapters/cache.py` | `requests_cache.install_cache` runs at import time; caches all HTTP traffic | Acceptable for dev; do not import cache.py in test environments that need live HTTP |
| `adapters/comtrade.py` | Requires valid `Ocp-Apim-Subscription-Key`; returns empty on expired key | Falls through to empty list; `build_graph` continues without trade-flow edges |
