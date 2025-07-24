#!/usr/bin/env python3
"""
Virtual Society of Philosophers - Main Runner

This script initializes and runs the simulation of a virtual society of philosophers
where agents write essays, critique each other, and form schools of thought.
"""

import argparse
import asyncio
import uvicorn
from typing import Optional
import signal
import sys

from src.simulation import PhilosopherModel
from src.database import Neo4jManager
from src.dashboard import DashboardApp
from src.utils import Config, setup_logger


class SimulationRunner:
    def __init__(self):
        self.logger = setup_logger()
        self.model: Optional[PhilosopherModel] = None
        self.db_manager: Optional[Neo4jManager] = None
        self.dashboard: Optional[DashboardApp] = None
        self.running = False
    
    def setup_database(self) -> Optional[Neo4jManager]:
        """Initialize Neo4j database connection if configured."""
        if not Config.NEO4J_PASSWORD:
            self.logger.warning("Neo4j not configured, running without database persistence")
            return None
        
        try:
            db_manager = Neo4jManager(
                Config.NEO4J_URI,
                Config.NEO4J_USER,
                Config.NEO4J_PASSWORD
            )
            self.logger.info("Connected to Neo4j database")
            return db_manager
        except Exception as e:
            self.logger.error(f"Failed to connect to Neo4j: {e}")
            self.logger.info("Continuing without database persistence")
            return None
    
    def setup_model(self, n_agents: int, use_llm: bool) -> PhilosopherModel:
        """Initialize the philosopher simulation model."""
        self.logger.info(f"Initializing simulation with {n_agents} agents")
        
        model = PhilosopherModel(
            n_agents=n_agents,
            belief_vector_dim=Config.BELIEF_VECTOR_DIM,
            db_manager=self.db_manager,
            use_llm=use_llm and bool(Config.OPENAI_API_KEY)
        )
        
        if not use_llm or not Config.OPENAI_API_KEY:
            self.logger.warning("Running without LLM integration - using placeholder text")
        
        return model
    
    async def run_simulation(self, steps: int, dashboard: bool = False):
        """Run the simulation for a specified number of steps."""
        self.running = True
        
        try:
            for step in range(steps):
                if not self.running:
                    break
                
                self.model.step()
                
                if step % 12 == 0:  # Log every "year"
                    state = self.model.get_model_state()
                    year = step // 12
                    self.logger.info(
                        f"Year {year}: {len(state['agents'])} agents, "
                        f"{len(state['essays'])} essays, "
                        f"{len(state['schools'])} schools"
                    )
                
                if dashboard and self.dashboard and step % 6 == 0:
                    # Update dashboard every 6 months
                    await self.dashboard.broadcast_update({
                        'type': 'model_update',
                        'data': self.model.get_model_state()
                    })
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.1)
        
        except KeyboardInterrupt:
            self.logger.info("Simulation interrupted by user")
        except Exception as e:
            self.logger.error(f"Simulation error: {e}")
        finally:
            self.running = False
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers."""
        def signal_handler(signum, frame):
            self.logger.info("Received shutdown signal, stopping simulation...")
            self.running = False
            if self.db_manager:
                self.db_manager.close()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run_dashboard_only(self):
        """Run only the dashboard server."""
        self.dashboard = DashboardApp(self.model)
        
        config = uvicorn.Config(
            self.dashboard.app,
            host=Config.DASHBOARD_HOST,
            port=Config.DASHBOARD_PORT,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    async def run_with_dashboard(self, steps: int):
        """Run simulation with dashboard in parallel."""
        self.dashboard = DashboardApp(self.model)
        
        # Start dashboard server
        config = uvicorn.Config(
            self.dashboard.app,
            host=Config.DASHBOARD_HOST,
            port=Config.DASHBOARD_PORT,
            log_level="warning"
        )
        server = uvicorn.Server(config)
        
        # Run both simulation and dashboard
        await asyncio.gather(
            server.serve(),
            self.run_simulation(steps, dashboard=True)
        )


async def main():
    parser = argparse.ArgumentParser(description="Virtual Society of Philosophers")
    parser.add_argument("--agents", type=int, default=Config.DEFAULT_N_AGENTS,
                       help="Number of philosopher agents")
    parser.add_argument("--steps", type=int, default=Config.MAX_SIMULATION_STEPS,
                       help="Number of simulation steps to run")
    parser.add_argument("--no-llm", action="store_true",
                       help="Run without LLM integration (faster, less realistic)")
    parser.add_argument("--dashboard", action="store_true",
                       help="Run with web dashboard")
    parser.add_argument("--dashboard-only", action="store_true",
                       help="Run only the dashboard server")
    
    args = parser.parse_args()
    
    # Validate configuration
    Config.validate()
    
    runner = SimulationRunner()
    runner.setup_signal_handlers()
    
    # Setup components
    runner.db_manager = runner.setup_database()
    
    if not args.dashboard_only:
        runner.model = runner.setup_model(args.agents, not args.no_llm)
    
    # Run based on arguments
    if args.dashboard_only:
        runner.logger.info(f"Starting dashboard server at http://{Config.DASHBOARD_HOST}:{Config.DASHBOARD_PORT}")
        await runner.run_dashboard_only()
    elif args.dashboard:
        runner.logger.info(f"Starting simulation with dashboard at http://{Config.DASHBOARD_HOST}:{Config.DASHBOARD_PORT}")
        await runner.run_with_dashboard(args.steps)
    else:
        runner.logger.info("Starting simulation (console mode)")
        await runner.run_simulation(args.steps)
    
    # Save comprehensive simulation data if any content was created
    if runner.model and (runner.model.essays or runner.model.critiques or runner.model.schedule.agents):
        import os
        import json
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"output_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/essays", exist_ok=True)
        os.makedirs(f"{output_dir}/critiques", exist_ok=True)
        
        runner.logger.info(f"Saving comprehensive simulation data to {output_dir}/")
        
        # 1. Save agent information
        with open(f"{output_dir}/agents.txt", "w") as f:
            f.write("PHILOSOPHER AGENTS\n")
            f.write("==================\n\n")
            for agent in runner.model.schedule.agents:
                f.write(f"Agent ID: {agent.unique_id}\n")
                f.write(f"Persona: {agent.persona}\n")
                f.write(f"Influence Score: {agent.influence:.3f}\n")
                f.write(f"School: {agent.school_id or 'None'}\n")
                f.write(f"Birth Tick: {agent.birth_tick}\n")
                f.write(f"Last Activity: {agent.last_activity_tick}\n")
                f.write(f"Essays Written: {len(agent.essays_written)}\n")
                f.write(f"Critiques Written: {len(agent.critiques_written)}\n")
                f.write(f"Critiques Received: {len(agent.critiques_received)}\n")
                f.write(f"Citation Count: {agent.citation_count}\n")
                f.write(f"Belief Vector (first 10): {agent.belief_vector[:10].round(3).tolist()}\n")
                f.write("-" * 50 + "\n\n")
        
        # 2. Save essays with full context
        for i, (essay_id, essay) in enumerate(runner.model.essays.items(), 1):
            # Find author persona
            author_persona = "Unknown"
            for agent in runner.model.schedule.agents:
                if str(agent.unique_id) == essay.author_id:
                    author_persona = agent.persona
                    break
            
            with open(f"{output_dir}/essays/essay_{i:02d}.txt", "w") as f:
                f.write(f"ESSAY #{i}\n")
                f.write("=" * 50 + "\n")
                f.write(f"Essay ID: {essay.id}\n")
                f.write(f"Author ID: {essay.author_id}\n")
                f.write(f"Author Persona: {author_persona}\n")
                f.write(f"Timestamp: {essay.timestamp}\n")
                f.write(f"Topic: {essay.topic}\n")
                f.write(f"Quality Score: {essay.quality_score:.3f}\n")
                f.write(f"Novelty Score: {essay.novelty_score:.3f}\n")
                f.write(f"Citation Count: {essay.citation_count}\n")
                f.write(f"Author Influence: {essay.author_influence:.3f}\n")
                f.write(f"Citations: {essay.citations}\n")
                f.write(f"Belief Context (first 10): {essay.belief_context[:10].round(3).tolist()}\n")
                f.write("=" * 50 + "\n\n")
                f.write(essay.text or "No text generated")
        
        # 3. Save critiques with full context
        for i, (critique_id, critique) in enumerate(runner.model.critiques.items(), 1):
            # Find critic and target personas  
            critic_persona = "Unknown"
            target_essay = runner.model.essays.get(critique.target_id)
            target_persona = "Unknown"
            target_topic = "Unknown"
            
            for agent in runner.model.schedule.agents:
                if str(agent.unique_id) == critique.critic_id:
                    critic_persona = agent.persona
                if target_essay and str(agent.unique_id) == target_essay.author_id:
                    target_persona = agent.persona
                    
            if target_essay:
                target_topic = target_essay.topic
            
            with open(f"{output_dir}/critiques/critique_{i:02d}.txt", "w") as f:
                f.write(f"CRITIQUE #{i}\n")
                f.write("=" * 50 + "\n")
                f.write(f"Critique ID: {critique.id}\n")
                f.write(f"Critic ID: {critique.critic_id}\n")
                f.write(f"Critic Persona: {critic_persona}\n")
                f.write(f"Target Essay ID: {critique.target_id}\n")
                f.write(f"Target Author Persona: {target_persona}\n")
                f.write(f"Target Topic: {target_topic}\n")
                f.write(f"Stance: {'Positive' if critique.stance > 0 else 'Negative'} ({critique.stance})\n")
                f.write(f"Timestamp: {critique.timestamp}\n")
                f.write(f"Persuasiveness Score: {critique.persuasiveness_score:.3f}\n")
                f.write(f"Belief Context (first 10): {critique.belief_context[:10].round(3).tolist()}\n")
                f.write("=" * 50 + "\n\n")
                f.write(critique.text or "No text generated")
        
        # 4. Save relationships and citations
        with open(f"{output_dir}/relationships.txt", "w") as f:
            f.write("CITATION NETWORK & RELATIONSHIPS\n")
            f.write("=================================\n\n")
            
            f.write("CITATIONS:\n")
            f.write("-" * 20 + "\n")
            for essay_id, essay in runner.model.essays.items():
                if essay.citations:
                    author_persona = "Unknown"
                    for agent in runner.model.schedule.agents:
                        if str(agent.unique_id) == essay.author_id:
                            author_persona = agent.persona
                            break
                    f.write(f"{author_persona} (Essay {essay_id[:8]}) cites: {essay.citations}\n")
            
            f.write("\nCRITIQUE RELATIONSHIPS:\n")
            f.write("-" * 20 + "\n")
            for critique_id, critique in runner.model.critiques.items():
                critic_persona = target_persona = "Unknown"
                for agent in runner.model.schedule.agents:
                    if str(agent.unique_id) == critique.critic_id:
                        critic_persona = agent.persona
                target_essay = runner.model.essays.get(critique.target_id)
                if target_essay:
                    for agent in runner.model.schedule.agents:
                        if str(agent.unique_id) == target_essay.author_id:
                            target_persona = agent.persona
                            break
                stance_word = "supports" if critique.stance > 0 else "criticizes"
                f.write(f"{critic_persona} {stance_word} {target_persona}'s essay\n")
        
        # 5. Save analysis and statistics
        with open(f"{output_dir}/analysis.txt", "w") as f:
            f.write("SIMULATION ANALYSIS\n")
            f.write("===================\n\n")
            f.write(f"Total Agents: {len(runner.model.schedule.agents)}\n")
            f.write(f"Total Essays: {len(runner.model.essays)}\n")
            f.write(f"Total Critiques: {len(runner.model.critiques)}\n")
            f.write(f"Total Schools: {len(runner.model.schools)}\n\n")
            
            if runner.model.essays:
                qualities = [e.quality_score for e in runner.model.essays.values()]
                novelties = [e.novelty_score for e in runner.model.essays.values()]
                f.write(f"Average Essay Quality: {sum(qualities)/len(qualities):.3f}\n")
                f.write(f"Average Essay Novelty: {sum(novelties)/len(novelties):.3f}\n")
            
            if runner.model.critiques:
                persuasiveness = [c.persuasiveness_score for c in runner.model.critiques.values()]
                f.write(f"Average Critique Persuasiveness: {sum(persuasiveness)/len(persuasiveness):.3f}\n")
            
            f.write("\nPHILOSOPHER PRODUCTIVITY:\n")
            f.write("-" * 25 + "\n")
            for agent in sorted(runner.model.schedule.agents, key=lambda a: len(a.essays_written), reverse=True):
                f.write(f"{agent.persona:15} - {len(agent.essays_written)} essays, {len(agent.critiques_written)} critiques, influence {agent.influence:.3f}\n")
            
            f.write("\nTOPIC DISTRIBUTION:\n")
            f.write("-" * 18 + "\n")
            topics = {}
            for essay in runner.model.essays.values():
                topics[essay.topic] = topics.get(essay.topic, 0) + 1
            for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True):
                f.write(f"{topic:20} - {count} essays\n")
        
        runner.logger.info(f"Saved complete analysis with {len(runner.model.essays)} essays and {len(runner.model.critiques)} critiques")
    
    # Cleanup
    if runner.db_manager:
        runner.db_manager.close()
    
    runner.logger.info("Simulation completed")


if __name__ == "__main__":
    asyncio.run(main())