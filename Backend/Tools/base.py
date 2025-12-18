from abc import ABC, abstractmethod
from typing import Dict, Any, List

class Tool(ABC):
    def __init__(self, name: str, description: str, domain: str = "general", priority: str = "LOW", allowed_intents: List[str] = None):
        self.name = name
        self.description = description
        self.domain = domain
        self.priority = priority
        self.allowed_intents = allowed_intents or []
        
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """
        Return JSON Schema for the tool's parameters.
        Example:
        {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["on", "off"]}
            },
            "required": ["action"]
        }
        """
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the tool with the given arguments."""
        pass

    def to_schema(self) -> Dict[str, Any]:
        """Return the schema format expected by LLMs (e.g., OpenAI/Groq)."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
