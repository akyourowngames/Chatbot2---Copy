"""
Automation Intent Classifier - Goal-Based OS Automation Detection
===================================================================
LLM-based classifier that determines if user's goal requires OS-level
interaction and generates structured automation payloads.

Mental Model:
    Kai = Brain (all intelligence)
    Local Agent = Hands (execution only)
    WebSocket = Nerves (communication)

This classifier keeps all decision-making in Kai.
"""

import json
from typing import Dict, List, Optional, Tuple
from Backend.LLM import ChatCompletion


class AutomationIntentClassifier:
    """
    Classifies user goals for automation and generates executable plans.
    
    Key Principles:
    - Goal-based, NOT keyword-based
    - Probabilistic with confidence scores
    - Safety-aware with risk classification
    """
    
    def __init__(self):
        """Initialize the automation classifier."""
        self.confidence_threshold = 0.65  # Below this, ask user
        
        # Safety levels for different action types
        self.action_safety_levels = {
            # Low risk - easily reversible
            "open_app": "low",
            "focus_window": "low",
            "minimize_window": "low",
            "maximize_window": "low",
            
            # Medium risk - affects state but recoverable
            "close_app": "medium",
            "type": "medium",
            "click": "medium",
            "run_command": "medium",
            "write_notepad": "medium",
            "system_control": "medium",  # volume, brightness
            
            # High risk - potentially destructive
            "delete_file": "high",
            "delete_folder": "high",
            "system_settings": "high",
            "shutdown": "high",
            "restart": "high",
        }
        
        # Available actions that local agent can execute
        self.available_actions = [
            "open_app", "close_app", "focus_window",
            "type", "click", "run_command",
            "system_control", "write_notepad", "file_manager",
            "screenshot"
        ]

        
        self.system_prompt = """You are an automation intent classifier for Kai, an AI assistant.
Your job is to determine if a user's goal requires OS-level automation.

AUTOMATION is required when the goal needs:
- Opening/closing applications
- Switching windows or focus
- Typing or clicking in desktop apps
- File system operations (create, move, delete)
- System settings (volume, brightness, lock)
- Running commands or scripts
- Taking screenshots or screen captures

AUTOMATION is NOT required for:
- General conversation/questions
- Web searches (handled by search tool)
- Image generation (handled by image tool)
- Document creation (handled by document tool)
- Information queries (weather, news, etc.)

When AUTOMATION is required, respond with JSON:
{
  "is_automation": true,
  "confidence": 0.0-1.0,
  "goal": "clear description of what user wants",
  "reasoning": "why this requires OS automation",
  "steps": [
    {
      "action": "open_app|close_app|system_control|write_notepad|file_manager|focus_window|screenshot",
      "target": "application or target name (use 'screen' for screenshot)",
      "parameters": {}
    }
  ],
  "safety_level": "low|medium|high",
  "fallback": "what to do if automation fails"
}

IMPORTANT: For system_control actions, use these EXACT parameter formats:
- Volume up: {"action": "volume_up", "target": "volume", "parameters": {"action": "volume_up"}}
- Volume down: {"action": "system_control", "target": "volume", "parameters": {"action": "volume_down"}}
- Set volume: {"action": "system_control", "target": "volume", "parameters": {"action": "set_volume", "level": 50}}
- Mute: {"action": "system_control", "target": "audio", "parameters": {"action": "mute"}}
- Unmute: {"action": "system_control", "target": "audio", "parameters": {"action": "unmute"}}
- Brightness up: {"action": "system_control", "target": "brightness", "parameters": {"action": "brightness_up"}}
- Brightness down: {"action": "system_control", "target": "brightness", "parameters": {"action": "brightness_down"}}
- Set brightness: {"action": "system_control", "target": "brightness", "parameters": {"action": "set_brightness", "level": 70}}
- Lock screen: {"action": "system_control", "target": "screen", "parameters": {"action": "lock_screen"}}

For open_app actions, use the app name as target:
- Open notepad: {"action": "open_app", "target": "notepad", "parameters": {}}
- Open chrome: {"action": "open_app", "target": "chrome", "parameters": {}}
- Close app: {"action": "close_app", "target": "chrome", "parameters": {}}
- Screenshot: {"action": "screenshot", "target": "screen", "parameters": {}}

When NOT automation, respond with:
{
  "is_automation": false,
  "confidence": 0.0-1.0,
  "reasoning": "why this is not automation",
  "suggested_route": "chat|tool_name"
}

RULES:
- Be GOAL-based, not keyword-based
- "search for X" → NOT automation (web search tool)
- "open chrome and search X" → AUTOMATION (needs to open app)
- "write a poem" → NOT automation (chat response)
- "write a poem in notepad" → AUTOMATION (needs to open notepad and type)
- Prefer atomic, reversible actions
- Never include UI coordinates - use semantic targets
- Set safety_level based on risk of the actions

Respond with ONLY valid JSON, no markdown."""


    def classify(self, query: str, context: Dict = None) -> Dict:
        """
        Classify if a query requires automation.
        
        Args:
            query: User's natural language query
            context: Optional context (chat history, current state)
            
        Returns:
            Dict with classification result and automation payload if needed
        """
        # Build context string
        context_str = ""
        if context:
            if context.get("history"):
                recent = context["history"][-3:]
                context_str = "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', '')}" 
                    for msg in recent
                ])
                context_str = f"\nRecent conversation:\n{context_str}\n"
        
        prompt = f"""{context_str}
User query: {query}

Analyze if this requires OS-level automation:"""

        try:
            response = ChatCompletion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=self.system_prompt,
                model="llama-3.1-8b-instant"  # Fast model for classification
            )
            
            # Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            result = json.loads(response)
            
            # Validate and enhance result
            if result.get("is_automation"):
                result = self._enhance_automation_result(result, query)
            
            print(f"[AUTOMATION-CLASSIFIER] Query: '{query[:50]}...' → "
                  f"Automation: {result.get('is_automation')} "
                  f"(conf: {result.get('confidence', 0):.2f})")
            
            return result
            
        except Exception as e:
            print(f"[AUTOMATION-CLASSIFIER] Error: {e}")
            # Fallback: not automation
            return {
                "is_automation": False,
                "confidence": 0.5,
                "reasoning": f"Classification failed: {str(e)}",
                "suggested_route": "chat"
            }
    
    def _enhance_automation_result(self, result: Dict, query: str) -> Dict:
        """
        Enhance and validate automation result.
        
        - Validates action types
        - Calculates overall safety level
        - Ensures proper payload structure
        """
        steps = result.get("steps", [])
        
        # Validate each step
        validated_steps = []
        max_safety = "low"
        safety_order = {"low": 0, "medium": 1, "high": 2}
        
        for step in steps:
            action = step.get("action", "")
            
            # Map to available actions
            if action not in self.available_actions:
                # Try fuzzy matching
                action = self._map_action(action)
            
            if action:
                step["action"] = action
                validated_steps.append(step)
                
                # Update max safety level
                step_safety = self.action_safety_levels.get(action, "medium")
                if safety_order.get(step_safety, 1) > safety_order.get(max_safety, 0):
                    max_safety = step_safety
        
        # Build final payload
        return {
            "is_automation": True,
            "route": "local_agent",
            "type": "automation",
            "goal": result.get("goal", query),
            "confidence": result.get("confidence", 0.7),
            "safety_level": result.get("safety_level", max_safety),
            "steps": validated_steps,
            "fallback": result.get("fallback", "Ask user to perform action manually"),
            "reasoning": result.get("reasoning", "")
        }
    
    def _map_action(self, action: str) -> Optional[str]:
        """Map variant action names to canonical actions."""
        action_lower = action.lower()
        
        mappings = {
            "launch": "open_app",
            "start": "open_app",
            "run": "open_app",
            "execute": "run_command",
            "quit": "close_app",
            "exit": "close_app",
            "kill": "close_app",
            "terminate": "close_app",
            "write": "type",
            "input": "type",
            "press": "click",
            "volume": "system_control",
            "brightness": "system_control",
            "mute": "system_control",
            "lock": "system_control",
            "switch_window": "focus_window",
            "switch_app": "focus_window",
        }
        
        for key, canonical in mappings.items():
            if key in action_lower:
                return canonical
        
        return None
    
    def should_confirm(self, result: Dict) -> Tuple[bool, str]:
        """
        Determine if user confirmation is needed.
        
        Returns:
            (needs_confirmation, reason)
        """
        if not result.get("is_automation"):
            return False, ""
        
        confidence = result.get("confidence", 0)
        safety = result.get("safety_level", "medium")
        
        # Low confidence - always confirm
        if confidence < self.confidence_threshold:
            return True, f"I'm {confidence*100:.0f}% confident you want to: {result.get('goal')}. Should I proceed?"
        
        # High safety risk - always confirm
        if safety == "high":
            steps_desc = ", ".join([s.get("action", "") for s in result.get("steps", [])])
            return True, f"This action ({steps_desc}) may have significant effects. Proceed?"
        
        return False, ""
    
    def generate_payload(self, result: Dict) -> Dict:
        """
        Generate the final automation payload for the local agent.
        
        This is the STRICT CONTRACT format that gets sent via WebSocket.
        """
        if not result.get("is_automation"):
            return None
        
        return {
            "route": "local_agent",
            "type": "automation",
            "goal": result.get("goal", ""),
            "confidence": result.get("confidence", 0),
            "safety_level": result.get("safety_level", "medium"),
            "steps": result.get("steps", []),
            "fallback": result.get("fallback", "")
        }


