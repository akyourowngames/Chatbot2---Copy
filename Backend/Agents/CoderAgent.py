"""
Coder Agent - Code Writing, Debugging & Execution Specialist
=============================================================
Writes code, debugs issues, explains code, and can execute Python safely.
"""

import logging
import sys
import io
import traceback
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

from Backend.Agents.BaseAgent import BaseAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoderAgent(BaseAgent):
    """
    Specialist agent for code-related tasks.
    Can write, debug, explain, and execute code.
    """
    
    def __init__(self):
        super().__init__(
            name="Coder Agent",
            specialty="Code writing, debugging, execution, and explanation",
            description="I write clean code, debug issues, explain complex code, and can safely execute Python."
        )
        
        self.supported_languages = [
            "python", "javascript", "typescript", "html", "css", 
            "java", "c", "cpp", "csharp", "go", "rust", "sql"
        ]
        
        self.execution_history = []
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute coding task: write, debug, explain, or run code.
        """
        logger.info(f"[CoderAgent] Starting: {task[:50]}...")
        
        try:
            task_lower = task.lower()
            
            # Detect task type
            if any(word in task_lower for word in ["run", "execute", "test"]):
                # Extract and run code
                code = self._extract_code(task, context)
                if code:
                    return self._execute_code(code, task)
            
            if any(word in task_lower for word in ["debug", "fix", "error", "bug"]):
                return self._debug_code(task, context)
            
            if any(word in task_lower for word in ["explain", "what does", "how does"]):
                return self._explain_code(task, context)
            
            # Default: write code
            return self._write_code(task, context)
            
        except Exception as e:
            logger.error(f"[CoderAgent] Error: {e}")
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _write_code(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Write code based on requirements."""
        # Detect language from task
        language = self._detect_language(task)
        
        prompt = f"""You are an expert programmer. Write clean, well-documented code.

TASK: {task}

LANGUAGE: {language}

REQUIREMENTS:
1. Write production-ready code
2. Include helpful comments
3. Handle errors appropriately
4. Follow best practices for {language}
5. If it's a complete program, make it runnable

Provide the code with brief explanation:"""

        code_response = self.think(prompt)
        
        return {
            "status": "success",
            "agent": self.name,
            "output": code_response,
            "language": language,
            "task_type": "write_code",
            "timestamp": datetime.now().isoformat()
        }
    
    def _debug_code(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Debug code and explain the fix."""
        code = context.get("code", "") if context else ""
        error = context.get("error", "") if context else ""
        
        prompt = f"""You are a debugging expert. Analyze this code and fix any issues.

PROBLEM: {task}

{f'CODE:{chr(10)}{code}' if code else ''}
{f'ERROR:{chr(10)}{error}' if error else ''}

Provide:
1. ISSUE: What's wrong
2. FIX: The corrected code
3. EXPLANATION: Why it failed and how the fix works"""

        debug_response = self.think(prompt)
        
        return {
            "status": "success",
            "agent": self.name,
            "output": debug_response,
            "task_type": "debug",
            "timestamp": datetime.now().isoformat()
        }
    
    def _explain_code(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Explain code in simple terms."""
        code = self._extract_code(task, context)
        
        prompt = f"""Explain this code in simple terms. Break it down step by step.

{f'CODE:{chr(10)}{code}' if code else f'QUESTION: {task}'}

Provide:
1. OVERVIEW: What the code does (1-2 sentences)
2. STEP BY STEP: Line-by-line explanation
3. KEY CONCEPTS: Important programming concepts used
4. EXAMPLE: How to use it"""

        explanation = self.think(prompt)
        
        return {
            "status": "success",
            "agent": self.name,
            "output": explanation,
            "task_type": "explain",
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_code(self, code: str, task: str) -> Dict[str, Any]:
        """
        Safely execute Python code in a sandboxed environment.
        """
        logger.info(f"[CoderAgent] Executing Python code...")
        
        # Clean code
        code = self._clean_code(code)
        
        if not code:
            return {
                "status": "error",
                "agent": self.name,
                "error": "No valid Python code found to execute",
                "timestamp": datetime.now().isoformat()
            }
        
        # Capture output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = captured_output = io.StringIO()
        sys.stderr = captured_error = io.StringIO()
        
        result = None
        error = None
        execution_time = 0
        
        try:
            start = datetime.now()
            
            # Create safe execution environment
            safe_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    "bool": bool,
                    "sum": sum,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "round": round,
                    "sorted": sorted,
                    "reversed": reversed,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                    "isinstance": isinstance,
                    "type": type,
                    "True": True,
                    "False": False,
                    "None": None,
                }
            }
            
            # Execute
            exec(code, safe_globals)
            
            execution_time = (datetime.now() - start).total_seconds()
            result = captured_output.getvalue()
            
        except Exception as e:
            error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        # Log execution
        self.execution_history.append({
            "code": code[:200],
            "success": error is None,
            "timestamp": datetime.now().isoformat()
        })
        
        if error:
            return {
                "status": "error",
                "agent": self.name,
                "code": code,
                "error": error,
                "task_type": "execute",
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "status": "success",
            "agent": self.name,
            "code": code,
            "output": result or "(No output)",
            "execution_time": round(execution_time, 4),
            "task_type": "execute",
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_code(self, task: str, context: Dict[str, Any] = None) -> str:
        """Extract code from task or context."""
        # Check context first
        if context and context.get("code"):
            return context.get("code")
        
        # Try to extract from task
        # Look for code blocks
        code_block = re.search(r'```(?:python)?\n?(.*?)```', task, re.DOTALL)
        if code_block:
            return code_block.group(1).strip()
        
        # Look for inline code
        if ":" in task:
            potential_code = task.split(":", 1)[-1].strip()
            if any(keyword in potential_code for keyword in ["print", "def ", "import ", "for ", "if ", "="]):
                return potential_code
        
        return ""
    
    def _clean_code(self, code: str) -> str:
        """Clean and validate code before execution."""
        # Remove markdown code blocks
        code = re.sub(r'```(?:python)?\n?', '', code)
        code = code.replace('```', '').strip()
        
        # Security check - block dangerous operations
        dangerous = ["import os", "import sys", "subprocess", "eval(", "exec(", 
                    "__import__", "open(", "file(", "input(", "raw_input"]
        
        for danger in dangerous:
            if danger in code.lower():
                logger.warning(f"[CoderAgent] Blocked dangerous code: {danger}")
                return ""
        
        return code
    
    def _detect_language(self, task: str) -> str:
        """Detect programming language from task."""
        task_lower = task.lower()
        
        for lang in self.supported_languages:
            if lang in task_lower:
                return lang
        
        # Default to Python
        return "python"
    
    # Convenience methods
    def write(self, requirement: str, language: str = "python") -> str:
        """Write code for a requirement."""
        result = self._write_code(f"Write {language} code: {requirement}")
        return result.get("output", "")
    
    def debug(self, code: str, error: str = "") -> str:
        """Debug code."""
        result = self._debug_code("Debug this code", {"code": code, "error": error})
        return result.get("output", "")
    
    def explain(self, code: str) -> str:
        """Explain code."""
        result = self._explain_code("Explain this code", {"code": code})
        return result.get("output", "")
    
    def run(self, code: str) -> Dict[str, Any]:
        """Execute Python code."""
        return self._execute_code(code, "Run code")


# Global instance
coder_agent = CoderAgent()
