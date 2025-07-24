from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np


@dataclass
class School:
    id: str
    manifesto: str
    member_ids: List[str] = field(default_factory=list)
    doctrine_vector: np.ndarray = field(default_factory=lambda: np.zeros(50))
    fitness: float = 0.0
    founding_tick: int = 0
    
    def add_member(self, agent_id: str):
        if agent_id not in self.member_ids:
            self.member_ids.append(agent_id)
    
    def remove_member(self, agent_id: str):
        if agent_id in self.member_ids:
            self.member_ids.remove(agent_id)
    
    def update_doctrine_vector(self, member_belief_vectors: List[np.ndarray]):
        if member_belief_vectors:
            self.doctrine_vector = np.mean(member_belief_vectors, axis=0)
    
    def calculate_fitness(self, essays_by_members: List, citations_received: int, influence_sum: float):
        essay_quality = np.mean([essay.quality_score for essay in essays_by_members]) if essays_by_members else 0
        citation_factor = min(citations_received / 10.0, 2.0)
        influence_factor = min(influence_sum / len(self.member_ids) if self.member_ids else 0, 5.0)
        
        self.fitness = (essay_quality * 0.4 + citation_factor * 0.3 + influence_factor * 0.3)
    
    def generate_manifesto(self, topic_distribution: Dict[str, float]) -> str:
        dominant_topics = sorted(topic_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        topic_names = [topic for topic, _ in dominant_topics]
        
        manifestos = {
            "ethics": "We hold that moral truth emerges through rigorous examination of duty and consequence",
            "epistemology": "Knowledge must be grounded in systematic inquiry and critical reflection",
            "metaphysics": "Reality reveals itself through careful analysis of being and existence",
            "aesthetics": "Beauty and artistic value demand philosophical understanding and appreciation",
            "political_philosophy": "Just governance requires philosophical foundations and ethical principles",
            "philosophy_of_mind": "Consciousness and mental phenomena merit dedicated philosophical investigation",
            "logic": "Rational argument and valid inference form the bedrock of philosophical discourse"
        }
        
        primary_focus = topic_names[0] if topic_names else "ethics"
        return manifestos.get(primary_focus, "We seek truth through philosophical inquiry and debate")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'manifesto': self.manifesto,
            'member_ids': self.member_ids,
            'doctrine_vector': self.doctrine_vector.tolist(),
            'fitness': self.fitness,
            'founding_tick': self.founding_tick,
            'member_count': len(self.member_ids)
        }