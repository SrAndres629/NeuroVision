import asyncio
import os
from mcp_server import visualize_architecture, analyze_impact

# Fix for tool access in FastMCP
viz_fn = visualize_architecture.fn
impact_fn = analyze_impact.fn

async def final_check():
    print("=== Neuro-Vision Standalone Final Check ===")
    
    # Check 1: Visualize current directory
    print("\n[1] Testing visualization of current directory...")
    res = await viz_fn(action="render")
    if res["success"]:
        print(f"✅ Success! Map generated: {res['payload']['html_path']}")
    else:
        print(f"❌ Error: {res['error']}")

    # Check 2: Impact Analysis
    print("\n[2] Testing impact analysis on 'mcp_server.py'...")
    res = await impact_fn(target_node="mcp_server.py")
    if res["success"]:
        print(f"✅ Success! Risks: {res['payload']['risk_score']}")
    else:
        print(f"❌ Error: {res['error']}")

    print("\n=== Final Check Complete ===")

if __name__ == "__main__":
    asyncio.run(final_check())
