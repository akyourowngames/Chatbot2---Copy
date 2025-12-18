from typing import Dict, Any
from .base import Tool
import asyncio

class CodeTool(Tool):
    def __init__(self):
        super().__init__(
            name="python_execution",
            description="Execute Python code to calculate values, solve math, or process data. Use print() to see output.",
            domain="programming",
            priority="HIGH",
            allowed_intents=["execute_code", "conversation", "multi_step"]
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Valid Python code to execute. Standard libraries are available."
                }
            },
            "required": ["code"]
        }

    def execute(self, code: str, **kwargs) -> str:
        try:
            # Import on demand
            try:
                from Backend.CodeExecutor import CodeExecutor
                # Assuming CodeExecutor class exists or using the module directly?
                # Based on listings, it's a file `CodeExecutor.py`.
                # Let's try to instantiate or find the right entry point.
                # Common pattern in this repo: gl['code_executor'] = CodeExecutor()
                
                executor = CodeExecutor()
                result = executor.execute(code)
                
                # Result format expected: {'status': 'success', 'output': '...', ...}
                if result.get('status') == 'success':
                    return f"Code Executed Successfully.\nOutput:\n{result.get('output', '')}"
                else:
                    return f"Code Execution Failed.\nError:\n{result.get('error', '')}"
                    
            except ImportError:
                 return "Code Executor module not found."
                 
        except Exception as e:
            return f"Execution Error: {str(e)}"
