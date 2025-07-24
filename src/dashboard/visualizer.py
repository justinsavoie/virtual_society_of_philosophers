import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any
import numpy as np
import pandas as pd


class NetworkVisualizer:
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set3
    
    def create_citation_network(self, citation_data: List[Dict[str, Any]], 
                               agent_data: List[Dict[str, Any]]) -> go.Figure:
        
        G = nx.Graph()
        
        # Add nodes (agents)
        agent_lookup = {agent['id']: agent for agent in agent_data}
        for agent in agent_data:
            G.add_node(agent['id'], 
                      persona=agent['persona'],
                      influence=agent['influence'],
                      school_id=agent.get('school_id', 'None'))
        
        # Add edges (citations)
        edge_weights = {}
        for citation in citation_data:
            source, target = citation['source'], citation['target']
            if G.has_edge(source, target):
                edge_weights[(source, target)] += 1
            else:
                G.add_edge(source, target, weight=1)
                edge_weights[(source, target)] = 1
        
        # Create layout
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Extract node and edge information
        node_x = [pos[node][0] for node in G.nodes()]
        node_y = [pos[node][1] for node in G.nodes()]
        node_text = [f"{agent_lookup[node]['persona']}<br>Influence: {agent_lookup[node]['influence']:.2f}" 
                    for node in G.nodes()]
        node_colors = [hash(agent_lookup[node].get('school_id', 'None')) % len(self.color_palette) 
                      for node in G.nodes()]
        
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # Create the plot
        fig = go.Figure()
        
        # Add edges
        fig.add_trace(go.Scatter(x=edge_x, y=edge_y,
                                line=dict(width=0.5, color='#888'),
                                hoverinfo='none',
                                mode='lines'))
        
        # Add nodes
        fig.add_trace(go.Scatter(x=node_x, y=node_y,
                                mode='markers',
                                hoverinfo='text',
                                text=node_text,
                                marker=dict(
                                    size=[agent_lookup[node]['influence'] * 5 + 10 
                                         for node in G.nodes()],
                                    color=[self.color_palette[c] for c in node_colors],
                                    line=dict(width=2, color='rgb(50,50,50)')
                                )))
        
        fig.update_layout(title='Philosopher Citation Network',
                         titlefont_size=16,
                         showlegend=False,
                         hovermode='closest',
                         margin=dict(b=20,l=5,r=5,t=40),
                         annotations=[ dict(
                             text="Node size represents influence level",
                             showarrow=False,
                             xref="paper", yref="paper",
                             x=0.005, y=-0.002,
                             xanchor='left', yanchor='bottom',
                             font=dict(color='gray', size=12)
                         )],
                         xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                         yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
        
        return fig
    
    def create_influence_timeline(self, model_data: List[Dict[str, Any]]) -> go.Figure:
        df_list = []
        
        for tick_data in model_data:
            tick = tick_data['tick']
            for agent in tick_data['agents']:
                df_list.append({
                    'tick': tick,
                    'agent_id': agent['id'],
                    'persona': agent['persona'],
                    'influence': agent['influence']
                })
        
        df = pd.DataFrame(df_list)
        
        fig = px.line(df, x='tick', y='influence', color='persona',
                     title='Agent Influence Over Time',
                     labels={'tick': 'Simulation Tick', 'influence': 'Influence Score'})
        
        return fig
    
    def create_school_evolution(self, model_data: List[Dict[str, Any]]) -> go.Figure:
        school_sizes = {}
        
        for tick_data in model_data:
            tick = tick_data['tick']
            for school in tick_data['schools']:
                school_id = school['id']
                if school_id not in school_sizes:
                    school_sizes[school_id] = []
                school_sizes[school_id].append({'tick': tick, 'size': school['member_count']})
        
        fig = go.Figure()
        
        for school_id, data in school_sizes.items():
            ticks = [d['tick'] for d in data]
            sizes = [d['size'] for d in data]
            
            fig.add_trace(go.Scatter(
                x=ticks, y=sizes,
                mode='lines+markers',
                name=school_id,
                line=dict(width=2),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title='School of Thought Evolution',
            xaxis_title='Simulation Tick',
            yaxis_title='Number of Members',
            hovermode='x unified'
        )
        
        return fig
    
    def create_topic_distribution(self, essays: List[Dict[str, Any]]) -> go.Figure:
        topic_counts = {}
        for essay in essays:
            topic = essay['topic']
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        fig = go.Figure(data=[go.Pie(
            labels=list(topic_counts.keys()),
            values=list(topic_counts.values()),
            hole=0.3
        )])
        
        fig.update_layout(title_text="Distribution of Essay Topics")
        return fig
    
    def create_quality_novelty_scatter(self, essays: List[Dict[str, Any]]) -> go.Figure:
        df = pd.DataFrame(essays)
        
        if 'quality_score' not in df.columns or 'novelty_score' not in df.columns:
            return go.Figure().add_annotation(text="Quality/Novelty scores not available", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        fig = px.scatter(df, x='quality_score', y='novelty_score', color='topic',
                        title='Essay Quality vs Novelty',
                        labels={'quality_score': 'Quality Score', 'novelty_score': 'Novelty Score'},
                        hover_data=['author_id', 'timestamp'])
        
        return fig