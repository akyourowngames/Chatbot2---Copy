"""
Clarification Engine - Smart Question Asking
=============================================
Generates contextual clarification questions when confidence is low.
"""

import json
from typing import Dict, List
from Backend.LLM import ChatCompletion

class ClarificationEngine:
    def __init__(self):
        """Initialize clarification engine."""
        self.system_prompt = """You are a clarification question generator. When the system is uncertain about user intent, you generate helpful questions.

Your questions should be:
1. Natural and conversational
2. Offer specific options when possible
3. Brief (1-2 sentences max)
4. Friendly, not robotic

Generate a single clarifying question based on the hypotheses provided.

Return JSON ONLY:
{
  "question": "Your clarifying question here",
  "suggested_options": ["option 1", "option 2", "option 3"]  // optional
}

Examples:
- Ambiguous: "Did you want me to create an image or search for information about..."
- Missing param: "What style would you like for the image?"
- Multi-step unclear: "I can help with that! Should I start by searching for information or creating a document?"
"""
    
    def ask_question(self, hypotheses: Dict, goal: Dict) -> str:
        """
        Generate a clarification question based on hypotheses.
        
        Args:
            hypotheses: Hypotheses dict from IntentHypothesisGenerator
            goal: Goal dict from GoalInference
            
        Returns:
            Clarification question string
        """
        # Build context
        top_hypotheses = hypotheses.get("hypotheses", [])[:3]
        
        prompt = f"""User's Goal: {goal.get('primary_goal', 'unclear')}
Complexity: {goal.get('complexity', 'unknown')}

Possible Intents (ranked by confidence):
{json.dumps([{"intent": h["intent"], "confidence": h["confidence"]} for h in top_hypotheses], indent=2)}

Generate a clarifying question to determine which intent is correct:"""
        
        try:
            response = ChatCompletion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=self.system_prompt,
                model="llama-3.1-8b-instant"
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
            question = result.get("question", "")
            
            # Add options if provided
            if "suggested_options" in result and result["suggested_options"]:
                options = result["suggested_options"]
                question += "\n\nOptions:\n" + "\n".join([f"• {opt}" for opt in options])
            
            print(f"[CLARIFICATION] Generated question: {question[:50]}...")
            return question
            
        except Exception as e:
            print(f"[CLARIFICATION] Error generating question: {e}, using fallback")
            # Fallback: simple question based on top hypotheses
            if len(top_hypotheses) >= 2:
                intent1 = top_hypotheses[0]["intent"].replace("_", " ")
                intent2 = top_hypotheses[1]["intent"].replace("_", " ")
                return f"I'm not sure what you need. Did you want me to handle {intent1} or {intent2}?"
            else:
                return "I'm not quite sure what you need. Could you provide more details or rephrase your request?"
    
    def generate_confirmation(self, intent: str, params: Dict = None) -> str:
        """
        Generate a confirmation message for medium-confidence intents.
        
        Args:
            intent: The detected intent
            params: Parameters extracted
            
        Returns:
            Confirmation message
        """
        intent_display = intent.replace("_", " ").title()
        
        if params:
            param_str = ", ".join([f"{k}: {v}" for k, v in params.items() if v])
            return f"I think you want {intent_display} ({param_str}). Is that correct?"
        else:
            return f"Just to confirm - you want {intent_display}, right?"

# Global instance
clarification_engine = ClarificationEngine()

if __name__ == "__main__":
    # Test
    from Backend.GoalInference import goal_inference
    from Backend.IntentHypothesis import hypothesis_generator
    
    test_query = "help me with something cool"
    
    print("Testing Clarification Engine")
    print("=" * 70)
    
    goal = goal_inference.infer_goal(test_query)
    hypotheses = hypothesis_generator.generate(goal)
    
    if hypothesis_generator.should_ask_clarification(hypotheses):
        question = clarification_engine.ask_question(hypotheses, goal)
        print(f"\nQuery: {test_query}")
        print(f"Clarification: {question}")
