from typing import Dict, Any
from .base import Tool
import asyncio

class WorkflowTool(Tool):
    def __init__(self):
        super().__init__(
            name="workflow_execution",
            description="Run complex, multi-step workflows like 'morning routine', 'work mode', 'cleaning mode'.",
            domain="workflow",
            priority="MEDIUM",
            allowed_intents=["workflow", "conversation"]
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "workflow_name": {
                    "type": "string",
                    "description": "Name of the workflow to run"
                }
            },
            "required": ["workflow_name"]
        }

    def execute(self, workflow_name: str, **kwargs) -> str:
        try:
            # We need to import the engine.
            # Assuming Backend.WorkflowEngine exists as in api_server.py
            from Backend.WorkflowEngine import WorkflowEngine
            
            # Since tools are synchronous in my BaseTool design (for now), but WorkflowEngine is async...
            # We run it via asyncio.run
            
            async def run_wf():
                 engine = WorkflowEngine() # Init (loads definitions)
                 return await engine.execute_workflow(workflow_name)

            result = asyncio.run(run_wf())
            return f"Workflow Result: {result}"
            
        except Exception as e:
            return f"Workflow Error: {str(e)}"
