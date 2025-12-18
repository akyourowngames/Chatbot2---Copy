"""
Execution State Manager - BEAST MODE
=====================================
Central Nervous System for KAI. Handles cross-module communication and action memory.
"""

from typing import Any, Dict, Optional, List
import time

class ExecutionState:
    _instance = None
    
    def __init__(self):
        self._state: Dict[str, Any] = {
            "last_screenshot": None,
            "last_file_created": None,
            "last_web_search": None,
            "last_active_app": None,
            "now_playing": None,
            "session_start": time.time(),
            "action_history": []
        }
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ExecutionState()
        return cls._instance

    def set(self, key: str, value: Any):
        """Set state and log action"""
        self._state[key] = value
        # Action Logging
        self._state["action_history"].append({
            "t": time.time(),
            "k": key,
            "v": str(value)[:100]
        })
        if len(self._state["action_history"]) > 50:
            self._state["action_history"].pop(0)

    def get(self, key: str) -> Optional[Any]:
        return self._state.get(key)
    
    def get_all(self):
        return self._state

    def reset(self):
        """Reset temporary session state"""
        self._state["action_history"] = []
        return "Session Reset"

# Global helper functions
def set_state(key: str, value: Any):
    ExecutionState.get_instance().set(key, value)

def get_state(key: str) -> Optional[Any]:
    return ExecutionState.get_instance().get(key)
