"""
Automation Governor - Central Control for Automation Decisions
===============================================================
The brain's decision gate that controls WHEN and HOW MUCH automation happens.

Modes:
    MODE 0 (CHAT_ONLY): No automation, route to chat
    MODE 1 (SUGGEST_ONLY): Offer to automate, wait for approval
    MODE 2 (SINGLE_SAFE_ACTION): Execute single safe action immediately
    MODE 3 (MULTI_STEP_AUTOMATION): Confirm once, then execute sequence

Mental Model:
    Kai = Brain (this governor decides)
    Local Agent = Body (executes only)
    WebSocket = Nervous System
"""

from enum import IntEnum
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class AutomationMode(IntEnum):
    """Automation execution modes."""
    CHAT_ONLY = 0           # No automation, pure conversation
    SUGGEST_ONLY = 1        # Suggest automation, wait for user approval
    SINGLE_SAFE_ACTION = 2  # Execute immediately (single, safe)
    MULTI_STEP = 3          # Confirm once, then execute sequence


# ==================== SAFETY WALLS (NON-NEGOTIABLE) ====================

BLOCKED_ACTIONS = {
    # File destruction
    "delete_file", "delete_folder", "format_drive", "empty_recycle_bin",
    "rm_rf", "wipe", "shred",
    
    # Software installation
    "install_app", "uninstall_app", "install_software", "remove_software",
    "pip_install", "npm_install",  # Only blocked for system packages
    
    # Security modifications
    "change_password", "modify_firewall", "disable_antivirus",
    "modify_security", "change_permissions", "grant_admin",
    
    # Credential handling
    "login", "enter_credentials", "enter_password", "type_password",
    "authenticate", "sign_in",
    
    # Privacy violations
    "read_private_files", "access_browser_passwords", "read_emails",
    "access_messages", "read_documents", "export_data",
    
    # System critical
    "shutdown", "restart", "sleep", "hibernate",
    "registry_edit", "system_restore", "bios_access",
}

BLOCKED_TARGETS = {
    # Sensitive directories
    "system32", "windows", "program files", "appdata",
    "passwords", "credentials", "private", "secrets",
    ".ssh", ".gnupg", ".aws", ".env",
}


