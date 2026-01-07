"""
Intent Classifier - Using Local Zero-Shot Model
================================================
Fast, offline intent classification without API calls.
"""

import json
from typing import List, Dict
from Backend.LocalClassifier import get_classifier

class IntentClassifier:
    def __init__(self):
        """Initialize with local classifier."""
        self.local_classifier = get_classifier()
    
    def classify(self, query: str, history: List[Dict[str, str]] = None) -> dict:
        """
        Classify user intent using local model.
        
        Returns:
            dict: {
                "intent": str,
                "tool": str,
                "args": dict,
                "needs_chat_response": bool,
                "confidence": float
            }
        """
        return self.local_classifier.classify(query)

# Global instance
intent_classifier = IntentClassifier()

if __name__ == "__main__":
    # Test
    test_queries = [
        "Remember that I love anime",
        "Search for Python tutorials",
        "Write code to sort a list",
        "What's the weather?",
        "Increase volume"
    ]
    
    print("Testing Intent Classifier with Local Model")
    print("=" * 60)
    
    for query in test_queries:
        result = intent_classifier.classify(query)
        print(f"\nQuery: {query}")
        print(f"Intent: {result['intent']} (confidence: {result.get('confidence', 0):.2f})")
        print(f"Tool: {result['tool']}")
        print(f"Args: {result['args']}")
        print(f"Needs Response: {result['needs_chat_response']}")
