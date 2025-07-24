# Virtual Society of Philosophers

A sophisticated agent-based model simulating a virtual intellectual economy where AI philosopher agents write essays, critique each other's work, form schools of thought, and evolve their beliefs over time.

## Overview

This project implements a **Virtual Society of Philosophers** where autonomous agents:
- **Write philosophical essays** on various topics using LLM-generated content
- **Critique each other's work** with stance-based evaluation
- **Form schools of thought** through citation network analysis and belief clustering
- **Evolve their beliefs** through intellectual discourse and influence dynamics
- **Experience birth/death cycles** based on intellectual relevance and activity

The simulation tracks the emergence and evolution of philosophical ideas across simulated decades, providing insights into how intellectual communities form, compete, and adapt.

## Key Features

### 🧠 **Intelligent Agents**
- **Persona-driven behavior**: Each agent embodies a philosophical tradition (Kantian, Humean, Nietzschean, etc.)
- **Belief vectors**: High-dimensional representations of philosophical positions
- **Influence dynamics**: Agents gain/lose influence based on citation counts and critique quality
- **Memory and learning**: Agents adapt their beliefs through intellectual interaction

### 📝 **Content Generation**
- **LLM-powered essays**: GPT-generated philosophical essays tailored to agent personas
- **Intelligent critiques**: Context-aware critique generation with stance evaluation
- **Quality assessment**: Automated scoring of essay quality, novelty, and critique persuasiveness
- **Citation networks**: Agents build upon previous work, creating intellectual genealogies

### 🏫 **School Formation**
- **Community detection**: Louvain algorithm identifies citation-based clusters
- **Belief clustering**: DBSCAN groups agents by philosophical similarity  
- **Dynamic manifestos**: Schools generate doctrine statements based on member beliefs
- **Fitness tracking**: Schools compete for intellectual relevance and membership

### 📊 **Real-time Visualization**
- **Interactive dashboard**: Live network graphs and statistical tracking
- **Citation networks**: Visual representation of intellectual influence flows
- **Influence timelines**: Track agent prominence over simulation time
- **School evolution**: Monitor the birth, growth, and decline of philosophical movements

### 🗄️ **Data Persistence**
- **Neo4j graph database**: Stores agents, essays, critiques, and relationships
- **Citation analysis**: Fast graph queries for network analysis
- **Historical tracking**: Complete simulation state preservation and analysis

## Architecture

### Core Components

#### **Models** (`src/models/`)
- `PhilosopherAgent`: Mesa agent implementing philosophical reasoning and content creation
- `Essay`: Data structure for philosophical essays with quality/novelty scoring
- `Critique`: Stance-based critique system with persuasiveness evaluation
- `School`: Dynamic philosophical schools with member tracking and doctrine evolution

#### **Simulation Engine** (`src/simulation/`)
- `PhilosopherModel`: Mesa model orchestrating the complete simulation loop
- `SchoolDetector`: Community detection combining citation analysis and belief clustering

#### **LLM Integration** (`src/llm/`)
- `LLMWrapper`: OpenAI API integration with fallback mechanisms
- `EssayGenerator`: Persona-driven essay generation with citation integration
- `CritiqueGenerator`: Context-aware critique generation with stance modeling

#### **Database Layer** (`src/database/`)
- `Neo4jManager`: Graph database operations for agents, essays, and citations
- Schema management and complex graph queries

#### **Dashboard** (`src/dashboard/`)
- `DashboardApp`: FastAPI web server with WebSocket real-time updates
- `NetworkVisualizer`: Plotly-based interactive visualizations

## Installation

### Prerequisites
- Python 3.8+
- Neo4j database (optional but recommended)
- OpenAI API key (optional, fallback text generation available)

### Setup

1. **Clone the repository**:
```bash
git clone <repository-url>
cd virtual_society_of_philosophers
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment** (copy and edit):
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
OPENAI_API_KEY=your_openai_api_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

4. **Start Neo4j** (if using database persistence):
```bash
# Using Docker
docker run --publish=7474:7474 --publish=7687:7687 --env=NEO4J_AUTH=neo4j/yourpassword neo4j:latest
```

## Usage

### Basic Simulation
Run a console-based simulation with 20 agents for 360 steps (30 simulated years):
```bash
python main.py
```

### Custom Parameters
```bash
python main.py --agents 50 --steps 720 --dashboard
```

### Dashboard Mode
Run with real-time web visualization:
```bash
python main.py --dashboard
```
Visit `http://localhost:8000` for the interactive dashboard.

### Without LLM (Faster Testing)
```bash
python main.py --no-llm --agents 10 --steps 120
```

### Dashboard Only
Run just the visualization server:
```bash
python main.py --dashboard-only
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--agents N` | Number of philosopher agents | 20 |
| `--steps N` | Simulation steps to run | 360 |
| `--dashboard` | Enable web dashboard | False |
| `--dashboard-only` | Run only dashboard server | False |
| `--no-llm` | Disable LLM integration | False |

## Simulation Mechanics

### Time Structure
- **1 tick = 1 month** of simulated time
- **12 ticks = 1 year** with annual influence updates
- **360 ticks = 30 years** default simulation duration

### Agent Lifecycle
1. **Essay Writing Phase**: Agents decide whether to write based on influence and topic affinity
2. **Critique Phase**: Agents select essays to review, generating stance-based critiques
3. **Influence Updates**: Citations and critique quality modify agent influence scores
4. **School Detection**: Every 6 months, community detection identifies philosophical clusters
5. **Birth/Death Events**: Annually, low-influence agents may die, high-influence agents may spawn intellectual descendants

