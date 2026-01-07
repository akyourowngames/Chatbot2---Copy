"""
Tool-Using Agent - Autonomous API Calling and Function Execution
================================================================
Enables AI to autonomously call APIs and execute functions based on natural language.
"""

import logging
import json
import requests
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import inspect

from Backend.Agents.BaseAgent import BaseAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolUsingAgent(BaseAgent):
    """
    Agent that can autonomously call APIs and execute registered functions.
    Includes built-in tools and supports custom tool registration.
    """
    
    def __init__(self):
        super().__init__(
            name="ToolMaster",
            specialty="API calling and function execution",
            description="I can call APIs, execute functions, and use tools to accomplish tasks"
        )
        self.tools = {}
        self._register_builtin_tools()
        logger.info("[TOOL-AGENT] Initialized with built-in tools")
    
    def _register_builtin_tools(self):
        """Register built-in tools."""
        
        # Calculator tool
        self.register_tool(
            name="calculator",
            function=self._calculator,
            description="Perform mathematical calculations. Supports +, -, *, /, **, %, and parentheses.",
            parameters={
                "expression": {"type": "string", "description": "Mathematical expression to evaluate"}
            }
        )
        
        # Web request tool
        self.register_tool(
            name="web_request",
            function=self._web_request,
            description="Make HTTP GET requests to APIs or websites",
            parameters={
                "url": {"type": "string", "description": "URL to request"},
                "headers": {"type": "object", "description": "Optional headers", "optional": True}
            }
        )
        
        # JSON parser tool
        self.register_tool(
            name="json_parser",
            function=self._json_parser,
            description="Parse and extract data from JSON",
            parameters={
                "json_data": {"type": "string", "description": "JSON string or object"},
                "path": {"type": "string", "description": "JSON path to extract (e.g., 'data.user.name')"}
            }
        )
        
        # Text processor tool
        self.register_tool(
            name="text_processor",
            function=self._text_processor,
            description="Process text with operations like uppercase, lowercase, count words, etc.",
            parameters={
                "text": {"type": "string", "description": "Text to process"},
                "operation": {"type": "string", "description": "Operation: uppercase, lowercase, word_count, char_count, reverse"}
            }
        )
    
    def register_tool(self, name: str, function: Callable, description: str, 
                     parameters: Dict[str, Any]) -> bool:
        """
        Register a new tool/function.
        
        Args:
            name: Tool name
            function: Callable function
            description: What the tool does
            parameters: Parameter schema
            
        Returns:
            True if registered successfully
        """
        try:
            self.tools[name] = {
                "function": function,
                "description": description,
                "parameters": parameters
            }
            logger.info(f"[TOOL-AGENT] Registered tool: {name}")
            return True
        except Exception as e:
            logger.error(f"[TOOL-AGENT] Failed to register {name}: {e}")
            return False
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools with descriptions."""
        return [
            {
                "name": name,
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
            for name, tool in self.tools.items()
        ]
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a task by selecting and calling appropriate tools.
        
        Args:
            task: Natural language task description
            context: Additional context
            
        Returns:
            Execution result
        """
        try:
            logger.info(f"[TOOL-AGENT] Executing: {task[:50]}...")
            
            # Step 1: Analyze task and select tools
            tool_plan = self._analyze_and_plan(task)
            
            if not tool_plan.get("tools"):
                # No tools needed, just use regular thinking
                return super().execute(task, context)
            
            # Step 2: Execute tools in sequence
            results = []
            for tool_call in tool_plan["tools"]:
                tool_name = tool_call.get("name")
                params = tool_call.get("parameters", {})
                
                if tool_name not in self.tools:
                    results.append({"error": f"Tool '{tool_name}' not found"})
                    continue
                
                # Execute tool
                tool_result = self._execute_tool(tool_name, params)
                results.append({
                    "tool": tool_name,
                    "parameters": params,
                    "result": tool_result
                })
            
            # Step 3: Synthesize results
            final_output = self._synthesize_results(task, results)
            
            return {
                "status": "success",
                "agent": self.name,
                "task": task,
                "tools_used": [r["tool"] for r in results if "tool" in r],
                "tool_results": results,
                "output": final_output,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[TOOL-AGENT] Execution error: {e}")
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _analyze_and_plan(self, task: str) -> Dict[str, Any]:
        """Analyze task and create tool execution plan."""
        if not self.llm:
            return {"tools": []}
        
        tools_list = "\n".join([
            f"- {tool['name']}: {tool['description']}\n  Params: {json.dumps(tool['parameters'], indent=2)}"
            for tool in self.get_available_tools()
        ])
        
        prompt = f"""You are a tool selection AI. Analyze the task and determine which tools to use.

AVAILABLE TOOLS:
{tools_list}

TASK: {task}

If tools are needed, respond in this JSON format:
{{
  "tools": [
    {{
      "name": "tool_name",
      "parameters": {{"param1": "value1", "param2": "value2"}}
    }}
  ]
}}

If no tools needed, respond: {{"tools": []}}

Your response (JSON only):"""
        
        try:
            response = self.llm(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                inject_memory=False
            )
            
            # Extract JSON from response
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            plan = json.loads(response)
            return plan
            
        except Exception as e:
            logger.error(f"[TOOL-AGENT] Planning failed: {e}")
            return {"tools": []}
    
    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a specific tool with parameters."""
        try:
            tool = self.tools[tool_name]
            function = tool["function"]
            
            # Call the function
            result = function(**parameters)
            logger.info(f"[TOOL-AGENT] Executed {tool_name} successfully")
            return result
            
        except Exception as e:
            logger.error(f"[TOOL-AGENT] Tool execution error ({tool_name}): {e}")
            return {"error": str(e)}
    
    def _synthesize_results(self, task: str, results: List[Dict]) -> str:
        """Synthesize tool results into final answer."""
        if not self.llm:
            return str(results)
        
        results_text = "\n\n".join([
            f"Tool: {r.get('tool', 'unknown')}\nResult: {r.get('result', 'error')}"
            for r in results
        ])
        
        prompt = f"""Synthesize these tool execution results into a clear answer.

ORIGINAL TASK: {task}

TOOL RESULTS:
{results_text}

Provide a clear, concise answer based on the tool results:"""
        
        try:
            response = self.llm(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                inject_memory=False
            )
            return response.strip()
        except:
            return results_text
    
    # ============ Built-in Tool Functions ============
    
    def _calculator(self, expression: str) -> Dict[str, Any]:
        """Safe calculator tool."""
        try:
            # Clean up expression  
            cleaned = expression.replace('×', '*').replace('÷', '/').replace('^', '**')
            
            # Remove dangerous functions
            safe_dict = {
                "__builtins__": {},
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow
            }
            result = eval(cleaned, safe_dict, {})
            
            # Return formatted output
            return {
                "result": result,
                "expression": expression,
                "parsed": cleaned,
                "formatted": f"{expression} = {result}"
            }
        except Exception as e:
            return {"error": f"Calculation failed: {e}"}
    
    def _web_request(self, url: str, headers: Dict = None) -> Dict[str, Any]:
        """Make HTTP GET request."""
        try:
            response = requests.get(url, headers=headers or {}, timeout=10)
            return {
                "status_code": response.status_code,
                "content": response.text[:5000],  # Limit content
                "headers": dict(response.headers)
            }
        except Exception as e:
            return {"error": f"Request failed: {e}"}
    
    def _json_parser(self, json_data: Any, path: str) -> Any:
        """Extract data from JSON using path."""
        try:
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data
            
            # Navigate path
            parts = path.split('.')
            for part in parts:
                if isinstance(data, dict):
                    data = data.get(part)
                elif isinstance(data, list) and part.isdigit():
                    data = data[int(part)]
                else:
                    return {"error": f"Cannot access '{part}' in {type(data)}"}
            
            return {"result": data}
        except Exception as e:
            return {"error": f"JSON parsing failed: {e}"}
    
    def _text_processor(self, text: str, operation: str) -> Dict[str, Any]:
        """Process text with various operations."""
        try:
            operations = {
                "uppercase": lambda t: t.upper(),
                "lowercase": lambda t: t.lower(),
                "word_count": lambda t: len(t.split()),
                "char_count": lambda t: len(t),
                "reverse": lambda t: t[::-1],
                "title": lambda t: t.title(),
                "strip": lambda t: t.strip()
            }
            
            if operation not in operations:
                return {"error": f"Unknown operation: {operation}"}
            
            result = operations[operation](text)
            return {"result": result, "operation": operation}
        except Exception as e:
            return {"error": f"Text processing failed: {e}"}


# Global instance
tool_using_agent = ToolUsingAgent()


# Convenience function
def use_tool(task: str) -> Dict[str, Any]:
    """Execute a task using tools."""
    return tool_using_agent.execute(task)


# Test
if __name__ == "__main__":
    print("🔧 Testing Tool-Using Agent\n")
    
    # Test 1: Calculator
    result = tool_using_agent.execute("Calculate 15 * 23 + 100")
    print(f"Calculator Test: {result.get('output')}\n")
    
    # Test 2: Text processing
    result = tool_using_agent.execute("Count the words in this sentence: The quick brown fox jumps over the lazy dog")
    print(f"Text Processing Test: {result.get('output')}\n")
    
    # Show available tools
    print("Available Tools:")
    for tool in tool_using_agent.get_available_tools():
        print(f"  - {tool['name']}: {tool['description']}")
