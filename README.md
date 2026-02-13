# Neuro-Vision MCP

Servidor especializado en **Visualización Arquitectónica 3D** y **Análisis de Impacto** diseñado específicamente para asistir a Agentes de IA.

## Características
- **Live Graph 3D**: Visualiza la estructura de archivos y sus dependencias en tiempo real.
- **Impact Analysis**: Predice el "ripple effect" de un cambio en el código antes de ejecutarlo.
- **Telemetry Bridge**: Permite a otros agentes inyectar logs de ejecución o errores directamente en el mapa visual.

## Instalación
```bash
pip install -r requirements.txt
```

## Ejecución
```bash
python mcp_server.py
```

## Guía para Agentes de IA
Este MCP proporciona un "sexto sentido" visual. Úsalo para:
1. **Planificar**: Antes de editar un archivo, usa `analyze_impact` para ver qué otros módulos podrían romperse.
2. **Visualizar**: Usa `visualize_architecture` para entender el flujo de un proyecto desconocido rápidamente.
3. **Monitorear**: Inyecta telemetría con `send_telemetry` durante tus tareas de depuración para ver dónde fallan los nodos visualmente.
