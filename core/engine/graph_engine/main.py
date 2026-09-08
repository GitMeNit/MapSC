import sys
import yaml
import logging
from typing import Dict, Any
from adapters.base import RawRecord
from graph_engine.loader import GenericGraphLoader
from graph_engine.risk_scores import SupplyChainRiskEngine
from graph_engine.simulator import CascadingFailureSimulator

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def run_pipeline(config_path: str):
    print(f"\n=======================================================")
    print(f"RUNNING AGNOSTIC ENGINE FOR CONFIG: {config_path}")
    print(f"=======================================================")

    # 1. Load Industry Configuration
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    sector_name = config.get("sector_name")
    hs_codes = config.get("hs_codes", [])
    seed_entities = config.get("seed_entities", [])
    key_materials = config.get("key_materials", [])

    print(f"Loaded Sector: {sector_name}")

    # 2. Simulate Ingestion Records from Adapters
    # (In production, call comtrade, bse_nse, ogd, bq adapters directly)
    simulated_records = []
    
    # Synthetic seed entities & materials into graph primitives
    for entity in seed_entities:
        for mat in key_materials:
            simulated_records.append(RawRecord(
                source_name="pipeline_ingest",
                raw_data={
                    "nodes": [
                        {"id": entity, "type": "Company", "attributes": {"sector": sector_name}},
                        {"id": mat, "type": "Material", "attributes": {}},
                        {"id": "India", "type": "Country", "attributes": {}}
                    ],
                    "edges": [
                        {"source": entity, "target": mat, "type": "produces", "attributes": {}},
                        {"source": entity, "target": "India", "type": "located_in", "attributes": {}}
                    ]
                },
                timestamp="2026-08-29T00:00:00"
            ))

    # Add bilateral import trade flows based on HS codes
    for hs in hs_codes:
        simulated_records.append(RawRecord(
            source_name="comtrade_india",
            raw_data={
                "reporterDesc": "India",
                "partnerDesc": "China" if "8507" in hs else "Taiwan",
                "cmdCode": hs,
                "primaryValue": 50000000.0
            },
            timestamp="2026-08-29T00:00:00"
        ))

    # 3. Load Graph (Industry-Agnostic)
    loader = GenericGraphLoader()
    graph = loader.load_from_records(simulated_records)

    # 4. Compute Risk Metrics
    risk_engine = SupplyChainRiskEngine(graph)
    top_10_risky = risk_engine.compute_composite_risk_scores()

    print("\n--- TOP RISKEY NODES TABLE ---")
    print(top_10_risky.to_string(index=False))

    # 5. Run Cascading Failure Simulation
    simulator = CascadingFailureSimulator(graph)
    first_target = seed_entities[0] if seed_entities else list(graph.nodes())[0]
    sim_result = simulator.simulate_removal(first_target)

    print(f"\n--- CASCADING FAILURE SIMULATION ---")
    print(f"Removed Node: {sim_result['removed_node']}")
    print(f"Systemic Impact: {sim_result['impact_percentage']}% of network affected")
    print(f"Disrupted Nodes: {sim_result['affected_node_list']}")

if __name__ == "__main__":
    # Proof of Generalization: Run both configs sequentially on the same engine
    run_pipeline("configs/semiconductors_india.yaml")
    run_pipeline("configs/ev_batteries_india.yaml")