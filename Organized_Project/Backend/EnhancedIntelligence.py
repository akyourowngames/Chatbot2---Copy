"""
Enhanced Intelligence System - Advanced AI Brain
================================================
Multi-model ensemble, context awareness, and intelligent routing
"""

import os
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re

class EnhancedIntelligence:
    def __init__(self):
        self.context_history = []
        self.user_preferences = self._load_preferences()
        self.command_patterns = self._init_command_patterns()
        
    def _load_preferences(self) -> Dict:
        """Load user preferences"""
        pref_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "user_preferences.json")
        if os.path.exists(pref_file):
            with open(pref_file, 'r') as f:
                return json.load(f)
        return {
            "preferred_image_style": "realistic",
            "preferred_music_genre": "lofi",
            "timezone": "UTC",
            "language": "en"
        }
    
    def _init_command_patterns(self) -> Dict[str, List[str]]:
        """Initialize comprehensive command patterns"""
        return {
            # Document creation
            "create_pdf": [
                r"create (?:a |an )?pdf",
                r"make (?:a |an )?pdf",
                r"generate (?:a |an )?pdf",
                r"write (?:a |an )?pdf"
            ],
            "create_powerpoint": [
                r"create (?:a |an )?(?:powerpoint|presentation|ppt|slides)",
                r"make (?:a |an )?(?:powerpoint|presentation|ppt|slides)",
                r"generate (?:a |an )?(?:powerpoint|presentation|ppt|slides)"
            ],
            
            # Image generation
            "generate_image": [
                r"create (?:a |an )?(?:hd )?(?:image|img|picture|photo|artwork)",
                r"generate (?:a |an )?(?:hd )?(?:image|img|picture|photo|artwork)",
                r"make (?:a |an )?(?:hd )?(?:image|img|picture|photo|artwork)",
                r"draw (?:a |an )?(?:hd )?",
                r"(?:image|img|picture|photo) of (.+)"
            ],
            
            # Music
            "play_music": [
                r"play (?:some )?music",
                r"play (?:me )?(.+)",
                r"start (?:playing )?(.+)",
                r"listen to (.+)"
            ],
            "stop_music": [
                r"stop (?:the )?music",
                r"stop (?:the )?song",
                r"stop playing"
            ],
            "pause_music": [
                r"pause (?:the )?music",
                r"pause (?:the )?song"
            ],
            "resume_music": [
                r"resume (?:the )?music",
                r"continue (?:the )?music",
                r"unpause"
            ],
            "volume_music": [
                r"(?:set )?volume (?:to )?(\d+)",
                r"volume (\d+)",
                r"(?:turn )?(?:up|down) (?:the )?volume"
            ],
            "music_status": [
                r"what's playing",
                r"current song",
                r"music status",
                r"what song is this"
            ],
            
            # Video player (NEW)
            # Video player (NEW)
            "play_video": [
                r"play (?:video|youtube) (.+)",
                r"watch (?:video )?(.*)",
                r"show (?:me )?(?:video|youtube) (.+)",
                r"search (?:on )?(?:youtube) (.+)" # Removed generic video search that conflicted with files
            ],
            "stop_video": [
                r"stop (?:the )?video",
                r"stop (?:the )?youtube",
                r"close (?:the )?video"
            ],
            "video_status": [
                r"what video is playing",
                r"current video",
                r"video status"
            ],
            
            # File operations
            "create_file": [
                r"create (?:a |an )?file",
                r"make (?:a |an )?file",
                r"new file"
            ],
            "read_file": [
                r"read (?:the )?file",
                r"show (?:me )?(?:the )?file",
                r"open (?:the )?file"
            ],
            "write_file": [
                r"write to (?:the )?file",
                r"save to (?:the )?file",
                r"update (?:the )?file"
            ],
            
            # File Operations (Enhanced)
            # File Operations (Enhanced)
            "file_action": [
                r"list (?:all )?items(?: in| at| from)?\s*(.+)?",
                r"list (?:all )?files(?: in| at| from)?\s*(.+)?",
                r"show (?:all )?files(?: in| at| from)?\s*(.+)?",
                r"list (.+) files",
                r"what files are in (.+)",
                r"find (?:file )?(.+?)(?: in (.+))?",
                r"search for (.+?)(?: in (.+))?",
                r"move (.+) to (.+)",
                r"copy (.+) to (.+)",
                r"rename (.+) to (.+)",
                r"find duplicates(?: in (.+))?",
                r"open (?:file )?(.+)",
                r"open it",
                r"show details (?:of|for) (.+)",
                r"properties of (.+)",
                r"summarize (?:file )?(.+)",
                r"what is in (?:file )?(.+)"
            ],
            
            # Web scraping
            "scrape_web": [
                r"scrape (?:the )?(?:website|page|url)",
                r"extract (?:data )?from (.+)",
                r"get (?:content|data) from (.+)"
            ],
            
            # System
            "screenshot": [
                r"take (?:a )?screenshot",
                r"capture (?:the )?screen",
                r"screen(?:shot| capture)"
            ],
            "battery": [
                r"(?:what's |what is |check )?(?:my )?battery",
                r"battery (?:status|level|percentage)"
            ],
            
            # Information
            "weather": [
                r"(?:what's |what is )?(?:the )?weather",
                r"weather (?:in |for )?(.+)?"
            ],
            "news": [
                r"(?:get |show |tell me )?(?:the )?(?:latest )?news",
                r"news (?:about |on )?(.+)?"
            ],
            
            # Entertainment
            "joke": [
                r"tell (?:me )?(?:a )?joke",
                r"make me laugh",
                r"something funny"
            ],
            "fact": [
                r"tell (?:me )?(?:a )?fact",
                r"interesting fact",
                r"random fact"
            ],
            "quote": [
                r"(?:give me |tell me )?(?:a |an )?(?:inspirational )?quote",
                r"inspire me",
                r"motivate me"
            ],
            
            # Code execution (NEW v11.0)
            "execute_code": [
                r"run (?:python )?code",
                r"execute (?:python )?code",
                r"run (?:this )?(?:python )?script",
                r"eval(?:uate)?"
            ],
            
            # Math solver (NEW v11.0)
            "calculate": [
                r"calculate (.+)",
                r"compute (.+)",
                r"what (?:is|are) (.+)",
                r"solve (.+)"
            ],
            "solve_equation": [
                r"solve (?:the )?equation (.+)",
                r"solve for (.+)"
            ],
            
            # Translation (NEW v11.0)
            "translate": [
                r"translate (.+) to (\w+)",
                r"how do you say (.+) in (\w+)",
                r"what is (.+) in (\w+)"
            ],
            
            # QR Code (NEW v11.0)
            "generate_qr": [
                r"create (?:a )?qr (?:code )?(?:for )?(.+)",
                r"generate (?:a )?qr (?:code )?(?:for )?(.+)",
                r"make (?:a )?qr (?:code )?(?:for )?(.+)"
            ]
        }
    
    def analyze_intent(self, query: str) -> Tuple[str, Dict[str, Any], float]:
        """
        Analyze user intent with confidence scoring
        
        Returns:
            (intent, parameters, confidence)
        """
        query_lower = query.lower().strip()
        
        # Check each command pattern
        for intent, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query_lower)
                if match:
                    # Extract parameters
                    params = self._extract_parameters(intent, match, query)
                    confidence = self._calculate_confidence(query, intent, match)
                    return intent, params, confidence
        
        # No specific intent found
        return "general_chat", {"query": query}, 0.5
    
    def _extract_parameters(self, intent: str, match, query: str) -> Dict[str, Any]:
        """Extract parameters from matched pattern"""
        params = {}
        
        # Extract topic/subject from query
        if intent in ["create_pdf", "create_powerpoint"]:
            # Extract topic after "about", "on", "for"
            topic_match = re.search(r"(?:about|on|for)\s+(.+)", query, re.IGNORECASE)
            if topic_match:
                params["topic"] = topic_match.group(1).strip()
            else:
                params["topic"] = "General Topic"
        
        elif intent == "generate_image":
            # Extract description
            desc_match = re.search(r"(?:of|showing|with)\s+(.+)", query, re.IGNORECASE)
            if desc_match:
                params["prompt"] = desc_match.group(1).strip()
            else:
                # Use everything after the command
                params["prompt"] = re.sub(r"^(?:create|generate|make|draw)\s+(?:a|an)?\s*(?:image|picture|photo|artwork)?\s*", "", query, flags=re.IGNORECASE).strip()
            
            # Extract style
            style_match = re.search(r"in\s+(\w+)\s+style", query, re.IGNORECASE)
            if style_match:
                params["style"] = style_match.group(1).lower()
            else:
                params["style"] = self.user_preferences.get("preferred_image_style", "realistic")
        
        elif intent == "play_music":
            # Extract song/artist
            if match.groups():
                params["query"] = match.group(1).strip()
            else:
                params["query"] = self.user_preferences.get("preferred_music_genre", "lofi music")
        
        elif intent == "file_action":
            # Determine logic
            q = query.lower()
            if "open it" in q:
                params["action"] = "open_last"         
            elif "open" in q:
                params["action"] = "open"
                if match.groups() and match.group(1):
                     params["path"] = match.group(1).strip()
            elif "details" in q or "info" in q or "properties" in q:
                params["action"] = "details"
                if match.groups() and match.group(1):
                     params["path"] = match.group(1).strip()
            elif "summarize" in q or "summary" in q:
                params["action"] = "summarize"
                if match.groups() and match.group(1):
                    params["path"] = match.group(1).strip()
            elif "list" in q or "show files" in q or "what files" in q:
                params["action"] = "list"
                if match.groups() and match.group(1):
                    params["path"] = match.group(1).strip()
                else: 
                     params["path"] = "."
            elif "move" in q:
                params["action"] = "move"
                if len(match.groups()) >= 2:
                    params["files"] = [match.group(1).strip()] # Supports single file move for now via regex
                    params["destination"] = match.group(2).strip()
            elif "copy" in q:
                params["action"] = "copy"
                if len(match.groups()) >= 2:
                    params["files"] = [match.group(1).strip()]
                    params["destination"] = match.group(2).strip()
            elif "rename" in q:
                params["action"] = "rename"
                if len(match.groups()) >= 2:
                    params["files"] = [match.group(1).strip()]
                    params["destination"] = match.group(2).strip() # Destination here acts as new name
            elif "find duplicates" in q:
                params["action"] = "duplicates"
                if match.groups() and match.group(1):
                    params["path"] = match.group(1).strip()
                else: 
                     params["path"] = "."
            elif "find" in q or "search" in q:
                params["action"] = "search"
                if match.groups():
                    params["query"] = match.group(1).strip()
                    if len(match.groups()) > 1 and match.group(2):
                        params["path"] = match.group(2).strip()
                    else:
                        params["path"] = "."

        elif intent == "play_video":
            # Extract video query
            if match.groups() and match.group(1):
                params["query"] = match.group(1).strip()
            else:
                # Try to extract from full query
                video_query = re.sub(r"^(?:play|watch|show|search)\\s+(?:video|youtube)?\\s*(?:of|for)?\\s*", "", query, flags=re.IGNORECASE).strip()
                params["query"] = video_query if video_query else "trending videos"
        
        elif intent == "scrape_web":
            # Extract URL
            url_match = re.search(r"(https?://[^\s]+)", query)
            if url_match:
                params["url"] = url_match.group(1)
            elif match.groups():
                params["url"] = match.group(1).strip()
        
        elif intent in ["weather", "news"]:
            if match.groups() and match.group(1):
                params["location" if intent == "weather" else "topic"] = match.group(1).strip()
        
        return params
    
    def _calculate_confidence(self, query: str, intent: str, match) -> float:
        """Calculate confidence score for intent detection"""
        confidence = 0.7  # Base confidence
        
        # Increase confidence for exact matches
        if match.group(0) == query.lower():
            confidence += 0.2
        
        # Increase confidence if parameters are clear
        if match.groups():
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def enhance_response(self, response: str, context: Dict[str, Any]) -> str:
        """Enhance response with context and personality"""
        # Add context-aware enhancements
        if context.get("command_executed"):
            response = f"✅ {response}"
        
        # Add helpful suggestions
        if "error" in response.lower():
            response += "\n\n💡 Tip: Try rephrasing your request or check if all required information is provided."
        
        return response
    
    def update_context(self, query: str, response: str, intent: str):
        """Update conversation context"""
        self.context_history.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response,
            "intent": intent
        })
        
        # Keep only last 10 interactions
        if len(self.context_history) > 10:
            self.context_history = self.context_history[-10:]
    
    def get_smart_suggestions(self, query: str) -> List[str]:
        """Get smart suggestions based on query"""
        suggestions = []
        
        if "image" in query.lower():
            suggestions.append("Try: 'create a sunset in anime style'")
            suggestions.append("Available styles: realistic, anime, cyberpunk, watercolor")
        
        elif "pdf" in query.lower():
            suggestions.append("Try: 'create a PDF about machine learning'")
            suggestions.append("I can create professional PDFs with custom content")
        
        elif "music" in query.lower():
            suggestions.append("Try: 'play lofi music' or 'play jazz'")
            suggestions.append("I have a built-in music player!")
        
        return suggestions

# Global instance
enhanced_intelligence = EnhancedIntelligence()

if __name__ == "__main__":
    # Test
    test_queries = [
        "create a PDF about AI",
        "generate a sunset in anime style",
        "play some lofi music",
        "what's the weather in Tokyo",
        "take a screenshot"
    ]
    
    for query in test_queries:
        intent, params, confidence = enhanced_intelligence.analyze_intent(query)
        print(f"\nQuery: {query}")
        print(f"Intent: {intent} (confidence: {confidence:.2f})")
        print(f"Params: {params}")
