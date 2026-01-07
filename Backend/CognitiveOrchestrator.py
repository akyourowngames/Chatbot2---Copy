"""
Cognitive Orchestrator - Unified Goal-Based Pipeline
====================================================
The SINGLE brain loop that routes all user inputs through:
1. Goal Inference
2. Hypothesis Generation
3. Confidence Gating
4. Automation Governor (NEW: 4-mode decision engine)
5. Decision Gate: CHAT | SUGGEST | EXECUTE | MULTI-STEP
6. Execution & Response

Mental Model:
    Kai = Brain (all intelligence here)
    Local Agent = Hands (execution only)
    WebSocket = Nerves (communication)
"""

import os
from typing import Dict, List, Optional, Tuple

# Environment flag to enable/disable new architecture
USE_GOAL_INFERENCE = os.getenv("USE_GOAL_INFERENCE", "true").lower() == "true"
USE_AUTOMATION_ROUTING = os.getenv("USE_AUTOMATION_ROUTING", "true").lower() == "true"


class CognitiveOrchestrator:
    def __init__(self):
        """Initialize the cognitive orchestrator."""
        self.goal_inference = None
        self.hypothesis_generator = None
        self.clarification_engine = None
        self.automation_classifier = None
        self.automation_router = None
        self.automation_governor = None  # NEW: Governor
        self.automation_state = None     # NEW: State tracker
        self.smart_trigger = None  # Fallback
        
        self._init_components()
    
    def _init_components(self):
        """Lazy load components to avoid circular imports."""
        try:
            from Backend.GoalInference import goal_inference
            from Backend.IntentHypothesis import hypothesis_generator
            from Backend.ClarificationEngine import clarification_engine
            
            self.goal_inference = goal_inference
            self.hypothesis_generator = hypothesis_generator
            self.clarification_engine = clarification_engine
            print("[COGNITIVE] ✅ Goal-based inference initialized")
        except Exception as e:
            print(f"[COGNITIVE] ⚠️ Goal inference init failed: {e}, will use fallback")
        
        # Load Automation components
        if USE_AUTOMATION_ROUTING:
            try:
                from Backend.AutomationIntentClassifier import automation_classifier
                from Backend.AutomationRouter import automation_router
                from Backend.AutomationGovernor import automation_governor
                from Backend.AutomationState import automation_state
                
                self.automation_classifier = automation_classifier
                self.automation_router = automation_router
                self.automation_governor = automation_governor
                self.automation_state = automation_state
                print("[COGNITIVE] 🤖 Automation routing + Governor initialized")
            except Exception as e:
                print(f"[COGNITIVE] ⚠️ Automation routing init failed: {e}")
        
        # Always load SmartTrigger as fallback
        try:
            from Backend.SmartTrigger import smart_trigger
            self.smart_trigger = smart_trigger
            print("[COGNITIVE] 📦 SmartTrigger loaded as fallback")
        except Exception as e:
            print(f"[COGNITIVE] ❌ SmartTrigger fallback unavailable: {e}")

    
    def process(self, query: str, history: List[Dict] = None, user_id: str = None) -> Dict:
        """
        Main processing pipeline - the SINGLE brain loop.
        
        Args:
            query: User's input
            history: Chat history for context
            user_id: User ID for device lookup (automation)
            
        Returns:
            Dict with:
                - action: "proceed" | "clarify" | "confirm" | "automation"
                - intent: Detected intent (if proceed)
                - command: Extracted command/params
                - confidence: Confidence score
                - clarification: Question to ask (if clarify)
                - trigger_type: For backward compatibility with existing handlers
                - automation_result: Result from automation routing (if automation)
        """
        # === STEP 0: CHECK FOR AUTOMATION INTENT (NEW DECISION GATE) ===
        if USE_AUTOMATION_ROUTING and self.automation_classifier:
            automation_result = self._check_automation(query, history, user_id)
            if automation_result:
                return automation_result
        
        # === GOAL INFERENCE PIPELINE ===
        if USE_GOAL_INFERENCE and self.goal_inference:
            try:
                # Step 1: Infer Goal
                goal = self.goal_inference.infer_goal(query, history)
                
                # Step 2: Generate Hypotheses
                hypotheses = self.hypothesis_generator.generate(goal)
                
                top_hypothesis = hypotheses["hypotheses"][0] if hypotheses["hypotheses"] else None
                
                if not top_hypothesis:
                    # No hypothesis generated, fallback
                    return self._fallback_to_smart_trigger(query)
                
                # Step 3: Confidence Gating
                action = hypotheses["recommended_action"]
                
                if action == "ask":
                    # Low confidence - ask clarification
                    question = self.clarification_engine.ask_question(hypotheses, goal)
                    return {
                        "action": "clarify",
                        "intent": top_hypothesis["intent"],
                        "confidence": top_hypothesis["confidence"],
                        "clarification": question,
                        "trigger_type": None,
                        "command": None
                    }
                
                # High/Medium confidence - proceed
                intent = top_hypothesis["intent"]
                
                # Map new intents to legacy trigger_types for backward compatibility
                trigger_map = {
                    "image_generation": "image",
                    "document_generation": "document",
                    "web_search": "chrome",
                    "local_search": "file",
                    "app_control": "app",
                    "system_control": "system_control",
                    "media_playback": "music",
                    "information_query": "info",
                    "conversation": None,  # No tool needed
                    "code_generation": "code",
                    "file_management": "file",
                    # Additional mappings
                    "open_app": "open_app",
                    "close_app": "close_app",
                    "volume_control": "system_control",
                    "weather": "weather",
                    "news": "news",
                    "reminder": "reminder",
                    # Automation intents (handled by automation gate, but map for fallback)
                    "automation": "automation",
                    "automation_required": "automation"
                }
                
                trigger_type = trigger_map.get(intent)
                
                # Extract command from entities
                entities = goal.get("entities", {})
                command = entities.get("target", query)
                
                print(f"[COGNITIVE] ✅ Processed: {intent} (conf: {top_hypothesis['confidence']:.2f}) → trigger: {trigger_type}")
                
                return {
                    "action": "proceed",
                    "intent": intent,
                    "confidence": top_hypothesis["confidence"],
                    "trigger_type": trigger_type,
                    "command": command,
                    "goal": goal,
                    "clarification": None
                }
                
            except Exception as e:
                print(f"[COGNITIVE] ⚠️ Pipeline error: {e}, falling back")
                return self._fallback_to_smart_trigger(query)
        
        # Fallback path
        return self._fallback_to_smart_trigger(query)
    
    def _check_automation(self, query: str, history: List[Dict] = None, user_id: str = None) -> Optional[Dict]:
        """
        Check if query requires OS-level automation and route via Governor.
        
        NEW: Uses Automation Governor for 4-mode decision:
            MODE 0: CHAT_ONLY - Route to chat, no automation
            MODE 1: SUGGEST_ONLY - Offer to automate, wait for approval
            MODE 2: SINGLE_SAFE_ACTION - Execute immediately
            MODE 3: MULTI_STEP - Confirm once, then execute
        
        Returns:
            Dict with automation result, or None if not automation
        """
        try:
            # === STEP 0: Check for follow-up queries ===
            if self.automation_state:
                follow_up = self.automation_state.resolve_follow_up(query)
                if follow_up:
                    return self._handle_follow_up(follow_up, user_id)
            
            # === STEP 1: Classify intent ===
            context = {"history": history} if history else None
            classification = self.automation_classifier.classify(query, context)
            
            if not classification.get("is_automation"):
                # Not automation - continue with normal pipeline
                return None
            
            # === STEP 2: Get current system state (if available) ===
            system_state = None
            if self.automation_state:
                system_state = self.automation_state.get_state()
            
            # === STEP 3: Governor Decision ===
            if self.automation_governor:
                decision = self.automation_governor.decide(
                    classification, 
                    query, 
                    system_state=system_state
                )
                return self._execute_governor_decision(decision, classification, user_id)
            
            # Fallback to old logic if governor not available
            return self._legacy_automation_check(classification, user_id)
            
        except Exception as e:
            print(f"[COGNITIVE] ⚠️ Automation check error: {e}")
            return None
    
    def _execute_governor_decision(self, decision: Dict, classification: Dict, user_id: str = None) -> Optional[Dict]:
        """
        Execute based on Governor's mode decision.
        
        Args:
            decision: Governor decision with mode and payload
            classification: Original classification result
            user_id: User ID for device lookup
        """
        from Backend.AutomationGovernor import AutomationMode
        
        mode = decision.get("mode", AutomationMode.CHAT_ONLY)
        action = decision.get("action", "")
        
        # === MODE 0: CHAT_ONLY ===
        if mode == AutomationMode.CHAT_ONLY:
            # Check for blocked or already_done special cases
            if decision.get("blocked"):
                return {
                    "action": "blocked",
                    "intent": "automation",
                    "response": decision.get("response", "I can't do that for safety reasons."),
                    "skip_llm": True,  # Don't call ChatBot
                    "trigger_type": None,
                    "command": None
                }
            
            if decision.get("already_done"):
                return {
                    "action": "already_done",
                    "intent": "automation",
                    "response": decision.get("response"),
                    "skip_llm": True,  # Concise response, no LLM
                    "trigger_type": None,
                    "command": None
                }
            
            # Normal chat - return None to continue pipeline
            print(f"[GOVERNOR] MODE 0 (CHAT): {decision.get('reason')}")
            return None
        
        # === MODE 1: SUGGEST_ONLY ===
        if mode == AutomationMode.SUGGEST_ONLY:
            print(f"[GOVERNOR] MODE 1 (SUGGEST): {decision.get('reason')}")
            return {
                "action": "suggest",
                "intent": "automation",
                "confidence": classification.get("confidence", 0),
                "trigger_type": "automation",
                "command": None,
                "clarification": decision.get("confirmation_prompt"),
                "automation_payload": self.automation_classifier.generate_payload(classification),
                "safety_level": classification.get("safety_level", "low"),
                "suggested_actions": decision.get("suggested_actions", [])
            }
        
        # === MODE 2: SINGLE_SAFE_ACTION ===
        if mode == AutomationMode.SINGLE_SAFE_ACTION:
            print(f"[GOVERNOR] MODE 2 (EXECUTE): {decision.get('reason')}")
            return self._execute_automation(classification, user_id)
        
        # === MODE 3: MULTI_STEP ===
        if mode == AutomationMode.MULTI_STEP:
            print(f"[GOVERNOR] MODE 3 (CONFIRM): {decision.get('reason')}")
            
            # Check if confirmation is explicitly required
            if decision.get("action") == "confirm_required":
                return {
                    "action": "confirm",
                    "intent": "automation",
                    "confidence": classification.get("confidence", 0),
                    "trigger_type": "automation",
                    "command": None,
                    "clarification": decision.get("confirmation_prompt"),
                    "automation_payload": self.automation_classifier.generate_payload(classification),
                    "safety_level": classification.get("safety_level", "medium")
                }
            
            # For multi-step, confirm once
            return {
                "action": "confirm",
                "intent": "automation",
                "confidence": classification.get("confidence", 0),
                "trigger_type": "automation",
                "command": None,
                "clarification": decision.get("confirmation_prompt"),
                "automation_payload": self.automation_classifier.generate_payload(classification),
                "safety_level": classification.get("safety_level", "medium"),
                "multi_step": True
            }
        
        return None
    
    def _execute_automation(self, classification: Dict, user_id: str = None) -> Dict:
        """Execute automation and record to memory."""
        payload = self.automation_classifier.generate_payload(classification)
        
        if not payload:
            return None
        
        route_result = self.automation_router.route(payload, user_id)
        
        if route_result.get("success"):
            # Record to automation memory
            if self.automation_state:
                steps = classification.get("steps", [])
                if steps:
                    first_step = steps[0]
                    self.automation_state.record_action(
                        action=first_step.get("action", "automation"),
                        dimension=self._infer_dimension(first_step),
                        target=first_step.get("target")
                    )
            
            # Generate concise response (NO LLM call)
            response = self._generate_concise_response(classification, route_result)
            
            print(f"[COGNITIVE] 🤖 Automation executed: {classification.get('goal')}")
            return {
                "action": "automation",
                "intent": "automation",
                "confidence": classification.get("confidence", 0),
                "trigger_type": "automation",
                "command": classification.get("goal"),
                "automation_result": route_result,
                "automation_payload": payload,
                "response": response,
                "skip_llm": True,  # Post-automation: No ChatBot
                "clarification": None
            }
        else:
            print(f"[COGNITIVE] ⚠️ Automation routing failed: {route_result.get('error')}")
            return {
                "action": "automation_failed",
                "intent": "automation",
                "confidence": classification.get("confidence", 0),
                "trigger_type": None,
                "command": None,
                "error": route_result.get("error"),
                "fallback": route_result.get("fallback", classification.get("fallback")),
                "clarification": f"I couldn't complete that. {route_result.get('error', '')}"
            }
    
    def _handle_follow_up(self, follow_up: Dict, user_id: str = None) -> Optional[Dict]:
        """Handle follow-up queries like 'increase it more'."""
        dimension = follow_up.get("dimension")
        follow_type = follow_up.get("type")
        last_action = follow_up.get("last_action", {})
        
        # Build a synthetic classification for the follow-up
        if dimension == "volume":
            if follow_type == "increase":
                action = "volume_up"
            elif follow_type == "decrease":
                action = "volume_down"
            elif follow_type == "undo":
                action = "set_volume"
            else:
                return None
                
            classification = {
                "is_automation": True,
                "confidence": 0.9,
                "goal": f"{follow_type} volume",
                "safety_level": "low",
                "steps": [{
                    "action": "system_control",
                    "target": "volume",
                    "parameters": {"action": action}
                }]
            }
            
            if follow_type == "undo":
                classification["steps"][0]["parameters"]["level"] = follow_up.get("restore_value", 50)
            
            print(f"[COGNITIVE] 🔄 Follow-up resolved: {follow_type} {dimension}")
            return self._execute_automation(classification, user_id)
        
        return None
    
    def _infer_dimension(self, step: Dict) -> str:
        """Infer the dimension affected by an action."""
        action = step.get("action", "")
        params = step.get("parameters", {})
        
        if action == "system_control":
            param_action = params.get("action", "")
            if "volume" in param_action:
                return "volume"
            if "brightness" in param_action:
                return "brightness"
            if "mute" in param_action:
                return "audio"
            return "system"
        
        if action in ["open_app", "close_app"]:
            return "app"
        
        if action == "screenshot":
            return "screenshot"
        
        return action
    
    def _generate_concise_response(self, classification: Dict, result: Dict) -> str:
        """Generate a concise post-automation response (no LLM)."""
        steps = classification.get("steps", [])
        
        if not steps:
            return "✓ Done"
        
        first_step = steps[0]
        action = first_step.get("action", "")
        target = first_step.get("target", "")
        params = first_step.get("parameters", {})
        
        # Volume/brightness responses
        if action == "system_control":
            param_action = params.get("action", "")
            level = params.get("level")
            
            if "volume_up" in param_action:
                return "🔊 Volume increased"
            if "volume_down" in param_action:
                return "🔉 Volume decreased"
            if "set_volume" in param_action and level:
                return f"🔊 Volume set to {level}%"
            if "mute" in param_action:
                return "🔇 Muted"
            if "unmute" in param_action:
                return "🔊 Unmuted"
            if "brightness_up" in param_action:
                return "☀️ Brightness increased"
            if "brightness_down" in param_action:
                return "🔅 Brightness decreased"
            if "set_brightness" in param_action and level:
                return f"☀️ Brightness set to {level}%"
            if "lock_screen" in param_action:
                return "🔒 Screen locked"
        
        # App responses
        if action == "open_app":
            return f"📱 Opened {target.title()}"
        if action == "close_app":
            return f"❌ Closed {target.title()}"
        
        # Screenshot
        if action == "screenshot":
            return "📸 Screenshot captured"
        
        # Generic
        goal = classification.get("goal", "task")
        return f"✓ {goal}"
    
    def _legacy_automation_check(self, classification: Dict, user_id: str = None) -> Optional[Dict]:
        """Fallback to old automation logic if Governor unavailable."""
        needs_confirm, confirm_msg = self.automation_classifier.should_confirm(classification)
        
        if needs_confirm:
            return {
                "action": "confirm",
                "intent": "automation",
                "confidence": classification.get("confidence", 0),
                "trigger_type": "automation",
                "command": None,
                "clarification": confirm_msg,
                "automation_payload": self.automation_classifier.generate_payload(classification),
                "safety_level": classification.get("safety_level", "medium")
            }
        
        return self._execute_automation(classification, user_id)

    
    def execute_confirmed_automation(self, payload: Dict, user_id: str = None) -> Dict:
        """
        Execute an automation that was previously confirmed by user.
        
        Args:
            payload: The automation_payload from a confirm response
            user_id: User ID for device lookup
            
        Returns:
            Dict with execution result
        """
        if not self.automation_router:
            return {
                "success": False,
                "error": "Automation router not available"
            }
        
        route_result = self.automation_router.route(payload, user_id)
        
        if route_result.get("success"):
            return {
                "action": "automation",
                "success": True,
                "result": route_result,
                "message": f"Automation executed: {payload.get('goal', 'task')}"
            }
        else:
            return {
                "action": "automation_failed",
                "success": False,
                "error": route_result.get("error"),
                "fallback": payload.get("fallback", "")
            }
    
    def _fallback_to_smart_trigger(self, query: str) -> Dict:
        """
        Fallback to legacy SmartTrigger for backward compatibility.
        """
        if self.smart_trigger:
            trigger_type, command, confidence = self.smart_trigger.detect(query)
            print(f"[COGNITIVE] 📦 Fallback: SmartTrigger → {trigger_type} (conf: {confidence:.2f})")
            return {
                "action": "proceed",
                "intent": trigger_type or "conversation",
                "confidence": confidence,
                "trigger_type": trigger_type,
                "command": command,
                "clarification": None
            }
        else:
            # Ultimate fallback - conversation mode
            return {
                "action": "proceed",
                "intent": "conversation",
                "confidence": 0.5,
                "trigger_type": None,
                "command": None,
                "clarification": None
            }
    
    def should_use_tool(self, result: Dict) -> bool:
        """Check if a tool should be used based on processing result."""
        return result.get("trigger_type") is not None and result.get("action") == "proceed"
    
    def needs_clarification(self, result: Dict) -> bool:
        """Check if clarification is needed."""
        return result.get("action") == "clarify"
    
    def needs_confirmation(self, result: Dict) -> bool:
        """Check if user confirmation is needed (for automation)."""
        return result.get("action") == "confirm"
    
    def is_automation(self, result: Dict) -> bool:
        """Check if result is an automation action."""
        return result.get("action") in ["automation", "automation_failed", "confirm"]
    
    def get_automation_status(self, user_id: str = None) -> Dict:
        """Get automation capability status."""
        if not self.automation_router:
            return {"available": False, "reason": "Automation router not initialized"}
        
        return self.automation_router.get_device_status(user_id)


