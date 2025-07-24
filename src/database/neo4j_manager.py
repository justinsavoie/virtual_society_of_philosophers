from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import logging


class Neo4jManager:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.setup_schema()
    
    def close(self):
        self.driver.close()
    
    def setup_schema(self):
        with self.driver.session() as session:
            session.run("""
                CREATE CONSTRAINT agent_id IF NOT EXISTS
                FOR (a:Agent) REQUIRE a.id IS UNIQUE
            """)
            
            session.run("""
                CREATE CONSTRAINT essay_id IF NOT EXISTS
                FOR (e:Essay) REQUIRE e.id IS UNIQUE
            """)
            
            session.run("""
                CREATE CONSTRAINT critique_id IF NOT EXISTS
                FOR (c:Critique) REQUIRE c.id IS UNIQUE
            """)
            
            session.run("""
                CREATE CONSTRAINT school_id IF NOT EXISTS
                FOR (s:School) REQUIRE s.id IS UNIQUE
            """)
    
    def create_agent(self, agent_data: Dict[str, Any]):
        with self.driver.session() as session:
            session.run("""
                CREATE (a:Agent {
                    id: $id,
                    persona: $persona,
                    belief_vector: $belief_vector,
                    influence: $influence,
                    birth_tick: $birth_tick,
                    school_id: $school_id
                })
            """, **agent_data)
    
    def create_essay(self, essay_data: Dict[str, Any]):
        with self.driver.session() as session:
            session.run("""
                CREATE (e:Essay {
                    id: $id,
                    author_id: $author_id,
                    timestamp: $timestamp,
                    topic: $topic,
                    text: $text,
                    quality_score: $quality_score,
                    novelty_score: $novelty_score,
                    citation_count: $citation_count
                })
            """, **essay_data)
            
            session.run("""
                MATCH (a:Agent {id: $author_id}), (e:Essay {id: $essay_id})
                CREATE (a)-[:WROTE]->(e)
            """, author_id=essay_data['author_id'], essay_id=essay_data['id'])
    
    def create_critique(self, critique_data: Dict[str, Any]):
        with self.driver.session() as session:
            session.run("""
                CREATE (c:Critique {
                    id: $id,
                    critic_id: $critic_id,
                    target_id: $target_id,
                    stance: $stance,
                    timestamp: $timestamp,
                    text: $text,
                    persuasiveness_score: $persuasiveness_score
                })
            """, **critique_data)
            
            session.run("""
                MATCH (a:Agent {id: $critic_id}), (c:Critique {id: $critique_id})
                CREATE (a)-[:WROTE_CRITIQUE]->(c)
            """, critic_id=critique_data['critic_id'], critique_id=critique_data['id'])
            
            session.run("""
                MATCH (c:Critique {id: $critique_id}), (e:Essay {id: $target_id})
                CREATE (c)-[:CRITIQUES]->(e)
            """, critique_id=critique_data['id'], target_id=critique_data['target_id'])
    
    def create_citation(self, citing_essay_id: str, cited_essay_id: str):
        with self.driver.session() as session:
            session.run("""
                MATCH (e1:Essay {id: $citing_id}), (e2:Essay {id: $cited_id})
                CREATE (e1)-[:CITES]->(e2)
            """, citing_id=citing_essay_id, cited_id=cited_essay_id)
    
    def create_school(self, school_data: Dict[str, Any]):
        with self.driver.session() as session:
            session.run("""
                CREATE (s:School {
                    id: $id,
                    manifesto: $manifesto,
                    doctrine_vector: $doctrine_vector,
                    fitness: $fitness,
                    founding_tick: $founding_tick
                })
            """, **school_data)
    
    def add_agent_to_school(self, agent_id: str, school_id: str):
        with self.driver.session() as session:
            session.run("""
                MATCH (a:Agent {id: $agent_id}), (s:School {id: $school_id})
                CREATE (a)-[:BELONGS_TO]->(s)
                SET a.school_id = $school_id
            """, agent_id=agent_id, school_id=school_id)
    
    def get_citation_graph(self) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e1:Essay)-[:CITES]->(e2:Essay)
                RETURN e1.id as source, e2.id as target, e1.author_id as source_author, e2.author_id as target_author
            """)
            return [dict(record) for record in result]
    
    def get_agent_citation_network(self) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a1:Agent)-[:WROTE]->(e1:Essay)-[:CITES]->(e2:Essay)<-[:WROTE]-(a2:Agent)
                RETURN a1.id as source, a2.id as target, count(*) as weight
            """)
            return [dict(record) for record in result]
    
    def get_school_members(self, school_id: str) -> List[str]:
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a:Agent)-[:BELONGS_TO]->(s:School {id: $school_id})
                RETURN a.id as agent_id
            """, school_id=school_id)
            return [record['agent_id'] for record in result]
    
    def update_agent_influence(self, agent_id: str, influence: float):
        with self.driver.session() as session:
            session.run("""
                MATCH (a:Agent {id: $agent_id})
                SET a.influence = $influence
            """, agent_id=agent_id, influence=influence)
    
    def update_essay_citation_count(self, essay_id: str, count: int):
        with self.driver.session() as session:
            session.run("""
                MATCH (e:Essay {id: $essay_id})
                SET e.citation_count = $count
            """, essay_id=essay_id, count=count)
    
    def get_essays_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e:Essay {topic: $topic})
                RETURN e.id as id, e.author_id as author_id, e.timestamp as timestamp,
                       e.quality_score as quality_score, e.citation_count as citation_count
                ORDER BY e.timestamp DESC
            """, topic=topic)
            return [dict(record) for record in result]
    
    def get_agent_statistics(self) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a:Agent)
                OPTIONAL MATCH (a)-[:WROTE]->(e:Essay)
                OPTIONAL MATCH (a)-[:WROTE_CRITIQUE]->(c:Critique)
                RETURN a.id as agent_id, a.persona as persona, a.influence as influence,
                       a.school_id as school_id, count(DISTINCT e) as essays_written,
                       count(DISTINCT c) as critiques_written
            """)
            return [dict(record) for record in result]