"""
Swarm Orchestrator - Autonomous Agent Fleet Manager
===================================================
Manages the lifecycle, communication, and task assignment of the agent swarm.
Enables parallel execution and dynamic task routing.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import uuid

from Backend.Agents.AutonomousAgent import AutonomousAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    TASK_REQUEST = "task_request"
    TASK_RESULT = "task_result"
    BROADCAST = "broadcast"
    QUERY = "query"
    RESPONSE = "response"

class Message:
    def __init__(self, sender: str, recipient: str, type: MessageType, content: Any):
        self.id = str(uuid.uuid4())
        self.sender = sender
        self.recipient = recipient
        self.type = type
        self.content = content
        self.timestamp = datetime.now()

class SwarmOrchestrator:
    """
    Coordinator for the autonomous agent swarm.
    Handles:
    - Agent registry
    - Inter-Agent Communication (IAC)
    - Task routing
    - Parallel execution
    """
    
    def __init__(self):
        self.agents: Dict[str, AutonomousAgent] = {}
        self.message_bus: List[Message] = []
        self.active_tasks: Dict[str, Any] = {}
        
        # Initialize fleet
        self._init_swarm()
        logger.info("[SWARM] Swarm Orchestrator initialized")

    def _init_swarm(self):
        """Initialize the core specialist agents."""
        try:
            from Backend.Agents.PlannerAgent import planner_agent
            from Backend.Agents.ResearchAgent import research_agent
            from Backend.Agents.CoderAgent import coder_agent
            from Backend.Agents.CriticAgent import critic_agent
            from Backend.Agents.CreativeAgent import creative_agent
            
            self.register_agent(planner_agent)
            self.register_agent(research_agent)
            self.register_agent(coder_agent)
            self.register_agent(critic_agent)
            self.register_agent(creative_agent)
            
            logger.info(f"[SWARM] Initialized {len(self.agents)} autonomous agents.")
        except Exception as e:
            logger.error(f"[SWARM] Agent initialization failed: {e}")

    def register_agent(self, agent: AutonomousAgent):
        """Add an agent to the swarm."""
        self.agents[agent.name] = agent
        logger.info(f"[SWARM] Agent registered: {agent.name}")

    def get_agent(self, name: str) -> Optional[AutonomousAgent]:
        return self.agents.get(name)
        
    def broadcast(self, sender: str, content: str):
        """Send a message to all agents."""
        msg = Message(sender, "ALL", MessageType.BROADCAST, content)
        self.message_bus.append(msg)
        logger.info(f"[SWARM] Broadcast from {sender}: {content[:50]}")

    def send_message(self, sender: str, recipient: str, content: Any, type: MessageType = MessageType.QUERY):
        """Direct message between agents."""
        msg = Message(sender, recipient, type, content)
        self.message_bus.append(msg)
        # In a real async system, we might push this to the recipient's inbox queue
        
    async def run_swarm_task(self, task: str) -> Dict[str, Any]:
        """
        Execute a complex task using the swarm.
        1. Formulate a plan (using PlannerAgent if available, else heuristic)
        2. Assign subtasks
        3. Aggregate results
        """
        logger.info(f"[SWARM] Starting swarm task: {task[:50]}")
        start_time = datetime.now()
        
        # Temporary: For now, just route to a "General" agent or fail gracefully if empty
        # In Phase 3, we will use the PlannerAgent here.
        
        if not self.agents:
            return {"status": "error", "error": "No agents registered in swarm"}

        # Basic routing logic for now (backward compatibility style)
        # This will be replaced by PlannerAgent logic later
        assigned_agent = None
        if "research" in task.lower():
            assigned_agent = self.agents.get("Research Agent")
        elif "code" in task.lower():
            assigned_agent = self.agents.get("Coder Agent")
        
        # Fallback to first available if specific one not found
        if not assigned_agent:
            assigned_agent = next(iter(self.agents.values()))
            
        if assigned_agent:
            result = assigned_agent.execute(task)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "success",
                "task": task,
                "swarm_output": result.get("output"),
                "primary_agent": assigned_agent.name,
                "execution_time": execution_time
            }
            
        return {"status": "error", "error": "Could not assign agent"}

# Global instance
swarm = SwarmOrchestrator()
