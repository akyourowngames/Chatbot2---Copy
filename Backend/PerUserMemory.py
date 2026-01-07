"""
Advanced Per-User Memory System - Beast Mode
=============================================
Semantic vector memory with:
- Per-user isolation (not unified)
- pgvector embeddings via Supabase
- Memory compression for old conversations
- Cross-session context linking
- Importance decay over time
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import embedding providers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMER_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMER_AVAILABLE = False
    logger.warning("[MEMORY] sentence-transformers not installed, using fallback embeddings")


@dataclass
class MemoryItem:
    """Single memory unit"""
    id: str
    user_id: str
    content: str
    embedding: List[float]
    category: str  # personal, fact, preference, event, context
    importance: float  # 0.0 - 1.0
    session_id: str  # Links to chat session
    created_at: str
    last_accessed: str
    access_count: int
    compressed: bool = False
    parent_memory_id: Optional[str] = None  # For compressed memories
    metadata: Dict = None

    def to_dict(self) -> dict:
        return asdict(self)


class PerUserMemorySystem:
    """
    Advanced memory system with per-user isolation.
    Each user has their own memory space - no cross-user data leakage.
    """
    
    def __init__(self):
        self.embedding_model = None
        self.embedding_dim = 384  # Default for all-MiniLM-L6-v2
        
        # Initialize embedding model
        self._init_embedding_model()
        
        # Supabase client
        self.supabase = None
        self._init_supabase()
        
        # Memory compression settings
        self.compression_threshold_days = 7  # Compress memories older than this
        self.compression_min_count = 5  # Min memories to compress together
        self.importance_decay_rate = 0.02  # Daily decay rate
        
        # 🔧 BEAST MODE: Content hash cache for deduplication
        self._content_hashes: Dict[str, set] = {}  # user_id -> set of content hashes
        self._embedding_cache: Dict[str, List[float]] = {}  # text_hash -> embedding
        self._cache_max_size = 500
        
        logger.info("[MEMORY] Per-User Memory System initialized (Beast Mode)")
    
    def _init_embedding_model(self):
        """Initialize the embedding model"""
        if SENTENCE_TRANSFORMER_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.embedding_dim = 384
                logger.info("[MEMORY] Loaded SentenceTransformer embedding model")
            except Exception as e:
                logger.error(f"[MEMORY] Failed to load SentenceTransformer: {e}")
                self.embedding_model = None
        else:
            self.embedding_model = None
    
    def _init_supabase(self):
        """Initialize Supabase client"""
        try:
            from supabase import create_client
            url = os.getenv("SUPABASE_URL", "https://skbfmcwrshxnmaxfqyaw.supabase.co")
            key = os.getenv("SUPABASE_KEY", "sb_secret_kT3r_lTsBYBLwpv313A0qQ_przZ-Q8v")
            self.supabase = create_client(url, key)
            logger.info("[MEMORY] Supabase connected for vector storage")
        except Exception as e:
            logger.error(f"[MEMORY] Supabase connection failed: {e}")
            self.supabase = None
    
    # ==================== EMBEDDING GENERATION ====================
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text with caching."""
        # 🔧 BEAST MODE: Check cache first
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self._embedding_cache:
            return self._embedding_cache[text_hash]
        
        if self.embedding_model:
            try:
                import time
                start = time.time()
                embedding = self.embedding_model.encode(text, convert_to_numpy=True)
                result = embedding.tolist()
                duration_ms = (time.time() - start) * 1000
                logger.debug(f"[MEMORY] Embedding generated in {duration_ms:.0f}ms")
                
                # Cache the result
                self._cache_embedding(text_hash, result)
                return result
            except Exception as e:
                logger.error(f"[MEMORY] Embedding error: {e}")
        
        # Fallback: Simple hash-based pseudo-embedding
        return self._fallback_embedding(text)
    
    def _generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        🔧 BEAST MODE: Generate embeddings for multiple texts at once.
        Up to 3x faster than individual calls.
        """
        if not texts:
            return []
        
        # Check cache for all texts
        results = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []
        
        for i, text in enumerate(texts):
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if text_hash in self._embedding_cache:
                results[i] = self._embedding_cache[text_hash]
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)
        
        # Batch encode uncached texts
        if uncached_texts and self.embedding_model:
            try:
                import time
                start = time.time()
                embeddings = self.embedding_model.encode(uncached_texts, convert_to_numpy=True, batch_size=32)
                duration_ms = (time.time() - start) * 1000
                logger.info(f"[MEMORY] Batch embedded {len(uncached_texts)} texts in {duration_ms:.0f}ms")
                
                for idx, embedding in zip(uncached_indices, embeddings):
                    result = embedding.tolist()
                    results[idx] = result
                    # Cache each result
                    text_hash = hashlib.md5(texts[idx].encode()).hexdigest()
                    self._cache_embedding(text_hash, result)
                    
            except Exception as e:
                logger.error(f"[MEMORY] Batch embedding error: {e}")
                # Fallback to individual encoding
                for idx in uncached_indices:
                    results[idx] = self._fallback_embedding(texts[idx])
        else:
            # Fallback for uncached without model
            for idx in uncached_indices:
                results[idx] = self._fallback_embedding(texts[idx])
        
        return results
    
    def _cache_embedding(self, text_hash: str, embedding: List[float]):
        """Cache an embedding with size limit."""
        if len(self._embedding_cache) >= self._cache_max_size:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(self._embedding_cache.keys())[:100]
            for key in keys_to_remove:
                del self._embedding_cache[key]
        self._embedding_cache[text_hash] = embedding
    
    def _fallback_embedding(self, text: str) -> List[float]:
        """Fallback embedding using word hashing"""
        # Create a deterministic pseudo-embedding from text
        words = text.lower().split()
        embedding = [0.0] * self.embedding_dim
        
        for i, word in enumerate(words):
            hash_val = int(hashlib.md5(word.encode()).hexdigest(), 16)
            for j in range(min(10, self.embedding_dim)):
                idx = (hash_val + j * 100) % self.embedding_dim
                embedding[idx] += 1.0 / (i + 1)  # Weight by position
        
        # Normalize
        magnitude = sum(x**2 for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = sum(a**2 for a in vec1) ** 0.5
        mag2 = sum(b**2 for b in vec2) ** 0.5
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    # ==================== MEMORY OPERATIONS ====================
    
    def add_memory(self, user_id: str, content: str, category: str = "general",
                   importance: float = 0.5, session_id: str = None,
                   metadata: Dict = None) -> Optional[str]:
        """
        Add a new memory for a specific user.
        
        Args:
            user_id: Unique user identifier (e.g., Firebase UID)
            content: Memory content
            category: personal/fact/preference/event/context
            importance: 0.0 to 1.0
            session_id: Chat session ID for cross-session linking
            metadata: Additional data
            
        Returns:
            Memory ID if successful
        """
        if not user_id or not content:
            return None
        
        # 🔧 BEAST MODE: Fast deduplication via content hash
        content_hash = hashlib.md5(content.encode()).hexdigest()
        if user_id in self._content_hashes and content_hash in self._content_hashes[user_id]:
            logger.debug(f"[MEMORY] Skipping duplicate content for user {user_id[:8]}")
            return None
        
        # Generate embedding
        embedding = self._generate_embedding(content)
        
        # Check for similar memories (semantic dedup)
        existing = self.search_similar(user_id, content, limit=1, threshold=0.9)
        if existing:
            # Update existing memory instead
            return self._update_existing_memory(existing[0], content, importance)
        
        # Create memory ID
        memory_id = f"mem_{user_id[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
        
        now = datetime.now().isoformat()
        
        memory_data = {
            'id': memory_id,
            'user_id': user_id,
            'content': content,
            'embedding': embedding,
            'category': category,
            'importance': min(1.0, max(0.0, importance)),
            'session_id': session_id or 'global',
            'created_at': now,
            'last_accessed': now,
            'access_count': 0,
            'compressed': False,
            'parent_memory_id': None,
            'metadata': json.dumps(metadata or {})
        }
        
        # Save to Supabase with retry logic
        if self.supabase:
            saved = self._save_to_supabase_with_retry(memory_data, max_retries=3)
            if saved:
                logger.info(f"[MEMORY] ✅ Synced to Supabase for user {user_id[:8]}: {content[:40]}...")
                # Add to content hash cache
                if user_id not in self._content_hashes:
                    self._content_hashes[user_id] = set()
                self._content_hashes[user_id].add(content_hash)
                return memory_id
            else:
                logger.warning(f"[MEMORY] ⚠️ Supabase save failed, memory only in local cache")
        
        return None
    
    def _save_to_supabase_with_retry(self, data: Dict, max_retries: int = 3) -> bool:
        """Save to Supabase with exponential backoff retry"""
        import time
        
        for attempt in range(max_retries):
            try:
                # Convert embedding to JSON string format
                data_copy = data.copy()
                if 'embedding' in data_copy and isinstance(data_copy['embedding'], list):
                    data_copy['embedding'] = json.dumps(data_copy['embedding'])
                
                # Try to insert
                result = self.supabase.table('user_memories').insert(data_copy).execute()
                
                if result.data:
                    return True
                    
            except Exception as e:
                error_str = str(e).lower()
                
                # Table doesn't exist - try to create it
                if "does not exist" in error_str or "relation" in error_str:
                    logger.warning(f"[MEMORY] Table doesn't exist, attempting to create...")
                    # Note: Actual table creation needs to be done in Supabase dashboard
                    # This is just for logging
                    logger.error(f"[MEMORY] Please create 'user_memories' table in Supabase")
                    return False
                
                # Retry on network/timeout errors
                if attempt < max_retries - 1:
                    if any(err in error_str for err in ["timeout", "connection", "network", "unavailable"]):
                        wait_time = (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                        logger.warning(f"[MEMORY] Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                
                # Log final error
                if attempt == max_retries - 1:
                    logger.error(f"[MEMORY] Supabase save failed after {max_retries} attempts: {e}")
                
            except KeyboardInterrupt:
                raise
        
        return False

    
    def _update_existing_memory(self, existing: Dict, new_content: str, 
                                 new_importance: float) -> str:
        """Update an existing similar memory"""
        memory_id = existing.get('id')
        current_importance = existing.get('importance', 0.5)
        access_count = existing.get('access_count', 0) + 1
        
        # Boost importance if accessed again
        updated_importance = min(1.0, max(current_importance, new_importance) + 0.05)
        
        if self.supabase:
            try:
                self.supabase.table('user_memories').update({
                    'importance': updated_importance,
                    'access_count': access_count,
                    'last_accessed': datetime.now().isoformat()
                }).eq('id', memory_id).execute()
                logger.info(f"[MEMORY] Updated existing: {memory_id}")
            except Exception as e:
                logger.error(f"[MEMORY] Update failed: {e}")
        
        return memory_id
    
    def search_similar(self, user_id: str, query: str, limit: int = 5,
                       threshold: float = 0.3, category: str = None) -> List[Dict]:
        """
        Search for semantically similar memories FOR A SPECIFIC USER ONLY.
        
        Args:
            user_id: User to search memories for (REQUIRED)
            query: Search query
            limit: Max results
            threshold: Minimum similarity score (0-1)
            category: Optional category filter
            
        Returns:
            List of matching memories with similarity scores
        """
        if not user_id or not query:
            return []
        
        query_embedding = self._generate_embedding(query)
        
        if self.supabase:
            try:
                # Get user's memories only
                query_builder = self.supabase.table('user_memories')\
                    .select('*')\
                    .eq('user_id', user_id)\
                    .eq('compressed', False)
                
                if category:
                    query_builder = query_builder.eq('category', category)
                
                data = query_builder.execute()
                
                if not data.data:
                    return []
                
                # Calculate similarities
                results = []
                for mem in data.data:
                    try:
                        mem_embedding = json.loads(mem.get('embedding', '[]'))
                        similarity = self._cosine_similarity(query_embedding, mem_embedding)
                        
                        if similarity >= threshold:
                            results.append({
                                **mem,
                                'similarity': similarity,
                                'embedding': None  # Don't return raw embedding
                            })
                    except:
                        continue
                
                # Sort by similarity and limit
                results.sort(key=lambda x: x['similarity'], reverse=True)
                return results[:limit]
                
            except Exception as e:
                logger.error(f"[MEMORY] Search failed: {e}")
        
        return []
    
    def get_context_for_session(self, user_id: str, session_id: str,
                                 current_query: str = None) -> List[Dict]:
        """
        Get relevant context from previous sessions for cross-session linking.
        
        Args:
            user_id: User ID
            session_id: Current session ID
            current_query: Current query for relevance matching
            
        Returns:
            List of relevant memories from other sessions
        """
        if not user_id:
            return []
        
        if self.supabase:
            try:
                # Get memories from OTHER sessions
                data = self.supabase.table('user_memories')\
                    .select('*')\
                    .eq('user_id', user_id)\
                    .neq('session_id', session_id)\
                    .order('importance', desc=True)\
                    .order('last_accessed', desc=True)\
                    .limit(20)\
                    .execute()
                
                if not data.data:
                    return []
                
                # If we have a query, filter by relevance
                if current_query:
                    query_embedding = self._generate_embedding(current_query)
                    scored = []
                    for mem in data.data:
                        try:
                            mem_embedding = json.loads(mem.get('embedding', '[]'))
                            similarity = self._cosine_similarity(query_embedding, mem_embedding)
                            if similarity > 0.2:  # Low threshold for context
                                scored.append({**mem, 'relevance': similarity})
                        except:
                            continue
                    scored.sort(key=lambda x: x['relevance'], reverse=True)
                    return scored[:10]
                
                return data.data[:10]
                
            except Exception as e:
                logger.error(f"[MEMORY] Get context failed: {e}")
        
        return []
    
    def get_user_memories(self, user_id: str, category: str = None,
                          limit: int = 50, include_compressed: bool = False) -> List[Dict]:
        """Get all memories for a user"""
        if not user_id:
            return []
        
        if self.supabase:
            try:
                query = self.supabase.table('user_memories')\
                    .select('*')\
                    .eq('user_id', user_id)
                
                if category:
                    query = query.eq('category', category)
                
                if not include_compressed:
                    query = query.eq('compressed', False)
                
                data = query.order('importance', desc=True)\
                    .order('last_accessed', desc=True)\
                    .limit(limit)\
                    .execute()
                
                # Don't return raw embeddings
                results = []
                for mem in data.data or []:
                    mem['embedding'] = None
                    results.append(mem)
                
                return results
                
            except Exception as e:
                logger.error(f"[MEMORY] Get memories failed: {e}")
        
        return []
    
    # ==================== MEMORY COMPRESSION ====================
    
    def compress_old_memories(self, user_id: str) -> int:
        """
        Compress old memories into summaries to save space.
        
        Returns number of memories compressed
        """
        if not user_id or not self.supabase:
            return 0
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=self.compression_threshold_days)).isoformat()
            
            # Get old, uncompressed memories
            data = self.supabase.table('user_memories')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('compressed', False)\
                .lt('created_at', cutoff_date)\
                .order('category')\
                .execute()
            
            if not data.data or len(data.data) < self.compression_min_count:
                return 0
            
            # Group by category
            by_category = {}
            for mem in data.data:
                cat = mem.get('category', 'general')
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(mem)
            
            compressed_count = 0
            
            for category, memories in by_category.items():
                if len(memories) >= self.compression_min_count:
                    # Create compressed summary
                    contents = [m['content'] for m in memories]
                    summary = self._summarize_memories(contents)
                    
                    # Average importance
                    avg_importance = sum(m['importance'] for m in memories) / len(memories)
                    
                    # Create compressed memory
                    self.add_memory(
                        user_id=user_id,
                        content=f"[COMPRESSED SUMMARY] {summary}",
                        category=f"{category}_summary",
                        importance=min(1.0, avg_importance + 0.1),
                        metadata={
                            'compressed_from': [m['id'] for m in memories],
                            'original_count': len(memories),
                            'date_range': f"{memories[0]['created_at']} to {memories[-1]['created_at']}"
                        }
                    )
                    
                    # Mark originals as compressed
                    for mem in memories:
                        self.supabase.table('user_memories').update({
                            'compressed': True
                        }).eq('id', mem['id']).execute()
                    
                    compressed_count += len(memories)
                    logger.info(f"[MEMORY] Compressed {len(memories)} {category} memories for user {user_id[:8]}")
            
            return compressed_count
            
        except Exception as e:
            logger.error(f"[MEMORY] Compression failed: {e}")
            return 0
    
    def _summarize_memories(self, contents: List[str]) -> str:
        """Create a summary from multiple memory contents"""
        # Simple summary: extract key phrases
        all_text = " ".join(contents)
        
        # Extract sentences
        sentences = re.split(r'[.!?]', all_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        # Keep unique key information
        unique_info = []
        seen = set()
        for s in sentences[:20]:  # Limit
            key = s.lower()[:50]
            if key not in seen:
                seen.add(key)
                unique_info.append(s[:100])
        
        return " | ".join(unique_info[:5])
    
    # ==================== IMPORTANCE DECAY ====================
    
    def apply_importance_decay(self, user_id: str) -> int:
        """
        Apply time-based decay to memory importance.
        Memories that aren't accessed decay in importance.
        
        Returns number of memories decayed
        """
        if not user_id or not self.supabase:
            return 0
        
        try:
            # Get uncompressed memories
            data = self.supabase.table('user_memories')\
                .select('id, importance, last_accessed, access_count')\
                .eq('user_id', user_id)\
                .eq('compressed', False)\
                .execute()
            
            if not data.data:
                return 0
            
            decayed_count = 0
            now = datetime.now()
            
            for mem in data.data:
                try:
                    last_accessed = datetime.fromisoformat(mem['last_accessed'].replace('Z', '+00:00'))
                    days_since_access = (now - last_accessed.replace(tzinfo=None)).days
                    
                    if days_since_access > 0:
                        current_importance = mem['importance']
                        access_count = mem.get('access_count', 0)
                        
                        # Decay formula: importance * (1 - decay_rate)^days * access_bonus
                        access_bonus = min(1.0, 1.0 + (access_count * 0.01))
                        new_importance = current_importance * ((1 - self.importance_decay_rate) ** days_since_access) * access_bonus
                        new_importance = max(0.1, min(1.0, new_importance))  # Clamp
                        
                        if abs(new_importance - current_importance) > 0.01:
                            self.supabase.table('user_memories').update({
                                'importance': new_importance
                            }).eq('id', mem['id']).execute()
                            decayed_count += 1
                            
                except Exception as inner_e:
                    continue
            
            logger.info(f"[MEMORY] Decayed importance for {decayed_count} memories (user {user_id[:8]})")
            return decayed_count
            
        except Exception as e:
            logger.error(f"[MEMORY] Decay failed: {e}")
            return 0
    
    # ==================== STATS & MANAGEMENT ====================
    
    def get_memory_stats(self, user_id: str) -> Dict:
        """Get memory statistics for a user"""
        if not user_id or not self.supabase:
            return {"total": 0, "categories": {}, "compressed": 0}
        
        try:
            data = self.supabase.table('user_memories')\
                .select('category, compressed, importance')\
                .eq('user_id', user_id)\
                .execute()
            
            if not data.data:
                return {"total": 0, "categories": {}, "compressed": 0}
            
            categories = {}
            compressed = 0
            total_importance = 0
            
            for mem in data.data:
                cat = mem.get('category', 'general')
                categories[cat] = categories.get(cat, 0) + 1
                if mem.get('compressed'):
                    compressed += 1
                total_importance += mem.get('importance', 0.5)
            
            return {
                "total": len(data.data),
                "active": len(data.data) - compressed,
                "compressed": compressed,
                "categories": categories,
                "avg_importance": total_importance / len(data.data) if data.data else 0
            }
            
        except Exception as e:
            logger.error(f"[MEMORY] Stats failed: {e}")
            return {"total": 0, "categories": {}, "compressed": 0}
    
    def delete_user_memories(self, user_id: str, category: str = None) -> bool:
        """Delete memories for a user (GDPR compliance)"""
        if not user_id or not self.supabase:
            return False
        
        try:
            query = self.supabase.table('user_memories').delete().eq('user_id', user_id)
            
            if category:
                query = query.eq('category', category)
            
            query.execute()
            logger.info(f"[MEMORY] Deleted memories for user {user_id[:8]}")
            return True
            
        except Exception as e:
            logger.error(f"[MEMORY] Delete failed: {e}")
            return False
    
    def _create_memories_table(self) -> bool:
        """Create the user_memories table if it doesn't exist"""
        # This needs to be done in Supabase dashboard or via SQL
        logger.warning("[MEMORY] Please create 'user_memories' table in Supabase with columns:")
        logger.warning("  - id (text, primary key)")
        logger.warning("  - user_id (text, indexed)")
        logger.warning("  - content (text)")
        logger.warning("  - embedding (text/jsonb)")
        logger.warning("  - category (text)")
        logger.warning("  - importance (float)")
        logger.warning("  - session_id (text)")
        logger.warning("  - created_at (timestamp)")
        logger.warning("  - last_accessed (timestamp)")
        logger.warning("  - access_count (integer)")
        logger.warning("  - compressed (boolean)")
        logger.warning("  - parent_memory_id (text, nullable)")
        logger.warning("  - metadata (jsonb)")
        return False


