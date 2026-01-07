"""
Contextual Memory System - JARVIS Level (UPGRADED)
===================================================
Remembers conversation context, learns preferences, builds knowledge graph.
Now with: importance scoring, categories, auto-extraction, semantic integration.
UPGRADED: Supabase sync for persistence across server restarts!
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextualMemory:
    """Enhanced contextual memory with Supabase persistence"""
    
    # Memory categories
    CATEGORIES = ["personal", "work", "preference", "task", "emotion", "project", "general"]
    
    def __init__(self):
        self.memory_file = "Data/contextual_memory.json"
        self.session_file = "Data/current_session.json"
        self.memory = self._load_memory()
        self.session = self._load_session()
        
        # Integration with intelligence modules (lazy load)
        self._memory_intel = None
        self._semantic_memory = None
        self._supabase = None  # Lazy-loaded Supabase connection
        
        # === LOAD FROM SUPABASE ON STARTUP ===
        self._sync_from_cloud()
        
        logger.info(f"[MEMORY] Loaded {len(self.memory.get('facts', []))} facts, {len(self.memory.get('conversations', []))} conversations")
        
    def _load_memory(self) -> Dict:
        """Load long-term memory from local file (fast cache)"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure all required keys exist
                    defaults = {
                        "facts": [],
                        "preferences": {},
                        "projects": [],
                        "people": [],
                        "locations": [],
                        "events": [],
                        "conversations": [],
                        "relationships": {},  # NEW: entity relationships
                        "stats": {"total_interactions": 0}  # NEW: usage stats
                    }
                    for key, default in defaults.items():
                        if key not in data:
                            data[key] = default
                    return data
            except Exception as e:
                logger.error(f"[MEMORY] Load error: {e}")
        
        return {
            "facts": [],
            "preferences": {},
            "projects": [],
            "people": [],
            "locations": [],
            "events": [],
            "conversations": [],
            "relationships": {},
            "stats": {"total_interactions": 0}
        }
    
    def _load_session(self) -> Dict:
        """Load current session context"""
        return {
            "start_time": datetime.now().isoformat(),
            "current_topic": None,
            "recent_queries": [],
            "active_tasks": [],
            "context_window": []  # NEW: sliding context window
        }
    
    @property
    def supabase(self):
        """Lazy load Supabase connection"""
        if self._supabase is None:
            try:
                from Backend.SupabaseDB import supabase_db
                self._supabase = supabase_db
            except Exception as e:
                logger.warning(f"[MEMORY] Supabase not available: {e}")
        return self._supabase
    
    def _sync_from_cloud(self):
        """Load memories from Supabase on startup"""
        if self.supabase:
            try:
                cloud_memories = self.supabase.get_memories(limit=200)
                if cloud_memories:
                    # Merge cloud memories with local
                    local_contents = set(f.get('content', '') for f in self.memory.get('facts', []))
                    for mem in cloud_memories:
                        if mem.get('content') and mem['content'] not in local_contents:
                            self.memory['facts'].append({
                                'id': mem.get('id', ''),
                                'content': mem['content'],
                                'category': mem.get('category', 'general'),
                                'importance': mem.get('importance', 0.5),
                                'timestamp': mem.get('created_at', datetime.now().isoformat()),
                                'last_accessed': mem.get('last_accessed', datetime.now().isoformat()),
                                'access_count': mem.get('access_count', 0),
                                'confidence': 1.0,
                                'cloud_synced': True
                            })
                    logger.info(f"[MEMORY] 🌐 Synced {len(cloud_memories)} memories from Supabase")
                    self._save_memory_local()  # Save to local cache
            except Exception as e:
                logger.warning(f"[MEMORY] Cloud sync error (will use local): {e}")
    
    def _save_memory(self):
        """Save memory to both local file AND Supabase"""
        # Local save (fast cache)
        self._save_memory_local()
        
        # Cloud sync happens in remember_fact directly
    
    def _save_memory_local(self):
        """Save memory to local file only"""
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[MEMORY] Local save error: {e}")
    
    @property
    def memory_intel(self):
        """Lazy load MemoryIntelligence"""
        if self._memory_intel is None:
            try:
                from Backend.MemoryIntelligence import memory_intelligence
                self._memory_intel = memory_intelligence
            except ImportError:
                logger.warning("[MEMORY] MemoryIntelligence not available")
        return self._memory_intel
    
    @property
    def semantic_memory(self):
        """Lazy load SemanticMemory"""
        if self._semantic_memory is None:
            try:
                from Backend.SemanticMemory import semantic_memory
                self._semantic_memory = semantic_memory
            except ImportError:
                logger.warning("[MEMORY] SemanticMemory not available")
        return self._semantic_memory
    
    def remember_fact(self, fact: str, category: str = "general") -> bool:
        """
        Store a new fact with metadata - NOW SYNCS TO SUPABASE!
        
        Args:
            fact: The fact to remember
            category: Category (personal, work, preference, task, emotion, general)
            
        Returns:
            True if new fact added, False if duplicate
        """
        # Validate category
        if category not in self.CATEGORIES:
            category = "general"
        
        # Calculate importance
        importance = 0.5
        if self.memory_intel:
            importance = self.memory_intel.score_importance({
                "content": fact,
                "category": category
            })
        
        fact_entry = {
            "id": f"fact_{len(self.memory['facts'])+1}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "content": fact,
            "category": category,
            "importance": importance,
            "timestamp": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "access_count": 0,
            "confidence": 1.0
        }
        
        # Avoid duplicates (fuzzy match)
        for existing in self.memory["facts"]:
            if self._is_similar(existing.get("content", ""), fact):
                # Update existing instead
                existing["importance"] = max(existing.get("importance", 0.5), importance)
                existing["access_count"] = existing.get("access_count", 0) + 1
                existing["last_accessed"] = datetime.now().isoformat()
                self._save_memory()
                return False
        
        self.memory["facts"].append(fact_entry)
        
        
        # === SYNC TO SUPABASE (PERSISTENT) ===
        # Do this FIRST to ensure data is saved even if semantic memory fails
        if self.supabase:
            try:
                self.supabase.save_memory(
                    content=fact,
                    category=category,
                    importance=importance,
                    metadata={"source": "contextual_memory"}
                )
                fact_entry["cloud_synced"] = True
                logger.info(f"[MEMORY] ☁️ Synced to Supabase: {fact[:40]}...")
            except Exception as e:
                logger.warning(f"[MEMORY] Cloud sync failed (saved locally): {e}")

        # Also add to semantic memory for vector search
        try:
            if self.semantic_memory:
                self.semantic_memory.add_memory(fact, {
                    "category": category,
                    "importance": importance,
                    "source": "contextual"
                })
        except Exception as e:
            logger.warning(f"[MEMORY] Semantic memory update failed: {e}")
        
        self._save_memory()
        logger.info(f"[MEMORY] Remembered: {fact[:50]}... (category: {category})")
        return True
    
    def _is_similar(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Check if two texts are similar"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1.intersection(words2))
        max_len = max(len(words1), len(words2))
        
        return (overlap / max_len) >= threshold
    
    def remember_preference(self, key: str, value: str):
        """Store user preference"""
        self.memory["preferences"][key] = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "access_count": 0
        }
        
        # Also store as fact for search
        self.remember_fact(f"User prefers {key}: {value}", "preference")
        
        self._save_memory()
        logger.info(f"[MEMORY] Preference: {key} = {value}")
    
    def remember_project(self, name: str, description: str = "") -> bool:
        """Remember a project"""
        project = {
            "id": f"project_{len(self.memory['projects'])+1}",
            "name": name,
            "description": description,
            "started": datetime.now().isoformat(),
            "status": "active",
            "importance": 0.85,
            "notes": [],
            "milestones": []
        }
        
        # Check if project exists
        for p in self.memory["projects"]:
            if p["name"].lower() == name.lower():
                p["description"] = description or p.get("description", "")
                p["status"] = "active"
                self._save_memory()
                return False
        
        self.memory["projects"].append(project)
        
        # Also store as fact
        self.remember_fact(f"Working on project: {name} - {description}", "project")
        
        self._save_memory()
        logger.info(f"[MEMORY] Project: {name}")
        return True
    
    def add_conversation(self, user_query: str, ai_response: str):
        """
        Add to conversation history with auto-extraction
        
        This is the main integration point - extracts memories from conversations
        """
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "user": user_query,
            "assistant": ai_response
        }
        
        self.memory["conversations"].append(conversation)
        self.session["recent_queries"].append(user_query)
        
        # Update context window (last 5 exchanges)
        self.session["context_window"].append({
            "user": user_query,
            "assistant": ai_response[:200]  # Truncate for context
        })
        if len(self.session["context_window"]) > 5:
            self.session["context_window"] = self.session["context_window"][-5:]
        
        # === AUTO-EXTRACTION ===
        if self.memory_intel:
            try:
                extracted = self.memory_intel.auto_extract(user_query, ai_response)
                for mem in extracted:
                    self.remember_fact(
                        mem.get("content", ""),
                        mem.get("category", "general")
                    )
                if extracted:
                    logger.info(f"[MEMORY] Auto-extracted {len(extracted)} memories")
            except Exception as e:
                logger.error(f"[MEMORY] Auto-extraction error: {e}")
        
        # Keep conversations within limit (increased to 500)
        if len(self.memory["conversations"]) > 500:
            self.memory["conversations"] = self.memory["conversations"][-500:]
        
        # Keep only last 20 in session
        if len(self.session["recent_queries"]) > 20:
            self.session["recent_queries"] = self.session["recent_queries"][-20:]
        
        # Update stats
        self.memory["stats"]["total_interactions"] = self.memory["stats"].get("total_interactions", 0) + 1
        
        self._save_memory()
    
    def get_context(self, query: str) -> str:
        """
        Get relevant context for a query
        
        Uses both keyword matching and semantic search
        """
        context_parts = []
        query_lower = query.lower()
        
        # 1. Check context window (recent conversation)
        if self.session["context_window"]:
            last = self.session["context_window"][-1]
            if self._is_follow_up(query, last.get("user", "")):
                context_parts.append(f"Previous: {last['user'][:100]}")
        
        # 2. Check for project references
        for project in self.memory["projects"]:
            if project["status"] == "active":
                if project["name"].lower() in query_lower or "project" in query_lower:
                    context_parts.append(f"Active project: {project['name']} - {project['description']}")
        
        # 3. Check preferences
        for key, pref in self.memory["preferences"].items():
            if key.lower() in query_lower:
                context_parts.append(f"Preference: {key} = {pref['value']}")
                # Update access count
                pref["access_count"] = pref.get("access_count", 0) + 1
        
        # 4. Semantic search for relevant facts
        if self.semantic_memory:
            try:
                results = self.semantic_memory.search(query, limit=3)
                for r in results:
                    if r.get("score", 0) > 0.4:
                        context_parts.append(f"Memory: {r.get('content', '')}")
            except Exception as e:
                logger.error(f"[MEMORY] Semantic search error: {e}")
        
        # 5. Keyword search through facts (fallback)
        if len(context_parts) < 3:
            for fact in self.memory["facts"][-20:]:  # Recent facts
                content = fact.get("content", "")
                if any(word in content.lower() for word in query_lower.split() if len(word) > 3):
                    if content not in [p.replace("Memory: ", "") for p in context_parts]:
                        context_parts.append(f"Known: {content}")
                        if len(context_parts) >= 5:
                            break
        
        # 6. Intelligent context from memory_intel
        if self.memory_intel and len(context_parts) < 3:
            try:
                intel_context = self.memory_intel.get_relevant_context(
                    query, 
                    self.memory["facts"], 
                    limit=3
                )
                if intel_context:
                    context_parts.append(intel_context)
            except:
                pass
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _is_follow_up(self, current: str, previous: str) -> bool:
        """Check if current query is a follow-up"""
        follow_up_words = ["it", "that", "this", "they", "them", "he", "she", "what about", "and", "also"]
        current_lower = current.lower()
        
        # Check for pronouns
        if any(word in current_lower.split() for word in follow_up_words):
            return True
        
        # Check for short queries (likely follow-ups)
        if len(current.split()) <= 3:
            return True
        
        # Check for continuation words
        if current_lower.startswith(("and ", "also ", "what about ", "how about ")):
            return True
        
        return False
    
    def search_memory(self, query: str, limit: int = 10) -> List[str]:
        """
        Search through memory using both keyword and semantic search
        """
        results = []
        query_lower = query.lower()
        
        # Semantic search first
        if self.semantic_memory:
            try:
                semantic_results = self.semantic_memory.search(query, limit=limit)
                results.extend([r.get("content", "") for r in semantic_results])
            except:
                pass
        
        # Keyword search for facts
        for fact in self.memory["facts"]:
            content = fact.get("content", "")
            if query_lower in content.lower() and content not in results:
                results.append(content)
        
        # Search projects
        for project in self.memory["projects"]:
            name = project.get("name", "")
            desc = project.get("description", "")
            if query_lower in name.lower() or query_lower in desc.lower():
                results.append(f"Project: {name} - {desc}")
        
        return results[:limit]
    
    def get_summary(self) -> str:
        """Get memory summary"""
        fact_categories = {}
        for fact in self.memory["facts"]:
            cat = fact.get("category", "general")
            fact_categories[cat] = fact_categories.get(cat, 0) + 1
        
        category_str = ", ".join([f"{k}: {v}" for k, v in fact_categories.items()])
        
        return f"""🧠 Memory Summary:
- {len(self.memory['facts'])} facts stored ({category_str})
- {len(self.memory['preferences'])} preferences
- {len(self.memory['projects'])} projects
- {len(self.memory['conversations'])} conversations
- {self.memory['stats'].get('total_interactions', 0)} total interactions
"""
    
    def decay_old_memories(self, days_threshold: int = 30) -> int:
        """
        Apply importance decay to old, unused memories
        
        Returns:
            Number of memories affected
        """
        now = datetime.now()
        affected = 0
        
        for fact in self.memory["facts"]:
            try:
                last_accessed = datetime.fromisoformat(fact.get("last_accessed", now.isoformat()))
                days_old = (now - last_accessed).days
                
                if days_old > days_threshold:
                    old_importance = fact.get("importance", 0.5)
                    # Decay by 10% per week after threshold
                    weeks = (days_old - days_threshold) / 7
                    decay = 0.1 * weeks
                    new_importance = max(0.1, old_importance - decay)
                    
                    if new_importance != old_importance:
                        fact["importance"] = new_importance
                        affected += 1
            except:
                pass
        
        if affected > 0:
            self._save_memory()
            logger.info(f"[MEMORY] Decayed {affected} old memories")
        
        return affected
    
    def consolidate_memories(self) -> int:
        """
        Consolidate old, low-importance memories
        
        Returns:
            Number of memories consolidated
        """
        if self.memory_intel:
            try:
                original_count = len(self.memory["facts"])
                self.memory["facts"] = self.memory_intel.consolidate_memories(
                    self.memory["facts"],
                    threshold_days=60
                )
                consolidated = original_count - len(self.memory["facts"])
                
                if consolidated > 0:
                    self._save_memory()
                    logger.info(f"[MEMORY] Consolidated {consolidated} memories")
                
                return consolidated
            except Exception as e:
                logger.error(f"[MEMORY] Consolidation error: {e}")
        
        return 0
    
    def add_relationship(self, entity1: str, relation: str, entity2: str):
        """Add a relationship between entities"""
        if "relationships" not in self.memory:
            self.memory["relationships"] = {}
        
        key = f"{entity1.lower()}|{entity2.lower()}"
        self.memory["relationships"][key] = {
            "entity1": entity1,
            "relation": relation,
            "entity2": entity2,
            "timestamp": datetime.now().isoformat()
        }
        
        self._save_memory()
        logger.info(f"[MEMORY] Relationship: {entity1} {relation} {entity2}")
    
    def get_relationships(self, entity: str) -> List[Dict]:
        """Get all relationships involving an entity"""
        entity_lower = entity.lower()
        results = []
        
        for key, rel in self.memory.get("relationships", {}).items():
            if entity_lower in key:
                results.append(rel)
        
        return results


# Global instance
contextual_memory = ContextualMemory()

if __name__ == "__main__":
    # Test
    print("🧠 Testing Enhanced Contextual Memory\n")
    
    contextual_memory.remember_fact("User likes Python programming", "preference")
    contextual_memory.remember_project("AI Assistant", "Building JARVIS-level AI")
    contextual_memory.remember_preference("favorite_language", "Python")
    
    print(contextual_memory.get_summary())
    print("\nContext for 'How's my project?':")
    print(contextual_memory.get_context("How's my project?"))
    
    print("\n✅ Contextual Memory test complete!")
