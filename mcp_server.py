"""
NEURO-VISION MCP SERVER v1.0
============================
Servidor MCP de alto rendimiento para manipulación de archivos y análisis arquitectural.
Diseñado para Agentes de IA con seguridad "Jail" integrada.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastmcp import FastMCP
from neuro_architect import get_neuro_architect

# --- Configuración de Logs ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("neurovision.mcp")

# --- Inicialización del Servidor ---
mcp = FastMCP("Vision Neuronal")

# --- Capa de Seguridad (Jail) ---
SENSITIVE_DIRS = {".git", ".env", ".ssh", "__pycache__", "node_modules", ".venv", "venv"}

def validate_path(path: str, allow_sensitive: bool = False) -> Path:
    """
    Valida que el path esté dentro del directorio de trabajo y no sea sensible.
    """
    try:
        root = Path.cwd().resolve()
        target = Path(path).resolve()
        
        # 1. Verificar si está dentro del root (Jail)
        if not str(target).startswith(str(root)):
            raise PermissionError(f"Acceso denegado: El path {path} está fuera de la zona permitida.")
        
        # 2. Verificar si toca carpetas sensibles
        if not allow_sensitive:
            for part in target.parts:
                if part in SENSITIVE_DIRS:
                    raise PermissionError(f"Acceso denegado: El path {path} contiene componentes restringidos.")
        
        return target
    except Exception as e:
        logger.error(f"Error de validación de path: {e}")
        raise

# --- Lógica de Herramientas (Separada para Testeo) ---

async def list_files_logic(directory: str = ".", recursive: bool = False) -> dict:
    try:
        root = validate_path(directory)
        files = []
        count = 0
        max_files = 500
        
        pattern = "**/*" if recursive else "*"
        
        for p in root.glob(pattern):
            # Obtener partes relativas al root para filtrar
            try:
                rel_parts = p.relative_to(root).parts
                if any(part in SENSITIVE_DIRS for part in rel_parts):
                    continue
            except ValueError:
                # Si no es relativo al root (raro), lo filtramos por si acaso
                if any(part in SENSITIVE_DIRS for part in p.parts):
                    continue
            
            # También filtrar si el target mismo es sensible
            if p.name in SENSITIVE_DIRS:
                continue
                
            is_dir = p.is_dir()
            files.append({
                "name": p.name,
                "path": str(p.relative_to(Path.cwd())),
                "type": "directory" if is_dir else "file",
                "size": p.stat().st_size if not is_dir else 0
            })
            
            count += 1
            if count >= max_files:
                break
                
        return {"success": True, "files": files, "count": len(files), "truncated": count >= max_files}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def read_file_logic(path: str) -> dict:
    try:
        target = validate_path(path)
        if not target.is_file():
            return {"success": False, "error": f"{path} no es un archivo."}
            
        content = target.read_text(encoding="utf-8")
        return {"success": True, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def write_file_logic(path: str, content: str) -> dict:
    try:
        target = validate_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        logger.info(f"Archivo escrito: {path}")
        return {"success": True, "path": path}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def get_file_info_logic(path: str) -> dict:
    try:
        target = validate_path(path)
        stat = target.stat()
        return {
            "success": True,
            "name": target.name,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_dir": target.is_dir()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

async def refresh_vision_logic(target_project: str = ".") -> dict:
    try:
        root = validate_path(target_project)
        get_neuro_architect(str(root))
        return {"success": True, "message": f"Arquitectura refrescada para {root}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def visualize_architecture_logic(action: str = "render", target_project: str = ".") -> dict:
    try:
        root = validate_path(target_project)
        neuro = get_neuro_architect(str(root))
        if action == "render":
            html_path = neuro.export_neuro_map()
            return {"success": True, "html_path": str(html_path)}
        elif action == "graph":
            return {"success": True, "data": neuro.get_brain_state()}
        return {"success": False, "error": f"Acción '{action}' no soportada."}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def analyze_impact_logic(target_node: str, target_project: str = ".") -> dict:
    try:
        root = validate_path(target_project)
        neuro = get_neuro_architect(str(root))
        prediction = neuro.analyze_impact(target_node)
        return {"success": True, "prediction": prediction.to_dict()}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def send_telemetry_logic(node: str, event_type: str, metadata: dict = None, project: str = ".") -> dict:
    try:
        root = validate_path(project)
        neuro = get_neuro_architect(str(root))
        neuro.ingest_telemetry(node, event_type, metadata or {})
        return {"success": True, "message": f"Evento {event_type} recibido para {node}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# --- Herramientas MCP (Wrappers Decorados) ---

@mcp.tool()
async def list_files(directory: str = ".", recursive: bool = False) -> dict:
    """Lista archivos en un directorio con límites de seguridad."""
    return await list_files_logic(directory, recursive)

@mcp.tool()
async def read_file(path: str) -> dict:
    """Lee el contenido de un archivo en formato UTF-8."""
    return await read_file_logic(path)

@mcp.tool()
async def write_file(path: str, content: str) -> dict:
    """Escribe contenido en un archivo, creando directorios si es necesario."""
    return await write_file_logic(path, content)

@mcp.tool()
async def get_file_info(path: str) -> dict:
    """Obtiene metadatos básicos de un archivo o directorio."""
    return await get_file_info_logic(path)

@mcp.tool()
async def refresh_vision(target_project: str = ".") -> dict:
    """Fuerza un re-escaneo arquitectural del proyecto."""
    return await refresh_vision_logic(target_project)

@mcp.tool()
async def visualize_architecture(action: str = "render", target_project: str = ".") -> dict:
    """Representación visual 3D de la arquitectura."""
    return await visualize_architecture_logic(action, target_project)

@mcp.tool()
async def analyze_impact(target_node: str, target_project: str = ".") -> dict:
    """Analiza el efecto dominó de cambiar un archivo/clase/función."""
    return await analyze_impact_logic(target_node, target_project)

@mcp.tool()
async def send_telemetry(node: str, event_type: str, metadata: dict = None, project: str = ".") -> dict:
    """Inyecta eventos en tiempo real en el grafo visual."""
    return await send_telemetry_logic(node, event_type, metadata, project)

if __name__ == "__main__":
    mcp.run()
