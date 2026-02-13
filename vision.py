"""
NEURO-VISION: VISION ENGINE v1.0
================================
Analizador de dependencias estático optimizado para agentes de IA.
"""

import ast
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx

logger = logging.getLogger("neurovision.vision")

@dataclass
class DependencyNode:
    name: str
    node_type: str
    file_path: Optional[str] = None

@dataclass
class DependencyEdge:
    source: str
    target: str
    edge_type: str

class VisionArchitect:
    """Arquitecto de visualización (AST Local)."""

    def __init__(self, project_root: Optional[str] = None):
        if project_root:
            self._project_root = Path(project_root).resolve()
        else:
            self._project_root = Path.cwd().resolve()

    def scan_project(self) -> tuple[List[DependencyNode], List[DependencyEdge]]:
        nodes: Dict[str, DependencyNode] = {}
        edges: List[DependencyEdge] = []
        
        exclude = {".git", ".ai", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}

        for py_file in self._project_root.rglob("*.py"):
            if any(p in str(py_file) for p in exclude): continue
            
            rel_path = str(py_file.relative_to(self._project_root))
            file_node_id = rel_path
            
            nodes[file_node_id] = DependencyNode(py_file.stem, "file", rel_path)
            
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    # Detection of Imports
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        module = ""
                        if isinstance(node, ast.Import):
                            module = node.names[0].name.split('.')[0]
                        else:
                            if node.module: module = node.module.split('.')[0]
                        
                        if module and module not in {"os", "sys", "json", "typing", "logging", "pathlib", "datetime", "ast"}:
                             edges.append(DependencyEdge(file_node_id, module, "import"))
                    
                    # Detection of Classes
                    elif isinstance(node, ast.ClassDef):
                        class_node_id = f"{rel_path}::{node.name}"
                        nodes[class_node_id] = DependencyNode(node.name, "class", rel_path)
                        edges.append(DependencyEdge(file_node_id, class_node_id, "contains"))
                        
                        # Check inheritance
                        for base in node.bases:
                            if isinstance(base, ast.Name):
                                edges.append(DependencyEdge(class_node_id, base.id, "inherits"))
                    
                    # Detection of Functions
                    elif isinstance(node, ast.FunctionDef):
                        # Avoid nested functions for now to keep it clean, or tag them
                        parent = getattr(node, 'parent', None)
                        func_node_id = f"{rel_path}::{node.name}"
                        nodes[func_node_id] = DependencyNode(node.name, "function", rel_path)
                        
                        # Find if it's inside a class
                        is_method = False
                        for p in ast.walk(tree):
                            if isinstance(p, ast.ClassDef):
                                if node in p.body:
                                    class_node_id = f"{rel_path}::{p.name}"
                                    edges.append(DependencyEdge(class_node_id, func_node_id, "method"))
                                    is_method = True
                                    break
                        
                        if not is_method:
                            edges.append(DependencyEdge(file_node_id, func_node_id, "contains"))
            except Exception as e:
                logger.error(f"Error parsing {py_file}: {e}")
            
        return list(nodes.values()), edges

    def build_graph(self, nodes: List[DependencyNode], edges: List[DependencyEdge]) -> nx.DiGraph:
        G = nx.DiGraph()
        for n in nodes: 
            # Use unique ID as node key
            node_id = f"{n.file_path}::{n.name}" if n.node_type in ["class", "function"] else n.file_path
            G.add_node(node_id, node_type=n.node_type, name=n.name, file_path=n.file_path)
            
        for e in edges:
            if G.has_node(e.source) and G.has_node(e.target):
                G.add_edge(e.source, e.target, edge_type=e.edge_type)
            elif G.has_node(e.source):
                # Target might be an external module
                if not G.has_node(e.target):
                    G.add_node(e.target, node_type="module", name=e.target)
                G.add_edge(e.source, e.target, edge_type=e.edge_type)
        return G

# SINGLETON
_instance = None
def get_vision(project_root: Optional[str] = None):
    global _instance
    if _instance is None:
        _instance = VisionArchitect(project_root)
    else:
        # Update project root if it changed
        if project_root and Path(project_root) != _instance._project_root:
            _instance = VisionArchitect(project_root)
    return _instance
