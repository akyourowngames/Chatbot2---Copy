"""
Base Agent - Foundation for All Specialist Agents
===================================================
Provides core functionality that all agents inherit.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Base class for all KAI agents.
    Each agent has a specialty and set of tools it can use.
    """
    
    def __init__(self, name: str, specialty: str, description: str = ""):
        self.name = name
        self.specialty = specialty
        self.description = description
        self.created_at = datetime.now()
        self.execution_history = []
        
        # Available tools - lazy loaded
        self._llm = None
        self._scraper = None
        self._memory = None
        
        logger.info(f"[AGENT] Initialized {self.name} ({self.specialty})")
    
    @property
    def llm(self):
        """Lazy load LLM for agent conversations."""
        if self._llm is None:
            try:
                from Backend.LLM import ChatCompletion
                self._llm = ChatCompletion
            except Exception as e:
                logger.error(f"[AGENT] Failed to load LLM: {e}")
        return self._llm
    
    @property
    def scraper(self):
        """Lazy load web scraper for research."""
        if self._scraper is None:
            try:
                from Backend.JarvisWebScraper import JarvisWebScraper
                self._scraper = JarvisWebScraper()
            except Exception as e:
                logger.error(f"[AGENT] Failed to load scraper: {e}")
        return self._scraper
    
    @property
    def memory(self):
        """Lazy load memory system."""
        if self._memory is None:
            try:
                from Backend.ContextualMemory import contextual_memory
                self._memory = contextual_memory
            except Exception as e:
                logger.error(f"[AGENT] Failed to load memory: {e}")
        return self._memory
    
    def think(self, task: str, context: str = "") -> str:
        """
        Use LLM to reason about the task.
        
        Args:
            task: What to think about
            context: Additional context
            
        Returns:
            Agent's thoughts/response
        """
        if not self.llm:
            return f"[{self.name}] Error: LLM not available"
        
        system_prompt = f"""You are {self.name}, a specialist AI agent.
Your specialty: {self.specialty}
Your role: {self.description}

Think step by step and provide clear, actionable output.
Focus only on your specialty - don't try to do things outside your expertise."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{context}\n\nTask: {task}" if context else task}
        ]
        
        try:
            response = self.llm(messages, inject_memory=False)
            self._log_execution(task, response[:100])
            return response
        except Exception as e:
            logger.error(f"[{self.name}] Think error: {e}")
            return f"Error: {str(e)}"
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a task. Override in subclasses for specialized behavior.
        
        Args:
            task: Task description
            context: Additional context from orchestrator
            
        Returns:
            Result dict with status, output, and metadata
        """
        try:
            result = self.think(task, str(context) if context else "")
            return {
                "status": "success",
                "agent": self.name,
                "output": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"[{self.name}] Execution error: {e}")
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _log_execution(self, task: str, result_preview: str):
        """Log execution for history tracking."""
        self.execution_history.append({
            "task": task[:100],
            "result_preview": result_preview,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only last 20 executions
        if len(self.execution_history) > 20:
            self.execution_history = self.execution_history[-20:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status and stats."""
        return {
            "name": self.name,
            "specialty": self.specialty,
            "executions": len(self.execution_history),
            "created_at": self.created_at.isoformat(),
            "status": "active"
        }
    
    def __repr__(self):
        return f"<Agent: {self.name} ({self.specialty})>"


# Convenience function to create agents
def create_agent(name: str, specialty: str, description: str = "") -> BaseAgent:
    """Factory function to create a base agent."""
    return BaseAgent(name, specialty, description)
