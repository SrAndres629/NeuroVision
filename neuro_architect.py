"""
NEURO-VISION: NEURO-ARCHITECT v1.0
==================================
Gestor de grafos vivos y telemetría para agentes de IA.
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

import networkx as nx
from vision import get_vision

logger = logging.getLogger("neurovision.neuro")

@dataclass
class NeuronState:
    last_active: Optional[datetime] = None
    activation_level: float = 0.0
    error_rate: float = 0.0
    active_variables: Dict[str, str] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "activation_level": self.activation_level,
            "error_rate": self.error_rate,
            "active_variables": self.active_variables,
            "logs": self.logs[-5:]
        }

@dataclass
class ImpactPrediction:
    target_node: str
    direct_impact: List[str]
    ripple_effect: List[str]
    risk_score: float

    @property
    def affected_nodes(self) -> List[str]:
        return list(set(self.direct_impact + self.ripple_effect))

    def to_dict(self) -> dict:
        data = asdict(self)
        data["affected_nodes"] = self.affected_nodes
        return data

class NeuroArchitect:
    """Arquitecto del Sistema Nervioso."""

    def __init__(self, project_root: Optional[str] = None):
        self._lock = Lock()
        self._graph: nx.DiGraph = nx.DiGraph()
        self._states: Dict[str, NeuronState] = {}
        if project_root:
            self._project_root = Path(project_root).resolve()
        else:
            self._project_root = Path.cwd().resolve()
        self._vision = get_vision(str(self._project_root))
        self._brain_path = self._project_root / ".ai" / "neuro_brain.json"
        self._initialize()

    def _initialize(self):
        try:
            nodes, edges = self._vision.scan_project()
            with self._lock:
                self._graph = self._vision.build_graph(nodes, edges)
                for node in self._graph.nodes():
                    self._states[node] = NeuronState()
            
            # Memoria: Intentar cargar estado previo
            self.load_state()
        except Exception as e:
            logger.error(f"Failed to initialize neuro architect: {e}")

    def save_state(self):
        """Serializa el estado del cerebro a disco."""
        try:
            with self._lock:
                data = {
                    "timestamp": datetime.now().isoformat(),
                    "states": {node: state.to_dict() for node, state in self._states.items()},
                    # Note: Graph topology is mostly reconstructed by vision, 
                    # but we keep states tied to node IDs.
                }
            
            self._brain_path.parent.mkdir(parents=True, exist_ok=True)
            self._brain_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            logger.info(f"BRAIN SAVED: {self._brain_path}")
        except Exception as e:
            logger.error(f"Error saving brain state: {e}")

    def load_state(self):
        """Carga el estado del cerebro si existe."""
        if not self._brain_path.exists():
            return
        
        try:
            data = json.loads(self._brain_path.read_text(encoding="utf-8"))
            with self._lock:
                for node_id, state_dict in data.get("states", {}).items():
                    if node_id in self._states:
                        state = self._states[node_id]
                        if state_dict.get("last_active"):
                            state.last_active = datetime.fromisoformat(state_dict["last_active"])
                        state.activation_level = state_dict.get("activation_level", 0.0)
                        state.error_rate = state_dict.get("error_rate", 0.0)
                        state.active_variables = state_dict.get("active_variables", {})
                        state.logs = state_dict.get("logs", [])
            logger.info(f"BRAIN LOADED: {len(data.get('states', {}))} neurons restored.")
        except Exception as e:
            logger.warning(f"Failed to load brain state: {e}")

    def ingest_telemetry(self, node_name: str, event_type: str, payload: Dict[str, Any]):
        with self._lock:
            if node_name not in self._states:
                if node_name not in self._graph:
                    self._graph.add_node(node_name, node_type="dynamic")
                self._states[node_name] = NeuronState()

            state = self._states[node_name]
            state.last_active = datetime.now()
            
            if event_type == "execution":
                state.activation_level = min(1.0, state.activation_level + 0.2)
            elif event_type == "error":
                state.error_rate = min(1.0, state.error_rate + 0.1)
                state.logs.append(f"ERROR: {payload.get('message', 'Unknown')}")
            elif event_type == "variable_update":
                state.active_variables.update(payload)
        
        # Guardado proactivo
        self.save_state()

    def analyze_impact(self, target_node: str) -> ImpactPrediction:
        if target_node not in self._graph:
            # Try to find node by partial name if full name fails (e.g. filename vs filename::func)
            matches = [n for n in self._graph.nodes() if n.endswith(target_node)]
            if matches:
                target_node = matches[0]
            else:
                return ImpactPrediction(target_node, [], [], 0.0)

        direct_dependents = list(self._graph.predecessors(target_node))
        ripple_dependents = set()
        for bid in direct_dependents:
            try:
                ancestors = nx.ancestors(self._graph, bid)
                ripple_dependents.update(ancestors)
            except Exception: pass
        
        ripple_list = [n for n in ripple_dependents if n not in direct_dependents and n != target_node]
        risk_score = min(100.0, (len(direct_dependents) * 10) + (len(ripple_list) * 2))

        return ImpactPrediction(target_node, direct_dependents, ripple_list[:20], risk_score)

    def get_brain_state(self) -> Dict[str, Any]:
        nodes_data = []
        for n, attrs in self._graph.nodes(data=True):
            state = self._states.get(n, NeuronState())
            nodes_data.append({
                "id": n,
                "label": attrs.get("name", n),
                "type": attrs.get("node_type", "unknown"),
                "state": state.to_dict(),
                "metrics": {
                    "in_degree": self._graph.in_degree(n) if n in self._graph else 0,
                    "out_degree": self._graph.out_degree(n) if n in self._graph else 0,
                }
            })

        edges_data = []
        for u, v, attrs in self._graph.edges(data=True):
            edges_data.append({"source": u, "target": v, "type": attrs.get("edge_type", "unknown")})

        return {
            "timestamp": datetime.now().isoformat(),
            "nodes": nodes_data,
            "links": edges_data,
            "neuron_count": len(nodes_data),
            "synapse_count": len(edges_data)
        }

    def export_neuro_map(self) -> Path:
        data = self.get_brain_state()
        html_content = self._generate_html_template(data)
        
        ai_dir = self._project_root / ".ai"
        neuro_dir = ai_dir / "visuals"
        neuro_dir.mkdir(parents=True, exist_ok=True)
        
        html_path = neuro_dir / "neuro_map.html"
        html_path.write_text(html_content, encoding="utf-8")
        return html_path

    def _generate_html_template(self, data: Dict[str, Any]) -> str:
        json_payload = json.dumps(data)
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Neuro-Vision Dashboard</title>
    <script src="//unpkg.com/3d-force-graph"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {{ margin: 0; background-color: #050505; color: #e0e0e0; font-family: 'JetBrains Mono', monospace; overflow: hidden; }}
        #3d-graph {{ z-index: 1; position: absolute; top: 0; left: 0; width: 100%; height: 100%; }}
        #hud {{ position: absolute; top: 20px; left: 20px; z-index: 10; background: rgba(10,10,15,0.8); backdrop-filter: blur(10px); padding: 20px; border: 1px solid rgba(100,255,218,0.3); border-radius: 8px; width: 280px; }}
        h1 {{ font-size: 14px; margin: 0 0 15px 0; color: #64ffda; text-transform: uppercase; }}
        .metric {{ display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 11px; }}
        .metric-value {{ color: #fff; font-weight: bold; }}
    </style>
</head>
<body>
    <div id="3d-graph"></div>
    <div id="hud">
        <h1>Neuro-Vision LIVE</h1>
        <div class="metric"><span>Project Neurons</span><span class="metric-value">{data['neuron_count']}</span></div>
        <div class="metric"><span>Connections</span><span class="metric-value">{data['synapse_count']}</span></div>
        <div style="font-size: 9px; color: #666; margin-top: 15px;">MEMORY-ENABLED EDITION</div>
    </div>
    <script>
        const Graph = ForceGraph3D()(document.getElementById('3d-graph'))
            .graphData({json_payload})
            .nodeLabel(node => `[${{node.type}}] ${{node.id}}`)
            .nodeAutoColorBy('type')
            .linkWidth(1.2)
            .linkDirectionalParticles(2)
            .onNodeClick(node => {{
                console.log(node);
                // Future: Show HUD with node state
            }});
    </script>
</body>
</html>"""

# SINGLETON
_instance = None
def get_neuro_architect(project_root: Optional[str] = None):
    global _instance
    if _instance is None:
        _instance = NeuroArchitect(project_root)
    else:
        # Update project root if it changed
        if project_root and Path(project_root) != _instance._project_root:
            _instance = NeuroArchitect(project_root)
    return _instance
