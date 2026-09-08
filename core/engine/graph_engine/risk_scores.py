import networkx as nx
import numpy as np
import pandas as pd
from typing import Dict, List, Any

class SupplyChainRiskEngine:
    """Calculates graph topology risk metrics without domain assumptions."""

    def __init__(self, graph: nx.DiGraph):
        self.graph = graph

    def calculate_betweenness_centrality(self) -> Dict[str, float]:
        """Measures how often a node sits on the shortest path between all other node pairs."""
        return nx.betweenness_centrality(self.graph, normalized=True)

    def calculate_hhi(self) -> Dict[str, float]:
        """
        Calculates Herfindahl-Hirschman Index for incoming dependency concentration.
        Formula: $HHI = \\sum_{i=1}^{n} s_i^2$, where $s_i$ is the share of supply from vendor $i$.
        """
        hhi_scores = {}
        for node in self.graph.nodes():
            in_edges = self.graph.in_edges(node, data=True)
            if not in_edges:
                hhi_scores[node] = 0.0
                continue
            
            weights = [data.get('weight', 1.0) for _, _, data in in_edges]
            total_weight = sum(weights)
            
            if total_weight == 0:
                hhi_scores[node] = 0.0
                continue
            
            shares = [w / total_weight for w in weights]
            hhi = sum([s ** 2 for s in shares]) # Scale 0.0 to 1.0
            hhi_scores[node] = float(hhi)
            
        return hhi_scores

    def detect_articulation_points(self) -> List[str]:
        """Identifies single nodes whose removal disconnects the graph (treated as an undirected network)."""
        undirected_g = self.graph.to_undirected()
        return list(nx.articulation_points(undirected_g))

    def compute_composite_risk_scores(self) -> pd.DataFrame:
        """Combines metrics into a unified 0-100 vulnerability score and returns a top-10 table."""
        betweenness = self.calculate_betweenness_centrality()
        hhi = self.calculate_hhi()
        articulation_points = set(self.detect_articulation_points())

        results = []
        for node in self.graph.nodes():
            n_type = self.graph.nodes[node].get("node_type", "Unknown")
            b_score = betweenness.get(node, 0.0)
            h_score = hhi.get(node, 0.0)
            is_ap = 1.0 if node in articulation_points else 0.0

            # Composite Score Formula (Weighted normalization)
            composite_risk = (b_score * 0.45 + h_score * 0.35 + is_ap * 0.20) * 100

            results.append({
                "Node_ID": node,
                "Node_Type": n_type,
                "Betweenness_Centrality": round(b_score, 4),
                "Supply_HHI": round(h_score, 4),
                "Is_Articulation_Point": bool(is_ap),
                "Risk_Score": round(composite_risk, 2)
            })

        df = pd.DataFrame(results)
        df = df.sort_values(by="Risk_Score", ascending=False).reset_index(drop=True)
        return df.head(10)