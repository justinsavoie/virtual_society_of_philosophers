from dataclasses import dataclass
from typing import Dict, Any, Optional
import numpy as np


@dataclass
class Critique:
    id: str
    critic_id: str
    target_id: str
    stance: int  # +1 for positive, -1 for negative
    timestamp: int
    belief_context: np.ndarray
    text: Optional[str] = None
    persuasiveness_score: float = 0.0
    
    def __post_init__(self):
        if self.text is None:
            self.text = self.generate_placeholder_text()
    
    def generate_placeholder_text(self) -> str:
        stance_word = "supports" if self.stance > 0 else "challenges"
        intensity = "strongly" if abs(self.stance) > 0.5 else "cautiously"
        
        return f"This critique {intensity} {stance_word} the central thesis of the target essay, offering {'' if self.stance > 0 else 'counter-'}arguments that draw from established philosophical traditions and contemporary scholarship."
    
    def update_persuasiveness(self, score: float):
        self.persuasiveness_score = score
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'critic_id': self.critic_id,
            'target_id': self.target_id,
            'stance': self.stance,
            'timestamp': self.timestamp,
            'text': self.text,
            'persuasiveness_score': self.persuasiveness_score,
            'belief_vector': self.belief_context.tolist() if self.belief_context is not None else []
        }