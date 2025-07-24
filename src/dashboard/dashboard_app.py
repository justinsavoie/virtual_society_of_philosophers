from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
from typing import List, Dict, Any
import asyncio
from .visualizer import NetworkVisualizer


class DashboardApp:
    def __init__(self, philosopher_model=None):
        self.app = FastAPI(title="Virtual Society of Philosophers Dashboard")
        self.model = philosopher_model
        self.visualizer = NetworkVisualizer()
        self.connected_clients: List[WebSocket] = []
        
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.get("/")
        async def dashboard():
            return HTMLResponse(self.get_dashboard_html())
        
        @self.app.get("/api/model-state")
        async def get_model_state():
            if not self.model:
                return {"error": "No model connected"}
            return self.model.get_model_state()
        
        @self.app.get("/api/statistics")
        async def get_statistics():
            if not self.model:
                return {"error": "No model connected"}
            
            state = self.model.get_model_state()
            return {
                "total_agents": len(state['agents']),
                "total_essays": len(state['essays']),
                "total_critiques": len(state['critiques']),
                "total_schools": len(state['schools']),
                "current_tick": state['tick'],
                "avg_influence": sum(a['influence'] for a in state['agents']) / len(state['agents']) if state['agents'] else 0
            }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.connected_clients.append(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    # Handle websocket messages if needed
            except WebSocketDisconnect:
                self.connected_clients.remove(websocket)
    
    async def broadcast_update(self, data: Dict[str, Any]):
        if self.connected_clients:
            message = json.dumps(data)
            for client in self.connected_clients[:]:
                try:
                    await client.send_text(message)
                except:
                    self.connected_clients.remove(client)
    
    def get_dashboard_html(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Virtual Society of Philosophers</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .header { text-align: center; margin-bottom: 30px; }
                .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
                .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .stat-number { font-size: 2em; font-weight: bold; color: #2c3e50; }
                .stat-label { color: #7f8c8d; margin-top: 5px; }
                .chart-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
                .controls { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
                button { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-right: 10px; }
                button:hover { background: #2980b9; }
                .refresh-btn { background: #27ae60; }
                .refresh-btn:hover { background: #229954; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Virtual Society of Philosophers</h1>
                <p>Real-time visualization of intellectual discourse and school formation</p>
            </div>
            
            <div class="controls">
                <button onclick="refreshData()" class="refresh-btn">Refresh Data</button>
                <button onclick="toggleAutoRefresh()">Toggle Auto-refresh</button>
                <span id="auto-refresh-status">Auto-refresh: OFF</span>
            </div>
            
            <div class="stats-grid" id="stats-grid">
                <!-- Statistics will be populated here -->
            </div>
            
            <div class="chart-container">
                <div id="network-chart" style="height: 600px;"></div>
            </div>
            
            <div class="chart-container">
                <div id="influence-timeline" style="height: 400px;"></div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div class="chart-container">
                    <div id="topic-distribution" style="height: 400px;"></div>
                </div>
                <div class="chart-container">
                    <div id="school-evolution" style="height: 400px;"></div>
                </div>
            </div>
            
            <script>
                let autoRefresh = false;
                let refreshInterval;
                
                async function fetchStatistics() {
                    try {
                        const response = await fetch('/api/statistics');
                        const stats = await response.json();
                        
                        if (stats.error) {
                            document.getElementById('stats-grid').innerHTML = '<div class="stat-card"><div class="stat-label">Error: ' + stats.error + '</div></div>';
                            return;
                        }
                        
                        document.getElementById('stats-grid').innerHTML = `
                            <div class="stat-card">
                                <div class="stat-number">${stats.total_agents}</div>
                                <div class="stat-label">Active Philosophers</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${stats.total_essays}</div>
                                <div class="stat-label">Essays Written</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${stats.total_critiques}</div>
                                <div class="stat-label">Critiques Published</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${stats.total_schools}</div>
                                <div class="stat-label">Schools of Thought</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${stats.current_tick}</div>
                                <div class="stat-label">Simulation Month</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${stats.avg_influence.toFixed(2)}</div>
                                <div class="stat-label">Average Influence</div>
                            </div>
                        `;
                    } catch (error) {
                        console.error('Error fetching statistics:', error);
                    }
                }
                
                async function refreshData() {
                    await fetchStatistics();
                    
                    // Placeholder for chart updates
                    Plotly.newPlot('network-chart', [{
                        x: [1, 2, 3, 4],
                        y: [10, 11, 12, 13],
                        type: 'scatter',
                        mode: 'markers',
                        name: 'Network (Placeholder)'
                    }], {
                        title: 'Citation Network (Connect to simulation for live data)',
                        xaxis: { title: 'X Position' },
                        yaxis: { title: 'Y Position' }
                    });
                    
                    Plotly.newPlot('influence-timeline', [{
                        x: [1, 2, 3, 4, 5],
                        y: [1, 1.2, 1.1, 1.3, 1.25],
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Average Influence'
                    }], {
                        title: 'Influence Over Time (Placeholder)',
                        xaxis: { title: 'Simulation Tick' },
                        yaxis: { title: 'Influence Score' }
                    });
                    
                    Plotly.newPlot('topic-distribution', [{
                        values: [4, 3, 2, 3, 1],
                        labels: ['Ethics', 'Epistemology', 'Metaphysics', 'Aesthetics', 'Logic'],
                        type: 'pie',
                        hole: 0.3
                    }], {
                        title: 'Topic Distribution (Placeholder)'
                    });
                    
                    Plotly.newPlot('school-evolution', [{
                        x: [1, 2, 3, 4],
                        y: [3, 4, 3, 5],
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: 'School Size'
                    }], {
                        title: 'School Evolution (Placeholder)',
                        xaxis: { title: 'Simulation Tick' },
                        yaxis: { title: 'Members' }
                    });
                }
                
                function toggleAutoRefresh() {
                    autoRefresh = !autoRefresh;
                    const status = document.getElementById('auto-refresh-status');
                    
                    if (autoRefresh) {
                        status.textContent = 'Auto-refresh: ON';
                        refreshInterval = setInterval(refreshData, 5000);
                    } else {
                        status.textContent = 'Auto-refresh: OFF';
                        clearInterval(refreshInterval);
                    }
                }
                
                // Initialize dashboard
                refreshData();
            </script>
        </body>
        </html>
        """