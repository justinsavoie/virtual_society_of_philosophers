import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Neo4j Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    
    # Chroma Configuration
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    
    # Simulation Configuration
    DEFAULT_N_AGENTS = int(os.getenv("DEFAULT_N_AGENTS", "20"))
    BELIEF_VECTOR_DIM = int(os.getenv("BELIEF_VECTOR_DIM", "50"))
    MAX_SIMULATION_STEPS = int(os.getenv("MAX_SIMULATION_STEPS", "360"))  # 30 years * 12 months
    
    # Dashboard Configuration
    DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "127.0.0.1")
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8000"))
    
    @classmethod
    def validate(cls) -> bool:
        missing = []
        
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        
        if not cls.NEO4J_PASSWORD:
            missing.append("NEO4J_PASSWORD")
        
        if missing:
            print(f"Warning: Missing environment variables: {', '.join(missing)}")
            print("The system will run with reduced functionality or mock data.")
            return False
        
        return True