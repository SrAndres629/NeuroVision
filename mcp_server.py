"""
NEURO-VISION MCP SERVER v1.0
============================
Interfaz unificada para agentes de IA para visualización y análisis de impacto.
"""

import logging
from pathlib import Path
from typing import Any, Optional

from fastmcp import FastMCP
from neuro_architect import get_neuro_architect

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

mcp = FastMCP("Neuro-Vision")
logger = logging.getLogger("neurovision.mcp")

class GlobalContext:
    def __init__(self):
        self.project_root: Optional[Path] = None

    def mount(self, path: str):
        if not path:
            return False
            
        new_path = Path(path).resolve()
        if not new_path.exists():
            raise FileNotFoundError(f"El directorio especificado no existe: {path}")
            
        # Seguridad: Evitar analizar el propio directorio del MCP por accidente si se pasa "."
        # desde un contexto equivocado.
        if "AppData" in str(new_path) and "NeuroVision" in str(new_path):
             logger.warning(f"Intento de montar directorio interno del MCP bloqueado: {new_path}")
             return False

        self.project_root = new_path
        # Re-inicializar el arquitecto con la nueva raíz
        get_neuro_architect(str(self.project_root))
        logger.info(f"PROYECTO ACTIVO: {self.project_root}")
        return True

ctx = GlobalContext()

def udp_wrapper(success: bool, payload: Any = None, error: str = None) -> dict:
    return {
        "success": success,
        "payload": payload if success else None,
        "error": error if not success else None
    }

# ═══════════════════════════════════════════════════════════════════════════════
# HERRAMIENTAS MCP
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def refresh_vision(target_project: str) -> dict:
    """
    Fuerza un re-escaneo completo del proyecto para detectar cambios en la arquitectura.
    Util cuando se han añadido nuevas clases o funciones.
    
    Args:
        target_project: RUTA ABSOLUTA al directorio raíz del proyecto (Ej: 'C:/Users/name/project').
    """
    if not target_project:
        return udp_wrapper(False, error="Se requiere la RUTA ABSOLUTA del proyecto (target_project).")
    
    ctx.mount(target_project)
    try:
        from neuro_architect import NeuroArchitect
        import neuro_architect
        neuro_architect._instance = NeuroArchitect(str(ctx.project_root))
        return udp_wrapper(True, f"Vision refreshed for {ctx.project_root}")
    except Exception as e:
        return udp_wrapper(False, error=str(e))

@mcp.tool()
async def visualize_architecture(action: str = "render", target_project: str = "") -> dict:
    """
    Visualiza la arquitectura del proyecto en 3D (incluye Archivos, Clases y Funciones).
    
    Acciones: 
      - 'render': Genera un mapa HTML dinámico en .ai/visuals/ del proyecto.
      - 'graph': Retorna los datos crudos del grafo en JSON.

    Args:
        action: 'render' o 'graph'.
        target_project: RUTA ABSOLUTA al directorio raíz del proyecto. 
                        REQUERIDO si no se ha montado previamente.
    """
    if target_project: 
        ctx.mount(target_project)
    
    if not ctx.project_root:
        return udp_wrapper(False, error="No hay un proyecto montado. Proporcione 'target_project' con una RUTA ABSOLUTA.")

    try:
        neuro = get_neuro_architect(str(ctx.project_root))
        if action == "render":
            html_path = neuro.export_neuro_map()
            return udp_wrapper(True, {"html_path": str(html_path)})
        elif action == "graph":
            return udp_wrapper(True, neuro.get_brain_state())
        return udp_wrapper(False, error=f"Acción desconocida: {action}")
    except Exception as e:
        return udp_wrapper(False, error=str(e))

@mcp.tool()
async def analyze_impact(target_node: str, target_project: str = "") -> dict:
    """
    Analiza el impacto y riesgo de modificar un nodo (Archivo, Clase o Función).

    Args:
        target_node: Nombre del archivo, clase o función a analizar.
        target_project: RUTA ABSOLUTA al proyecto.
    """
    if target_project: 
        ctx.mount(target_project)
        
    if not ctx.project_root:
        return udp_wrapper(False, error="No hay un proyecto montado. Proporcione 'target_project' con una RUTA ABSOLUTA.")

    try:
        neuro = get_neuro_architect(str(ctx.project_root))
        prediction = neuro.analyze_impact(target_node)
        return udp_wrapper(True, prediction.to_dict())
    except Exception as e:
        return udp_wrapper(False, error=str(e))

@mcp.tool()
async def send_telemetry(node: str, event_type: str, metadata: dict = None, project: str = "") -> dict:
    """
    Inyecta eventos en tiempo real para visualizar actividad en el grafo.
    Eventos: 'execution', 'error', 'variable_update'.

    Args:
        node: ID del nodo (Ej: 'api/index.py' o 'Clase.metodo').
        event_type: 'execution', 'error', o 'variable_update'.
        metadata: Datos adicionales del evento.
        project: RUTA ABSOLUTA al proyecto.
    """
    if project: 
        ctx.mount(project)

    if not ctx.project_root:
        return udp_wrapper(False, error="No hay un proyecto montado. Proporcione 'project' con una RUTA ABSOLUTA.")

    try:
        neuro = get_neuro_architect(str(ctx.project_root))
        neuro.ingest_telemetry(node, event_type, metadata or {})
        return udp_wrapper(True, f"Telemetry processed for {node}")
    except Exception as e:
        return udp_wrapper(False, error=str(e))

if __name__ == "__main__":
    mcp.run()
