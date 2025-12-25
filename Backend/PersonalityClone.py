"""
Personality Clone - Create a Mini-You That Talks Like You
==========================================================
Analyze user's chat style and create a personalized AI clone.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PersonalityClone:
    """
    Analyze user's communication style and create a personality clone.
    The clone mimics the user's way of talking, their phrases, and personality.
    """
    
    def __init__(self):
        self._llm = None
        self.clones = {}  # Store personality profiles by user_id
        self.supported_formats = ['json', 'txt', 'csv', 'whatsapp', 'telegram', 'discord']
        logger.info("[CLONE] Personality Clone system initialized with file upload support")
    
    @property
    def llm(self):
        """Lazy load LLM."""
        if self._llm is None:
            try:
                from Backend.LLM import ChatCompletion
                self._llm = ChatCompletion
            except Exception as e:
                logger.error(f"[CLONE] LLM load failed: {e}")
        return self._llm
    
    def analyze_messages(self, messages: List[str], user_id: str = "default") -> Dict[str, Any]:
        """
        Analyze user messages to build personality profile.
        
        Args:
            messages: List of user's messages/texts
            user_id: Unique identifier for the user
            
        Returns:
            Personality profile dict
        """
        if len(messages) < 5:
            return {"status": "error", "message": "Need at least 5 messages to analyze"}
        
        logger.info(f"[CLONE] Analyzing {len(messages)} messages for {user_id}")
        
        # Basic statistics
        total_messages = len(messages)
        avg_length = sum(len(m) for m in messages) / total_messages
        
        # Count patterns
        all_text = " ".join(messages).lower()
        words = re.findall(r'\b\w+\b', all_text)
        word_freq = Counter(words)
        
        # Find signature phrases/words
        emojis = re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', all_text)
        emoji_freq = Counter(emojis)
        
        # Detect patterns
        uses_caps = sum(1 for m in messages if m.isupper()) / total_messages
        uses_emoji = len(emojis) / total_messages
        avg_word_count = sum(len(m.split()) for m in messages) / total_messages
        
        # Slang/informal detection
        slang_words = ["lol", "lmao", "bruh", "bro", "ngl", "tbh", "idk", "omg", "wtf", "fr", "imo"]
        slang_count = sum(all_text.count(s) for s in slang_words)
        
        # Question frequency
        question_rate = sum(1 for m in messages if "?" in m) / total_messages
        
        # AI-powered deep analysis
        personality_analysis = self._deep_analyze(messages)
        
        # Build profile
        profile = {
            "user_id": user_id,
            "message_count": total_messages,
            "avg_message_length": round(avg_length, 1),
            "avg_word_count": round(avg_word_count, 1),
            "top_words": [w for w, c in word_freq.most_common(10) if len(w) > 3],
            "top_emojis": [e for e, c in emoji_freq.most_common(5)],
            "emoji_usage": round(uses_emoji, 2),
            "caps_usage": round(uses_caps, 2),
            "slang_level": "high" if slang_count > 10 else "medium" if slang_count > 3 else "low",
            "question_rate": round(question_rate, 2),
            "communication_style": self._determine_style(avg_word_count, uses_emoji, slang_count),
            "personality_traits": personality_analysis.get("traits", []),
            "tone": personality_analysis.get("tone", "neutral"),
            "sample_phrases": messages[:3],
            "created_at": datetime.now().isoformat()
        }
        
        # Store the profile
        self.clones[user_id] = profile
        
        return {
            "status": "success",
            "profile": profile,
            "message": f"Personality profile created for {user_id}!"
        }
    
    def _determine_style(self, avg_words: float, emoji_rate: float, slang_count: int) -> str:
        """Determine communication style."""
        if avg_words < 5 and slang_count > 5:
            return "casual_brief"
        elif avg_words > 20:
            return "detailed"
        elif emoji_rate > 0.5:
            return "expressive"
        elif slang_count > 10:
            return "informal"
        else:
            return "balanced"
    
    def _deep_analyze(self, messages: List[str]) -> Dict[str, Any]:
        """Use AI to deeply analyze personality from messages."""
        if not self.llm:
            return {"traits": ["unknown"], "tone": "neutral"}
        
        sample = "\n".join(messages[:20])  # Use up to 20 messages
        
        prompt = f"""Analyze these messages and identify personality traits.

MESSAGES:
{sample}

