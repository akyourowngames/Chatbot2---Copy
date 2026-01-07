"""
Cognitive Orchestrator - Unified Goal-Based Pipeline
====================================================
The SINGLE brain loop that routes all user inputs through:
1. Goal Inference
2. Hypothesis Generation
3. Confidence Gating
4. Tool Selection
5. Execution & Response

This replaces the old SmartTrigger keyword-based approach.
"""

import os
from typing import Dict, List, Optional, Tuple

# Environment flag to enable/disable new architecture
USE_GOAL_INFERENCE = os.getenv("USE_GOAL_INFERENCE", "true").lower() == "true"

class CognitiveOrchestrator:
    def __init__(self):
        """Initialize the cognitive orchestrator."""
        self.goal_inference = None
        self.hypothesis_generator = None
        self.clarification_engine = None
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
        
        # Always load SmartTrigger as fallback
        try:
            from Backend.SmartTrigger import smart_trigger
            self.smart_trigger = smart_trigger
            print("[COGNITIVE] 📦 SmartTrigger loaded as fallback")
        except Exception as e:
            print(f"[COGNITIVE] ❌ SmartTrigger fallback unavailable: {e}")
    
    def process(self, query: str, history: List[Dict] = None) -> Dict:
        """
        Main processing pipeline - the SINGLE brain loop.
        
        Args:
            query: User's input
            history: Chat history for context
            
        Returns:
            Dict with:
                - action: "proceed" | "clarify" | "fallback"
                - intent: Detected intent (if proceed)
                - command: Extracted command/params
                - confidence: Confidence score
                - clarification: Question to ask (if clarify)
                - trigger_type: For backward compatibility with existing handlers
        """
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
                    "reminder": "reminder"
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

if __name__ == "__main__":
    # Test the orchestrator
    test_queries = [
        "create an image of a sunset",
        "what's the weather in London",
        "open notepad",
        "help me with something",
        "play some music",
        "search python tutorials"
    ]
    
    print("Testing Cognitive Orchestrator")
    print("=" * 70)
    
    for query in test_queries:
        result = cognitive_orchestrator.process(query)
        print(f"\nQuery: {query}")
        print(f"  Action: {result['action']}")
        print(f"  Intent: {result['intent']}")
        print(f"  Trigger: {result['trigger_type']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        if result.get('clarification'):
            print(f"  Clarification: {result['clarification']}")
