from typing import List, Dict, Any
import numpy as np
from .llm_wrapper import LLMWrapper


class EssayGenerator:
    def __init__(self, llm_wrapper: LLMWrapper):
        self.llm = llm_wrapper
    
    def generate_essay(self, persona: str, topic: str, belief_vector: np.ndarray, 
                      citations: List[str], citation_texts: List[str]) -> str:
        
        persona_prompts = {
            "Kantian": "You are a philosopher in the tradition of Immanuel Kant. You believe in the categorical imperative, moral duty, and transcendental idealism.",
            "Humean": "You are a philosopher in the tradition of David Hume. You are skeptical about causation, emphasize empirical experience, and question metaphysical claims.",
            "Aristotelian": "You are a philosopher in the tradition of Aristotle. You focus on virtue ethics, teleology, and the golden mean.",
            "Nietzschean": "You are a philosopher in the tradition of Friedrich Nietzsche. You question traditional values, emphasize will to power, and critique moral systems.",
            "Cartesian": "You are a philosopher in the tradition of René Descartes. You employ methodical doubt, emphasize rational thought, and seek clear and distinct ideas.",
            "Utilitarian": "You are a philosopher in the utilitarian tradition. You focus on maximizing happiness and well-being for the greatest number.",
            "Existentialist": "You are an existentialist philosopher. You emphasize individual existence, freedom, choice, and authentic living.",
            "Stoic": "You are a philosopher in the Stoic tradition. You emphasize virtue, wisdom, and acceptance of what cannot be changed."
        }
        
        base_persona = persona.split("_")[0] if "_" in persona else persona
        persona_prompt = persona_prompts.get(base_persona, "You are a thoughtful philosopher seeking truth through reason and inquiry.")
        
        belief_emphasis = self._interpret_belief_vector(belief_vector, topic)
        
        citation_context = ""
        if citations and citation_texts:
            citation_context = "\n\nBuild upon these previous works:\n"
            for i, (cit_id, cit_text) in enumerate(zip(citations[:3], citation_texts[:3])):
                citation_context += f"- {cit_text[:150]}...\n"
        
        prompt = f"""
        {persona_prompt}
        
        Write a philosophical essay on the topic of {topic}. Your essay should be approximately 300-500 words.
        
        Key philosophical leanings to incorporate:
        {belief_emphasis}
        
        {citation_context}
        
        Structure your essay with:
        1. A clear thesis statement
        2. Well-reasoned arguments
        3. Engagement with the philosophical tradition
        4. A thoughtful conclusion
        
        Write in an academic but accessible style, as if for publication in a philosophical journal.
        """
        
        return self.llm.generate_response(prompt, max_tokens=600, temperature=0.8)
    
    def _interpret_belief_vector(self, belief_vector: np.ndarray, topic: str) -> str:
        topics = ["ethics", "epistemology", "metaphysics", "aesthetics", 
                 "political_philosophy", "philosophy_of_mind", "logic"]
        
        interpretations = []
        
        for i, weight in enumerate(belief_vector[:len(topics)]):
            if abs(weight) > 0.5:
                topic_name = topics[i]
                stance = "strongly emphasize" if weight > 0 else "critically question"
                interpretations.append(f"- {stance} {topic_name}")
        
        if len(belief_vector) > len(topics):
            additional_weights = belief_vector[len(topics):]
            
            if np.mean(additional_weights[:5]) > 0.3:
                interpretations.append("- Favor systematic and analytical approaches")
            if np.mean(additional_weights[5:10]) > 0.3:
                interpretations.append("- Emphasize experiential and phenomenological insights")
            if np.mean(additional_weights[10:15]) > 0.3:
                interpretations.append("- Value practical and applied philosophical perspectives")
        
        return "\n".join(interpretations) if interpretations else "- Maintain a balanced philosophical approach"