Respond in this exact format:
TRAITS: [trait1], [trait2], [trait3], [trait4], [trait5]
TONE: [one word: friendly/professional/casual/sarcastic/serious/playful/analytical]
VIBE: [one sentence describing how this person comes across]"""

        response = self.llm(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            inject_memory=False
        )
        
        traits = []
        tone = "neutral"
        vibe = ""
        
        for line in response.strip().split('\n'):
            if line.upper().startswith("TRAITS:"):
                traits = [t.strip() for t in line.split(":", 1)[-1].split(",")]
            elif line.upper().startswith("TONE:"):
                tone = line.split(":", 1)[-1].strip().lower()
            elif line.upper().startswith("VIBE:"):
                vibe = line.split(":", 1)[-1].strip()
        
        return {"traits": traits, "tone": tone, "vibe": vibe}
    
    def chat_as_clone(self, user_id: str, message: str) -> str:
        """
        Generate a response as the user's personality clone.
        
        Args:
            user_id: The user whose clone to use
            message: What to respond to
            
        Returns:
            Response in the user's style
        """
        if user_id not in self.clones:
            return "❌ No personality clone found. Create one first with analyze_messages()!"
        
        profile = self.clones[user_id]
        
        # Build personality prompt
        style_desc = {
            "casual_brief": "very short, casual responses with slang",
            "detailed": "longer, more detailed explanations",
            "expressive": "using lots of emojis and enthusiasm",
            "informal": "casual and relaxed with slang",
            "balanced": "normal conversational style"
        }
        
        style = style_desc.get(profile.get("communication_style", "balanced"), "conversational")
        traits = ", ".join(profile.get("personality_traits", ["friendly"]))
        tone = profile.get("tone", "friendly")
        top_words = ", ".join(profile.get("top_words", [])[:5])
        emojis = " ".join(profile.get("top_emojis", []))
        
        prompt = f"""You are a personality clone of a user. Respond EXACTLY how they would.

PERSONALITY PROFILE:
- Style: {style}
- Traits: {traits}
- Tone: {tone}
- Avg message length: {profile.get('avg_word_count', 10)} words
- Their common words: {top_words}
- Their favorite emojis: {emojis}
- Slang level: {profile.get('slang_level', 'medium')}

Sample of how they write:
{chr(10).join(profile.get('sample_phrases', [])[:3])}

Now respond to this message AS THEM (match their exact style, length, tone):
"{message}"

