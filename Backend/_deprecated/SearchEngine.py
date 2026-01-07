"""
Universal Search Engine for JARVIS
Aggregates search results from multiple sources: files, chat, screenshots, web
"""

import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
import glob

class SearchEngine:
    def __init__(self, data_dir: str = "Data"):
        self.data_dir = data_dir
        self.uploads_dir = os.path.join(data_dir, "Uploads")
        self.screenshots_dir = os.path.join(data_dir, "Screenshots")
        self.recent_searches = []
        
    def fuzzy_match(self, query: str, text: str) -> float:
        """Calculate fuzzy match score between query and text"""
        query = query.lower()
        text = text.lower()
        
        # Exact match
        if query in text:
            return 1.0
        
        # Sequence matcher
        ratio = SequenceMatcher(None, query, text).ratio()
        
        # Bonus for matching start
        if text.startswith(query):
            ratio += 0.3
            
        # Bonus for word boundaries
        words = text.split()
        for word in words:
            if word.startswith(query):
                ratio += 0.2
                break
                
        return min(ratio, 1.0)
    
    def search_files(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search recent files by name"""
        results = []
        
        try:
            # Search in uploads directory
            if os.path.exists(self.uploads_dir):
                for filename in os.listdir(self.uploads_dir):
                    filepath = os.path.join(self.uploads_dir, filename)
                    if os.path.isfile(filepath):
                        score = self.fuzzy_match(query, filename)
                        if score > 0.3:
                            stat = os.stat(filepath)
                            results.append({
                                "type": "file",
                                "title": filename,
                                "path": filepath,
                                "size": stat.st_size,
                                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                "score": score,
                                "icon": self._get_file_icon(filename)
                            })
            
            # Search in project root for code files
            code_extensions = ['.py', '.js', '.html', '.css', '.json', '.md']
            for ext in code_extensions:
                pattern = f"*.{ext.lstrip('.')}"
                for filepath in glob.glob(pattern):
                    filename = os.path.basename(filepath)
                    score = self.fuzzy_match(query, filename)
                    if score > 0.3:
                        stat = os.stat(filepath)
                        results.append({
                            "type": "code",
                            "title": filename,
                            "path": os.path.abspath(filepath),
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "score": score,
                            "icon": "💻"
                        })
                        
        except Exception as e:
            print(f"[SEARCH] File search error: {e}")
        
        # Sort by score and limit
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def search_chat_history(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search chat history"""
        results = []
        
        try:
            db_path = os.path.join(self.data_dir, "jarvis.db")
            if os.path.exists(db_path):
                # Simple file-based search for now
                # In production, would use proper database queries
                pass
                
        except Exception as e:
            print(f"[SEARCH] Chat search error: {e}")
        
        return results[:limit]
    
    def search_screenshots(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search screenshots by filename and metadata"""
        results = []
        
        try:
            if os.path.exists(self.screenshots_dir):
                for filename in os.listdir(self.screenshots_dir):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        filepath = os.path.join(self.screenshots_dir, filename)
                        score = self.fuzzy_match(query, filename)
                        
                        if score > 0.2:
                            stat = os.stat(filepath)
                            results.append({
                                "type": "screenshot",
                                "title": filename,
                                "path": filepath,
                                "size": stat.st_size,
                                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                "score": score,
                                "icon": "📸",
                                "thumbnail": f"/data/Screenshots/{filename}"
                            })
        except Exception as e:
            print(f"[SEARCH] Screenshot search error: {e}")
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def search_web(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Placeholder for web search integration"""
        return [{
            "type": "web",
            "title": f"Search web for '{query}'",
            "url": f"https://www.google.com/search?q={query}",
            "description": "Open in browser",
            "score": 0.5,
            "icon": "🌐"
        }]
    
    def universal_search(self, query: str, sources: Optional[List[str]] = None, limit: int = 50) -> Dict[str, Any]:
        """
        Universal search across all sources
        
        Args:
            query: Search query
            sources: List of sources to search ['files', 'chat', 'screenshots', 'web']
            limit: Max results per source
            
        Returns:
            Categorized search results
        """
        if not query or len(query.strip()) < 2:
            return {
                "success": False,
                "error": "Query too short",
                "results": {}
            }
        
        query = query.strip()
        
        # Default to all sources
        if sources is None:
            sources = ['files', 'chat', 'screenshots', 'web']
        
        results = {
            "success": True,
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "results": {}
        }
        
        # Search each source
        if 'files' in sources:
            results["results"]["files"] = self.search_files(query, limit)
            
        if 'chat' in sources:
            results["results"]["chat"] = self.search_chat_history(query, limit)
            
        if 'screenshots' in sources:
            results["results"]["screenshots"] = self.search_screenshots(query, limit)
            
        if 'web' in sources:
            results["results"]["web"] = self.search_web(query, 5)
        
        # Calculate total results
        total = sum(len(v) for v in results["results"].values())
        results["total_results"] = total
        
        # Save to recent searches
        self.recent_searches.insert(0, {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "total_results": total
        })
        self.recent_searches = self.recent_searches[:10]  # Keep last 10
        
        return results
    
    def get_recent_searches(self) -> List[Dict[str, Any]]:
        """Get recent search queries"""
        return self.recent_searches
    
    def get_suggestions(self, partial_query: str) -> List[str]:
        """Get autocomplete suggestions based on recent searches"""
        if len(partial_query) < 2:
            return []
        
        suggestions = []
        for search in self.recent_searches:
            if partial_query.lower() in search["query"].lower():
                suggestions.append(search["query"])
        
        return suggestions[:5]
    
    def _get_file_icon(self, filename: str) -> str:
        """Get icon emoji for file type"""
        ext = os.path.splitext(filename)[1].lower()
        
        icons = {
            '.py': '🐍',
            '.js': '📜',
            '.html': '🌐',
            '.css': '🎨',
            '.json': '📋',
            '.md': '📝',
            '.txt': '📄',
            '.pdf': '📕',
            '.png': '🖼️',
            '.jpg': '🖼️',
            '.jpeg': '🖼️',
            '.gif': '🎞️',
            '.mp4': '🎬',
            '.mp3': '🎵',
            '.zip': '📦',
        }
        
        return icons.get(ext, '📄')


# Global instance
_search_engine = None

def get_search_engine() -> SearchEngine:
    """Get or create global search engine instance"""
    global _search_engine
    if _search_engine is None:
        _search_engine = SearchEngine()
    return _search_engine
