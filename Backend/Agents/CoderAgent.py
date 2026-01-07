"""
Coder Agent - Autonomous Developer
==================================
Writes, executes, and fixes code autonomously.
Uses a feedback loop: Write -> Run -> Fix -> Verify.
"""

from Backend.Agents.AutonomousAgent import AutonomousAgent
import sys
import io
import traceback
import logging

logger = logging.getLogger(__name__)

class CoderAgent(AutonomousAgent):
    """
    Autonomous ReAct agent for coding tasks.
    Can write code, execute it in a sandbox, and debug errors.
    """
    def __init__(self):
        super().__init__(
            name="Coder Agent",
            specialty="Programming, debugging, code execution",
            description="I write and execute Python code. If it fails, I analyze the error and fix it autonomously."
        )
        self._register_coding_tools()
        
    def _register_coding_tools(self):
        """Register coding tools."""
        
        # Tool 1: Execute Python
        def execute_python(params: str):
            """Execute python code. Params: code string"""
            # Clean wrapping
            code = params.strip()
            if code.startswith("```python"):
                code = code[9:]
            if code.startswith("```"):
                code = code[3:]
            if code.endswith("```"):
                code = code[:-3]
            
            return self._execute_safe(code)
            
        self.register_tool(
            name="execute_python",
            func=execute_python,
            description="Execute Python code and get stdout/stderr.",
            parameters="code: str"
        )
        
    def _execute_safe(self, code: str) -> str:
        """Safely execute code with output capture."""
        # Security checks same as before
        forbidden = ["import os", "subprocess", "eval", "exec", "open", "__import__"]
        for bad in forbidden:
            if bad in code and "import os.path" not in code: # Allow os.path? Maybe strict for now
                 return f"Security Error: Operation '{bad}' is not allowed."

        # Capture output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirected_output = sys.stdout = io.StringIO()
        redirected_error = sys.stderr = io.StringIO()

        try:
            # Restricted globals
            safe_globals = {
                "print": print, "range": range, "len": len, "int": int, "str": str, 
                "list": list, "dict": dict, "set": set, "tuple": tuple, "bool": bool,
                "sum": sum, "min": min, "max": max, "abs": abs, "sorted": sorted,
                "enumerate": enumerate, "zip": zip, "map": map, "filter": filter
            }
            exec(code, safe_globals)
            out = redirected_output.getvalue()
            err = redirected_error.getvalue()
            return f"OUTPUT:\n{out}\nERRORS:\n{err}" if err else f"OUTPUT:\n{out}"
            
        except Exception as e:
            return f"RUNTIME ERROR:\n{traceback.format_exc()}"
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

coder_agent = CoderAgent()
