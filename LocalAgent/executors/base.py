"""
Kai Local Agent - Base Executor
================================
Abstract base class for all command executors.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseExecutor(ABC):
    """
    Base class for command executors.
    Each executor handles one specific command type.
    """
    
    @property
    @abstractmethod
    def command_name(self) -> str:
        """Return the command name this executor handles."""
        pass
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the command with given parameters.
        
        Args:
            params: Command parameters (already validated)
        
        Returns:
            Dict with:
                - status: "success" or "error"
                - message: Human-readable result message
                - data: Optional additional data
        """
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Optional additional validation. Override if needed.
        By default, assumes params are already validated by schemas.
        """
        return True