Your response (AS THE CLONE):"""

        response = self.llm(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            inject_memory=False
        )
        
        return response.strip()
    
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user's personality profile."""
        return self.clones.get(user_id)
    
    def create_clone_from_text(self, text: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Create a clone from a block of text (conversations, emails, etc.)
        Automatically splits into messages.
        """
        # Split by common delimiters
        messages = re.split(r'\n+|(?<=[.!?])\s+', text)
        messages = [m.strip() for m in messages if len(m.strip()) > 10]
        
        if len(messages) < 5:
            return {"status": "error", "message": "Need more text to analyze"}
        
        return self.analyze_messages(messages, user_id)
    
    def get_compatibility(self, user_id1: str, user_id2: str) -> Dict[str, Any]:
        """
        Compare two personality profiles for compatibility.
        """
        if user_id1 not in self.clones or user_id2 not in self.clones:
            return {"status": "error", "message": "Both profiles must exist"}
        
        p1 = self.clones[user_id1]
        p2 = self.clones[user_id2]
        
        # Compare traits
        traits1 = set(p1.get("personality_traits", []))
        traits2 = set(p2.get("personality_traits", []))
        shared_traits = traits1 & traits2
        
        # Compare style
        same_style = p1.get("communication_style") == p2.get("communication_style")
        
        # Calculate score
        score = len(shared_traits) * 20 + (30 if same_style else 0)
        score = min(score, 100)
        
        return {
            "status": "success",
            "user1": user_id1,
            "user2": user_id2,
            "compatibility_score": score,
            "shared_traits": list(shared_traits),
            "style_match": same_style
        }
    
    def analyze_file(self, filepath: str, format_type: str = "auto", user_id: str = "default") -> Dict[str, Any]:
        """
        Analyze personality from a file (chat exports, text dumps).
        
        Args:
            filepath: Path to the file
            format_type: File format (auto, json, txt, csv, whatsapp, etc.)
            user_id: User identifier
            
        Returns:
            Personality profile
        """
        try:
            # Detect format if auto
            if format_type == "auto":
                format_type = self._detect_format(filepath)
            
            # Parse file based on format
            messages = self._parse_file(filepath, format_type)
            
            if not messages:
                return {"status": "error", "message": "No messages extracted from file"}
            
            # Analyze messages
            return self.analyze_messages(messages, user_id)
            
        except Exception as e:
            logger.error(f"[CLONE] File analysis failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def _detect_format(self, filepath: str) -> str:
        """Auto-detect file format."""
        import os
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.json':
            return 'json'
        elif ext == '.csv':
            return 'csv'
        else:
            # Check content for WhatsApp/Telegram patterns
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read(1000)
                    if '[' in content and '] ' in content and ':' in content:
                        return 'whatsapp'
                    elif 'Telegram' in content:
                        return 'telegram'
            except:
                pass
        
        return 'txt'
    
    def _parse_file(self, filepath: str, format_type: str) -> List[str]:
        """Parse file and extract messages."""
        messages = []
        
        try:
            if format_type == 'json':
                import json
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Try common JSON structures
                    if isinstance(data, list):
                        messages = [str(item.get('text', item)) for item in data if isinstance(item, dict)]
                    elif isinstance(data, dict) and 'messages' in data:
                        messages = [str(m.get('text', m)) for m in data['messages']]
            
            elif format_type == 'csv':
                import csv
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Try common column names
                        text = row.get('message', row.get('text', row.get('content', '')))
                        if text:
                            messages.append(text)
            
            elif format_type == 'whatsapp':
                import re
                with open(filepath, 'r', encoding='utf-8') as f:
                    # WhatsApp format: [timestamp] Name: Message
                    for line in f:
                        match = re.search(r'\d+/\d+/\d+.*?\]\s*([^:]+):\s*(.+)', line)
                        if match:
                            messages.append(match.group(2).strip())
            
            elif format_type == 'telegram':
                # Similar to WhatsApp
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        if ':' in line:
                            parts = line.split(':', 1)
                            if len(parts) > 1:
                                messages.append(parts[1].strip())
            
            else:  # txt or unknown
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Split by newlines or double newlines
                    messages = [m.strip() for m in content.split('\n') if len(m.strip()) > 10]
        
        except Exception as e:
            logger.error(f"[CLONE] File parsing failed: {e}")
        
        return messages
    
    def update_clone(self, user_id: str, new_messages: List[str]) -> Dict[str, Any]:
        """Update/evolve an existing clone with new messages."""
        if user_id not in self.clones:
            return {"status": "error", "message": "Clone doesn't exist. Create one first."}
        
        # Combine old and new messages
        old_profile = self.clones[user_id]
        old_samples = old_profile.get("sample_phrases", [])
        combined = old_samples + new_messages
        
        # Re-analyze with combined data
        result = self.analyze_messages(combined, user_id)
        
        if result.get("status") == "success":
            result["message"] = f"Clone updated with {len(new_messages)} new messages"
        
        return result
    
    def style_transfer(self, text: str, user_id: str) -> str:
        """Rewrite text in the user's communication style."""
        if user_id not in self.clones:
            return "❌ Clone not found. Create one first!"
        
        profile = self.clones[user_id]
        
        if not self.llm:
            return text
        
        style_desc = {
            "casual_brief": "very short, casual with slang",
            "detailed": "longer, more detailed",
            "expressive": "using emojis and enthusiasm",
            "informal": "casual and relaxed",
            "balanced": "normal conversational"
        }
        
        style = style_desc.get(profile.get("communication_style", "balanced"), "conversational")
        emojis = " ".join(profile.get("top_emojis", []))
        
        prompt = f"""Rewrite this text to match this person's style:

Style: {style}
Tone: {profile.get('tone', 'friendly')}
Common emojis: {emojis}
Avg length: {profile.get('avg_word_count', 10)} words

Original text: "{text}"

Rewritten version (match their style exactly):"""
        
        result = self.llm(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            inject_memory=False
        )
        
        return result.strip()
    
    def get_writing_insights(self, user_id: str) -> Dict[str, Any]:
        """Get detailed writing analytics for a user."""
        if user_id not in self.clones:
            return {"status": "error", "message": "Clone not found"}
        
        profile = self.clones[user_id]
        
        return {
            "status": "success",
            "user_id": user_id,
            "insights": {
                "communication_style": profile.get("communication_style"),
                "tone": profile.get("tone"),
                "personality_traits": profile.get("personality_traits", []),
                "avg_message_length": f"{profile.get('avg_message_length', 0)} chars",
                "avg_word_count": f"{profile.get('avg_word_count', 0)} words",
                "emoji_frequency": profile.get("emoji_usage", 0),
                "slang_level": profile.get("slang_level"),
                "question_rate": f"{profile.get('question_rate', 0) * 100:.1f}%",
                "top_words": profile.get("top_words", [])[:10],
                "favorite_emojis": profile.get("top_emojis", [])
            }
        }


# Global instance
personality_clone = PersonalityClone()


# Convenience functions
def create_clone(messages: List[str], user_id: str = "default") -> Dict[str, Any]:
    """Create a personality clone from messages."""
    return personality_clone.analyze_messages(messages, user_id)


def talk_to_clone(user_id: str, message: str) -> str:
    """Talk to a personality clone."""
    return personality_clone.chat_as_clone(user_id, message)


if __name__ == "__main__":
    # Test
    test_messages = [
        "lol thats crazy bro",
        "ngl i didnt expect that 😂",
        "yo check this out fr fr",
        "bruh moment tbh",
        "wait what happened??",
        "thats actually fire ngl",
        "im dead 💀💀",
        "no way lmaooo"
    ]
    
    result = personality_clone.analyze_messages(test_messages, "test_user")
    print("Profile:", result)
    
    response = personality_clone.chat_as_clone("test_user", "What do you think about the new iPhone?")
    print("Clone response:", response)