# Global instance
per_user_memory = PerUserMemorySystem()


# ==================== CONVENIENCE FUNCTIONS ====================

def remember(user_id: str, content: str, category: str = "general", 
             importance: float = 0.5, session_id: str = None) -> bool:
    """Quick function to save a memory"""
    return per_user_memory.add_memory(user_id, content, category, importance, session_id) is not None


def recall(user_id: str, query: str, limit: int = 5) -> List[Dict]:
    """Quick function to search memories"""
    return per_user_memory.search_similar(user_id, query, limit)


def get_context(user_id: str, session_id: str, query: str = None) -> List[Dict]:
    """Quick function to get cross-session context"""
    return per_user_memory.get_context_for_session(user_id, session_id, query)


if __name__ == "__main__":
    # Test
    test_user = "test_user_123"
    
    print("Testing Per-User Memory System...")
    
    # Add memories
    per_user_memory.add_memory(test_user, "I prefer dark mode interfaces", "preference", 0.8)
    per_user_memory.add_memory(test_user, "My favorite programming language is Python", "preference", 0.7)
    per_user_memory.add_memory(test_user, "I'm working on a chatbot project called KAI", "context", 0.9)
    
    # Search
    results = per_user_memory.search_similar(test_user, "coding preferences")
    print(f"\nSearch results for 'coding preferences':")
    for r in results:
        print(f"  [{r['similarity']:.2f}] {r['content']}")
    
    # Stats
    stats = per_user_memory.get_memory_stats(test_user)
    print(f"\nMemory stats: {stats}")
