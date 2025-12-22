"""
Action History Manager
======================
Tracks the last significant action performed by the AI.
Used to enable "retry", "do it again", or "fix it" commands.
"""

import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ActionContext:
    def __init__(self, action_type: str, params: Dict[str, Any], description: str = ""):
        self.action_type = action_type
        self.params = params
        self.description = description
        self.status = "pending"
        self.timestamp = time.time()
        self.error = None

    def to_dict(self):
        return {
            "type": self.action_type,
            "params": self.params,
            "desc": self.description,
            "status": self.status,
            "time": self.timestamp
        }

class ActionHistoryManager:
    """
    Singleton to track the global state of the last action.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ActionHistoryManager, cls).__new__(cls)
            cls._instance.last_action = None
            cls._instance.history = []
        return cls._instance

    def log_action(self, action_type: str, params: Dict[str, Any], description: str = ""):
        """Record a new action starting."""
        context = ActionContext(action_type, params, description)
        self.last_action = context
        self.history.append(context)
        # Keep history small
        if len(self.history) > 10:
            self.history.pop(0)
        
        logger.info(f"[ACTION] Logged: {action_type} - {description}")
        return context

    def update_status(self, status: str, error: str = None):
        """Update status of the last action."""
        if self.last_action:
            self.last_action.status = status
            self.last_action.error = error
            logger.info(f"[ACTION] Status updated: {status}")

    def get_last_action(self) -> Optional[ActionContext]:
        """Get the most recent action context."""
        return self.last_action

    def clear(self):
        self.last_action = None
        self.history = []

# Global instance
action_history = ActionHistoryManager()
