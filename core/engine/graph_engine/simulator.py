import networkx as nx
import logging
from typing import Dict, List, Set, Any

logger = logging.getLogger("FailureSimulator")

class CascadingFailureSimulator:
    """Evaluates systemic disruption resulting from node removal."""

    def __init__(self, graph: nx.DiGraph):
        self.original_graph = graph

    def simulate_removal(self, target_node: str) -> Dict[str, Any]:
        """
        Removes target_node and calculates downstream affected entities 
        that can no longer reach their necessary inputs.
        """
        if target_node not in self.original_graph:
            raise ValueError(f"Node '{target_node}' does not exist in the graph.")

        g_temp = self.original_graph.copy()
        
        # Identify immediate downstream dependent nodes before removal
        downstream_nodes: Set[str] = set()
        for successor in g_temp.successors(target_node):
            # Find all nodes transitively reachable through the target node
            descendants = nx.descendants(g_temp, successor)
            downstream_nodes.add(successor)
            downstream_nodes.update(descendants)

        # Remove target node
        g_temp.remove_node(target_node)

        total_nodes = self.original_graph.number_of_nodes()
        affected_count = len(downstream_nodes)
        impact_percentage = (affected_count / total_nodes * 100) if total_nodes > 0 else 0.0

        result = {
            "removed_node": target_node,
            "total_graph_nodes": total_nodes,
            "downstream_affected_count": affected_count,
            "impact_percentage": round(impact_percentage, 2),
            "affected_node_list": list(downstream_nodes)
        }

        logger.info(
            f"[SIMULATION] Removing '{target_node}' disrupted {affected_count}/{total_nodes} nodes ({impact_percentage:.1f}% of supply chain)."
        )
        return result