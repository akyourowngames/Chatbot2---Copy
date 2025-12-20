"""
Local Intent Classifier - Sentence Transformer Model
=====================================================
Uses lightweight MiniLM model for fast intent classification.
"""

import json
import re
from typing import Dict, Optional
import time

class LocalClassifier:
    def __init__(self, use_model=False):
        """
        Initialize classifier.
        
        Args:
            use_model: If True, load sentence transformer model (fast). If False, use keyword fallback (instant).
        """
        self.use_model = use_model
        self.classifier = None
        
        # Intent labels for classification
        self.intent_labels = [
            "vision_analysis",
            "web_search",
            "memory_update",
            "memory_query",
            "chat_response",
            "code_generation",
            "workflow_trigger",
            "file_operation",
            "system_command",
            "conversation_meta"
        ]
        
        # Intent to tool mapping
        self.tool_mapping = {
            "vision_analysis": "image_analyzer",
            "web_search": "google_search",
            "memory_update": "memory_manager",
            "memory_query": "memory_manager",
            "chat_response": "llm_chat",
            "code_generation": "code_tool",
            "workflow_trigger": "workflow_manager",
            "file_operation": "file_service",
            "system_command": "system_control",
            "conversation_meta": "llm_chat"
        }

        if use_model:
            print("[CLASSIFIER] Loading MiniLM sentence transformer model...")
            try:
                from sentence_transformers import SentenceTransformer
                import numpy as np
                
                # Load lightweight model (80MB)
                self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                print("[CLASSIFIER] MiniLM model loaded successfully (80MB)")
                
                # Pre-compute intent embeddings
                self.intent_embeddings = self.model.encode(self.intent_labels)
                
            except Exception as e:
                print(f"[CLASSIFIER] Error loading model: {e}")
                print("[CLASSIFIER] Falling back to keyword-based classification")
                self.use_model = False
        else:
            print("[CLASSIFIER] Using fast keyword-based classification")
    
    def classify(self, user_message: str) -> Dict:
        """
        Classify user intent and return routing information.
        
        Args:
            user_message: User's input message
            
        Returns:
            dict: {
                "intent": str,
                "tool": str,
                "args": dict,
                "needs_chat_response": bool
            }
        """
        # Use fast keyword-based classification by default
        if not self.use_model:
            return self._fallback_classification(user_message)
        
        try:
            import numpy as np
            start_time = time.time()
            
            # Encode user message
            message_embedding = self.model.encode([user_message])[0]
            
            # Calculate cosine similarity with intent embeddings
            similarities = np.dot(self.intent_embeddings, message_embedding) / (
                np.linalg.norm(self.intent_embeddings, axis=1) * np.linalg.norm(message_embedding)
            )
            
            # Get best match
            best_idx = np.argmax(similarities)
            intent = self.intent_labels[best_idx]
            confidence = float(similarities[best_idx])
            
            classification_time = time.time() - start_time
            print(f"[CLASSIFIER] Intent: {intent} (confidence: {confidence:.2f}, time: {classification_time:.3f}s)")
            
            # If confidence too low, use fallback
            if confidence < 0.3:
                print("[CLASSIFIER] Low confidence, using keyword fallback")
                return self._fallback_classification(user_message)
            
            # Map to tool
            tool = self.tool_mapping.get(intent, "llm_chat")
            
            # Extract arguments
            args = self._extract_arguments(user_message, intent)
            
            # Determine if chat response needed
            needs_chat_response = self._needs_response(intent)
            
            return {
                "intent": intent,
                "tool": tool,
                "args": args,
                "needs_chat_response": needs_chat_response,
                "confidence": confidence
            }
            
        except Exception as e:
            print(f"[CLASSIFIER] Classification error: {e}")
            return self._fallback_classification(user_message)
    
    def _extract_arguments(self, message: str, intent: str) -> Dict:
        """Extract relevant arguments based on intent."""
        args = {}
        message_lower = message.lower()
        
        if intent == "memory_update":
            # Extract the fact to remember
            args["fact"] = message
            
        elif intent == "web_search":
            # Extract search query
            # Remove common search prefixes
            query = re.sub(r'^(search for|google|find|look up)\s+', '', message_lower, flags=re.IGNORECASE)
            args["query"] = query.strip() or message
            
        elif intent == "code_generation":
            # Extract language if mentioned
            languages = ["python", "javascript", "java", "c++", "go", "rust"]
            for lang in languages:
                if lang in message_lower:
                    args["language"] = lang
                    break
            args["task"] = message
            
        elif intent == "file_operation":
            # Extract file path if present
            file_match = re.search(r'[\w\-]+\.\w+', message)
            if file_match:
                args["filename"] = file_match.group(0)
            args["operation"] = message
            
        elif intent == "system_command":
            # Extract command type
            if "volume" in message_lower:
                args["command"] = "volume"
            elif "brightness" in message_lower:
                args["command"] = "brightness"
            elif "screenshot" in message_lower:
                args["command"] = "screenshot"
            else:
                args["command"] = message
        
        return args
    
    def _needs_response(self, intent: str) -> bool:
        """Determine if a chat response is needed."""
        # Intents that don't need chat response (just store/execute)
        silent_intents = ["memory_update"]
        return intent not in silent_intents
    
    def _fallback_classification(self, message: str) -> Dict:
        """Enhanced keyword-based fallback classification (instant)."""
        args = {}
        message_lower = message.lower()
        
        # Memory operations
        if any(word in message_lower for word in ["remember", "note that", "save this", "keep in mind"]):
            intent = "memory_update"
        
        # Web search
        elif any(word in message_lower for word in ["search", "google", "find", "look up", "weather", "news"]):
            intent = "web_search"
        
        # Code generation
        elif any(word in message_lower for word in ["code", "python", "javascript", "write a", "function", "script"]):
            intent = "code_generation"
        
        # System commands
        elif any(word in message_lower for word in ["volume", "brightness", "screenshot", "mute", "unmute"]):
            intent = "system_command"
        
        # File operations
        elif any(word in message_lower for word in ["create file", "delete file", "open file", "save file"]):
            intent = "file_operation"
        
        # Vision analysis
        elif any(word in message_lower for word in ["what is this", "analyze image", "describe", "what do you see"]):
            intent = "vision_analysis"
        
        # Default to chat
        else:
            intent = "chat_response"
        
        tool = self.tool_mapping.get(intent, "llm_chat")
        args = self._extract_arguments(message, intent)
        
        return {
            "intent": intent,
            "tool": tool,
            "args": args,
            "needs_chat_response": self._needs_response(intent),
            "confidence": 1.0  # High confidence for keyword matches
        }

# Global instance (lazy loaded)
_classifier_instance = None

def get_classifier():
    """Get or create classifier instance."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = LocalClassifier()
    return _classifier_instance

if __name__ == "__main__":
    # Test the classifier
    classifier = LocalClassifier()
    
    test_messages = [
        "Remember that I love pizza",
        "Search for the latest AI news",
        "Write Python code to sort a list",
        "What's the weather today?",
        "Increase the volume",
        "Create a file called test.txt"
    ]
    
    print("\n" + "="*60)
    print("Testing Local Classifier")
    print("="*60 + "\n")
    
    for msg in test_messages:
        result = classifier.classify(msg)
        print(f"Message: {msg}")
        print(f"Result: {json.dumps(result, indent=2)}")
        print("-" * 60)
