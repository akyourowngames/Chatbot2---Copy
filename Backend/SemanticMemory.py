"""
Semantic Memory System - Vector-Based Memory Search
====================================================
Uses embeddings for semantic similarity search of memories.
Supports lightweight hash-based embeddings (default) or optional
SentenceTransformers for better accuracy.
"""

import json
import os
import hashlib
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticMemory:
    """Vector-based semantic memory with similarity search"""
    
    def __init__(self, storage_path: str = "Data/semantic_memory.json"):
        self.storage_path = storage_path
        self.embedding_dim = 128  # Dimension of embeddings
        self.memories = self._load_memories()
        self.encoder = None  # Optional: SentenceTransformer
        self._try_load_encoder()
        logger.info(f"[SEMANTIC] Loaded {len(self.memories)} memories")
    
    def _try_load_encoder(self):
        """Try to load SentenceTransformer for better embeddings"""
        try:
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_dim = 384  # MiniLM dimension
            logger.info("[SEMANTIC] Using SentenceTransformer for embeddings")
        except ImportError:
            logger.info("[SEMANTIC] Using lightweight hash-based embeddings")
            self.encoder = None
    
    def _load_memories(self) -> List[Dict]:
        """Load memories from storage"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _save_memories(self):
        """Save memories to storage"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.memories, f, indent=2, ensure_ascii=False)
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text
        
        Uses SentenceTransformer if available, otherwise hash-based approach
        """
        if self.encoder is not None:
            # Use SentenceTransformer
            embedding = self.encoder.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        else:
            # Lightweight hash-based embedding
            return self._hash_embedding(text)
    
    def _hash_embedding(self, text: str) -> List[float]:
        """
        Generate hash-based embedding (no ML dependencies)
        
        Uses word hashing with position weights and n-gram features
        """
        embedding = [0.0] * self.embedding_dim
        text_lower = text.lower()
        words = text_lower.split()
        
        # Word-level features
        for i, word in enumerate(words):
            # Primary hash
            hash_val = int(hashlib.md5(word.encode()).hexdigest()[:8], 16)
            idx = hash_val % self.embedding_dim
            weight = 1.0 / (1 + i * 0.1)  # Position decay
            embedding[idx] += weight
            
            # Secondary hash for disambiguation
            hash_val2 = int(hashlib.sha256(word.encode()).hexdigest()[:8], 16)
            idx2 = hash_val2 % self.embedding_dim
            embedding[idx2] += weight * 0.5
        
        # Bigram features
        for i in range(len(words) - 1):
            bigram = words[i] + " " + words[i+1]
            hash_val = int(hashlib.md5(bigram.encode()).hexdigest()[:8], 16)
            idx = hash_val % self.embedding_dim
            embedding[idx] += 0.3
        
        # Character-level features (catch typos and partial matches)
        for i in range(len(text_lower) - 2):
            trigram = text_lower[i:i+3]
            hash_val = int(hashlib.md5(trigram.encode()).hexdigest()[:6], 16)
            idx = hash_val % self.embedding_dim
            embedding[idx] += 0.1
        
        # Normalize
        magnitude = math.sqrt(sum(x*x for x in embedding))
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors"""
        if len(a) != len(b):
            return 0.0
        
        dot = sum(x*y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x*x for x in a))
        mag_b = math.sqrt(sum(x*x for x in b))
        
        if mag_a * mag_b == 0:
            return 0.0
        
        return dot / (mag_a * mag_b)
    
    def add_memory(self, content: str, metadata: Optional[Dict] = None) -> str:
        """
        Add a memory with its embedding
        
        Args:
            content: Memory content text
            metadata: Optional metadata (category, importance, etc.)
            
        Returns:
            Memory ID
        """
        # Generate unique ID
        memory_id = f"mem_{hashlib.md5(f'{content}{datetime.now()}'.encode()).hexdigest()[:12]}"
        
        # Check for duplicates
        for m in self.memories:
            if m.get("content", "").lower() == content.lower():
                logger.info(f"[SEMANTIC] Memory already exists: {content[:50]}...")
                return m.get("id", memory_id)
        
        # Generate embedding
        embedding = self.get_embedding(content)
        
        # Create memory object
        memory = {
            "id": memory_id,
            "content": content,
            "embedding": embedding,
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "access_count": 0,
            **(metadata or {})
        }
        
        self.memories.append(memory)
        self._save_memories()
        
        logger.info(f"[SEMANTIC] Added memory: {memory_id}")
        return memory_id
    
    def search(self, query: str, limit: int = 10, threshold: float = 0.2) -> List[Dict]:
        """
        Search memories by semantic similarity (ENHANCED)
        
        Args:
            query: Search query
            limit: Max results to return
            threshold: Minimum similarity score (lowered from 0.3 to 0.2)
            
        Returns:
            List of matching memories with scores
        """
        if not self.memories:
            return []
        
        # Get query embedding
        query_embedding = self.get_embedding(query)
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Score all memories
        scored = []
        for memory in self.memories:
            embedding = memory.get("embedding", [])
            if not embedding:
                continue
            
            # 1. Semantic similarity (base score)
            semantic_score = self.cosine_similarity(query_embedding, embedding)
            
            # 2. Keyword overlap boost (NEW)
            content_lower = memory.get("content", "").lower()
            content_words = set(content_lower.split())
            keyword_overlap = len(query_words.intersection(content_words))
            keyword_boost = min(0.2, keyword_overlap * 0.05)  # Up to 0.2 boost
            
            # 3. Exact substring match boost
            exact_match_boost = 0.2 if query_lower in content_lower else 0
            
            # 4. Importance boost
            importance = memory.get("importance", 0.5)
            importance_boost = importance * 0.1
            
            # 5. Recency boost (NEW - recent memories more relevant)
            try:
                last_accessed = datetime.fromisoformat(memory.get("last_accessed", ""))
                days_ago = (datetime.now() - last_accessed).days
                recency_boost = max(0, 0.05 * (1 - days_ago / 30))  # Decay over 30 days
            except:
                recency_boost = 0
            
            # 6. Access count boost (frequently accessed = important)
            access_count = memory.get("access_count", 0)
            access_boost = min(0.05, access_count * 0.01)
            
            # Combined score
            total_score = (semantic_score + keyword_boost + exact_match_boost + 
                          importance_boost + recency_boost + access_boost)
            
            if total_score >= threshold:
                scored.append({
                    **memory,
                    "score": total_score,
                    "semantic": semantic_score,
                    "keyword_boost": keyword_boost
                })
        
        # Sort by score
        scored.sort(key=lambda x: x["score"], reverse=True)
        
        # Update access counts for returned memories
        result_ids = set(m["id"] for m in scored[:limit])
        for memory in self.memories:
            if memory.get("id") in result_ids:
                memory["access_count"] = memory.get("access_count", 0) + 1
                memory["last_accessed"] = datetime.now().isoformat()
        
        # Save updated access stats
        if result_ids:
            self._save_memories()
        
        return scored[:limit]
    
    def find_similar(self, memory_id: str, limit: int = 5) -> List[Dict]:
        """
        Find memories similar to a given memory
        
        Args:
            memory_id: ID of the reference memory
            limit: Max results
            
        Returns:
            List of similar memories
        """
        # Find the reference memory
        ref_memory = None
        for m in self.memories:
            if m.get("id") == memory_id:
                ref_memory = m
                break
        
        if not ref_memory:
            return []
        
        ref_embedding = ref_memory.get("embedding", [])
        if not ref_embedding:
            return []
        
        # Find similar memories
        similar = []
        for memory in self.memories:
            if memory.get("id") == memory_id:
                continue
            
            embedding = memory.get("embedding", [])
            if not embedding:
                continue
            
            similarity = self.cosine_similarity(ref_embedding, embedding)
            if similarity > 0.3:
                similar.append({
                    **memory,
                    "score": similarity
                })
        
        similar.sort(key=lambda x: x["score"], reverse=True)
        return similar[:limit]
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID"""
        for i, m in enumerate(self.memories):
            if m.get("id") == memory_id:
                self.memories.pop(i)
                self._save_memories()
                logger.info(f"[SEMANTIC] Deleted memory: {memory_id}")
                return True
        return False
    
    def get_all_memories(self) -> List[Dict]:
        """Get all memories"""
        return self.memories
    
    def get_memory_count(self) -> int:
        """Get total memory count"""
        return len(self.memories)
    
    def rebuild_embeddings(self):
        """Rebuild all embeddings (useful after upgrading encoder)"""
        logger.info("[SEMANTIC] Rebuilding all embeddings...")
        for memory in self.memories:
            content = memory.get("content", "")
            if content:
                memory["embedding"] = self.get_embedding(content)
        self._save_memories()
        logger.info(f"[SEMANTIC] Rebuilt {len(self.memories)} embeddings")
    
    def get_summary(self) -> Dict:
        """Get memory system summary"""
        categories = {}
        for m in self.memories:
            cat = m.get("category", "general")
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_memories": len(self.memories),
            "categories": categories,
            "encoder": "SentenceTransformer" if self.encoder else "Hash-based",
            "embedding_dim": self.embedding_dim
        }


# Global instance
semantic_memory = SemanticMemory()


if __name__ == "__main__":
    # Test
    print("🧠 Testing Semantic Memory\n")
    
    # Add test memories
    test_memories = [
        "I love Python programming and building AI projects",
        "My favorite food is pizza, especially pepperoni",
        "I work as a software engineer at a tech startup",
        "I'm learning machine learning and deep learning",
        "My birthday is on March 15th",
    ]
    
    for mem in test_memories:
        semantic_memory.add_memory(mem, {"category": "test"})
    
    print(f"Added {len(test_memories)} test memories\n")
    
    # Test search
    queries = ["programming", "food preferences", "work", "AI"]
    for query in queries:
        print(f"Search: '{query}'")
        results = semantic_memory.search(query, limit=3)
        for r in results:
            print(f"  → [{r['score']:.2f}] {r['content'][:50]}...")
        print()
    
    # Summary
    print("Summary:", semantic_memory.get_summary())
    print("\n✅ Semantic Memory test complete!")
