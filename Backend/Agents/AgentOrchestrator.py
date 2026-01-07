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
    CODE = "code"  # Code writing, debugging, execution
    TOOL_USE = "tool_use"  # API calling, function execution
    WEB_BROWSE = "web_browse"  # Browser automation
    DOC_ANALYSIS = "doc_analysis"  # Document deep analysis
    MULTIMODAL = "multimodal"  # Image + text reasoning
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
            from Backend.Agents.CoderAgent import coder_agent
            from Backend.Agents.ToolUsingAgent import tool_using_agent
            from Backend.Agents.WebBrowsingAgent import web_browsing_agent
            from Backend.Agents.DocumentAnalysisAgent import document_analysis_agent
            from Backend.Agents.MultiModalAgent import multimodal_agent
            from Backend.Agents.AgentCollaboration import agent_collaboration
            
            self.agents = {
                "research": research_agent,
                "writer": writer_agent,
                "analyst": analyst_agent,
                "coder": coder_agent,
                "tool_using": tool_using_agent,
                "web_browsing": web_browsing_agent,
                "doc_analysis": document_analysis_agent,
                "multimodal": multimodal_agent
            }
            
            # Register agents in collaboration system
            agent_collaboration.register_agent("research", research_agent, ["research", "web search", "information gathering"])
            agent_collaboration.register_agent("writer", writer_agent, ["writing", "content creation", "articles"])
            agent_collaboration.register_agent("analyst", analyst_agent, ["analysis", "review", "critique"])
            agent_collaboration.register_agent("coder", coder_agent, ["coding", "programming", "debugging"])
            agent_collaboration.register_agent("tool_using", tool_using_agent, ["API calling", "functions", "tools"])
            agent_collaboration.register_agent("web_browsing", web_browsing_agent, ["web automation", "browser", "scraping"])
            agent_collaboration.register_agent("doc_analysis", document_analysis_agent, ["document analysis", "PDF", "DOCX"])
            agent_collaboration.register_agent("multimodal", multimodal_agent, ["vision", "image analysis", "multimodal"])
            
            self.collaboration = agent_collaboration
            logger.info(f"[ORCHESTRATOR] Loaded {len(self.agents)} agents with collaboration")
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Failed to load agents: {e}")
            self.agents = {}
            self.collaboration = None
    
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
4. CODER - Code writing, debugging, execution
5. TOOL_USE - API calling, function execution
6. WEB_BROWSE - Browser automation, web scraping
7. DOC_ANALYSIS - Deep document analysis (PDF/DOCX)
8. MULTIMODAL - Image and text reasoning

Reply with ONLY one of these task types:
- RESEARCH (just need facts/research)
- WRITE (just need content creation)
- ANALYZE (just need analysis/review)
- CODE (code writing, debugging, or execution)
- TOOL_USE (need to call APIs or use tools)
- WEB_BROWSE (browser automation needed)
- DOC_ANALYSIS (document analysis)
- MULTIMODAL (image analysis with context)
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
                "CODE": TaskType.CODE,
                "TOOL_USE": TaskType.TOOL_USE,
                "WEB_BROWSE": TaskType.WEB_BROWSE,
                "DOC_ANALYSIS": TaskType.DOC_ANALYSIS,
                "MULTIMODAL": TaskType.MULTIMODAL,
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
            TaskType.WRITE: ["writer"],
            TaskType.ANALYZE: ["analyst"],
            TaskType.CODE: ["coder"],
            TaskType.TOOL_USE: ["tool_using"],
            TaskType.WEB_BROWSE: ["web_browsing"],
            TaskType.DOC_ANALYSIS: ["doc_analysis"],
            TaskType.MULTIMODAL: ["multimodal"],
            TaskType.RESEARCH_AND_WRITE: ["research", "writer"],
            TaskType.FULL_PIPELINE: ["research", "writer", "analyst"]
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
                TaskType.WRITE: ["writer"],
                TaskType.ANALYZE: ["analyst"],
                TaskType.CODE: ["coder"],
                TaskType.TOOL_USE: ["tool_using"],
                TaskType.WEB_BROWSE: ["web_browsing"],
                TaskType.DOC_ANALYSIS: ["doc_analysis"],
                TaskType.MULTIMODAL: ["multimodal"],
                TaskType.RESEARCH_AND_WRITE: ["research", "writer"],
                TaskType.FULL_PIPELINE: ["research", "writer", "analyst"]
            }
            steps = steps_map.get(task_type, ["research", "writer", "analyst"])
        
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
                if step == "writer":
                    context["research"] = results[-1].get("output", "")
                elif step == "analyst":
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
        """Log execution for history and save to Supabase."""
        log_entry = {
            "task": task[:100],
            "status": result.get("status"),
            "steps": result.get("steps_executed"),
            "time": result.get("execution_time_seconds"),
            "timestamp": result.get("timestamp")
        }
        
        self.execution_log.append(log_entry)
        
        # Keep last 50 executions in memory
        if len(self.execution_log) > 50:
            self.execution_log = self.execution_log[-50:]
        
        # Save to Supabase for persistent history
        try:
            from Backend.SupabaseDB import supabase_db
            if supabase_db and supabase_db.client:
                supabase_db.client.table('agent_logs').insert({
                    'task': task[:500],
                    'status': result.get('status'),
                    'task_type': result.get('task_type'),
                    'steps': ','.join(result.get('steps_executed', [])),
                    'execution_time': result.get('execution_time_seconds'),
                    'output_preview': result.get('final_output', '')[:1000]
                }).execute()
                logger.info("[ORCHESTRATOR] Logged to Supabase")
        except Exception as e:
            logger.debug(f"[ORCHESTRATOR] Supabase logging skipped: {e}")
    
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
    
    def code(self, code_task: str) -> Dict[str, Any]:
        """Shortcut: Run coder agent only."""
        return self.execute(code_task, TaskType.CODE)


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
        "code": TaskType.CODE,
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
