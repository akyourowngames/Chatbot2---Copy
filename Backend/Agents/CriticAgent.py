"""
Critic Agent - Quality Assurance
================================
Reviews outputs for accuracy, logic, and safety.
"""

from Backend.Agents.AutonomousAgent import AutonomousAgent

class CriticAgent(AutonomousAgent):
    """
    Critic agent that evaluates plans and outputs.
    """
    def __init__(self):
        super().__init__(
            name="Critic Agent",
            specialty="Quality assurance, logic verification, hallucination check",
            description="I review content for errors, logical fallacies, and potential hallucinations."
        )
    
    # Critic mainly uses internal knowledge, but could use search tools to verify facts
    # For now, it logic-checks via LLM.

critic_agent = CriticAgent()
