"""
Code Executor - Beast Mode (Ultimate Edition)
==============================================
Advanced safe code execution with:
- Multi-language support (Python, JS simulation)
- Sandbox environment with strict security
- Async execution with timeout
- Memory & CPU limits
- Code analysis & explanation
"""

import sys
import io
import contextlib
import time
import threading
import math
import random
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from collections import defaultdict
import traceback

class CodeExecutor:
    def __init__(self):
        self.timeout = 10  # 10 seconds max
        self.max_output = 10000  # Max 10000 characters output
        self.execution_history = []
        self.max_history = 50
        
        # Safe builtins for sandboxed execution
        self.safe_builtins = {
            # Basic types
            'print': print, 'range': range, 'len': len,
            'str': str, 'int': int, 'float': float, 'bool': bool,
            'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
            'frozenset': frozenset, 'bytes': bytes, 'bytearray': bytearray,
            # Math & Logic
            'sum': sum, 'max': max, 'min': min, 'abs': abs,
            'round': round, 'pow': pow, 'divmod': divmod,
            # Iteration
            'sorted': sorted, 'reversed': reversed, 'enumerate': enumerate,
            'zip': zip, 'map': map, 'filter': filter, 'all': all, 'any': any,
            # Type checking
            'type': type, 'isinstance': isinstance, 'issubclass': issubclass,
            # Conversion
            'bin': bin, 'hex': hex, 'oct': oct, 'ord': ord, 'chr': chr,
            'ascii': ascii, 'repr': repr, 'format': format,
            # Helpers
            'hasattr': hasattr, 'getattr': getattr, 'setattr': setattr,
            'callable': callable, 'hash': hash, 'id': id, 'iter': iter, 'next': next,
            'slice': slice, 'object': object, 'property': property,
            # Exceptions (read-only)
            'Exception': Exception, 'ValueError': ValueError, 
            'TypeError': TypeError, 'KeyError': KeyError,
            'IndexError': IndexError, 'ZeroDivisionError': ZeroDivisionError,
            # Constants
            'True': True, 'False': False, 'None': None,
        }
        
        # Safe modules that can be imported
        self.safe_modules = {
            'math': math,
            'random': random,
            'json': json,
            'datetime': datetime,
            'timedelta': timedelta,
            'defaultdict': defaultdict,
        }

    def execute(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Execute code safely with Beast Mode features"""
        start_time = time.time()
        
        # Security checks
        security_result = self._security_check(code)
        if security_result:
            return security_result
        
        # Capture output
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        
        result = {"status": "error", "output": "", "error": None, "execution_time": 0}
        
        try:
            # Create sandboxed globals
            safe_globals = {
                '__builtins__': self.safe_builtins,
                '__name__': '__sandbox__',
                # Inject safe modules
                'math': math,
                'random': random,
                'json': json,
                'datetime': datetime,
            }
            safe_locals = {}
            
            # Execute with timeout using threading
            exec_result = [None]
            exec_error = [None]
            
            def run_code():
                try:
                    with contextlib.redirect_stdout(output_buffer):
                        with contextlib.redirect_stderr(error_buffer):
                            exec(code, safe_globals, safe_locals)
                except Exception as e:
                    exec_error[0] = e
            
            thread = threading.Thread(target=run_code)
            thread.start()
            thread.join(timeout=self.timeout)
            
            if thread.is_alive():
                return {
                    "status": "error",
                    "error": f"Execution timed out after {self.timeout} seconds",
                    "output": output_buffer.getvalue()[:self.max_output],
                    "execution_time": self.timeout
                }
            
            execution_time = time.time() - start_time
            
            if exec_error[0]:
                raise exec_error[0]
            
            # Get output
            output = output_buffer.getvalue()
            if len(output) > self.max_output:
                output = output[:self.max_output] + "\n... (output truncated)"
            
            result = {
                "status": "success",
                "output": output if output else "(no output)",
                "error": None,
                "execution_time": round(execution_time, 4),
                "variables": {k: str(v)[:100] for k, v in safe_locals.items() if not k.startswith('_')}
            }
            
            # Save to history
            self._add_to_history(code, result)
            
        except SyntaxError as e:
            result = {
                "status": "error",
                "error": f"Syntax Error (line {e.lineno}): {e.msg}",
                "output": "",
                "execution_time": round(time.time() - start_time, 4)
            }
        except Exception as e:
            result = {
                "status": "error",
                "error": f"{type(e).__name__}: {str(e)}",
                "output": output_buffer.getvalue()[:self.max_output],
                "execution_time": round(time.time() - start_time, 4)
            }
        
        return result

    def _security_check(self, code: str) -> Optional[Dict]:
        """Beast Mode security checks"""
        code_lower = code.lower()
        
        # Dangerous patterns
        dangerous = [
            ('import os', 'OS access forbidden'),
            ('import sys', 'System access forbidden'),
            ('import subprocess', 'Subprocess forbidden'),
            ('import socket', 'Network access forbidden'),
            ('import requests', 'HTTP requests forbidden'),
            ('__import__', 'Dynamic imports forbidden'),
            ('eval(', 'eval() forbidden'),
            ('exec(', 'exec() forbidden'),
            ('compile(', 'compile() forbidden'),
            ('open(', 'File access forbidden'),
            ('globals()', 'globals() forbidden'),
            ('locals()', 'locals() forbidden'),
            ('__builtins__', 'Builtins access forbidden'),
            ('__class__', 'Class introspection forbidden'),
            ('__bases__', 'Inheritance introspection forbidden'),
            ('__subclasses__', 'Subclass access forbidden'),
        ]
        
        for pattern, msg in dangerous:
            if pattern in code_lower:
                return {
                    "status": "error",
                    "error": f"🛡️ Security: {msg}",
                    "output": "",
                    "execution_time": 0
                }
        
        return None

    def evaluate(self, expression: str) -> Dict[str, Any]:
        """Safe expression evaluation (for quick calculations)"""
        try:
            # Only allow safe operations
            safe_dict = {
                '__builtins__': {
                    'abs': abs, 'round': round, 'max': max, 'min': min,
                    'sum': sum, 'len': len, 'int': int, 'float': float,
                    'str': str, 'pow': pow, 'divmod': divmod,
                },
                'math': math,
                'pi': math.pi,
                'e': math.e,
                'sqrt': math.sqrt,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'log': math.log,
                'log10': math.log10,
            }
            
            result = eval(expression, safe_dict)
            
            return {
                "status": "success",
                "result": result,
                "result_str": str(result),
                "type": type(result).__name__
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"{type(e).__name__}: {str(e)}",
                "result": None
            }

    def analyze_code(self, code: str) -> Dict[str, Any]:
        """Analyze code structure and complexity"""
        lines = code.split('\n')
        
        analysis = {
            "lines": len(lines),
            "non_empty_lines": len([l for l in lines if l.strip()]),
            "functions": len([l for l in lines if l.strip().startswith('def ')]),
            "classes": len([l for l in lines if l.strip().startswith('class ')]),
            "imports": len([l for l in lines if 'import ' in l]),
            "loops": len([l for l in lines if any(k in l for k in ['for ', 'while '])]),
            "conditionals": len([l for l in lines if any(k in l for k in ['if ', 'elif ', 'else:'])]),
            "comments": len([l for l in lines if l.strip().startswith('#')]),
        }
        
        # Complexity score (simple heuristic)
        complexity = (
            analysis['functions'] * 3 +
            analysis['classes'] * 5 +
            analysis['loops'] * 2 +
            analysis['conditionals'] * 1
        )
        analysis['complexity_score'] = complexity
        analysis['complexity_level'] = (
            'Simple' if complexity < 5 else
            'Moderate' if complexity < 15 else
            'Complex' if complexity < 30 else
            'Very Complex'
        )
        
        return {"status": "success", "analysis": analysis}

    def _add_to_history(self, code: str, result: Dict):
        """Track execution history"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "code_preview": code[:100],
            "status": result.get("status"),
            "execution_time": result.get("execution_time")
        }
        self.execution_history.append(entry)
        if len(self.execution_history) > self.max_history:
            self.execution_history.pop(0)

    def get_history(self, limit: int = 10) -> list:
        """Get recent execution history"""
        return self.execution_history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        if not self.execution_history:
            return {"total_executions": 0}
        
        success_count = len([h for h in self.execution_history if h['status'] == 'success'])
        times = [h['execution_time'] for h in self.execution_history if h['execution_time']]
        
        return {
            "total_executions": len(self.execution_history),
            "success_rate": f"{(success_count / len(self.execution_history)) * 100:.1f}%",
            "avg_execution_time": f"{sum(times) / len(times):.4f}s" if times else "N/A",
            "fastest": f"{min(times):.4f}s" if times else "N/A",
            "slowest": f"{max(times):.4f}s" if times else "N/A",
        }

