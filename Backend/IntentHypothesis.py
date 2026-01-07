"""
Intent Hypothesis Generator - Multi-Hypothesis with Confidence
===============================================================
Generates ranked hypotheses for what the user might want.
Applies confidence gating to decide: act, confirm, or ask.
"""

import json
from typing import Dict, List, Tuple
from Backend.LLM import ChatCompletion

class IntentHypothesisGenerator:
    def __init__(self):
        """Initialize the hypothesis generator."""
        self.confidence_thresholds = {
            "high": 0.8,      # >= 0.8: Proceed without asking
            "medium": 0.5,    # 0.5-0.8: Confirm with user
            "low": 0.5        # < 0.5: Ask clarifying questions
        }
        
        self.system_prompt = """You are an intent hypothesis generator. Given a user's goal, generate possible intent hypotheses with confidence scores.

Your job is to:
1. Generate 1-3 possible interpretations of what the user wants
2. Assign confidence scores (0.0-1.0) to each
3. Provide reasoning for each hypothesis

Available intent categories:
- image_generation: Create visual content
- document_generation: Create text documents (PDF, reports)
- web_search: Search for information online
- local_search: Search files on computer
- app_control: Open/close applications
- system_control: Volume, brightness, lock, etc.
- media_playback: Music, videos, streams
- information_query: Weather, news, time, etc.
- conversation: General chat, no tool needed
- code_generation: Write or execute code
- file_management: Create, delete, move files

Return JSON ONLY in this format:
{
  "hypotheses": [
    {"intent": "intent_name", "confidence": 0.95, "reasoning": "why this is likely"},
    {"intent": "alternative", "confidence": 0.05, "reasoning": "alternative possibility"}
  ],
  "recommended_action": "proceed|confirm|ask"
}

Confidence Guidelines:
- 0.9-1.0: Very clear, unambiguous
- 0.7-0.9: Likely but some uncertainty
- 0.5-0.7: Multiple plausible interpretations
- < 0.5: Unclear, need more info
"""
    
    def generate(self, goal: Dict, context: str = "") -> Dict:
        """
        Generate intent hypotheses from inferred goal.
        
        Args:
            goal: Goal dict from GoalInference
            context: Additional context if needed
            
        Returns:
            Dict containing:
                - hypotheses: List of ranked hypotheses with confidence scores
                - recommended_action: "proceed", "confirm", or "ask"
        """
        # Build prompt with goal information
        prompt = f"""User Goal Analysis:
- Primary Goal: {goal.get('primary_goal', 'unclear')}
- Expected Output: {goal.get('output_type', 'unknown')}
- Entities: {json.dumps(goal.get('entities', {}))}
- Complexity: {goal.get('complexity', 'unknown')}
- Reasoning: {goal.get('reasoning', '')}

{f"Additional Context: {context}" if context else ""}

Generate intent hypotheses:"""
        
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
            
            # Validate and sort hypotheses by confidence
            if "hypotheses" in result and len(result["hypotheses"]) > 0:
                result["hypotheses"] = sorted(
                    result["hypotheses"], 
                    key=lambda h: h.get("confidence", 0), 
                    reverse=True
                )
                
                # Determine action based on top confidence
                top_confidence = result["hypotheses"][0].get("confidence", 0)
                if top_confidence >= self.confidence_thresholds["high"]:
                    result["recommended_action"] = "proceed"
                elif top_confidence >= self.confidence_thresholds["medium"]:
                    result["recommended_action"] = "confirm"
                else:
                    result["recommended_action"] = "ask"
                
                print(f"[HYPOTHESIS] Top: {result['hypotheses'][0]['intent']} (confidence: {top_confidence:.2f}) → Action: {result['recommended_action']}")
                return result
            else:
                raise ValueError("No hypotheses generated")
                
        except Exception as e:
            print(f"[HYPOTHESIS] Error: {e}, using fallback")
            # Fallback: map goal to intent directly with low confidence
            intent_map = {
                "create_visual": "image_generation",
                "get_information": "information_query",
                "control_system": "system_control",
                "manage_media": "media_playback",
                "conversation": "conversation",
                "unclear": "conversation"
            }
            
            primary_goal = goal.get("primary_goal", "conversation")
            intent = intent_map.get(primary_goal, "conversation")
            
            return {
                "hypotheses": [
                    {"intent": intent, "confidence": 0.6, "reasoning": "Fallback mapping from goal"}
                ],
                "recommended_action": "proceed" if intent != "conversation" else "ask"
            }
    
    def should_ask_clarification(self, hypotheses_result: Dict) -> bool:
        """Check if we should ask for clarification."""
        return hypotheses_result.get("recommended_action") == "ask"
    
    def should_confirm(self, hypotheses_result: Dict) -> bool:
        """Check if we should confirm before acting."""
        return hypotheses_result.get("recommended_action") == "confirm"

# Global instance
hypothesis_generator = IntentHypothesisGenerator()

if __name__ == "__main__":
    # Test with sample goals
    from Backend.GoalInference import goal_inference
    
    test_queries = [
        "create an image of a sunset",
        "help me with something",
        "open notepad",
        "search python"
    ]
    
    print("Testing Intent Hypothesis Generator")
    print("=" * 70)
    
    for query in test_queries:
        goal = goal_inference.infer_goal(query)
        result = hypothesis_generator.generate(goal)
        
        print(f"\nQuery: {query}")
        print(f"  Top Intent: {result['hypotheses'][0]['intent']} (conf: {result['hypotheses'][0]['confidence']:.2f})")
        print(f"  Action: {result['recommended_action']}")
        if len(result['hypotheses']) > 1:
            print(f"  Alternatives: {[h['intent'] for h in result['hypotheses'][1:]]}")
