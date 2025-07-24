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
    
    # Cleanup
    if runner.db_manager:
        runner.db_manager.close()
    
    runner.logger.info("Simulation completed")


if __name__ == "__main__":
    asyncio.run(main())