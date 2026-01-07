"""
Planner Agent - Swarm Strategist
================================
Analyzes complex requests and breaks them down into actionable subtasks.
Does not execute tasks itself, but directs the swarm.
"""

from Backend.Agents.AutonomousAgent import AutonomousAgent
import json

class PlannerAgent(AutonomousAgent):
    """
    Strategic agent that plans the execution path for the swarm.
    """
    def __init__(self):
        super().__init__(
            name="Planner Agent",
            specialty="Strategic planning, task decomposition, dependency management",
            description="I break complex goals into clear, ordered steps for other agents to execute."
        )

    def _get_system_prompt(self) -> str:
        return """You are the Planner Agent, the strategist and architect of the AI swarm.
Your goal is to break down a complex user request into a specific set of subtasks.

Available Agent Specialists:
- Research Agent: Web search, fact finding.
- Writer Agent: Content creation, drafting.
- Coder Agent: Writing code, debugging, execution.
- Analyst Agent: Reviewing, fact-checking, logic verification.
- Creative Agent: Image generation, creative ideas.

OUTPUT FORMAT:
You must output a valid JSON plan in the following format inside a code block:

```json
{
  "goal": "Brief summary of the goal",
  "steps": [
    {
      "id": 1,
      "agent": "Agent Name",
      "instruction": "Specific instruction for this agent",
      "dependency": null  // or ID of previous step if it must wait
    },
    ...
  ]
}
```

Do not output "THOUGHT/ACTION" like a normal agent. Your ACTION is to produce this plan.
Just analyze the request and provide the JSON plan.
"""

    def execute(self, task: str, context: dict = None) -> dict:
        """
        Override execute to produce a plan instead of a standard ReAct loop response.
        """
        self.state = "thinking"
        
        prompt = f"Create a step-by-step plan for this request:\n{task}"
        
        # We can reuse the BaseAgent think method or the parent's llm directly
        # Since Planner is a specialized "One-Shot" thinker usually, we don't strictly need the loop
        # But we can use the loop if we want it to "Think" then "Final Answer" the plan.
        
        # Let's use a simpler direct call for the Planner to ensure strict JSON output
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm(messages, inject_memory=False)
            
            # Extract JSON
            import re
            json_match = re.search(r'```json\n?(.*?)```', response, re.DOTALL)
            if json_match:
                plan_json = json_match.group(1)
                plan = json.loads(plan_json)
                return {
                    "status": "success",
                    "agent": self.name,
                    "output": plan,
                    "raw_response": response
                }
            else:
                 # Fallback if no code block
                return {
                    "status": "success",
                    "agent": self.name,
                    "output": response, # Raw text plan
                    "note": "Could not parse JSON, returning raw text plan" 
                }
                
        except Exception as e:
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e)
            }

planner_agent = PlannerAgent()
