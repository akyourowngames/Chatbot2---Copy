from typing import Dict, Any
from .base import Tool

class MathTool(Tool):
    def __init__(self):
        super().__init__(
            name="math_solver",
            description="Solve mathematical equations or calculate expressions.",
            domain="utilities",
            priority="MEDIUM",
            allowed_intents=["math", "conversation"]
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Equation (e.g. '2x + 5 = 15') or Expression (e.g. '5 * 10')"
                },
                "action": {
                    "type": "string",
                    "enum": ["solve_equation", "calculate"],
                    "description": "Type of math problem"
                }
            },
            "required": ["query"]
        }

    def execute(self, query: str, action: str = "calculate", **kwargs) -> str:
        try:
            from Backend.MathSolver import math_solver
            
            # Auto-detect if action not provided or ambiguous?
            # For now trust the LLM's choice
            
            if action == "solve_equation" or "=" in query:
                result = math_solver.solve_equation(query)
                if result.get("status") == "success":
                   steps = "\n".join(result.get("steps", []))
                   if "solution" in result:
                       return f"Solution: {result['solution']}\nSteps:\n{steps}"
                   else: # Quadratic
                       return f"Solutions: {result.get('solutions')}\nSteps:\n{steps}"
                
                # If equation solver failed, maybe try calculate if it was simpler?
                if result.get("status") != "success":
                    return f"Could not solve equation: {result.get('error')}"

            else:
                # Calculate
                result = math_solver.calculate(query)
                if result.get("status") == "success":
                    return f"Result: {result.get('result')}"
                else:
                    return f"Calculation Failed: {result.get('error')}"

            return "Unknown math action"

        except ImportError:
            return "Math module not found."
        except Exception as e:
            return f"Math Error: {str(e)}"
