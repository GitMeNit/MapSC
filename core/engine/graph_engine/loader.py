import logging
import networkx as nx
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from adapters.base import RawRecord

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("GraphLoader")

# Valid node and edge types defined in schema.md
VALID_NODE_TYPES = {"Company", "Facility", "Material", "Product", "Country"}
VALID_EDGE_TYPES = {"supplies_to", "depends_on", "located_in", "produces"}

@dataclass
class Node:
    id: str
    type: str
    attributes: Dict[str, Any]

@dataclass
class Edge:
    source_id: str
    target_id: str
    type: str
    attributes: Dict[str, Any]

class GenericGraphLoader:
    """Loads RawRecord streams into an industry-agnostic NetworkX DiGraph."""
    
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(self, node_id: str, node_type: str, **kwargs):
        if node_type not in VALID_NODE_TYPES:
            raise ValueError(f"Invalid node type: {node_type}. Must be one of {VALID_NODE_TYPES}")
        
        if not self.graph.has_node(node_id):
            self.graph.add_node(node_id, node_type=node_type, **kwargs)
        else:
            # Merge attributes if node already exists
            self.graph.nodes[node_id].update(kwargs)

    def add_edge(self, source_id: str, target_id: str, edge_type: str, **kwargs):
        if edge_type not in VALID_EDGE_TYPES:
            raise ValueError(f"Invalid edge type: {edge_type}. Must be one of {VALID_EDGE_TYPES}")
        
        self.graph.add_edge(source_id, target_id, edge_type=edge_type, **kwargs)

    def load_from_records(self, records: List[RawRecord]) -> nx.DiGraph:
        """Parse raw records generically into nodes and edges based on standardized field mappings."""
        for record in records:
            data = record.raw_data
            
            # Pattern 1: Explicit Node/Edge entities returned by transformation layer
            if "nodes" in data and "edges" in data:
                for n in data["nodes"]:
                    self.add_node(n["id"], n["type"], **n.get("attributes", {}))
                for e in data["edges"]:
                    self.add_edge(e["source"], e["target"], e["type"], **e.get("attributes", {}))
            
            # Pattern 2: Trade flow record (Country -> Material / Product)
            elif "reporterCode" in data or "cmdCode" in data:
                reporter = str(data.get("reporterDesc", "India"))
                partner = str(data.get("partnerDesc", "Unknown_Partner"))
                material_code = str(data.get("cmdCode", "Material_HS"))
                trade_value = float(data.get("primaryValue", 0))

                self.add_node(partner, "Country")
                self.add_node(reporter, "Country")
                self.add_node(material_code, "Material")

                self.add_edge(partner, material_code, "supplies_to", weight=trade_value)
                self.add_edge(material_code, reporter, "supplies_to", weight=trade_value)

        logger.info(f"Graph Construction Completed: {self.graph.number_of_nodes()} Nodes, {self.graph.number_of_edges()} Edges.")
        return self.graph