# Global instance
cognitive_orchestrator = CognitiveOrchestrator()


# Convenience function for backward compatibility
def process_with_goal_inference(query: str, history: List[Dict] = None) -> Tuple[str, str, float]:
    """
    Process query and return (trigger_type, command, confidence) for compatibility.
    """
    result = cognitive_orchestrator.process(query, history)
    return (
        result.get("trigger_type"),
        result.get("command"),
        result.get("confidence", 0.5)
    )


# New convenience function for automation-aware processing
def process_with_automation(query: str, history: List[Dict] = None, user_id: str = None) -> Dict:
    """
    Process query with full automation support.
    
    Returns complete result dict including automation handling.
    """
    return cognitive_orchestrator.process(query, history, user_id)


if __name__ == "__main__":
    # Test the orchestrator
    test_queries = [
        "create an image of a sunset",
        "what's the weather in London",
        "open notepad",
        "help me with something",
        "play some music",
        "search python tutorials",
        # Automation-specific tests
        "close chrome",
        "increase volume",
        "write hello world in notepad",
    ]
    
    print("Testing Cognitive Orchestrator (with Automation)")
    print("=" * 70)
    
    for query in test_queries:
        result = cognitive_orchestrator.process(query)
        print(f"\nQuery: {query}")
        print(f"  Action: {result['action']}")
        print(f"  Intent: {result.get('intent', 'N/A')}")
        print(f"  Trigger: {result.get('trigger_type', 'N/A')}")
        print(f"  Confidence: {result.get('confidence', 0):.2f}")
        if result.get('clarification'):
            print(f"  Clarification: {result['clarification']}")
        if result.get('automation_result'):
            print(f"  Automation: {result['automation_result']}")

