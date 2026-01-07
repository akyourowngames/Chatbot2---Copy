"""
Goal Inference Engine - Semantic Intent Understanding
======================================================
Understands WHAT the user wants to achieve, not which feature to trigger.
Uses LLM for semantic understanding without keyword matching.
"""

import json
from typing import Dict, List, Optional
from Backend.LLM import ChatCompletion

class GoalInferenceEngine:
    def __init__(self):
        """Initialize the goal inference engine."""
        self.system_prompt = """You are a goal inference system. Your job is to understand what the user wants to achieve from their message.

Analyze the user's query and determine:
1. PRIMARY GOAL: What does the user fundamentally want? (create something, get information, control system, have conversation)
2. OUTPUT TYPE: What kind of output do they expect? (image, document, action, data, conversation)
3. ENTITIES: Extract key entities (app names, topics, parameters)
4. COMPLEXITY: Is this simple, multi-step, or unclear?

Return JSON ONLY in this exact format:
{
  "primary_goal": "create_visual|get_information|control_system|manage_media|conversation|unclear",
  "output_type": "image|document|action|data|conversation|music|video|multiple",
  "entities": {
    "target": "extracted entity if any",
    "parameters": ["key", "parameters"]
  },
  "complexity": "simple|multi_step|unclear",
  "reasoning": "brief explanation of your inference"
}

Examples:
- "I need something cool for my startup poster" → primary_goal: create_visual, output_type: image
- "what's the weather" → primary_goal: get_information, output_type: data
- "open notepad" → primary_goal: control_system, output_type: action
- "play some music" → primary_goal: manage_media, output_type: music
- "help me with something" → primary_goal: unclear, complexity: unclear
"""
    
    def infer_goal(self, query: str, history: List[Dict[str, str]] = None) -> Dict:
        """
        Infer user's goal from their query using LLM semantic understanding.
        
        Args:
            query: User's input message
            history: Recent chat history for context
            
        Returns:
            Dict containing:
                - primary_goal: Main objective classification
                - output_type: Expected output format
                - entities: Extracted entities and parameters
                - complexity: Simple, multi_step, or unclear
                - reasoning: Brief explanation
        """
        # Build context from history
        context = ""
        if history and len(history) > 0:
            recent = history[-3:] if len(history) > 3 else history
            context = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', msg.get('message', ''))}" for msg in recent])
            context = f"\n\nRecent conversation:\n{context}\n\n"
        
        # Call LLM for semantic understanding
        prompt = f"{context}User query: {query}\n\nAnalyze the goal:"
        
        try:
            response = ChatCompletion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=self.system_prompt,
                model="llama-3.1-8b-instant"  # Using Groq as specified
            )
            
            # Clean and parse response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            goal = json.loads(response)
            
            # Validate required fields
            required_fields = ["primary_goal", "output_type", "complexity"]
            if not all(field in goal for field in required_fields):
                raise ValueError("Missing required fields in goal inference")
            
            print(f"[GOAL INFERENCE] Query: '{query[:50]}...' → Goal: {goal['primary_goal']}, Type: {goal['output_type']}, Complexity: {goal['complexity']}")
            return goal
            
        except Exception as e:
            print(f"[GOAL INFERENCE] Error: {e}, falling back to safe defaults")
            # Fallback: treat as conversation
            return {
                "primary_goal": "conversation",
                "output_type": "conversation",
                "entities": {},
                "complexity": "simple",
                "reasoning": f"Failed to infer goal: {str(e)}"
            }

# Global instance
goal_inference = GoalInferenceEngine()

if __name__ == "__main__":
    # Test cases
    test_queries = [
        "I need something cool for my startup poster",
        "what's the weather in London",
        "open notepad",
        "play some lofi music",
        "create a PDF about AI",
        "help me with something",
        "search for python tutorials",
        "increase volume"
    ]
    
    print("Testing Goal Inference Engine")
    print("=" * 70)
    
    for query in test_queries:
        result = goal_inference.infer_goal(query)
        print(f"\nQuery: {query}")
        print(f"  Goal: {result['primary_goal']}")
        print(f"  Output: {result['output_type']}")
        print(f"  Complexity: {result['complexity']}")
        print(f"  Reasoning: {result['reasoning']}")
