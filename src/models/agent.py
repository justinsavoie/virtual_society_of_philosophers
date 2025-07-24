from mesa import Agent
import numpy as np
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class PhilosopherAgent(Agent):
    def __init__(self, unique_id: str, model, persona: str, belief_vector_dim: int = 50):
        super().__init__(unique_id, model)
        self.persona = persona
        self.belief_vector = np.random.normal(0, 1, belief_vector_dim)
        self.influence = 1.0
        self.school_id: Optional[str] = None
        self.memory_refs: List[str] = []
        self.essays_written: List[str] = []
        self.critiques_written: List[str] = []
        self.critiques_received: List[str] = []
        self.birth_tick = model.schedule.time if hasattr(model, 'schedule') else 0
        self.last_activity_tick = self.birth_tick
        self.citation_count = 0
        
    def step(self):
        current_tick = self.model.schedule.time
        
        if self.should_write_essay():
            essay = self.write_essay()
            if essay:
                self.model.add_essay(essay)
                self.last_activity_tick = current_tick
        
        if self.should_write_critique():
            critique = self.write_critique()
            if critique:
                self.model.add_critique(critique)
                self.last_activity_tick = current_tick
    
    def should_write_essay(self) -> bool:
        base_probability = 0.3
        influence_modifier = min(self.influence / 10.0, 1.0)
        return np.random.random() < (base_probability * influence_modifier)
    
    def should_write_critique(self) -> bool:
        base_probability = 0.4
        influence_modifier = min(self.influence / 10.0, 1.0)
        return np.random.random() < (base_probability * influence_modifier)
    
    def write_essay(self):
        from .essay import Essay
        
        topic = self.select_topic()
        citations = self.select_citations()
        
        essay_id = str(uuid.uuid4())
        essay = Essay(
            id=essay_id,
            author_id=self.unique_id,
            timestamp=self.model.schedule.time,
            topic=topic,
            citations=citations,
            belief_context=self.belief_vector.copy()
        )
        
        if hasattr(self.model, 'essay_generator') and self.model.essay_generator:
            citation_texts = [self.model.essays[cid].text for cid in citations 
                            if cid in self.model.essays][:3]
            
            generated_text = self.model.essay_generator.generate_essay(
                self.persona, topic, self.belief_vector, citations, citation_texts
            )
            essay.text = generated_text
            
            if hasattr(self.model, 'llm_wrapper') and self.model.llm_wrapper:
                quality = self.model.llm_wrapper.evaluate_essay_quality(
                    generated_text, topic, citations
                )
                
                existing_essays = [e.text for e in self.model.essays.values() 
                                 if e.topic == topic]
                novelty = self.model.llm_wrapper.evaluate_essay_novelty(
                    generated_text, topic, existing_essays
                )
                
                essay.update_scores(quality, novelty)
        
        self.essays_written.append(essay_id)
        return essay
    
    def write_critique(self):
        from .critique import Critique
        
        target_essay = self.select_essay_to_critique()
        if not target_essay:
            return None
        
        stance = np.random.choice([1, -1])
        critique_id = str(uuid.uuid4())
        
        critique = Critique(
            id=critique_id,
            critic_id=self.unique_id,
            target_id=target_essay.id,
            stance=stance,
            timestamp=self.model.schedule.time,
            belief_context=self.belief_vector.copy()
        )
        
        if hasattr(self.model, 'critique_generator') and self.model.critique_generator:
            generated_text = self.model.critique_generator.generate_critique(
                self.persona, target_essay.text, stance, self.belief_vector
            )
            critique.text = generated_text
            
            if hasattr(self.model, 'llm_wrapper') and self.model.llm_wrapper:
                persuasiveness = self.model.llm_wrapper.evaluate_critique_persuasiveness(
                    generated_text, target_essay.text
                )
                critique.update_persuasiveness(persuasiveness)
        
        self.critiques_written.append(critique_id)
        return critique
    
    def select_topic(self) -> str:
        topics = ["ethics", "epistemology", "metaphysics", "aesthetics", 
                 "political_philosophy", "philosophy_of_mind", "logic"]
        weights = np.abs(self.belief_vector[:len(topics)])
        weights = weights / np.sum(weights)
        return np.random.choice(topics, p=weights)
    
    def select_citations(self) -> List[str]:
        available_essays = self.model.get_available_essays(exclude_author=self.unique_id)
        if not available_essays:
            return []
        
        num_citations = np.random.poisson(2)
        num_citations = min(num_citations, len(available_essays))
        
        if num_citations == 0:
            return []
        
        selected = np.random.choice(available_essays, size=num_citations, replace=False)
        return [essay.id for essay in selected]
    
    def select_essay_to_critique(self):
        available_essays = self.model.get_available_essays(exclude_author=self.unique_id)
        if not available_essays:
            return None
        
        influence_weights = [essay.author_influence for essay in available_essays]
        influence_weights = np.array(influence_weights)
        influence_weights = influence_weights / np.sum(influence_weights)
        
        selected_essay = np.random.choice(available_essays, p=influence_weights)
        return selected_essay
    
    def update_influence(self, delta: float):
        self.influence = max(0.1, self.influence + delta)
    
    def update_belief_vector(self, influence_vector: np.ndarray, weight: float):
        self.belief_vector += weight * influence_vector
        self.belief_vector = np.clip(self.belief_vector, -5, 5)
    
    def is_eligible_for_death(self, death_threshold: float = 0.5, inactive_ticks: int = 12) -> bool:
        current_tick = self.model.schedule.time
        return (self.influence < death_threshold and 
                current_tick - self.last_activity_tick > inactive_ticks)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.unique_id,
            'persona': self.persona,
            'belief_vector': self.belief_vector.tolist(),
            'influence': self.influence,
            'school_id': self.school_id,
            'birth_tick': self.birth_tick,
            'essays_count': len(self.essays_written),
            'critiques_written': len(self.critiques_written),
            'critiques_received': len(self.critiques_received),
            'citation_count': self.citation_count
        }