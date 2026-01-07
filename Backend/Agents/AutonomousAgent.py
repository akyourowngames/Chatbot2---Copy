"""
Autonomous Agent - ReAct Engine
===============================
Implements the Reason+Act (ReAct) pattern for autonomous agents.
Agents can think, use tools, observe results, and self-correct.
"""

import logging
import json
import traceback
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
from enum import Enum
import time

# Use existing BaseAgent as parent for compatibility, 
# but override execution logic significantly
from Backend.Agents.BaseAgent import BaseAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    DONE = "done"
    ERROR = "error"

class Tool:
    """Represents a tool effectively usable by an agent."""
    def __init__(self, name: str, func: Callable, description: str, parameters: str):
        self.name = name
        self.func = func
        self.description = description
        self.parameters = parameters  # JSON schema or text description

    def run(self, **kwargs):
        return self.func(**kwargs)

class AutonomousAgent(BaseAgent):
    """
    Advanced agent that operates in a ReAct loop:
    Thought -> Plan -> Action -> Observation -> Thought...
    """
    
    def __init__(self, name: str, specialty: str, description: str = ""):
        super().__init__(name, specialty, description)
        self.tools: Dict[str, Tool] = {}
        self.state = AgentState.IDLE
        self.max_steps = 10
        self.short_term_memory = [] # Conversation history
        
    def register_tool(self, name: str, func: Callable, description: str, parameters: str = ""):
        """Add a tool capability to this agent."""
        self.tools[name] = Tool(name, func, description, parameters)
        logger.info(f"[{self.name}] Registered tool: {name}")

    def _format_tools_prompt(self) -> str:
        """Create the tools section for the system prompt."""
        if not self.tools:
            return "No external tools available. Rely on your internal knowledge."
            
        tool_list = []
        for name, tool in self.tools.items():
            tool_list.append(f"- {name}: {tool.description}\n  Parameters: {tool.parameters}")
        
        return "You have access to the following tools:\n" + "\n".join(tool_list)

    def _get_system_prompt(self) -> str:
        return f"""You are {self.name}, an advanced autonomous AI.
Specialty: {self.specialty}
Role: {self.description}

You utilize the ReAct (Reasoning + Acting) pattern to solve tasks.
For every step, you must output a response in this EXACT format:

THOUGHT: [Your reasoning about the current state and what to do next]
ACTION: [The tool to use, format: tool_name(param=value)] OR [FINAL_ANSWER: your final response]

{self._format_tools_prompt()}

Guidelines:
1. ANALYZE the task deeply before acting.
2. USE TOOLS to gather information or perform actions. don't guess.
3. OBSERVE tool outputs to inform your next thought.
4. If a tool fails, THOUGHT should analyze why and try a different approach.
5. When finished, use FINAL_ANSWER.
"""

    def _parse_action(self, llm_response: str) -> tuple[Optional[str], Optional[Dict]]:
        """Parse the LLM response to extract action and parameters."""
        try:
            # Look for ACTION: prefix
            if "ACTION:" not in llm_response:
                return None, None
            
            action_line = llm_response.split("ACTION:", 1)[1].strip().split('\n')[0]
            
            if action_line.startswith("FINAL_ANSWER:"):
                return "FINAL_ANSWER", {"output": action_line.replace("FINAL_ANSWER:", "").strip()}
            
            # Simple parsing for python-like function calls: tool_name(arg="val", arg2=1)
            # This is a basic parser, in production we might use a robust one or JSON mode
            func_name = action_line.split("(", 1)[0].strip()
            
            if func_name not in self.tools:
                return None, None
                
            # Extract args - primitive string parsing for now to avoid using eval/exec on LLM output
            # For a truly robust system, we'd ask LLM for JSON output for the action
            # Let's assume the LLM follows instruction to output JSON in the action arguments if specifically requested,
            # but for now we'll rely on the LLM interface (which might support function calling natively later)
            # or we pass the raw string if the tool handles it.
            
            # Temporary: simple text extraction of content between parentheses
            import re
            params_match = re.search(r'\((.*)\)', action_line, re.DOTALL)
            params_str = params_match.group(1) if params_match else ""
            
            # Very basic param parsing - assuming the tool can handle the raw string or we do simple split
            # Ideally, we upgrade this to JSON parsing
            return func_name, {"raw_params": params_str}
            
        except Exception as e:
            logger.error(f"[{self.name}] Parse error: {e}")
            return None, None

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run the ReAct loop.
        """
        logger.info(f"[{self.name}] Starting ReAct loop for: {task[:50]}...")
        self.state = AgentState.THINKING
        self.short_term_memory = [] # Reset for new task (or keep if we want continuity)
        
        # Add task to memory
        self.short_term_memory.append({"role": "user", "content": f"Task: {task}\nContext: {context}"})
        
        step_count = 0
        final_output = ""
        
        while step_count < self.max_steps:
            step_count += 1
            
            # 1. THINK & DECIDE
            messages = [{"role": "system", "content": self._get_system_prompt()}] + self.short_term_memory
            
            try:
                response = self.llm(messages, inject_memory=False)
                self.short_term_memory.append({"role": "assistant", "content": response})
                logger.info(f"[{self.name}] Step {step_count} Thought: {response[:100]}...")
                
                # 2. ACT
                tool_name, params = self._parse_action(response)
                
                if tool_name == "FINAL_ANSWER":
                    final_output = params["output"]
                    self.state = AgentState.DONE
                    break
                    
                if tool_name and tool_name in self.tools:
                    self.state = AgentState.ACTING
                    logger.info(f"[{self.name}] Executing {tool_name}...")
                    
                    try:
                        # For now, pass raw params and let tool handle parsing or pass as specific arg
                        # This needs to be refined per tool signature
                        tool_result = self.tools[tool_name].run(params=params["raw_params"])
                        observation = f"OBSERVATION: {str(tool_result)}"
                    except Exception as e:
                        observation = f"OBSERVATION: Tool execution failed. Error: {str(e)}"
                        
                    self.state = AgentState.OBSERVING
                    self.short_term_memory.append({"role": "user", "content": observation})
                    
                else:
                    # No tool action found or invalid tool
                    if "ACTION:" in response:
                        observation = "OBSERVATION: Invalid Action format or unknown tool. Please parse tool usage correctly."
                        self.short_term_memory.append({"role": "user", "content": observation})
                    else:
                        # If no action found, maybe the LLM is just talking. Remind it to act.
                         # Or it might have finished without the keyword.
                         pass

            except Exception as e:
                logger.error(f"[{self.name}] Loop error: {e}")
                self.short_term_memory.append({"role": "user", "content": f"System Error: {str(e)}"})
                break
        
        return {
            "status": "success" if self.state == AgentState.DONE else "incomplete",
            "agent": self.name,
            "output": final_output if final_output else "Max steps reached without final answer.",
            "steps": step_count,
            "history_summary": [m['content'][:50] for m in self.short_term_memory],
            "timestamp": datetime.now().isoformat()
        }
