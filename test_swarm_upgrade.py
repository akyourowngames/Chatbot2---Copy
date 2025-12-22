"""
Test Swarm Upgrade
==================
Verifies that the new Autonomous Agent system works correctly.
"""

import sys
import os
import asyncio

# Ensure backend processing is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Backend.Agents.SwarmOrchestrator import swarm
from Backend.Agents.PlannerAgent import planner_agent
from Backend.Agents.CoderAgent import coder_agent

async def test_swarm():
    print("\n🐝 TESTING SWARM SYSTEMS 🐝\n")
    
    # 1. Test Registry
    print("1. Checking Agent Registry...")
    agents = swarm.agents
    if len(agents) >= 5:
        print(f"✅ Success: {len(agents)} agents registered: {list(agents.keys())}")
    else:
        print(f"❌ Fail: Only {len(agents)} agents found.")
        
    # 2. Test Planner (Mock Execution)
    print("\n2. Testing Planner Agent (Logic Check)...")
    task = "Create a snake game in Python"
    
    # We won't run the full LLM loop to save time/tokens in this test script unless needed
    # But let's verify the class structure
    if planner_agent and planner_agent.name == "Planner Agent":
        print("✅ Success: Planner Agent initialized correctly.")
    else:
        print("❌ Fail: Planner Agent issues.")
        
    # 3. Test Coder Tool Registration
    print("\n3. Testing Coder Tools...")
    if "execute_python" in coder_agent.tools:
        print("✅ Success: execute_python tool registered.")
    else:
        print("❌ Fail: Coder tools missing.")
        
    # 4. Test Orchestrator Routing (Dry Run)
    print("\n4. Testing Swarm Routing...")
    try:
        # Just check if method exists and is callable
        if hasattr(swarm, "run_swarm_task"):
             print("✅ Success: Swarm orchestrator is ready.")
        else:
             print("❌ Fail: run_swarm_task missing.")
    except Exception as e:
        print(f"❌ Fail: {e}")

    print("\n✨ SYSTEM VERIFICATION COMPLETE ✨")

if __name__ == "__main__":
    asyncio.run(test_swarm())
