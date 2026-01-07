"""
Multi-Agent System - Agent Package
===================================
KAI's team of specialist AI agents working together.
"""

from Backend.Agents.BaseAgent import BaseAgent
from Backend.Agents.AgentOrchestrator import AgentOrchestrator, run_multi_agent_task
from Backend.Agents.ResearchAgent import research_agent
from Backend.Agents.WriterAgent import writer_agent
from Backend.Agents.AnalystAgent import analyst_agent
from Backend.Agents.CoderAgent import coder_agent

__all__ = [
    'BaseAgent', 
    'AgentOrchestrator', 
    'run_multi_agent_task',
    'research_agent',
    'writer_agent', 
    'analyst_agent',
    'coder_agent'
]
