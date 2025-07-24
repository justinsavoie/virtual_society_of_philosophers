import networkx as nx
import numpy as np
from typing import Dict, List, Any, Tuple
from sklearn.cluster import DBSCAN
from collections import defaultdict
import community as community_louvain


class SchoolDetector:
    def __init__(self, eps: float = 0.5, min_samples: int = 3):
        self.eps = eps
        self.min_samples = min_samples
    
    def detect_schools(self, citation_network: List[Tuple[str, str]], 
                      belief_vectors: Dict[str, np.ndarray]) -> Dict[str, List[str]]:
        
        if len(belief_vectors) < self.min_samples:
            return {}
        
        graph_clusters = self._detect_citation_clusters(citation_network)
        
        belief_clusters = self._detect_belief_clusters(belief_vectors)
        
        merged_clusters = self._merge_clusters(graph_clusters, belief_clusters, belief_vectors)
        
        return merged_clusters
    
    def _detect_citation_clusters(self, citation_network: List[Tuple[str, str]]) -> Dict[str, List[str]]:
        if not citation_network:
            return {}
        
        G = nx.Graph()
        for source, target in citation_network:
            if G.has_edge(source, target):
                G[source][target]['weight'] += 1
            else:
                G.add_edge(source, target, weight=1)
        
        if len(G.nodes()) < 3:
            return {}
        
        try:
            partition = community_louvain.best_partition(G)
            
            clusters = defaultdict(list)
            for node, cluster_id in partition.items():
                clusters[f"graph_{cluster_id}"].append(node)
            
            return {k: v for k, v in clusters.items() if len(v) >= self.min_samples}
        
        except:
            return {}
    
    def _detect_belief_clusters(self, belief_vectors: Dict[str, np.ndarray]) -> Dict[str, List[str]]:
        if len(belief_vectors) < self.min_samples:
            return {}
        
        agent_ids = list(belief_vectors.keys())
        vectors = np.array([belief_vectors[aid] for aid in agent_ids])
        
        try:
            clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples)
            cluster_labels = clustering.fit_predict(vectors)
            
            clusters = defaultdict(list)
            for i, label in enumerate(cluster_labels):
                if label != -1:  # -1 indicates noise/outliers
                    clusters[f"belief_{label}"].append(agent_ids[i])
            
            return dict(clusters)
        
        except:
            return {}
    
    def _merge_clusters(self, graph_clusters: Dict[str, List[str]], 
                       belief_clusters: Dict[str, List[str]], 
                       belief_vectors: Dict[str, np.ndarray]) -> Dict[str, List[str]]:
        
        all_clusters = {**graph_clusters, **belief_clusters}
        
        if not all_clusters:
            return {}
        
        merged = {}
        used_agents = set()
        cluster_counter = 0
        
        for cluster_name, members in all_clusters.items():
            available_members = [m for m in members if m not in used_agents]
            
            if len(available_members) >= self.min_samples:
                merged[f"school_{cluster_counter}"] = available_members
                used_agents.update(available_members)
                cluster_counter += 1
        
        remaining_agents = set(belief_vectors.keys()) - used_agents
        if len(remaining_agents) >= self.min_samples:
            cohesion_threshold = 0.7
            cohesive_groups = self._find_cohesive_groups(
                list(remaining_agents), belief_vectors, cohesion_threshold
            )
            
            for group in cohesive_groups:
                if len(group) >= self.min_samples:
                    merged[f"school_{cluster_counter}"] = group
                    cluster_counter += 1
        
        return merged
    
    def _find_cohesive_groups(self, agents: List[str], belief_vectors: Dict[str, np.ndarray], 
                             threshold: float) -> List[List[str]]:
        
        if len(agents) < self.min_samples:
            return []
        
        groups = []
        remaining = set(agents)
        
        while len(remaining) >= self.min_samples:
            seed = next(iter(remaining))
            group = [seed]
            remaining.remove(seed)
            
            for candidate in list(remaining):
                avg_similarity = np.mean([
                    self._cosine_similarity(belief_vectors[candidate], belief_vectors[member])
                    for member in group
                ])
                
                if avg_similarity > threshold:
                    group.append(candidate)
                    remaining.remove(candidate)
            
            if len(group) >= self.min_samples:
                groups.append(group)
            else:
                remaining.update(group[1:])  # Put back all but the seed
        
        return groups
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return np.dot(vec1, vec2) / (norm1 * norm2)