# Global instance
automation_classifier = AutomationIntentClassifier()


# ==================== QUICK CLASSIFICATION HELPER ====================

def is_automation_intent(query: str, context: Dict = None) -> Tuple[bool, Dict]:
    """
    Quick helper to check if query is automation intent.
    
    Returns:
        (is_automation, result_dict)
    """
    result = automation_classifier.classify(query, context)
    return result.get("is_automation", False), result


# ==================== TEST ====================

if __name__ == "__main__":
    test_queries = [
        "open notepad",
        "close chrome",
        "write a poem",
        "write a poem in notepad",
        "search for python tutorials",
        "open chrome and search for python",
        "increase volume",
        "delete all files in downloads",
        "what's the weather today",
        "switch to vs code",
    ]
    
    print("Testing Automation Intent Classifier")
    print("=" * 70)
    
    for query in test_queries:
        result = automation_classifier.classify(query)
        print(f"\nQuery: {query}")
        print(f"  Is Automation: {result.get('is_automation')}")
        print(f"  Confidence: {result.get('confidence', 0):.2f}")
        if result.get("is_automation"):
            print(f"  Safety: {result.get('safety_level')}")
            print(f"  Steps: {[s.get('action') for s in result.get('steps', [])]}")
            needs_confirm, reason = automation_classifier.should_confirm(result)
            if needs_confirm:
                print(f"  ⚠️ Confirm: {reason}")
        else:
            print(f"  Route: {result.get('suggested_route')}")
