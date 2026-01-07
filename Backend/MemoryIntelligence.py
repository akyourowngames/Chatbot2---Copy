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
        
        # 1. Check for explicit "remember" commands FIRST (highest priority)
        for pattern in self.patterns["explicit"]:
            matches = re.findall(pattern, message_lower, re.IGNORECASE)
            for match in matches:
                content = match.strip() if isinstance(match, str) else " ".join(match).strip()
                if len(content) > 3:
                    # Get category from content
                    category = self._detect_category_from_content(content)
                    memory = self._create_memory(content, category, user_message)
                    memory["importance"] = min(1.0, memory["importance"] + 0.2)  # Boost explicit memories
                    if memory and not self._is_duplicate(memory, extracted):
                        extracted.append(memory)
                        logger.info(f"[MEMORY-INTEL] Explicit memory: {content[:50]}...")
        
        # 2. Extract from patterns
        for category, patterns in self.patterns.items():
            if category == "explicit":
                continue  # Already handled
                
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
        
        # 3. Extract from AI response if it confirms something
        if ai_response:
            confirmation_patterns = [
                r"(?:i'll remember|noted|got it|okay),? (?:that )?(.+?)(?:\.|$|!)",
                r"(?:understood|i(?:'ll| will) note) (?:that )?(.+?)(?:\.|$|!)"
            ]
            for pattern in confirmation_patterns:
                matches = re.findall(pattern, ai_response.lower(), re.IGNORECASE)
                for match in matches:
                    content = match.strip()
                    if len(content) > 5 and len(content) < 150:
                        category = self._detect_category_from_content(content)
                        memory = self._create_memory(content, category, user_message)
                        if memory and not self._is_duplicate(memory, extracted):
                            extracted.append(memory)
        
        if extracted:
            logger.info(f"[MEMORY-INTEL] ✅ Extracted {len(extracted)} memories from conversation")
        
        return extracted
    
    def _detect_category_from_content(self, content: str) -> str:
        """Detect category from memory content"""
        content_lower = content.lower()
        
        # Category keywords
        category_keywords = {
            "personal": ["my name", "i am", "i'm", "i live", "my age", "my birthday", "born"],
            "work": ["job", "work at", "company", "office", "colleague", "boss", "salary"],
            "preference": ["like", "prefer", "favorite", "love", "enjoy", "hate", "dislike"],
            "project": ["working on", "building", "project", "developing", "creating", "app", "website"],
            "task": ["need to", "have to", "must", "should", "remind me", "todo", "task"],
            "location": ["live in", "from", "located in", "city", "country"],
            "date": ["birthday", "anniversary", "deadline", "scheduled"],
        }
        
        # Score each category
        scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                scores[category] = score
        
        # Return highest scoring category
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return "general"

    
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
        - Category weight (higher for personal/project/task)
        - Emotional weight (emotional memories more memorable)
        - Content indicators (important, critical, etc.)
        - Entity presence (names, specific things)
        - Length (moderate length preferred)
        """
        score = 0.0
        content = memory.get("content", "").lower()
        
        # 1. Base category weight (IMPROVED WEIGHTS)
        category = memory.get("category", "general")
        category_weights = {
            "explicit": 0.95,    # User explicitly asked to remember
            "personal": 0.90,    # Names, personal info - very important
            "project": 0.85,     # Work/projects - high importance
            "task": 0.80,        # Tasks/todos - important
            "preference": 0.75,  # Preferences - fairly important  
            "date": 0.70,        # Dates/events - moderate importance
            "work": 0.65,        # Work info - moderate
            "location": 0.60,    # Location info
            "name": 0.90,        # Name category
            "emotion": 0.70,     # Emotional content
            "general": 0.40      # Uncategorized - lower
        }
        score += category_weights.get(category, 0.4)
        
        # 2. Emotional weight (ENHANCED)
        emotion = memory.get("emotion", "neutral")
        if emotion == "positive":
            score += 0.10
        elif emotion == "negative":
            score += 0.15  # Negative memories often more important to remember
        
        # 3. Importance indicators in content (NEW)
        importance_indicators = {
            "important": 0.20,
            "critical": 0.25,
            "urgent": 0.20,
            "remember": 0.15,
            "never forget": 0.25,
            "always": 0.10,
            "must": 0.15,
            "need to": 0.10,
            "have to": 0.10,
            "essential": 0.20,
            "crucial": 0.20
        }
        
        for indicator, boost in importance_indicators.items():
            if indicator in content:
                score += boost
                break  # Only count once
        
        # 4. Entity boost (names, specific things are important)
        entities = memory.get("entities", [])
        if entities:
            score += min(0.15, len(entities) * 0.03)
        
        # 5. Proper nouns boost (NEW)
        original = memory.get("original", memory.get("content", ""))
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', original)
        if proper_nouns:
            score += min(0.10, len(proper_nouns) * 0.03)
        
        # 6. Content length factor (prefer moderate length)
        word_count = len(content.split())
        if 3 <= word_count <= 20:
            score += 0.10
        elif 20 < word_count <= 40:
            score += 0.05
        elif word_count < 3:
            score -= 0.10  # Too short, probably not important
        
        # 7. Numbers/dates boost (specific info is valuable)
        if re.search(r'\d+', content):
            score += 0.05
        
        # Normalize to 0-1
        return min(1.0, max(0.1, score))
    
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
