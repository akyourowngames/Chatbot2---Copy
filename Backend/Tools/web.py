"""
Web Search Tool - Web Version
=============================
Web search functionality for cloud deployment.
"""

from typing import Dict, Any
from .base import Tool
from Backend.RealtimeSearchEngine import GoogleSearch
from Backend.JarvisWebScraper import quick_search, scrape_markdown


class WebSearchTool(Tool):
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the internet for information, news, stocks, or crypto.",
            domain="web_search",
            priority="HIGH",
            allowed_intents=["web_search", "conversation"]
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "search_type": {
                    "type": "string",
                    "description": "Type of search",
                    "enum": ["general", "news", "stock", "crypto", "youtube"]
                }
            },
            "required": ["query"]
        }

    def execute(self, query: str, search_type: str = "general", **kwargs) -> str:
        print(f"[WebTool] Searching: {query} ({search_type})")
        
        try:
            if search_type in ["crypto", "stock", "news"]:
                # Use Jarvis Search for these specialized domains
                import asyncio
                results = asyncio.run(quick_search(f"{query} {search_type}"))
                if results:
                    return f"Top Result: {results[0]['title']}\n{results[0]['link']}\n{results[0]['snippet']}"
                return f"No results found for {search_type} search."

            if search_type == "youtube":
                # On web, return a YouTube search link instead of opening browser
                from urllib.parse import quote_plus
                youtube_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
                return f"🔎 YouTube search for '{query}': {youtube_url}"

            # Default General Search
            result = GoogleSearch(query)
            return result
            
        except Exception as e:
            return f"Search failed: {str(e)}"