class AutomationGovernor:
    """
    Central governor that decides automation mode based on multiple signals.
    
    Decision Inputs:
        - Confidence score from classifier
        - Safety level of actions
        - User phrasing (command vs vague)
        - Current system state
        - Recent automation history
    """
    
    def __init__(self):
        """Initialize the governor."""
        self.confidence_thresholds = {
            "chat_only": 0.30,      # Below this → MODE 0
            "suggest": 0.50,        # Below this → MODE 1
            "execute": 0.65,        # Above this → MODE 2/3
        }
        
        # Command indicators (strong intent)
        self.command_verbs = {
            "open", "close", "launch", "start", "run",
            "increase", "decrease", "set", "change",
            "mute", "unmute", "lock", "screenshot",
            "switch", "focus", "minimize", "maximize",
            "type", "write", "create", "save",
        }
        
        # Vague indicators (weak intent)
        self.vague_phrases = {
            "maybe", "perhaps", "could you", "would you",
            "i think", "possibly", "might", "kind of",
            "something like", "somehow", "help me with",
        }
        
        # Question indicators (no automation)
        self.question_indicators = {
            "what is", "what's", "how does", "why is",
            "explain", "tell me about", "describe",
            "can you explain", "what do you think",
        }
    
    def decide(self, 
               classification: Dict, 
               query: str,
               system_state: Dict = None,
               automation_memory: Dict = None) -> Dict:
        """
        Make the governor decision.
        
        Args:
            classification: Result from AutomationIntentClassifier
            query: Original user query
            system_state: Current system state (optional)
            automation_memory: Recent automation history (optional)
            
        Returns:
            Dict with:
                - mode: AutomationMode (0-3)
                - action: What to do next
                - reason: Why this mode was chosen
                - payload: Automation payload (if applicable)
                - confirmation_prompt: Text to show user (if MODE 1 or needs confirm)
        """
        query_lower = query.lower()
        
        # === STEP 0: Check if automation is even detected ===
        if not classification.get("is_automation"):
            return self._mode_chat_only("Not an automation request")
        
        # === STEP 1: Safety Wall Check ===
        safety_result = self._check_safety_walls(classification)
        if safety_result["blocked"]:
            return self._mode_blocked(safety_result["reason"])
        
        # === STEP 2: Check if already satisfied ===
        if system_state:
            already_done = self._check_already_satisfied(classification, system_state)
            if already_done["satisfied"]:
                return self._mode_already_done(already_done["message"])
        
        # === STEP 3: Analyze user intent strength ===
        intent_strength = self._analyze_intent_strength(query_lower)
        
        # === STEP 4: Get confidence and safety ===
        confidence = classification.get("confidence", 0.5)
        safety_level = classification.get("safety_level", "medium")
        steps = classification.get("steps", [])
        num_steps = len(steps)
        
        # === STEP 5: Mode Selection Logic ===
        
        # Check for questions (always chat)
        if self._is_question(query_lower):
            return self._mode_chat_only("User is asking a question, not commanding")
        
        # Very low confidence → Chat only
        if confidence < self.confidence_thresholds["chat_only"]:
            return self._mode_chat_only(f"Confidence too low ({confidence:.2f})")
        
        # Low confidence OR vague phrasing → Suggest only
        if confidence < self.confidence_thresholds["suggest"] or intent_strength == "vague":
            return self._mode_suggest(classification, query)
        
        # Medium confidence, unclear intent → Suggest
        if confidence < self.confidence_thresholds["execute"] and intent_strength != "command":
            return self._mode_suggest(classification, query)
        
        # High safety → Always confirm
        if safety_level == "high":
            return self._mode_confirm_required(classification, "High-risk action requires confirmation")
        
        # Multi-step → Confirm once
        if num_steps > 1:
            return self._mode_multi_step(classification)
        
        # Single safe action with high confidence → Execute
        if confidence >= self.confidence_thresholds["execute"] and safety_level in ["low", "medium"]:
            return self._mode_single_action(classification)
        
        # Fallback: Suggest
        return self._mode_suggest(classification, query)
    
    def _check_safety_walls(self, classification: Dict) -> Dict:
        """Check if any action is blocked by safety walls."""
        steps = classification.get("steps", [])
        
        for step in steps:
            action = step.get("action", "").lower()
            target = str(step.get("target", "")).lower()
            params = step.get("parameters", {})
            
            # Check blocked actions
            if action in BLOCKED_ACTIONS:
                return {
                    "blocked": True,
                    "reason": f"Action '{action}' is not allowed for safety reasons"
                }
            
            # Check blocked targets
            for blocked_target in BLOCKED_TARGETS:
                if blocked_target in target:
                    return {
                        "blocked": True,
                        "reason": f"Cannot automate actions involving '{blocked_target}'"
                    }
            
            # Check parameters for sensitive content
            for key, value in params.items():
                if isinstance(value, str):
                    for blocked in BLOCKED_TARGETS:
                        if blocked in value.lower():
                            return {
                                "blocked": True,
                                "reason": f"Cannot perform actions on sensitive paths"
                            }
        
        return {"blocked": False}
    
    def _check_already_satisfied(self, classification: Dict, state: Dict) -> Dict:
        """Check if the desired state is already achieved."""
        steps = classification.get("steps", [])
        
        for step in steps:
            action = step.get("action", "")
            target = step.get("target", "").lower()
            params = step.get("parameters", {})
            
            # Check open_app
            if action == "open_app":
                open_apps = state.get("open_apps", [])
                if target in [app.lower() for app in open_apps]:
                    return {
                        "satisfied": True,
                        "message": f"✓ {target.title()} is already open"
                    }
            
            # Check mute
            if action == "system_control":
                action_type = params.get("action", "")
                if action_type == "mute" and state.get("muted"):
                    return {"satisfied": True, "message": "🔇 Already muted"}
                if action_type == "unmute" and not state.get("muted"):
                    return {"satisfied": True, "message": "🔊 Already unmuted"}
            
            # Check volume level
            if action == "system_control" and params.get("action") == "set_volume":
                target_level = params.get("level")
                current_level = state.get("volume")
                if target_level and current_level and abs(target_level - current_level) < 5:
                    return {
                        "satisfied": True,
                        "message": f"🔊 Volume is already at {current_level}%"
                    }
        
        return {"satisfied": False}
    
    def _analyze_intent_strength(self, query: str) -> str:
        """Analyze how strongly the user intends automation."""
        # Check for command verbs at start
        words = query.split()
        if words and words[0] in self.command_verbs:
            return "command"
        
        # Check for vague phrases
        for phrase in self.vague_phrases:
            if phrase in query:
                return "vague"
        
        # Check for any command verbs
        for verb in self.command_verbs:
            if verb in query:
                return "moderate"
        
        return "unclear"
    
    def _is_question(self, query: str) -> bool:
        """Check if query is a question (not a command)."""
        for indicator in self.question_indicators:
            if query.startswith(indicator):
                return True
        return query.strip().endswith("?") and "please" not in query
    
    # ==================== MODE BUILDERS ====================
    
    def _mode_chat_only(self, reason: str) -> Dict:
        """Return MODE 0: Route to chat."""
        return {
            "mode": AutomationMode.CHAT_ONLY,
            "action": "route_to_chat",
            "reason": reason,
            "payload": None,
            "confirmation_prompt": None
        }
    
    def _mode_suggest(self, classification: Dict, query: str) -> Dict:
        """Return MODE 1: Suggest automation."""
        goal = classification.get("goal", "perform this action")
        steps = classification.get("steps", [])
        actions = [s.get("action", "") for s in steps]
        
        return {
            "mode": AutomationMode.SUGGEST_ONLY,
            "action": "suggest_and_wait",
            "reason": "Confidence not high enough for immediate execution",
            "payload": classification,
            "confirmation_prompt": f"I can {goal} on your PC. Want me to proceed?",
            "suggested_actions": actions
        }
    
    def _mode_single_action(self, classification: Dict) -> Dict:
        """Return MODE 2: Execute single safe action."""
        return {
            "mode": AutomationMode.SINGLE_SAFE_ACTION,
            "action": "execute_now",
            "reason": "High confidence, single safe action",
            "payload": classification,
            "confirmation_prompt": None,
            "skip_llm": True  # Don't call ChatBot after
        }
    
    def _mode_multi_step(self, classification: Dict) -> Dict:
        """Return MODE 3: Confirm once, then execute."""
        steps = classification.get("steps", [])
        actions = [s.get("action", "") for s in steps]
        
        return {
            "mode": AutomationMode.MULTI_STEP,
            "action": "confirm_then_execute",
            "reason": f"Multi-step automation ({len(steps)} steps)",
            "payload": classification,
            "confirmation_prompt": f"This requires {len(steps)} steps: {', '.join(actions)}. Proceed?",
            "skip_llm": True
        }
    
    def _mode_confirm_required(self, classification: Dict, reason: str) -> Dict:
        """Return mode requiring confirmation."""
        goal = classification.get("goal", "this action")
        
        return {
            "mode": AutomationMode.MULTI_STEP,
            "action": "confirm_required",
            "reason": reason,
            "payload": classification,
            "confirmation_prompt": f"⚠️ {goal} - This needs your confirmation. Proceed?",
            "skip_llm": True
        }
    
    def _mode_blocked(self, reason: str) -> Dict:
        """Return blocked mode with polite refusal."""
        return {
            "mode": AutomationMode.CHAT_ONLY,
            "action": "blocked",
            "reason": reason,
            "payload": None,
            "response": f"I can't do that automatically for safety reasons. {reason}. "
                       f"I can guide you through doing it manually instead.",
            "blocked": True
        }
    
    def _mode_already_done(self, message: str) -> Dict:
        """Return when action is already satisfied."""
        return {
            "mode": AutomationMode.CHAT_ONLY,
            "action": "already_done",
            "reason": "Desired state already achieved",
            "payload": None,
            "response": message,
            "skip_llm": True,
            "already_done": True
        }


# Global instance
automation_governor = AutomationGovernor()


def govern_automation(classification: Dict, query: str, 
                      state: Dict = None, memory: Dict = None) -> Dict:
    """Quick helper to get governor decision."""
    return automation_governor.decide(classification, query, state, memory)
