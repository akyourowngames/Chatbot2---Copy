"""
Agent Collaboration Protocol - Enable Agents to Work Together
=============================================================
Allows agents to discover, communicate with, and delegate tasks to each other.
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentCollaboration:
    """
    Central collaboration system for agents.
    Enables agent discovery, messaging, delegation, and shared context.
    """
    
    def __init__(self):
        self.agents = {}  # Registry of available agents
        self.messages = defaultdict(list)  # Inter-agent messages
        self.shared_context = {}  # Shared memory/context
        self.delegations = []  # Track delegation history
        logger.info("[COLLABORATION] Agent collaboration system initialized")
    
    def register_agent(self, agent_id: str, agent_instance: Any, capabilities: List[str]) -> bool:
        """
        Register an agent in the collaboration network.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_instance: The agent object
            capabilities: List of what this agent can do
            
        Returns:
            True if registered successfully
        """
        try:
            self.agents[agent_id] = {
                "instance": agent_instance,
                "capabilities": capabilities,
                "registered_at": datetime.now().isoformat(),
                "tasks_completed": 0
            }
            logger.info(f"[COLLABORATION] Registered agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"[COLLABORATION] Registration failed for {agent_id}: {e}")
            return False
    
    def discover_agent(self, capability: str) -> Optional[str]:
        """
        Find an agent that has a specific capability.
        
        Args:
            capability: What you need help with
            
        Returns:
            Agent ID or None
        """
        for agent_id, info in self.agents.items():
            if capability.lower() in [c.lower() for c in info["capabilities"]]:
                return agent_id
        
        # Try fuzzy matching
        for agent_id, info in self.agents.items():
            for cap in info["capabilities"]:
                if capability.lower() in cap.lower() or cap.lower() in capability.lower():
                    return agent_id
        
        return None
    
    def discover_all_agents(self, capability: str) -> List[str]:
        """Find all agents that can help with a capability."""
        matching = []
        for agent_id, info in self.agents.items():
            for cap in info["capabilities"]:
                if capability.lower() in cap.lower() or cap.lower() in capability.lower():
                    matching.append(agent_id)
                    break
        return matching
    
    def request_help(self, from_agent: str, to_agent: str, task: str, 
                     context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        One agent requests help from another.
        
        Args:
            from_agent: Agent requesting help
            to_agent: Agent being asked for help
            task: What needs to be done
            context: Additional context/data
            
        Returns:
            Result from the helping agent
        """
        try:
            logger.info(f"[COLLABORATION] {from_agent} requesting help from {to_agent}")
            
            if to_agent not in self.agents:
                return {
                    "status": "error",
                    "message": f"Agent {to_agent} not found"
                }
            
            # Get the agent instance
            helper_agent = self.agents[to_agent]["instance"]
            
            # Execute the task
            result = helper_agent.execute(task, context)
            
            # Log delegation
            self.delegations.append({
                "from": from_agent,
                "to": to_agent,
                "task": task[:100],
                "status": result.get("status"),
                "timestamp": datetime.now().isoformat()
            })
            
            # Update task counter
            self.agents[to_agent]["tasks_completed"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"[COLLABORATION] Help request failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def delegate_task(self, from_agent: str, capability: str, task: str,
                     context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Delegate a task to any agent with the required capability.
        
        Args:
            from_agent: Agent delegating
            capability: Required capability
            task: Task description
            context: Additional context
            
        Returns:
            Result from delegated agent
        """
        # Find appropriate agent
        to_agent = self.discover_agent(capability)
        
        if not to_agent:
            return {
                "status": "error",
                "message": f"No agent found with capability: {capability}"
            }
        
        logger.info(f"[COLLABORATION] {from_agent} delegating '{capability}' task to {to_agent}")
        return self.request_help(from_agent, to_agent, task, context)
    
    def send_message(self, from_agent: str, to_agent: str, message: str, 
                    data: Any = None):
        """
        Send a message from one agent to another.
        
        Args:
            from_agent: Sender
            to_agent: Recipient
            message: Message content
            data: Optional data payload
        """
        msg = {
            "from": from_agent,
            "to": to_agent,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        self.messages[to_agent].append(msg)
        logger.info(f"[COLLABORATION] Message: {from_agent} → {to_agent}")
    
    def get_messages(self, agent_id: str, unread_only: bool = True) -> List[Dict]:
        """
        Get messages for an agent.
        
        Args:
            agent_id: Agent to get messages for
            unread_only: Only get unread messages
            
        Returns:
            List of messages
        """
        messages = self.messages.get(agent_id, [])
        
        if unread_only:
            # For simplicity, return all and clear
            unread = messages.copy()
            self.messages[agent_id] = []
            return unread
        
        return messages
    
    def broadcast_finding(self, from_agent: str, finding: str, 
                         relevant_to: List[str] = None, data: Any = None):
        """
        Broadcast a finding to relevant agents.
        
        Args:
            from_agent: Agent sharing the finding
            finding: What was discovered
            relevant_to: List of agent IDs to notify (None = all)
            data: Associated data
        """
        recipients = relevant_to if relevant_to else list(self.agents.keys())
        
        for agent_id in recipients:
            if agent_id != from_agent and agent_id in self.agents:
                self.send_message(from_agent, agent_id, f"FINDING: {finding}", data)
        
        logger.info(f"[COLLABORATION] {from_agent} broadcast finding to {len(recipients)} agents")
    
    def set_shared_context(self, key: str, value: Any, source_agent: str = None):
        """
        Set a value in shared context (shared memory).
        
        Args:
            key: Context key
            value: Context value
            source_agent: Agent setting the context
        """
        self.shared_context[key] = {
            "value": value,
            "source": source_agent,
            "updated_at": datetime.now().isoformat()
        }
        logger.info(f"[COLLABORATION] Shared context updated: {key}")
    
    def get_shared_context(self, key: str) -> Any:
        """Get a value from shared context."""
        context_item = self.shared_context.get(key)
        if context_item:
            return context_item.get("value")
        return None
    
    def collaborative_task(self, task: str, required_capabilities: List[str],
                          coordinator: str = "orchestrator") -> Dict[str, Any]:
        """
        Execute a task requiring multiple agents to collaborate.
        
        Args:
            task: Complex task description
            required_capabilities: List of capabilities needed
            coordinator: Agent coordinating the task
            
        Returns:
            Combined results from all agents
        """
        try:
            logger.info(f"[COLLABORATION] Collaborative task: {task[:50]}...")
            
            results = []
            
            # Execute subtasks with appropriate agents
            for capability in required_capabilities:
                agents = self.discover_all_agents(capability)
                
                if not agents:
                    results.append({
                        "capability": capability,
                        "status": "error",
                        "message": f"No agent found for {capability}"
                    })
                    continue
                
                # Use first available agent
                agent_id = agents[0]
                result = self.request_help(
                    coordinator,
                    agent_id,
                    f"{capability} for task: {task}",
                    {"shared_context": self.shared_context}
                )
                
                results.append({
                    "capability": capability,
                    "agent": agent_id,
                    "result": result
                })
                
                # Share result in context for next agent
                self.set_shared_context(
                    f"result_{capability}",
                    result.get("output"),
                    agent_id
                )
            
            return {
                "status": "success",
                "task": task,
                "capabilities_used": required_capabilities,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[COLLABORATION] Collaborative task failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_collaboration_stats(self) -> Dict[str, Any]:
        """Get collaboration statistics."""
        return {
            "registered_agents": len(self.agents),
            "total_delegations": len(self.delegations),
            "pending_messages": sum(len(msgs) for msgs in self.messages.values()),
            "shared_context_items": len(self.shared_context),
            "agents": {
                agent_id: {
                    "capabilities": info["capabilities"],
                    "tasks_completed": info["tasks_completed"]
                }
                for agent_id, info in self.agents.items()
            }
        }


# Global instance
agent_collaboration = AgentCollaboration()


# Convenience functions
def register_agent(agent_id: str, agent_instance: Any, capabilities: List[str]) -> bool:
    """Register an agent in the collaboration network."""
    return agent_collaboration.register_agent(agent_id, agent_instance, capabilities)


def find_agent_for(capability: str) -> Optional[str]:
    """Find an agent with a specific capability."""
    return agent_collaboration.discover_agent(capability)


def delegate(from_agent: str, capability: str, task: str, context: Dict = None) -> Dict[str, Any]:
    """Delegate a task to an agent with the required capability."""
    return agent_collaboration.delegate_task(from_agent, capability, task, context)


# Test
if __name__ == "__main__":
    print("🤝 Testing Agent Collaboration System\n")
    
    # Create mock agent
    class MockAgent:
        def execute(self, task, context=None):
            return {"status": "success", "output": f"Completed: {task}"}
    
    # Register agents
    agent_collaboration.register_agent("research", MockAgent(), ["research", "web search"])
    agent_collaboration.register_agent("writer", MockAgent(), ["writing", "content creation"])
    
    # Test discovery
    found = agent_collaboration.discover_agent("research")
    print(f"Found agent for 'research': {found}")
    
    # Test delegation
    result = agent_collaboration.delegate_task(
        "orchestrator",
        "research",
        "Find information about AI"
    )
    print(f"Delegation result: {result.get('status')}")
    
    # Get stats
    stats = agent_collaboration.get_collaboration_stats()
    print(f"\nCollaboration Stats: {stats}")
