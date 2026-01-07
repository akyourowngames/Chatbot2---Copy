"""
Automation State - System State Awareness & Memory
===================================================
Tracks current system state and recent automation history.

Responsibilities:
    - Track current volume, brightness, open apps, focused window
    - Maintain session-level automation memory
    - Enable "already done" detection
    - Enable follow-ups like "increase it more"
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import deque
import threading


class AutomationState:
    """
    Lightweight state tracker for automation intelligence.
    
    State is updated via agent heartbeats and execution results.
    Memory is ephemeral (session-only, expires quickly).
    """
    
    def __init__(self):
        """Initialize state tracker."""
        self._lock = threading.Lock()
        
        # Current system state (updated by agent)
        self._system_state: Dict[str, Any] = {
            "volume": None,
            "brightness": None,
            "muted": None,
            "open_apps": [],
            "focused_window": None,
            "last_update": None,
        }
        
        # Automation memory (session-level, expires)
        self._memory: deque = deque(maxlen=10)  # Last 10 actions
        self._memory_expiry = timedelta(minutes=5)  # Memory expires after 5 min
        
        # Dimension tracking for follow-ups
        self._last_dimension: Optional[str] = None
        self._last_value: Optional[Any] = None
    
    # ==================== STATE MANAGEMENT ====================
    
    def update_state(self, state_update: Dict[str, Any]) -> None:
        """
        Update system state from agent heartbeat.
        
        Args:
            state_update: Dict with any of: volume, brightness, muted, open_apps, focused_window
        """
        with self._lock:
            for key in ["volume", "brightness", "muted", "open_apps", "focused_window"]:
                if key in state_update:
                    self._system_state[key] = state_update[key]
            self._system_state["last_update"] = datetime.now().isoformat()
    
    def get_state(self) -> Dict[str, Any]:
        """Get current system state."""
        with self._lock:
            return self._system_state.copy()
    
    def is_state_fresh(self, max_age_seconds: int = 60) -> bool:
        """Check if state data is recent enough."""
        with self._lock:
            last_update = self._system_state.get("last_update")
            if not last_update:
                return False
            try:
                update_time = datetime.fromisoformat(last_update)
                age = (datetime.now() - update_time).total_seconds()
                return age < max_age_seconds
            except:
                return False
    
    # ==================== MEMORY MANAGEMENT ====================
    
    def record_action(self, action: str, dimension: str, 
                      value_before: Any = None, value_after: Any = None,
                      target: str = None) -> None:
        """
        Record an automation action to memory.
        
        Args:
            action: Action performed (e.g., "volume_up", "open_app")
            dimension: What was affected (e.g., "volume", "app", "brightness")
            value_before: State before action
            value_after: State after action
            target: Target of action (e.g., "notepad")
        """
        with self._lock:
            memory_entry = {
                "action": action,
                "dimension": dimension,
                "value_before": value_before,
                "value_after": value_after,
                "target": target,
                "timestamp": datetime.now(),
                "expires_at": datetime.now() + self._memory_expiry,
            }
            self._memory.append(memory_entry)
            
            # Update dimension tracking for follow-ups
            self._last_dimension = dimension
            self._last_value = value_after
    
    def get_last_action(self) -> Optional[Dict]:
        """Get the most recent non-expired action."""
        with self._lock:
            now = datetime.now()
            # Iterate from most recent
            for entry in reversed(self._memory):
                if entry["expires_at"] > now:
                    return entry
            return None
    
    def get_last_dimension(self) -> Optional[str]:
        """Get the dimension of the last action (for follow-ups)."""
        with self._lock:
            last = self.get_last_action()
            return last["dimension"] if last else None
    
    def clear_expired(self) -> int:
        """Clear expired memory entries. Returns count cleared."""
        with self._lock:
            now = datetime.now()
            original_len = len(self._memory)
            self._memory = deque(
                [e for e in self._memory if e["expires_at"] > now],
                maxlen=10
            )
            return original_len - len(self._memory)
    
    # ==================== FOLLOW-UP RESOLUTION ====================
    
    def resolve_follow_up(self, query: str) -> Optional[Dict]:
        """
        Resolve vague follow-up queries using memory.
        
        Examples:
            "increase it more" → {dimension: "volume", action: "volume_up"}
            "undo that" → {undo: True, original_action: ...}
            "lower it" → {dimension: last_dimension, action: "down"}
        
        Returns:
            Dict with resolved context, or None if not a follow-up
        """
        query_lower = query.lower()
        
        # Check for follow-up indicators
        follow_up_patterns = {
            "it": ["increase it", "decrease it", "lower it", "raise it", "more", "less"],
            "that": ["undo that", "reverse that", "cancel that"],
            "again": ["do that again", "again", "one more time"],
        }
        
        is_follow_up = False
        for pronoun, patterns in follow_up_patterns.items():
            if any(p in query_lower for p in patterns):
                is_follow_up = True
                break
        
        if not is_follow_up:
            return None
        
        # Get last action for context
        last_action = self.get_last_action()
        if not last_action:
            return None
        
        result = {
            "is_follow_up": True,
            "last_action": last_action,
            "dimension": last_action["dimension"],
            "target": last_action["target"],
        }
        
        # Determine follow-up type
        if any(p in query_lower for p in ["undo", "reverse", "cancel"]):
            result["type"] = "undo"
            result["restore_value"] = last_action["value_before"]
        elif any(p in query_lower for p in ["more", "increase", "raise", "up", "higher"]):
            result["type"] = "increase"
        elif any(p in query_lower for p in ["less", "decrease", "lower", "down", "reduce"]):
            result["type"] = "decrease"
        elif any(p in query_lower for p in ["again", "one more"]):
            result["type"] = "repeat"
        else:
            result["type"] = "continue"
        
        return result
    
    # ==================== STATE QUERIES ====================
    
    def is_app_open(self, app_name: str) -> bool:
        """Check if an app is currently open."""
        with self._lock:
            open_apps = self._system_state.get("open_apps", [])
            return app_name.lower() in [a.lower() for a in open_apps]
    
    def get_volume(self) -> Optional[int]:
        """Get current volume level."""
        with self._lock:
            return self._system_state.get("volume")
    
    def get_brightness(self) -> Optional[int]:
        """Get current brightness level."""
        with self._lock:
            return self._system_state.get("brightness")
    
    def is_muted(self) -> Optional[bool]:
        """Check if system is muted."""
        with self._lock:
            return self._system_state.get("muted")
    
    def get_focused_window(self) -> Optional[str]:
        """Get currently focused window."""
        with self._lock:
            return self._system_state.get("focused_window")


# Global instance
automation_state = AutomationState()


# ==================== CONVENIENCE FUNCTIONS ====================

def update_system_state(state: Dict) -> None:
    """Update system state from agent."""
    automation_state.update_state(state)

def get_system_state() -> Dict:
    """Get current system state."""
    return automation_state.get_state()

def record_automation(action: str, dimension: str, **kwargs) -> None:
    """Record an automation action."""
    automation_state.record_action(action, dimension, **kwargs)

def resolve_follow_up(query: str) -> Optional[Dict]:
    """Resolve a follow-up query."""
    return automation_state.resolve_follow_up(query)

def is_app_open(app: str) -> bool:
    """Check if app is open."""
    return automation_state.is_app_open(app)
