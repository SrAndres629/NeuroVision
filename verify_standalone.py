import os
import asyncio
from pathlib import Path
import logging

# Configuración de logs para ver qué pasa
logging.basicConfig(level=logging.INFO)

async def test_neurovision_logic():
    print("🚀 Iniciando Verificación de NeuroVision v1.0...")
    
    # Importamos las herramientas directamente para testear su lógica
    # (Esto asume que el entorno tiene las dependencias instaladas)
    try:
        from mcp_server import (
            list_files_logic as list_files, 
            read_file_logic as read_file, 
            write_file_logic as write_file, 
            validate_path
        )
    except ImportError as e:
        print(f"❌ Error: No se pudieron importar las herramientas. ¿Están instaladas las dependencias? {e}")
        return

    # 1. Test de Seguridad (Jailbreak)
    print("\n--- TEST: Seguridad (Jailbreak) ---")
    try:
        # Intentar acceder a Windows System32 (fuera del Jail)
        validate_path("C:/Windows/System32")
        print("❌ FALLO: El jailbreak no fue bloqueado.")
    except PermissionError as e:
        print(f"✅ ÉXITO: Acceso externo bloqueado correctamente: {e}")

    # 2. Test: Listar Archivos
    print("\n--- TEST: list_files ---")
    res_list = await list_files(".", recursive=False)
    if res_list["success"]:
        print(f"✅ ÉXITO: Se encontraron {res_list['count']} archivos.")
        for f in res_list["files"]:
            print(f"  - {f['path']} ({f['type']})")
        # Verificar que NO esté .git
        found_git = any(".git" == f["name"] or ".git" in f["path"].split(os.sep) for f in res_list["files"])
        if not found_git:
            print("✅ ÉXITO: Las carpetas sensibles (.git) fueron ignoradas.")
        else:
            print("❌ FALLO: Se encontró .git en la lista.")
    else:
        print(f"❌ FALLO: list_files falló: {res_list.get('error')}")

    # 3. Test: Escritura y Lectura
    print("\n--- TEST: write_file y read_file ---")
    test_file = "test_output_mcp.txt"
    test_content = "NeuroVision v1.0 Verification Content"
    
    res_write = await write_file(test_file, test_content)
    if res_write["success"]:
        print(f"✅ ÉXITO: Archivo de prueba escrito.")
        
        res_read = await read_file(test_file)
        if res_read["success"] and res_read["content"] == test_content:
            print("✅ ÉXITO: Contenido del archivo leído correctamente.")
        else:
            print(f"❌ FALLO: Error al leer o contenido incorrecto.")
            
        # Limpieza
        os.remove(test_file)
        print("🧹 Limpieza completada.")
    else:
        print(f"❌ FALLO: write_file falló: {res_write.get('error')}")

    print("\n--- VERIFICACIÓN FINALIZADA ---")

if __name__ == "__main__":
    asyncio.run(test_neurovision_logic())
