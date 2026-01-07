"""
Advanced Chat Command Parser - Natural Language to Actions
===========================================================
Parse natural language commands and execute corresponding actions
"""

import re
from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timedelta

class AdvancedChatParser:
    def __init__(self):
        self.command_patterns = {
            # Document Generation
            "create_pdf": [
                r"create (?:a )?pdf (?:about |on |for )?(.+)",
                r"generate (?:a )?pdf (?:document )?(?:about |on )?(.+)",
                r"make (?:a )?pdf (?:about |on )?(.+)"
            ],
            "create_powerpoint": [
                r"create (?:a )?(?:powerpoint|presentation|ppt) (?:about |on |for )?(.+)",
                r"generate (?:a )?(?:powerpoint|presentation|ppt) (?:about |on )?(.+)",
                r"make (?:a )?(?:powerpoint|presentation|ppt) (?:about |on )?(.+)"
            ],
            
            # Enhanced Image Generation
            "generate_image_style": [
                r"generate (?:an? )?(.+) (?:style |in )(.+) style",
                r"create (?:an? )?(.+) (?:image |picture )?in (.+) style",
                r"make (?:an? )?(.+) (?:in |as )(.+) style"
            ],
            "generate_image_hd": [
                r"generate (?:an? )?hd (?:image |picture )?(?:of )?(.+)",
                r"create (?:an? )?high(?:-| )(?:def|definition|res|resolution) (?:image |picture )?(?:of )?(.+)"
            ],
            "generate_image_variations": [
                r"generate (?:\d+ )?variations (?:of )?(.+)",
                r"create (?:multiple )?versions (?:of )?(.+)"
            ],
            
            # Weather & News
            "weather_forecast": [
                r"(?:what's |what is )?(?:the )?(?:weather )?forecast (?:for |in )?(.+)",
                r"(?:weather )?forecast (?:for |in )?(.+)"
            ],
            "news_topic": [
                r"(?:get |show |find )?(?:me )?(?:the )?(?:latest )?news (?:about |on )?(.+)",
                r"what's (?:the )?news (?:about |on )?(.+)"
            ],
            
            # Market Data
            "crypto_price": [
                r"(?:what's |what is )?(?:the )?(?:price of |current )?(.+) (?:price|crypto|cryptocurrency)",
                r"(?:how much is |price of )(.+) (?:crypto|cryptocurrency|coin)"
            ],
            "stock_price": [
                r"(?:what's |what is )?(?:the )?(?:stock price of |price of )(.+) stock",
                r"(?:how much is |price of )(.+) (?:stock|shares)"
            ],
            
            # YouTube Control
            "youtube_play": [
                r"play (.+) on youtube",
                r"youtube play (.+)",
                r"search youtube for (.+) and play"
            ],
            
            # Memory System
            "remember_fact": [
                r"remember (?:that )?(.+)",
                r"save (?:to memory )?(?:that )?(.+)",
                r"store (?:the fact )?(?:that )?(.+)"
            ],
            "recall_memory": [
                r"(?:what do you remember|recall) (?:about )?(.+)",
                r"(?:do you remember|tell me about) (.+)"
            ],
            
            # Advanced Features
            "summarize_url": [
                r"summarize (?:the )?(?:article|page|website) (?:at )?(.+)",
                r"give me (?:a )?summary of (.+)"
            ],
            "translate_text": [
                r"translate (.+) to (.+)",
                r"how do you say (.+) in (.+)"
            ],
            "calculate": [
                r"calculate (.+)",
                r"what (?:is |are )(.+)",
                r"solve (.+)"
            ],
            "code_help": [
                r"(?:how to |help me )?(?:write |code |program )(.+) in (.+)",
                r"(?:show me |give me )(?:code |example )(?:for |to )(.+) in (.+)"
            ],
            
            # Entertainment
            "tell_joke": [
                r"tell me (?:a )?joke",
                r"make me laugh",
                r"say something funny"
            ],
            "tell_fact": [
                r"tell me (?:a )?(?:random )?fact",
                r"give me (?:a )?fact",
                r"interesting fact"
            ],
            "get_quote": [
                r"(?:give me |tell me )?(?:an? )?(?:inspirational )?quote",
                r"inspire me",
                r"motivate me"
            ]
        }
    
    def parse(self, query: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Parse natural language query into command and parameters
        
        Args:
            query: User's natural language query
            
        Returns:
            Tuple of (command_type, parameters_dict)
        """
        query_lower = query.lower().strip()
        
        # Try to match against all patterns
        for command_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query_lower)
                if match:
                    params = self._extract_params(command_type, match)
                    return command_type, params
        
        return None, None
    
    def _extract_params(self, command_type: str, match) -> Dict[str, Any]:
        """Extract parameters from regex match"""
        params = {}
        
        if command_type == "create_pdf":
            params = {
                "topic": match.group(1).strip(),
                "type": "pdf"
            }
        
        elif command_type == "create_powerpoint":
            params = {
                "topic": match.group(1).strip(),
                "type": "powerpoint"
            }
        
        elif command_type == "generate_image_style":
            params = {
                "prompt": match.group(1).strip(),
                "style": match.group(2).strip()
            }
        
        elif command_type == "generate_image_hd":
            params = {
                "prompt": match.group(1).strip(),
                "quality": "hd"
            }
        
        elif command_type == "generate_image_variations":
            params = {
                "prompt": match.group(1).strip(),
                "variations": True
            }
        
        elif command_type == "weather_forecast":
            params = {
                "city": match.group(1).strip(),
                "forecast": True
            }
        
        elif command_type == "news_topic":
            params = {
                "topic": match.group(1).strip()
            }
        
        elif command_type in ["crypto_price", "stock_price"]:
            params = {
                "symbol": match.group(1).strip()
            }
        
        elif command_type == "youtube_play":
            params = {
                "query": match.group(1).strip()
            }
        
        elif command_type == "remember_fact":
            params = {
                "fact": match.group(1).strip()
            }
        
        elif command_type == "recall_memory":
            params = {
                "query": match.group(1).strip()
            }
        
        elif command_type == "summarize_url":
            params = {
                "url": match.group(1).strip()
            }
        
        elif command_type == "translate_text":
            params = {
                "text": match.group(1).strip(),
                "target_language": match.group(2).strip()
            }
        
        elif command_type == "calculate":
            params = {
                "expression": match.group(1).strip()
            }
        
        elif command_type == "code_help":
            params = {
                "task": match.group(1).strip(),
                "language": match.group(2).strip()
            }
        
        elif command_type in ["tell_joke", "tell_fact", "get_quote"]:
            params = {}
        
        return params
    
    def get_command_suggestions(self, partial_query: str) -> List[str]:
        """
        Get command suggestions based on partial query
        
        Args:
            partial_query: Partial user input
            
        Returns:
            List of suggested commands
        """
        suggestions = []
        query_lower = partial_query.lower()
        
        suggestion_templates = {
            "create": [
                "create a PDF about [topic]",
                "create a PowerPoint about [topic]",
                "create an image of [description]"
            ],
            "generate": [
                "generate a PDF about [topic]",
                "generate an HD image of [description]",
                "generate variations of [description]"
            ],
            "weather": [
                "what's the weather in [city]",
                "weather forecast for [city]"
            ],
            "news": [
                "get news about [topic]",
                "what's the news on [topic]"
            ],
            "remember": [
                "remember that [fact]",
                "what do you remember about [topic]"
            ],
            "youtube": [
                "play [song/video] on YouTube"
            ],
            "tell": [
                "tell me a joke",
                "tell me a fact",
                "tell me a quote"
            ]
        }
        
        for keyword, templates in suggestion_templates.items():
            if keyword in query_lower:
                suggestions.extend(templates)
        
        return suggestions[:5]  # Return top 5 suggestions

# Global instance
chat_parser = AdvancedChatParser()

if __name__ == "__main__":
    # Test parsing
    test_queries = [
        "create a PDF about artificial intelligence",
        "generate a PowerPoint on climate change",
        "create a sunset image in anime style",
        "what's the weather forecast for London",
        "get news about technology",
        "what's the price of Bitcoin",
        "play lofi music on YouTube",
        "remember that I like Python programming",
        "tell me a joke"
    ]
    
    print("Testing Advanced Chat Parser...\n")
    for query in test_queries:
        command, params = chat_parser.parse(query)
        print(f"Query: {query}")
        print(f"Command: {command}")
        print(f"Params: {params}")
        print()