### School Formation Algorithm
1. **Citation Network Analysis**: Louvain community detection on agent citation patterns
2. **Belief Space Clustering**: DBSCAN clustering on agent belief vectors
3. **Cluster Merging**: Combine graph and belief clusters for robust school identification
4. **Manifesto Generation**: Schools develop doctrine statements based on member topic preferences

### Influence Dynamics
- **Base Decay**: -0.01 per tick (encourages ongoing activity)
- **Citation Bonus**: +0.02 per citation received (within 6 months)
- **Critique Quality**: +0.01 per persuasive critique written
- **Critique Impact**: Persuasive critiques can shift target agent's beliefs

## Data Output

### Neo4j Graph Structure
- **Nodes**: Agents, Essays, Critiques, Schools
- **Relationships**: WROTE, CITES, CRITIQUES, BELONGS_TO
- **Properties**: Belief vectors, influence scores, timestamps, quality metrics

### Analysis Queries
```cypher
// Find most influential agents
MATCH (a:Agent)
RETURN a.persona, a.influence
ORDER BY a.influence DESC LIMIT 10

// Analyze citation patterns
MATCH (e1:Essay)-[:CITES]->(e2:Essay)
RETURN e1.topic, e2.topic, count(*) as citations
ORDER BY citations DESC

// School member evolution
MATCH (a:Agent)-[:BELONGS_TO]->(s:School)
RETURN s.id, collect(a.persona) as members, s.manifesto
```

## Performance Considerations

### Scaling Guidelines

| Agents | Compute Strategy | Expected Performance |
|--------|------------------|----------------------|
| 10-20 | Local CPU + 7B model | Real-time simulation |
| 100-300 | GPU acceleration + batching | Minutes per simulated year |
| 1000+ | Distributed processing + model sharding | Research cluster recommended |

### Optimization Tips
- Use `--no-llm` for rapid prototyping and algorithm testing
- Reduce belief vector dimensionality for faster clustering
- Implement essay summarization for large-scale simulations
- Archive old essays to manage context length

## Research Applications

This simulation enables investigation of:

### **Intellectual Evolution**
- How do philosophical ideas emerge, spread, and die out?
- What factors determine the survival of intellectual traditions?
- How do citation patterns reflect genuine intellectual influence?

### **Community Formation**  
- What drives philosophers to form schools of thought?
- How do competing paradigms coexist or conflict?
- What role does individual charisma vs. idea quality play?

### **Knowledge Dynamics**
- How does the structure of citation networks affect idea propagation?
- What are the optimal strategies for intellectual influence?
- How do external pressures shape philosophical discourse?

### **Agent-Based Modeling**
- Validation of community detection algorithms on evolving networks
- Multi-agent content generation and evaluation
- Emergent behavior in knowledge-producing communities

## Extending the System

### Adding New Agent Types
```python
class FeministPhilosopher(PhilosopherAgent):
    def select_topic(self):
        # Override to emphasize gender and ethics topics
        topics = ["ethics", "political_philosophy", "feminist_theory"]
        # ... custom logic
```

### Custom Evaluation Metrics
```python
def evaluate_intersectionality(essay_text: str) -> float:
    # Custom scoring for intersectional analysis
    pass

# Register with the model
model.llm_wrapper.custom_evaluators['intersectionality'] = evaluate_intersectionality
```

### Alternative School Detection
```python
class TopicBasedSchoolDetector(SchoolDetector):
    def detect_schools(self, citation_network, belief_vectors):
        # Group by dominant topics instead of citation patterns
        pass
```

## Contributing

We welcome contributions in several areas:

### **Core Algorithms**
- Improved school detection methods
- Alternative influence calculation models
- More sophisticated belief evolution mechanics

### **Content Generation**
- Enhanced persona modeling
- Domain-specific philosophical reasoning
- Multi-language support

### **Analysis Tools**
- Additional visualization types
- Statistical analysis modules
- Export formats for external tools

### **Performance**
- Distributed simulation support
- Memory optimization for large-scale runs
- GPU acceleration for LLM inference

## Troubleshooting

### Common Issues

**Neo4j Connection Failed**
```bash
# Check if Neo4j is running
docker ps

# Verify credentials in .env file
cat .env | grep NEO4J
```

**OpenAI API Errors**
```bash
# Verify API key
echo $OPENAI_API_KEY

# Check rate limits and billing status
```

**Memory Issues with Large Simulations**
- Reduce agent count or belief vector dimensions
- Enable essay archiving after N ticks
- Use `--no-llm` mode for algorithm testing

**Slow School Detection**
- Reduce clustering frequency (modify code to run every 12 ticks instead of 6)
- Tune DBSCAN parameters for faster convergence
- Use approximate clustering algorithms for >500 agents

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation

If you use this simulation in research, please cite:

```bibtex
@software{virtual_philosophers_2024,
  title={Virtual Society of Philosophers: An Agent-Based Model of Intellectual Discourse},
  author={[Your Name]},
  year={2024},
  url={https://github.com/your-repo/virtual-society-philosophers}
}
```

## Acknowledgments

- **Mesa**: Agent-based modeling framework
- **Neo4j**: Graph database for citation network storage  
- **OpenAI**: LLM integration for content generation
- **NetworkX**: Graph algorithms and analysis
- **Plotly**: Interactive visualization components
- **FastAPI**: Web dashboard framework

---

*Built with the goal of understanding how ideas compete, evolve, and survive in intellectual ecosystems.*