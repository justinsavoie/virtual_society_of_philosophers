from openai import OpenAI
from typing import Dict, Any, Optional, List
import os
import numpy as np


class LLMWrapper:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model
    
    def generate_response(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM API error: {e}")
            return self._generate_fallback_response(prompt)
    
    def _generate_fallback_response(self, prompt: str) -> str:
        fallback_responses = {
            "essay": "This philosophical inquiry examines fundamental questions about the nature of reality, knowledge, and ethics. Through careful analysis and reasoned argument, we explore the implications of various philosophical positions and their relevance to contemporary discourse.",
            "critique": "This critique offers a thoughtful examination of the presented arguments, highlighting both strengths and potential areas for further consideration. The analysis draws upon established philosophical traditions while engaging with contemporary scholarship.",
            "quality": "0.7",
            "novelty": "0.6",
            "persuasiveness": "0.65"
        }
        
        if "essay" in prompt.lower():
            return fallback_responses["essay"]
        elif "critique" in prompt.lower():
            return fallback_responses["critique"]
        elif "quality" in prompt.lower():
            return fallback_responses["quality"]
        elif "novelty" in prompt.lower():
            return fallback_responses["novelty"]
        elif "persuasiveness" in prompt.lower():
            return fallback_responses["persuasiveness"]
        else:
            return "A thoughtful philosophical response addressing the core questions raised."
    
    def evaluate_essay_quality(self, essay_text: str, topic: str, citations: List[str]) -> float:
        prompt = f"""
        Please evaluate the quality of this philosophical essay on {topic}.
        
        Essay: {essay_text}
        
        Number of citations: {len(citations)}
        
        Rate the quality from 0.0 to 1.0 based on:
        - Clarity of argument
        - Depth of analysis
        - Use of citations
        - Originality of thought
        
        Respond with only a decimal number between 0.0 and 1.0.
        """
        
        response = self.generate_response(prompt, max_tokens=10, temperature=0.3)
        try:
            return float(response)
        except:
            return np.random.beta(3, 2)  # Fallback to reasonable distribution
    
    def evaluate_essay_novelty(self, essay_text: str, topic: str, existing_essays: List[str]) -> float:
        if not existing_essays:
            return 0.8
        
        sample_existing = existing_essays[:3]  # Limit for API efficiency
        
        prompt = f"""
        Please evaluate the novelty of this philosophical essay on {topic}.
        
        New essay: {essay_text}
        
        Compared to these existing essays:
        {chr(10).join([f"{i+1}. {essay[:200]}..." for i, essay in enumerate(sample_existing)])}
        
        Rate the novelty from 0.0 to 1.0 based on how original and innovative the ideas are.
        
        Respond with only a decimal number between 0.0 and 1.0.
        """
        
        response = self.generate_response(prompt, max_tokens=10, temperature=0.3)
        try:
            return float(response)
        except:
            return np.random.beta(2, 2)
    
    def evaluate_critique_persuasiveness(self, critique_text: str, target_essay: str) -> float:
        prompt = f"""
        Please evaluate how persuasive this philosophical critique is.
        
        Target essay: {target_essay[:300]}...
        
        Critique: {critique_text}
        
        Rate the persuasiveness from 0.0 to 1.0 based on:
        - Strength of reasoning
        - Relevance to the target
        - Clarity of argument
        - Potential to change minds
        
        Respond with only a decimal number between 0.0 and 1.0.
        """
        
        response = self.generate_response(prompt, max_tokens=10, temperature=0.3)
        try:
            return float(response)
        except:
            return np.random.beta(2, 3)