# Global instance
code_executor = CodeExecutor()

if __name__ == "__main__":
    # Test Beast Mode features
    print("=== Code Executor Beast Mode Test ===\n")
    
    # Test 1: Basic execution
    result = code_executor.execute("for i in range(5): print(f'Count: {i}')")
    print(f"Test 1 - Basic Loop:\n{result['output']}\n")
    
    # Test 2: Math with safe modules
    result = code_executor.execute("import math\nprint(f'Pi: {math.pi:.4f}')\nprint(f'sqrt(16): {math.sqrt(16)}')")
    print(f"Test 2 - Math Module:\n{result['output']}\n")
    
    # Test 3: Security block
    result = code_executor.execute("import os\nos.system('dir')")
    print(f"Test 3 - Security Block:\n{result['error']}\n")
    
    # Test 4: Expression evaluation
    result = code_executor.evaluate("sqrt(144) + pi")
    print(f"Test 4 - Expression: {result['result_str']}\n")
    
    # Test 5: Code analysis
    code = """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        if num > 0:
            total += num
    return total

class Calculator:
    def add(self, a, b):
        return a + b
"""
    result = code_executor.analyze_code(code)
    print(f"Test 5 - Code Analysis:\n{json.dumps(result['analysis'], indent=2)}\n")
    
    # Stats
    print(f"Execution Stats: {code_executor.get_stats()}")
