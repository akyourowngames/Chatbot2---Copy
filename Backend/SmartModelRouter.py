"""
Smart Model Router - Beast Mode Intelligence
=============================================
Routes queries to the optimal model based on complexity, type, and requirements.
Uses fast models for simple queries, powerful models for complex reasoning.
"""

import re
from typing import Tuple, Dict, Any, Optional
import time


class SmartModelRouter:
    """
    Intelligent model selection based on query analysis.
    
    Models Available:
    - gemini-2.0-flash-exp: Best for complex reasoning, coding, analysis (DEFAULT)
    - gemini-2.0-flash-thinking-exp: For deep thinking/multi-step problems
    - llama-3.3-70b-versatile: Good for creative, conversational
    - llama-3.1-8b-instant: Fast for simple Q&A
    """
    
    # Model configurations - GROQ PRIMARY (fastest!) + Gemini fallback
    MODELS = {
        "thinking": {
            "name": "gemini-2.0-flash-thinking-exp",  # Only Gemini has thinking mode
            "provider": "gemini",
            "max_tokens": 8192,
            "description": "Deep reasoning with visible thinking process"
        },
        "powerful": {
            "name": "llama-3.3-70b-versatile",  # Groq - fast + smart
            "provider": "groq",
            "max_tokens": 4096,
            "description": "Best intelligence via Groq"
        },
        "creative": {
            "name": "llama-3.3-70b-versatile",  # Groq for creative
            "provider": "groq",
            "max_tokens": 2048,
            "description": "Great for creative and conversational"
        },
        "fast": {
            "name": "llama-3.1-8b-instant",  # Groq FASTEST model - sub 0.5s!
            "provider": "groq",
            "max_tokens": 1024,
            "description": "Ultra-fast response via Groq"
        }
    }
    
    # Query complexity patterns
    COMPLEX_PATTERNS = [
        r"\b(explain|analyze|compare|evaluate|design|architect|implement)\b",
        r"\b(why|how does|what causes|relationship between)\b",
        r"\b(step[- ]by[- ]step|in detail|comprehensive|thorough)\b",
        r"\b(algorithm|data structure|system design|optimize)\b",
        r"\b(debug|fix|error|issue|problem|not working)\b",
        r"\b(write|create|build|develop|code|program)\b.*\b(function|class|app|system|api)\b",
    ]
    
    THINKING_PATTERNS = [
        r"\b(think|reason|deduce|figure out|solve)\b.*\b(step|carefully|deeply)\b",
        r"\b(pros and cons|trade[- ]offs|advantages|disadvantages)\b",
        r"\b(if.*then|what would happen|hypothetically)\b",
        r"\b(logic|logical|reasoning|conclusion)\b",
        r"\b(complex|complicated|intricate|nuanced)\b",
        r"\b(math|calculate|equation|formula|proof)\b",
    ]
    
    CREATIVE_PATTERNS = [
        r"\b(write|compose|create)\b.*\b(story|poem|song|creative|fiction|joke)\b",
        r"\b(imaginative|creative|artistic|poetic)\b",
        r"\b(haiku|limerick|sonnet|essay|blog)\b",
        r"\b(funny|humorous|witty|entertaining)\b",
    ]
    
    SIMPLE_PATTERNS = [
        r"^(hi|hello|hey|yo|sup|greetings)",
        r"^(what time|what date|what day)",
        r"^(thanks|thank you|thx|ok|okay|got it|cool)",
        r"^(yes|no|maybe|sure|nope)",
        r"\b(define|meaning of|what is a|what are)\b\s+\w+$",
    ]
    
    def __init__(self):
        self.call_history = []
        self.stats = {
            "thinking": 0,
            "powerful": 0,
            "creative": 0,
            "fast": 0
        }
        print("[ROUTER] Smart Model Router initialized")
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze query to determine complexity and best model.
        
        Returns:
            Dict with 'complexity', 'category', 'recommended_model', 'reason'
        """
        query_lower = query.lower().strip()
        word_count = len(query.split())
        
        # Check for thinking mode triggers
        needs_thinking = any(re.search(p, query_lower) for p in self.THINKING_PATTERNS)
        if needs_thinking or word_count > 100:
            return {
                "complexity": "very_high",
                "category": "thinking",
                "recommended_model": self.MODELS["thinking"],
                "reason": "Query requires deep reasoning or multi-step analysis"
            }
        
        # Check for complex patterns
        is_complex = any(re.search(p, query_lower) for p in self.COMPLEX_PATTERNS)
        if is_complex or word_count > 50:
            return {
                "complexity": "high",
                "category": "powerful",
                "recommended_model": self.MODELS["powerful"],
                "reason": "Query is technical or requires detailed explanation"
            }
        
        # Check for creative patterns
        is_creative = any(re.search(p, query_lower) for p in self.CREATIVE_PATTERNS)
        if is_creative:
            return {
                "complexity": "medium",
                "category": "creative",
                "recommended_model": self.MODELS["creative"],
                "reason": "Query is creative/artistic in nature"
            }
        
        # Check for simple patterns
        is_simple = any(re.search(p, query_lower) for p in self.SIMPLE_PATTERNS)
        if is_simple or word_count < 5:
            return {
                "complexity": "low",
                "category": "fast",
                "recommended_model": self.MODELS["fast"],
                "reason": "Simple query benefits from fast response"
            }
        
        # Default to powerful model for best quality
        return {
            "complexity": "medium",
            "category": "powerful",
            "recommended_model": self.MODELS["powerful"],
            "reason": "Default to best overall model"
        }
    
    def route(self, query: str, force_model: str = None) -> Tuple[str, str, Dict]:
        """
        Route query to best model.
        
        Args:
            query: User's query
            force_model: Optional model override ("thinking", "powerful", "creative", "fast")
            
        Returns:
            Tuple of (model_name, provider, analysis_dict)
        """
        start_time = time.time()
        
        if force_model and force_model in self.MODELS:
            model_info = self.MODELS[force_model]
            analysis = {"category": force_model, "reason": "Forced model selection"}
        else:
            analysis = self.analyze_query(query)
            model_info = analysis["recommended_model"]
        
        # Track stats
        category = analysis.get("category", "powerful")
        self.stats[category] = self.stats.get(category, 0) + 1
        
        # Log routing decision
        routing_time = (time.time() - start_time) * 1000
        print(f"[ROUTER] Query routed to {model_info['name']} ({category}) in {routing_time:.1f}ms")
        print(f"[ROUTER] Reason: {analysis.get('reason', 'N/A')}")
        
        return model_info["name"], model_info["provider"], analysis
    
    def get_stats(self) -> Dict[str, int]:
        """Get routing statistics"""
        return self.stats.copy()
    
    def should_use_thinking_mode(self, query: str) -> bool:
        """
        Quick check if query needs thinking mode.
        Used for UI to show "thinking" indicator.
        """
        query_lower = query.lower()
        return (
            any(re.search(p, query_lower) for p in self.THINKING_PATTERNS) or
            len(query.split()) > 100 or
            "think" in query_lower or
            "step by step" in query_lower
        )


# Global instance
smart_router = SmartModelRouter()


def route_query(query: str, force_model: str = None) -> Tuple[str, str, Dict]:
    """Convenience function for routing"""
    return smart_router.route(query, force_model)


def should_think(query: str) -> bool:
    """Check if thinking mode should be used"""
    return smart_router.should_use_thinking_mode(query)


if __name__ == "__main__":
    # Test routing
    test_queries = [
        "hi",
        "what is python?",
        "write a haiku about coding",
        "explain how neural networks work step by step",
        "debug this code and fix the issue: def foo(): return x",
        "think carefully about the pros and cons of microservices",
    ]
    
    for q in test_queries:
        model, provider, analysis = route_query(q)
        print(f"\nQuery: '{q[:50]}...'")
        print(f"  -> Model: {model} ({provider})")
        print(f"  -> Complexity: {analysis.get('complexity')}")
        print(f"  -> Reason: {analysis.get('reason')}")
