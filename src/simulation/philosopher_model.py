import mesa
import numpy as np
from typing import List, Dict, Any, Optional
import uuid
from collections import defaultdict

from ..models import PhilosopherAgent, Essay, Critique, School
from ..database import Neo4jManager
from ..llm import LLMWrapper, EssayGenerator, CritiqueGenerator
from .school_detector import SchoolDetector


class PhilosopherModel(mesa.Model):
    def __init__(self, n_agents: int = 20, belief_vector_dim: int = 50, db_manager: Optional[Neo4jManager] = None, 
                 use_llm: bool = True):
        super().__init__()
        
        self.n_agents = n_agents
        self.belief_vector_dim = belief_vector_dim
        self.db_manager = db_manager
        self.school_detector = SchoolDetector()
        
        # Initialize LLM components
        if use_llm:
            self.llm_wrapper = LLMWrapper()
            self.essay_generator = EssayGenerator(self.llm_wrapper)
            self.critique_generator = CritiqueGenerator(self.llm_wrapper)
        else:
            self.llm_wrapper = None
            self.essay_generator = None
            self.critique_generator = None
        
        self.schedule = mesa.time.RandomActivation(self)
        
        self.essays: Dict[str, Essay] = {}
        self.critiques: Dict[str, Critique] = {}
        self.schools: Dict[str, School] = {}
        
        self.topic_agenda = self._generate_topic_agenda()
        
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Total_Essays": lambda m: len(m.essays),
                "Total_Critiques": lambda m: len(m.critiques),
                "Total_Schools": lambda m: len(m.schools),
                "Average_Influence": lambda m: np.mean([a.influence for a in m.schedule.agents]) if m.schedule.agents else 0,
                "Active_Agents": lambda m: len(m.schedule.agents)
            }
        )
        
        self._create_initial_agents()
    
    def _generate_topic_agenda(self) -> Dict[str, float]:
        topics = ["ethics", "epistemology", "metaphysics", "aesthetics", 
                 "political_philosophy", "philosophy_of_mind", "logic"]
        weights = np.random.dirichlet(np.ones(len(topics)))
        return dict(zip(topics, weights))
    
    def _create_initial_agents(self):
        personas = [
            "Kantian", "Humean", "Aristotelian", "Nietzschean", "Cartesian",
            "Utilitarian", "Existentialist", "Stoic", "Empiricist", "Rationalist",
            "Pragmatist", "Phenomenologist", "Analytic", "Continental", "Buddhist",
            "Confucian", "Platonic", "Hegelian", "Spinozan", "Lockean"
        ]
        
        for i in range(self.n_agents):
            persona = personas[i % len(personas)]
            
            agent = PhilosopherAgent(self, persona, self.belief_vector_dim)
            self.schedule.add(agent)
            
            if self.db_manager:
                self.db_manager.create_agent(agent.to_dict())
    
    def step(self):
        self.topic_agenda = self._generate_topic_agenda()
        
        self.schedule.step()
        
        self._update_influence_scores()
        
        if self.schedule.time % 6 == 0:
            self._detect_and_update_schools()
        
        if self.schedule.time % 12 == 0:
            self._handle_birth_death()
        
        self.datacollector.collect(self)
    
    def add_essay(self, essay: Essay):
        self.essays[essay.id] = essay
        
        if self.db_manager:
            self.db_manager.create_essay(essay.to_dict())
            
            for cited_id in essay.citations:
                self.db_manager.create_citation(essay.id, cited_id)
                if cited_id in self.essays:
                    self.essays[cited_id].add_citation()
                    self.db_manager.update_essay_citation_count(
                        cited_id, self.essays[cited_id].citation_count
                    )
    
    def add_critique(self, critique: Critique):
        self.critiques[critique.id] = critique
        
        if self.db_manager:
            self.db_manager.create_critique(critique.to_dict())
        
        self._process_critique_effects(critique)
    
    def get_available_essays(self, exclude_author: Optional[str] = None) -> List[Essay]:
        available = []
        for essay in self.essays.values():
            if exclude_author is None or essay.author_id != exclude_author:
                available.append(essay)
        return available
    
    def _process_critique_effects(self, critique: Critique):
        target_essay = self.essays.get(critique.target_id)
        if not target_essay:
            return
        
        critic_candidates = self.schedule.agents.select(lambda agent: agent.unique_id == int(critique.critic_id))
        target_author_candidates = self.schedule.agents.select(lambda agent: agent.unique_id == int(target_essay.author_id))
        
        critic = critic_candidates[0] if critic_candidates else None
        target_author = target_author_candidates[0] if target_author_candidates else None
        
        if not critic or not target_author:
            return
        
        persuasiveness = np.random.beta(2, 2)
        critique.update_persuasiveness(persuasiveness)
        
        influence_change = persuasiveness * 0.1 * critique.stance
        critic.update_influence(0.05)
        target_author.update_influence(influence_change)
        
        if persuasiveness > 0.6 and critique.stance > 0:
            belief_influence = 0.1 * persuasiveness
            target_author.update_belief_vector(critic.belief_vector, belief_influence)
    
    def _update_influence_scores(self):
        for agent in self.schedule.agents:
            base_decay = -0.01
            
            recent_essays = [e for e in self.essays.values() 
                           if e.author_id == str(agent.unique_id) and 
                           self.schedule.time - e.timestamp <= 6]
            
            citation_bonus = sum(e.citation_count * 0.02 for e in recent_essays)
            
            recent_critiques = [c for c in self.critiques.values() 
                              if c.critic_id == str(agent.unique_id) and 
                              self.schedule.time - c.timestamp <= 6]
            
            critique_bonus = sum(c.persuasiveness_score * 0.01 for c in recent_critiques)
            
            total_change = base_decay + citation_bonus + critique_bonus
            agent.update_influence(total_change)
            
            if self.db_manager:
                self.db_manager.update_agent_influence(str(agent.unique_id), agent.influence)
    
    def _detect_and_update_schools(self):
        if len(self.schedule.agents) < 3:
            return
        
        citation_network = self._build_citation_network()
        school_clusters = self.school_detector.detect_schools(
            citation_network, 
            {str(agent.unique_id): agent.belief_vector for agent in self.schedule.agents}
        )
        
        existing_schools = set(self.schools.keys())
        new_schools = set()
        
        for cluster_id, member_ids in school_clusters.items():
            if len(member_ids) >= 3:
                school_id = f"school_{cluster_id}"
                new_schools.add(school_id)
                
                if school_id not in self.schools:
                    member_beliefs = []
                    for mid in member_ids:
                        agent_candidates = self.schedule.agents.select(lambda agent: agent.unique_id == int(mid))
                        if agent_candidates:
                            member_beliefs.append(agent_candidates[0].belief_vector)
                    
                    school = School(
                        id=school_id,
                        manifesto="",
                        founding_tick=self.schedule.time
                    )
                    school.member_ids = list(member_ids)
                    school.update_doctrine_vector(member_beliefs)
                    school.manifesto = school.generate_manifesto(self.topic_agenda)
                    
                    self.schools[school_id] = school
                    
                    if self.db_manager:
                        self.db_manager.create_school(school.to_dict())
                
                for member_id in member_ids:
                    agent_candidates = self.schedule.agents.select(lambda agent: agent.unique_id == int(member_id))
                    if agent_candidates:
                        agent = agent_candidates[0]
                        if agent.school_id != school_id:
                            agent.school_id = school_id
                            if self.db_manager:
                                self.db_manager.add_agent_to_school(member_id, school_id)
        
        defunct_schools = existing_schools - new_schools
        for school_id in defunct_schools:
            del self.schools[school_id]
    
    def _build_citation_network(self) -> List[tuple]:
        network = []
        for essay in self.essays.values():
            for cited_id in essay.citations:
                cited_essay = self.essays.get(cited_id)
                if cited_essay:
                    network.append((essay.author_id, cited_essay.author_id))
        return network
    
    def _handle_birth_death(self):
        agents_to_remove = []
        
        for agent in self.schedule.agents:
            if agent.is_eligible_for_death():
                agents_to_remove.append(agent)
        
        for agent in agents_to_remove:
            self.schedule.remove(agent)
        
        high_influence_agents = [a for a in self.schedule.agents if a.influence > 2.0]
        
        if high_influence_agents and len(self.schedule.agents) < self.n_agents * 1.5:
            parent = np.random.choice(high_influence_agents)
            
            child_persona = parent.persona + "_descendant"
            
            child = PhilosopherAgent(self, child_persona, self.belief_vector_dim)
            
            mutation_strength = 0.3
            child.belief_vector = parent.belief_vector + np.random.normal(0, mutation_strength, self.belief_vector_dim)
            child.belief_vector = np.clip(child.belief_vector, -5, 5)
            
            child.influence = parent.influence * 0.5
            
            self.schedule.add(child)
            
            if self.db_manager:
                self.db_manager.create_agent(child.to_dict())
    
    def get_model_state(self) -> Dict[str, Any]:
        return {
            'tick': self.schedule.time,
            'agents': [agent.to_dict() for agent in self.schedule.agents],
            'essays': [essay.to_dict() for essay in self.essays.values()],
            'critiques': [critique.to_dict() for critique in self.critiques.values()],
            'schools': [school.to_dict() for school in self.schools.values()],
            'topic_agenda': self.topic_agenda
        }