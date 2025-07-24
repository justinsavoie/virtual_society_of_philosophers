from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np
import uuid


@dataclass
class Essay:
    id: str
    author_id: str
    timestamp: int
    topic: str
    citations: List[str]
    belief_context: np.ndarray
    text: Optional[str] = None
    quality_score: float = 0.0
    novelty_score: float = 0.0
    citation_count: int = 0
    author_influence: float = 1.0
    
    def __post_init__(self):
        if self.text is None:
            self.text = self.generate_placeholder_text()
    
    def generate_placeholder_text(self) -> str:
        persona_styles = {
            "Kantian": "argues that the categorical imperative demands",
            "Humean": "observes that experience suggests",
            "Aristotelian": "maintains that virtue ethics requires",
            "Nietzschean": "boldly proclaims that traditional values must",
            "Cartesian": "through methodical doubt concludes that",
            "Utilitarian": "calculates that the greatest good demands",
            "Existentialist": "authentically chooses to believe that",
            "Stoic": "with equanimity accepts that nature dictates"
        }
        
        style = np.random.choice(list(persona_styles.keys()))
        opening = persona_styles[style]
        
        return f"On the matter of {self.topic}, this philosopher {opening} a reconsideration of fundamental assumptions. Drawing from previous scholarship, this work builds upon {len(self.citations)} cited sources to advance our understanding of this crucial philosophical domain."
    
    def update_scores(self, quality: float, novelty: float):
        self.quality_score = quality
        self.novelty_score = novelty
    
    def add_citation(self):
        self.citation_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'author_id': self.author_id,
            'timestamp': self.timestamp,
            'topic': self.topic,
            'text': self.text,
            'citations': self.citations,
            'quality_score': self.quality_score,
            'novelty_score': self.novelty_score,
            'citation_count': self.citation_count,
            'belief_vector': self.belief_context.tolist() if self.belief_context is not None else []
        }