import numpy as np
from .llm_wrapper import LLMWrapper


class CritiqueGenerator:
    def __init__(self, llm_wrapper: LLMWrapper):
        self.llm = llm_wrapper
    
    def generate_critique(self, critic_persona: str, target_essay_text: str, 
                         stance: int, belief_vector: np.ndarray) -> str:
        
        persona_prompts = {
            "Kantian": "You are a Kantian philosopher who evaluates arguments through the lens of duty, universalizability, and moral law.",
            "Humean": "You are a Humean philosopher who applies empirical skepticism and questions unfounded metaphysical claims.",
            "Aristotelian": "You are an Aristotelian philosopher who emphasizes virtue, practical wisdom, and teleological thinking.",
            "Nietzschean": "You are a Nietzschean philosopher who challenges conventional morality and seeks to unmask hidden motivations.",
            "Cartesian": "You are a Cartesian philosopher who demands clear reasoning and methodical analysis.",
            "Utilitarian": "You are a utilitarian philosopher who evaluates arguments based on their consequences for human welfare.",
            "Existentialist": "You are an existentialist philosopher who emphasizes authenticity, freedom, and individual responsibility.",
            "Stoic": "You are a Stoic philosopher who values wisdom, virtue, and rational acceptance of natural order."
        }
        
        base_persona = critic_persona.split("_")[0] if "_" in critic_persona else critic_persona
        persona_prompt = persona_prompts.get(base_persona, "You are a thoughtful philosophical critic.")
        
        stance_instruction = self._get_stance_instruction(stance)
        philosophical_focus = self._get_philosophical_focus(belief_vector)
        
        prompt = f"""
        {persona_prompt}
        
        You are writing a philosophical critique of the following essay:
        
        "{target_essay_text}"
        
        {stance_instruction}
        
        Focus your critique on:
        {philosophical_focus}
        
        Write a 200-300 word critique that:
        1. Identifies the main argument of the target essay
        2. Provides your philosophical response
        3. Offers specific points of agreement or disagreement
        4. Maintains scholarly tone and rigor
        
        Be constructive and intellectually honest in your critique.
        """
        
        return self.llm.generate_response(prompt, max_tokens=400, temperature=0.7)
    
    def _get_stance_instruction(self, stance: int) -> str:
        if stance > 0:
            return """Your overall stance is SUPPORTIVE. You generally agree with the essay's main arguments but may offer refinements, extensions, or additional supporting evidence. Look for strengths to highlight while providing constructive suggestions."""
        else:
            return """Your overall stance is CRITICAL. You disagree with key aspects of the essay's arguments. Identify logical problems, questionable assumptions, or alternative perspectives that challenge the main thesis. Be respectful but intellectually rigorous in your disagreement."""
    
    def _get_philosophical_focus(self, belief_vector: np.ndarray) -> str:
        focus_areas = []
        
        # Analyze the belief vector to determine critical focus areas
        if len(belief_vector) > 0:
            ethics_weight = belief_vector[0] if len(belief_vector) > 0 else 0
            epistemology_weight = belief_vector[1] if len(belief_vector) > 1 else 0
            metaphysics_weight = belief_vector[2] if len(belief_vector) > 2 else 0
            
            if abs(ethics_weight) > 0.7:
                focus_areas.append("- The moral and ethical implications of the arguments")
            
            if abs(epistemology_weight) > 0.7:
                focus_areas.append("- The epistemological foundations and claims about knowledge")
            
            if abs(metaphysics_weight) > 0.7:
                focus_areas.append("- The metaphysical assumptions and ontological commitments")
        
        # Add general critical thinking points
        focus_areas.extend([
            "- The logical structure and validity of the reasoning",
            "- The use and interpretation of sources and citations",
            "- The clarity and precision of central concepts"
        ])
        
        return "\n".join(focus_areas)