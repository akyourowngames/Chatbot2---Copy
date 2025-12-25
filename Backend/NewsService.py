"""
Real-Time News Service
======================
Provides real news headlines using NewsAPI.org (free tier: 100 requests/day).
"""

import requests
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsService:
    """Real-time news service using NewsAPI."""
    
    def __init__(self, api_key: str = ""):
        """
        Initialize news service.
        
        Args:
            api_key: NewsAPI.org API key
        """
        # Try environment variable first, then parameter, then default
        self.api_key = api_key or os.getenv('NEWS_API_KEY') or "db201e01fee944d8a119115a844db161"
        self.base_url = "https://newsapi.org/v2"
        self._cache = {}
        self._cache_duration = timedelta(minutes=15)  # Cache for 15 mins
        logger.info("[NEWS] Service initialized")
    
    def get_top_headlines(self, category: str = None, country: str = "us", 
                          page_size: int = 10) -> Dict[str, Any]:
        """
        Get top headlines.
        
        Args:
            category: Category (business, entertainment, general, health, science, sports, technology)
            country: Country code (us, gb, in, etc.)
            page_size: Number of articles (max 100)
            
        Returns:
            Headlines data
        """
        try:
            # Check cache
            cache_key = f"headlines_{category}_{country}_{page_size}"
            if cache_key in self._cache:
                cached_data, cached_time = self._cache[cache_key]
                if datetime.now() - cached_time < self._cache_duration:
                    logger.info(f"[NEWS] Returning cached headlines")
                    return cached_data
            
            # Build request
            params = {
                "apiKey": self.api_key,
                "country": country,
                "pageSize": min(page_size, 100)
            }
            
            if category:
                params["category"] = category
            
            url = f"{self.base_url}/top-headlines"
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "ok":
                raise Exception(data.get("message", "API error"))
            
            # Parse articles
            articles = []
            for article in data.get("articles", []):
                articles.append({
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "url": article.get("url"),
                    "image": article.get("urlToImage"),
                    "source": article.get("source", {}).get("name"),
                    "published_at": article.get("publishedAt"),
                    "author": article.get("author")
                })
            
            result = {
                "status": "success",
                "category": category or "general",
                "country": country,
                "total_results": data.get("totalResults", 0),
                "articles": articles,
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache result
            self._cache[cache_key] = (result, datetime.now())
            
            logger.info(f"[NEWS] Fetched {len(articles)} headlines")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[NEWS] API request failed: {e}")
            return {
                "status": "error",
                "error": "Failed to fetch news",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"[NEWS] Unexpected error: {e}")
            return {
                "status": "error",
                "error": "News service error",
                "message": str(e)
            }
    
    def search_news(self, query: str, page_size: int = 10, 
                    sort_by: str = "relevancy") -> Dict[str, Any]:
        """
        Search for news articles.
        
        Args:
            query: Search keywords
            page_size: Number of results (max 100)
            sort_by: Sort by relevancy, popularity, or publishedAt
            
        Returns:
            Search results
        """
        try:
            params = {
                "apiKey": self.api_key,
                "q": query,
                "pageSize": min(page_size, 100),
                "sortBy": sort_by,
                "language": "en"
            }
            
            url = f"{self.base_url}/everything"
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "ok":
                raise Exception(data.get("message", "API error"))
            
            # Parse articles
            articles = []
            for article in data.get("articles", []):
                articles.append({
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "url": article.get("url"),
                    "image": article.get("urlToImage"),
                    "source": article.get("source", {}).get("name"),
                    "published_at": article.get("publishedAt"),
                    "author": article.get("author")
                })
            
            return {
                "status": "success",
                "query": query,
                "total_results": data.get("totalResults", 0),
                "articles": articles,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[NEWS] Search failed: {e}")
            return {
                "status": "error",
                "error": "Search failed",
                "message": str(e)
            }


# Global instance
news_service = NewsService()


# Convenience functions
def get_news(category: str = None) -> Dict[str, Any]:
    """Get top news headlines."""
    return news_service.get_top_headlines(category=category)


def search_news(query: str) -> Dict[str, Any]:
    """Search news articles."""
    return news_service.search_news(query)


# Test
if __name__ == "__main__":
    print("📰 Testing News Service\n")
    
    # Test top headlines
    news = get_news(category="technology")
    if news["status"] == "success":
        print(f"📱 Top {len(news['articles'])} Technology Headlines:\n")
        for i, article in enumerate(news["articles"][:5], 1):
            print(f"{i}. {article['title']}")
            print(f"   Source: {article['source']}")
            print()
    
    # Test search
    search_results = search_news("artificial intelligence")
    if search_results["status"] == "success":
        print(f"\n🔍 Found {search_results['total_results']} results for 'AI'")
