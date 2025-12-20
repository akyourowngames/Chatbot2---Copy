"""
Agent Orchestrator - Multi-Agent Task Coordinator
===================================================
Breaks down complex tasks and coordinates specialist agents.
This is the brain that manages the agent team.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks the orchestrator can handle."""
    RESEARCH = "research"
    WRITE = "write"
    ANALYZE = "analyze"
    RESEARCH_AND_WRITE = "research_and_write"
    FULL_PIPELINE = "full_pipeline"  # Research → Write → Analyze


class AgentOrchestrator:
    """
    Orchestrates multiple agents to complete complex tasks.
    Breaks down tasks, assigns to specialists, and combines results.
    """
    
    def __init__(self):
        self.agents = {}
        self.execution_log = []
        self._load_agents()
        logger.info("[ORCHESTRATOR] Multi-Agent System initialized")
    
    def _load_agents(self):
        """Load available specialist agents."""
        try:
            from Backend.Agents.ResearchAgent import research_agent
            from Backend.Agents.WriterAgent import writer_agent
            from Backend.Agents.AnalystAgent import analyst_agent
            
            self.agents = {
                "research": research_agent,
                "writer": writer_agent,
                "analyst": analyst_agent
            }
            logger.info(f"[ORCHESTRATOR] Loaded {len(self.agents)} agents")
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Failed to load agents: {e}")
            self.agents = {}
    
    def _get_llm(self):
        """Get LLM for orchestrator decisions."""
        try:
            from Backend.LLM import ChatCompletion
            return ChatCompletion
        except:
            return None
    
    def analyze_task(self, task: str) -> Dict[str, Any]:
        """
        Analyze a task and determine the execution plan.
        """
        llm = self._get_llm()
        if not llm:
            return {"type": TaskType.FULL_PIPELINE, "steps": ["research", "write", "analyze"]}
        
        prompt = f"""Analyze this task and determine what agents are needed.

TASK: {task}

Available agents:
1. RESEARCH - Web search, fact-finding, data gathering
2. WRITER - Content creation, articles, reports
3. ANALYST - Review, improve, fact-check

Reply with ONLY one of these task types:
- RESEARCH (just need facts/research)
- WRITE (just need content creation)
- ANALYZE (just need analysis/review)
- RESEARCH_AND_WRITE (research then write)
- FULL_PIPELINE (research, write, then review)

Answer with just the type, nothing else:"""

        try:
            response = llm(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                inject_memory=False
            ).strip().upper().replace(" ", "_")
            
            type_map = {
                "RESEARCH": TaskType.RESEARCH,
                "WRITE": TaskType.WRITE,
                "ANALYZE": TaskType.ANALYZE,
                "RESEARCH_AND_WRITE": TaskType.RESEARCH_AND_WRITE,
                "FULL_PIPELINE": TaskType.FULL_PIPELINE
            }
            
            task_type = type_map.get(response, TaskType.FULL_PIPELINE)
            
        except Exception as e:
            logger.warning(f"[ORCHESTRATOR] Task analysis failed: {e}, using full pipeline")
            task_type = TaskType.FULL_PIPELINE
        
        # Define steps based on task type
        steps_map = {
            TaskType.RESEARCH: ["research"],
            TaskType.WRITE: ["write"],
            TaskType.ANALYZE: ["analyze"],
            TaskType.RESEARCH_AND_WRITE: ["research", "write"],
            TaskType.FULL_PIPELINE: ["research", "write", "analyze"]
        }
        
        return {
            "type": task_type,
            "steps": steps_map[task_type]
        }
    
    def execute(self, task: str, task_type: TaskType = None) -> Dict[str, Any]:
        """
        Execute a task using the appropriate agent(s).
        
        Args:
            task: The task to complete
            task_type: Optional - force a specific execution pattern
            
        Returns:
            Combined results from all agents
        """
        start_time = datetime.now()
        logger.info(f"[ORCHESTRATOR] Starting task: {task[:50]}...")
        
        # Analyze task if type not specified
        if task_type is None:
            analysis = self.analyze_task(task)
            task_type = analysis["type"]
            steps = analysis["steps"]
        else:
            steps_map = {
                TaskType.RESEARCH: ["research"],
                TaskType.WRITE: ["write"],
                TaskType.ANALYZE: ["analyze"],
                TaskType.RESEARCH_AND_WRITE: ["research", "write"],
                TaskType.FULL_PIPELINE: ["research", "write", "analyze"]
            }
            steps = steps_map.get(task_type, ["research", "write", "analyze"])
        
        logger.info(f"[ORCHESTRATOR] Execution plan: {steps}")
        
        # Execute each step
        results = []
        context = {"original_task": task}
        
        for step in steps:
            agent = self.agents.get(step)
            if not agent:
                logger.warning(f"[ORCHESTRATOR] Agent '{step}' not available")
                continue
            
            logger.info(f"[ORCHESTRATOR] Running {agent.name}...")
            
            # Add previous results to context
            if results:
                context["previous_results"] = results[-1].get("output", "")
                if step == "write":
                    context["research"] = results[-1].get("output", "")
                elif step == "analyze":
                    context["content"] = results[-1].get("output", "")
            
            result = agent.execute(task, context)
            results.append(result)
            
            # Log progress
            status = "✓" if result.get("status") == "success" else "✗"
            logger.info(f"[ORCHESTRATOR] {status} {agent.name} completed")
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Compile final result
        final_result = {
            "status": "success" if all(r.get("status") == "success" for r in results) else "partial",
            "task": task,
            "task_type": task_type.value,
            "steps_executed": steps,
            "agent_results": results,
            "final_output": results[-1].get("output", "") if results else "No output",
            "execution_time_seconds": round(execution_time, 2),
            "timestamp": datetime.now().isoformat()
        }
        
        # Log execution
        self._log_execution(task, final_result)
        
        return final_result
    
    def _log_execution(self, task: str, result: Dict):
        """Log execution for history."""
        self.execution_log.append({
            "task": task[:100],
            "status": result.get("status"),
            "steps": result.get("steps_executed"),
            "time": result.get("execution_time_seconds"),
            "timestamp": result.get("timestamp")
        })
        # Keep last 50 executions
        if len(self.execution_log) > 50:
            self.execution_log = self.execution_log[-50:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator and agent status."""
        return {
            "agents": {name: agent.get_status() for name, agent in self.agents.items()},
            "total_executions": len(self.execution_log),
            "recent_executions": self.execution_log[-5:] if self.execution_log else []
        }
    
    def research(self, query: str) -> Dict[str, Any]:
        """Shortcut: Run research agent only."""
        return self.execute(query, TaskType.RESEARCH)
    
    def write(self, content_request: str) -> Dict[str, Any]:
        """Shortcut: Run writer agent only."""
        return self.execute(content_request, TaskType.WRITE)
    
    def analyze(self, content: str) -> Dict[str, Any]:
        """Shortcut: Run analyst agent only."""
        return self.execute(content, TaskType.ANALYZE)
    
    def research_and_write(self, topic: str) -> Dict[str, Any]:
        """Shortcut: Research then write."""
        return self.execute(topic, TaskType.RESEARCH_AND_WRITE)
    
    def full_pipeline(self, task: str) -> Dict[str, Any]:
        """Shortcut: Full pipeline (research → write → analyze)."""
        return self.execute(task, TaskType.FULL_PIPELINE)


# Global instance
agent_orchestrator = AgentOrchestrator()


# Convenience function for quick access
def run_multi_agent_task(task: str, mode: str = "auto") -> Dict[str, Any]:
    """
    Run a multi-agent task.
    
    Args:
        task: The task description
        mode: "auto", "research", "write", "analyze", "research_write", or "full"
        
    Returns:
        Result from the agent team
    """
    mode_map = {
        "research": TaskType.RESEARCH,
        "write": TaskType.WRITE,
        "analyze": TaskType.ANALYZE,
        "research_write": TaskType.RESEARCH_AND_WRITE,
        "full": TaskType.FULL_PIPELINE
    }
    
    if mode == "auto":
        return agent_orchestrator.execute(task)
    else:
        task_type = mode_map.get(mode, TaskType.FULL_PIPELINE)
        return agent_orchestrator.execute(task, task_type)


# Quick test
if __name__ == "__main__":
    print("🤖 Testing Multi-Agent System\n")
    
    # Test task analysis
    test_task = "Research the latest AI trends and write a summary"
    print(f"Task: {test_task}")
    print(f"Analysis: {agent_orchestrator.analyze_task(test_task)}")
