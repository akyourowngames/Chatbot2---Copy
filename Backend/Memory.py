"""
Memory System - Firebase-Backed Persistent Memory
==================================================
Store and recall user memories with Firebase persistence
"""

import os
from typing import List, Optional
import logging

# Import Firebase DAL
try:
    from Backend.FirebaseDAL import FirebaseDAL
    from Backend.FirebaseStorage import get_firebase_storage
    firebase_available = True
except ImportError:
    firebase_available = False
    logging.warning("[MEMORY] Firebase not available, using fallback mode")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemorySystem:
    """Firebase-backed memory system"""
    
    def __init__(self):
        """Initialize memory system"""
        if firebase_available:
            storage = get_firebase_storage()
            self.dal = FirebaseDAL(storage.db) if storage.db else None
        else:
            self.dal = None
        
        self.collection = "memory"
        logger.info("[MEMORY] Memory system initialized")
    
    def remember(self, user_id: str, content: str, tags: Optional[List[str]] = None) -> bool:
        """
        Store a memory for a user
        
        Args:
            user_id: User's unique identifier
            content: Memory content to store
            tags: Optional tags for categorization
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.dal:
                logger.warning("[MEMORY] Firebase DAL not available")
                return False
            
            # Check if memory already exists (avoid duplicates)
            existing = self.dal.list(self.collection, user_id, filters={"content": content}, limit=1)
            if existing:
                logger.info(f"[MEMORY] Memory already exists for user {user_id}")
                return True
            
            # Create memory document
            memory_data = {
                "content": content,
                "tags": tags or [],
                "embedding": None  # TODO: Add vector embedding generation
            }
            
            memory_id = self.dal.create(self.collection, user_id, memory_data)
            
            if memory_id:
                logger.info(f"[MEMORY] Stored memory for user {user_id}: {memory_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"[MEMORY] Remember error: {e}")
            return False
    
    def recall(self, user_id: str, limit: int = 50) -> str:
        """
        Recall all memories for a user
        
        Args:
            user_id: User's unique identifier
            limit: Maximum number of memories to recall
            
        Returns:
            Formatted string of memories
        """
        try:
            if not self.dal:
                return ""
            
            # Get all memories for user
            memories = self.dal.list(
                self.collection, 
                user_id, 
                limit=limit,
                order_by="created_at",
                descending=False
            )
            
            if not memories:
                return ""
            
            # Format memories for LLM context
            memory_string = "Here are things you remember about the user:\n"
            for memory in memories:
                content = memory.get("content", "")
                tags = memory.get("tags", [])
                tag_str = f" [{', '.join(tags)}]" if tags else ""
                memory_string += f"- {content}{tag_str}\n"
            
            return memory_string
            
        except Exception as e:
            logger.error(f"[MEMORY] Recall error: {e}")
            return ""
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate a simple TF-IDF-like embedding for text.
        Uses word frequencies normalized by document length.
        No external ML dependencies required.
        """
        import hashlib
        
        # Simple but effective: hash-based word vectors
        words = text.lower().split()
        embedding = [0.0] * 100  # 100-dimensional embedding
        
        for i, word in enumerate(words):
            # Hash word to get consistent vector position
            hash_val = int(hashlib.md5(word.encode()).hexdigest()[:8], 16)
            idx = hash_val % 100
            # Weight by position (earlier words matter more)
            weight = 1.0 / (1 + i * 0.1)
            embedding[idx] += weight
        
        # Normalize
        magnitude = sum(x*x for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors"""
        dot = sum(x*y for x, y in zip(a, b))
        mag_a = sum(x*x for x in a) ** 0.5
        mag_b = sum(x*x for x in b) ** 0.5
        if mag_a * mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)
    
    def search_memories(self, user_id: str, query: str, limit: int = 10) -> List[str]:
        """
        Search memories by content using semantic similarity
        
        Args:
            user_id: User's unique identifier
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching memory contents, ranked by relevance
        """
        try:
            if not self.dal:
                return []
            
            # Get all memories
            all_memories = self.dal.list(self.collection, user_id, limit=100)
            
            if not all_memories:
                return []
            
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Score each memory
            scored_memories = []
            query_lower = query.lower()
            
            for m in all_memories:
                content = m.get("content", "")
                
                # Compute semantic similarity
                memory_embedding = self._generate_embedding(content)
                semantic_score = self._cosine_similarity(query_embedding, memory_embedding)
                
                # Bonus for exact substring match
                if query_lower in content.lower():
                    semantic_score += 0.3
                
                scored_memories.append((semantic_score, content))
            
            # Sort by score descending
            scored_memories.sort(key=lambda x: x[0], reverse=True)
            
            # Return top matches above threshold
            return [content for score, content in scored_memories[:limit] if score > 0.1]
            
        except Exception as e:
            logger.error(f"[MEMORY] Search error: {e}")
            return []

    
    def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """
        Delete a specific memory
        
        Args:
            user_id: User's unique identifier
            memory_id: Memory document ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.dal:
                return False
            
            return self.dal.delete(self.collection, user_id, memory_id)
            
        except Exception as e:
            logger.error(f"[MEMORY] Delete error: {e}")
            return False
    
    def clear_all_memories(self, user_id: str) -> bool:
        """
        Clear all memories for a user
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.dal:
                return False
            
            # Get all memories
            memories = self.dal.list(self.collection, user_id, limit=1000)
            
            # Delete each one
            for memory in memories:
                self.dal.delete(self.collection, user_id, memory["id"])
            
            logger.info(f"[MEMORY] Cleared {len(memories)} memories for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"[MEMORY] Clear error: {e}")
            return False


# Global memory system instance
memory_system = MemorySystem()


# ==================== BACKWARD COMPATIBLE FUNCTIONS ====================

def Remember(query: str, user_id: str = "default") -> str:
    """
    Extract information to remember and save it (backward compatible)
    
    Args:
        query: Query containing information to remember
        user_id: User ID (default: "default" for backward compatibility)
        
    Returns:
        Confirmation message
    """
    # Simple extraction: remove "remember that" or "remember"
    fact = query.lower()
    for prefix in ["remember that ", "remember ", "save that ", "note that "]:
        if fact.startswith(prefix):
            fact = query[len(prefix):].strip()  # Use original case
            break
    
    if not fact:
        return "I didn't catch what I should remember."
    
    # Store in Firebase
    success = memory_system.remember(user_id, fact)
    
    if success:
        return f"Okay, I'll remember that {fact}."
    else:
        return "Sorry, I couldn't save that memory right now."


def Recall(user_id: str = "default") -> str:
    """
    Retrieve all memories (backward compatible)
    
    Args:
        user_id: User ID (default: "default" for backward compatibility)
        
    Returns:
        Formatted string of memories
    """
    return memory_system.recall(user_id)


# ==================== TESTING ====================

if __name__ == "__main__":
    print("🧠 Testing Memory System\n")
    
    test_user_id = "test_user_123"
    
    # Test remember
    print("1. Testing Remember:")
    result = Remember("remember that I like pizza", test_user_id)
    print(f"   {result}")
    
    result = Remember("remember that my favorite color is blue", test_user_id)
    print(f"   {result}")
    
    # Test recall
    print("\n2. Testing Recall:")
    memories = Recall(test_user_id)
    print(f"   {memories}")
    
    # Test search
    print("\n3. Testing Search:")
    matches = memory_system.search_memories(test_user_id, "pizza")
    print(f"   Search for 'pizza': {matches}")
    
    print("\n✅ Memory system tests completed!")

