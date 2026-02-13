import asyncio
import os
import json
from pathlib import Path
from mcp_server import visualize_architecture, send_telemetry, refresh_vision

# Fix for tool access in FastMCP
viz_fn = visualize_architecture.fn
telemetry_fn = send_telemetry.fn
refresh_fn = refresh_vision.fn

async def test_memory_and_vision():
    print("=== Neuro-Vision Integration Test: Memory & Vision ===")
    
    # 1. Test Vision Granularity
    print("\n[1] Testing Vision Granularity (Classes & Functions)...")
    res = await viz_fn(action="graph")
    if res["success"]:
        nodes = res["payload"]["nodes"]
        links = res["payload"]["links"]
        
        # Check for classes and functions in this project
        classes = [n for n in nodes if n["type"] == "class"]
        functions = [n for n in nodes if n["type"] == "function"]
        contains_links = [l for l in links if l["type"] == "contains"]
        
        print(f"✅ Detected {len(classes)} classes and {len(functions)} functions.")
        print(f"✅ Detected {len(contains_links)} 'contains' relations.")
        
        if len(classes) > 0 and len(functions) > 0:
            print("   (e.g., class: " + classes[0]["id"] + ")")
        else:
            print("❌ Error: No classes or functions detected!")
    else:
        print(f"❌ Error: {res['error']}")

    # 2. Test Memory (Persistence)
    print("\n[2] Testing Memory (Persistence)...")
    test_node = "vision.py::VisionArchitect"
    print(f"   Sending telemetry for {test_node}...")
    await telemetry_fn(node=test_node, event_type="execution", metadata={"test": "persistence"})
    
    # Check if brain file exists
    brain_file = Path(".ai/neuro_brain.json")
    if brain_file.exists():
        print(f"✅ Success! Brain file created: {brain_file}")
        with open(brain_file, "r") as f:
            data = json.load(f)
            if test_node in data.get("states", {}):
                print(f"✅ Success! State for {test_node} persisted.")
            else:
                print(f"❌ Error: {test_node} not found in persisted state.")
    else:
        print("❌ Error: Brain file not found!")

    # 3. Test Refresh
    print("\n[3] Testing Refresh Vision...")
    res = await refresh_fn()
    if res["success"]:
        print("✅ Success! Vision refreshed.")
    else:
        print(f"❌ Error: {res['error']}")

    print("\n=== Integration Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_memory_and_vision())
