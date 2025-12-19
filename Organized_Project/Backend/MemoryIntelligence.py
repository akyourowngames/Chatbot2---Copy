"""
Memory Intelligence System - Smart Auto-Extraction & Importance Scoring
========================================================================
Automatically extracts important information from conversations,
scores memory importance, and finds related memories.
"""

import re
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryIntelligence:
    """Intelligent memory extraction and scoring system"""
    
    def __init__(self):
        self.patterns = self._compile_patterns()
        self.emotion_keywords = self._load_emotion_keywords()
        self.importance_weights = {
            "name": 0.9,
            "preference": 0.8,
            "task": 0.7,
            "project": 0.85,
            "date": 0.6,
            "location": 0.5,
            "emotion": 0.7,
            "general": 0.4
        }
        logger.info("[MEMORY-INTEL] Memory Intelligence initialized")
    
    def _compile_patterns(self) -> Dict:
        """Compile regex patterns for extraction"""
        return {
            # Name patterns
            "name": [
                r"my name is (\w+)",
                r"i'm (\w+)",
                r"i am (\w+)",
                r"call me (\w+)",
                r"this is (\w+)",
            ],
            
            # Preference patterns
            "preference": [
                r"i (?:really )?(?:love|like|enjoy|prefer) (.+?)(?:\.|$|,)",
                r"i (?:hate|dislike|don't like) (.+?)(?:\.|$|,)",
                r"my favorite (.+?) is (.+?)(?:\.|$|,)",
                r"i'm a fan of (.+?)(?:\.|$|,)",
                r"i'm into (.+?)(?:\.|$|,)",
            ],
            
            # Task/Work patterns
            "task": [
                r"i(?:'m| am) working on (.+?)(?:\.|$|,)",
                r"i need to (.+?)(?:\.|$|,)",
                r"i have to (.+?)(?:\.|$|,)",
                r"i'm trying to (.+?)(?:\.|$|,)",
                r"my goal is to (.+?)(?:\.|$|,)",
            ],
            
            # Project patterns
            "project": [
                r"(?:my |the )?project (?:is |called )?(.+?)(?:\.|$|,)",
                r"i'm building (.+?)(?:\.|$|,)",
                r"i'm developing (.+?)(?:\.|$|,)",
                r"i'm creating (.+?)(?:\.|$|,)",
            ],
            
            # Date patterns
            "date": [
                r"(?:my )?birthday is (.+?)(?:\.|$|,)",
                r"(?:on|at) (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                r"remember (?:that )?(.+?) (?:is|was) on (.+?)(?:\.|$)",
            ],
            
            # Location patterns
            "location": [
                r"i live in (.+?)(?:\.|$|,)",
                r"i'm from (.+?)(?:\.|$|,)",
                r"i'm located in (.+?)(?:\.|$|,)",
                r"my (?:home|office|workplace) is (?:in|at) (.+?)(?:\.|$|,)",
            ],
            
            # Explicit remember patterns
            "explicit": [
                r"remember (?:that )?(.+?)(?:\.|$)",
                r"don't forget (?:that )?(.+?)(?:\.|$)",
                r"note (?:that )?(.+?)(?:\.|$)",
                r"keep in mind (?:that )?(.+?)(?:\.|$)",
            ]
        }
    
    def _load_emotion_keywords(self) -> Dict[str, List[str]]:
        """Load emotion detection keywords"""
        return {
            "positive": ["love", "like", "enjoy", "happy", "excited", "great", "awesome", 
                        "amazing", "wonderful", "fantastic", "pleased", "glad", "thrilled"],
            "negative": ["hate", "dislike", "sad", "angry", "frustrated", "annoyed", 
                        "disappointed", "upset", "worried", "anxious", "stressed"],
            "neutral": ["think", "believe", "know", "understand", "remember", "need", "want"]
        }
    
    def auto_extract(self, user_message: str, ai_response: str = "") -> List[Dict]:
        """
        Automatically extract important information from a conversation
        
        Args:
            user_message: User's message
            ai_response: AI's response (optional, for context)
            
        Returns:
            List of extracted memories with metadata
        """
        extracted = []
        message_lower = user_message.lower()
        
        # Check each pattern category
        for category, patterns in self.patterns.items():
            if category == "explicit":
                continue  # Handle explicit separately
                
            for pattern in patterns:
                matches = re.findall(pattern, message_lower, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        content = " ".join(match).strip()
                    else:
                        content = match.strip()
                    
                    if len(content) > 2 and len(content) < 200:  # Reasonable length
                        memory = self._create_memory(content, category, user_message)
                        if memory and not self._is_duplicate(memory, extracted):
                            extracted.append(memory)
        
        # Handle explicit "remember" commands
        for pattern in self.patterns["explicit"]:
            matches = re.findall(pattern, message_lower, re.IGNORECASE)
            for match in matches:
                content = match.strip() if isinstance(match, str) else " ".join(match).strip()
                if len(content) > 2:
                    memory = self._create_memory(content, "explicit", user_message)
                    memory["importance"] = 1.0  # Explicit memories are highest priority
                    if memory and not self._is_duplicate(memory, extracted):
                        extracted.append(memory)
        
        logger.info(f"[MEMORY-INTEL] Extracted {len(extracted)} memories from conversation")
        return extracted
    
    def _create_memory(self, content: str, category: str, original: str) -> Dict:
        """Create a memory object with metadata"""
        emotion = self._detect_emotion(original)
        importance = self.score_importance({
            "content": content,
            "category": category,
            "emotion": emotion,
            "original": original
        })
        
        return {
            "content": content,
            "category": category,
            "emotion": emotion,
            "importance": importance,
            "entities": self._extract_entities(content),
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "access_count": 1,
            "source": "auto_extract"
        }
    
    def _detect_emotion(self, text: str) -> str:
        """Detect emotional tone of text"""
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.emotion_keywords["positive"] if word in text_lower)
        negative_count = sum(1 for word in self.emotion_keywords["negative"] if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text"""
        entities = []
        
        # Capitalize words (likely names/proper nouns)
        words = text.split()
        for word in words:
            # Skip common words
            if word.lower() in ["i", "my", "the", "a", "an", "is", "are", "was", "were"]:
                continue
            if word[0].isupper() and len(word) > 1:
                entities.append(word)
        
        # Programming languages, technologies
        tech_keywords = ["python", "javascript", "react", "node", "ai", "ml", "web", "app", 
                        "api", "database", "sql", "html", "css", "java", "c++", "rust"]
        for tech in tech_keywords:
            if tech in text.lower():
                entities.append(tech.title())
        
        return list(set(entities))[:10]  # Limit to 10 entities
    
    def _is_duplicate(self, memory: Dict, existing: List[Dict]) -> bool:
        """Check if memory is duplicate"""
        for m in existing:
            if m["content"].lower() == memory["content"].lower():
                return True
            # Fuzzy match - 80% overlap
            words1 = set(m["content"].lower().split())
            words2 = set(memory["content"].lower().split())
            if words1 and words2:
                overlap = len(words1.intersection(words2)) / max(len(words1), len(words2))
                if overlap > 0.8:
                    return True
        return False
    
    def score_importance(self, memory: Dict) -> float:
        """
        Score the importance of a memory (0.0 to 1.0)
        
        Factors:
        - Category weight
        - Emotional weight
        - Content length (moderate is better)
        - Specificity (entities boost)
        """
        score = 0.0
        
        # Base category weight
        category = memory.get("category", "general")
        score += self.importance_weights.get(category, 0.4)
        
        # Emotional weight
        emotion = memory.get("emotion", "neutral")
        if emotion == "positive":
            score += 0.1
        elif emotion == "negative":
            score += 0.15  # Negative memories often more important to remember
        
        # Content length factor (prefer moderate length)
        content = memory.get("content", "")
        word_count = len(content.split())
        if 3 <= word_count <= 15:
            score += 0.1
        elif word_count > 15:
            score += 0.05
        
        # Entity boost
        entities = memory.get("entities", [])
        if entities:
            score += min(0.15, len(entities) * 0.03)
        
        # Normalize to 0-1
        return min(1.0, max(0.0, score))
    
    def decay_importance(self, memory: Dict, days_old: int) -> float:
        """Apply time decay to importance score"""
        base_importance = memory.get("importance", 0.5)
        access_count = memory.get("access_count", 1)
        
        # Decay factor: loses 10% importance per week, but access slows decay
        decay_rate = 0.1 / 7  # per day
        access_boost = min(0.3, access_count * 0.05)  # Accessed memories decay slower
        
        decayed = base_importance * (1 - (decay_rate * days_old)) + access_boost
        return max(0.1, min(1.0, decayed))  # Keep minimum 0.1
    
    def find_related_memories(self, memory: Dict, all_memories: List[Dict], limit: int = 5) -> List[Dict]:
        """Find memories related to the given memory"""
        related = []
        memory_entities = set(e.lower() for e in memory.get("entities", []))
        memory_words = set(memory.get("content", "").lower().split())
        
        for m in all_memories:
            if m.get("content") == memory.get("content"):
                continue
            
            # Calculate relevance score
            m_entities = set(e.lower() for e in m.get("entities", []))
            m_words = set(m.get("content", "").lower().split())
            
            # Entity overlap
            entity_overlap = len(memory_entities.intersection(m_entities))
            
            # Word overlap
            word_overlap = len(memory_words.intersection(m_words))
            
            # Same category bonus
            category_match = 1 if m.get("category") == memory.get("category") else 0
            
            relevance = entity_overlap * 3 + word_overlap * 0.5 + category_match * 2
            
            if relevance > 1:
                related.append((relevance, m))
        
        # Sort by relevance and return top matches
        related.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in related[:limit]]
    
    def consolidate_memories(self, memories: List[Dict], threshold_days: int = 30) -> List[Dict]:
        """
        Consolidate old, related memories into summaries
        
        Args:
            memories: List of all memories
            threshold_days: Age threshold for consolidation
            
        Returns:
            List of consolidated memories
        """
        now = datetime.now()
        old_memories = []
        new_memories = []
        
        for m in memories:
            created = datetime.fromisoformat(m.get("created_at", now.isoformat()))
            age = (now - created).days
            
            if age > threshold_days and m.get("importance", 1.0) < 0.5:
                old_memories.append(m)
            else:
                new_memories.append(m)
        
        if not old_memories:
            return memories
        
        # Group old memories by category
        by_category = {}
        for m in old_memories:
            cat = m.get("category", "general")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(m)
        
        # Create consolidated summaries
        consolidated = []
        for category, mems in by_category.items():
            if len(mems) >= 3:
                contents = [m["content"] for m in mems[:10]]
                summary = f"Consolidated {category} memories: " + "; ".join(contents[:5])
                
                consolidated.append({
                    "content": summary,
                    "category": f"consolidated_{category}",
                    "importance": 0.6,
                    "emotion": "neutral",
                    "entities": list(set(e for m in mems for e in m.get("entities", [])))[:10],
                    "created_at": datetime.now().isoformat(),
                    "last_accessed": datetime.now().isoformat(),
                    "access_count": sum(m.get("access_count", 1) for m in mems),
                    "source": "consolidation",
                    "original_count": len(mems)
                })
            else:
                # Keep individual memories if too few to consolidate
                consolidated.extend(mems)
        
        logger.info(f"[MEMORY-INTEL] Consolidated {len(old_memories)} old memories into {len(consolidated)}")
        return new_memories + consolidated
    
    def get_relevant_context(self, query: str, memories: List[Dict], limit: int = 5) -> str:
        """
        Get the most relevant memories for a query as context string
        
        Args:
            query: User's current query
            memories: List of all memories
            limit: Max memories to include
            
        Returns:
            Formatted context string for LLM
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Score each memory for relevance to this query
        scored = []
        for m in memories:
            content_lower = m.get("content", "").lower()
            content_words = set(content_lower.split())
            
            # Word overlap
            word_score = len(query_words.intersection(content_words))
            
            # Entity match
            entities = [e.lower() for e in m.get("entities", [])]
            entity_score = sum(2 for e in entities if e in query_lower)
            
            # Importance weight
            importance = m.get("importance", 0.5)
            
            # Recency boost
            try:
                last_accessed = datetime.fromisoformat(m.get("last_accessed", ""))
                days_ago = (datetime.now() - last_accessed).days
                recency_boost = max(0, 1 - (days_ago / 30))
            except:
                recency_boost = 0.5
            
            total_score = word_score * 2 + entity_score * 3 + importance + recency_boost
            
            if total_score > 0:
                scored.append((total_score, m))
        
        # Sort and get top matches
        scored.sort(key=lambda x: x[0], reverse=True)
        top_memories = [m for _, m in scored[:limit]]
        
        if not top_memories:
            return ""
        
        # Format as context
        context_parts = ["Relevant memories:"]
        for m in top_memories:
            category = m.get("category", "general")
            content = m.get("content", "")
            context_parts.append(f"- [{category}] {content}")
        
        return "\n".join(context_parts)


# Global instance
memory_intelligence = MemoryIntelligence()


if __name__ == "__main__":
    # Test
    print("🧠 Testing Memory Intelligence\n")
    
    test_messages = [
        "My name is Krishna and I love Python programming",
        "I'm working on an AI assistant project called KAI",
        "Remember that my birthday is on March 15th",
        "I really hate debugging at 3am",
        "I live in San Francisco and work at a tech startup",
    ]
    
    for msg in test_messages:
        print(f"Message: {msg}")
        extracted = memory_intelligence.auto_extract(msg)
        for mem in extracted:
            print(f"  → [{mem['category']}] {mem['content']} (importance: {mem['importance']:.2f})")
        print()
    
    print("✅ Memory Intelligence test complete!")
