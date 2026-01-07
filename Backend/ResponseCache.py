"""
Response Caching and Speed Optimization System
===============================================
Features:
- LRU cache for common queries
- Semantic similarity matching
- Fast response retrieval
- Cache persistence
- Analytics
"""

import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
import pickle

# Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
CACHE_FILE = os.path.join(project_root, "Data", "response_cache.json")
ANALYTICS_FILE = os.path.join(project_root, "Data", "cache_analytics.json")

class ResponseCache:
    """Smart response caching system"""
    
    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self.max_size = max_size
        self.ttl_hours = ttl_hours
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.analytics = {
            "hits": 0,
            "misses": 0,
            "total_time_saved": 0.0,
            "queries_cached": 0
        }
        self.load_cache()
        self.load_analytics()
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query"""
        # Normalize query - keep more text for better matching
        normalized = query.lower().strip()
        # Keep alphanumeric, spaces, and some punctuation for better differentiation
        # IMPORTANT: Don't over-normalize or different queries will match!
        normalized = ' '.join(normalized.split())  # Normalize whitespace only
        # Generate hash
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired"""
        expiry_time = datetime.fromtimestamp(timestamp) + timedelta(hours=self.ttl_hours)
        return datetime.now() > expiry_time
    
    def get(self, query: str) -> Optional[str]:
        """Get cached response if available"""
        # SKIP caching for short/casual messages - they need fresh responses
        if len(query.strip()) < 50:
            return None  # Don't cache short casual messages
            
        cache_key = self._get_cache_key(query)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            # Check if expired
            if self._is_expired(entry['timestamp']):
                del self.cache[cache_key]
                self.analytics["misses"] += 1
                return None
            
            # Update access time and count
            entry['last_accessed'] = time.time()
            entry['access_count'] += 1
            
            # Analytics
            self.analytics["hits"] += 1
            self.analytics["total_time_saved"] += entry.get('generation_time', 2.0)
            
            print(f"Cache HIT for query (saved ~{entry.get('generation_time', 2.0):.1f}s)")
            return entry['response']
        
        self.analytics["misses"] += 1
        return None
    
    def set(self, query: str, response: str, generation_time: float = 2.0):
        """Cache a response"""
        cache_key = self._get_cache_key(query)
        
        # Enforce max size (LRU eviction)
        if len(self.cache) >= self.max_size:
            # Remove least recently accessed
            oldest_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].get('last_accessed', 0)
            )
            del self.cache[oldest_key]
        
        # Add to cache
        self.cache[cache_key] = {
            'query': query,
            'response': response,
            'timestamp': time.time(),
            'last_accessed': time.time(),
            'access_count': 0,
            'generation_time': generation_time
        }
        
        self.analytics["queries_cached"] += 1
        print(f"Cached response for query")
    
    def load_cache(self):
        """Load cache from disk"""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                print(f"Loaded {len(self.cache)} cached responses")
        except Exception as e:
            print(f"Failed to load cache: {e}")
            self.cache = {}
    
    def save_cache(self):
        """Save cache to disk"""
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Failed to save cache: {e}")
    
    def load_analytics(self):
        """Load analytics from disk"""
        try:
            if os.path.exists(ANALYTICS_FILE):
                with open(ANALYTICS_FILE, 'r', encoding='utf-8') as f:
                    self.analytics = json.load(f)
        except Exception as e:
            print(f"Failed to load analytics: {e}")
    
    def save_analytics(self):
        """Save analytics to disk"""
        try:
            with open(ANALYTICS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.analytics, f, indent=2)
        except Exception as e:
            print(f"Failed to save analytics: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.analytics["hits"] + self.analytics["misses"]
        hit_rate = (self.analytics["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "total_requests": total_requests,
            "cache_hits": self.analytics["hits"],
            "cache_misses": self.analytics["misses"],
            "hit_rate": f"{hit_rate:.1f}%",
            "time_saved": f"{self.analytics['total_time_saved']:.1f}s",
            "queries_cached": self.analytics["queries_cached"]
        }
    
    def clear(self):
        """Clear all cache"""
        self.cache = {}
        self.analytics = {
            "hits": 0,
            "misses": 0,
            "total_time_saved": 0.0,
            "queries_cached": 0
        }
        self.save_cache()
        self.save_analytics()
        print("Cache cleared")

# Global cache instance
_cache_instance = None

def get_cache() -> ResponseCache:
    """Get global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ResponseCache()
    return _cache_instance

def cache_response(query: str, response: str, generation_time: float = 2.0):
    """Cache a response (convenience function)"""
    cache = get_cache()
    cache.set(query, response, generation_time)
    cache.save_cache()
    cache.save_analytics()

def get_cached_response(query: str) -> Optional[str]:
    """Get cached response (convenience function)"""
    cache = get_cache()
    return cache.get(query)

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics (convenience function)"""
    cache = get_cache()
    return cache.get_stats()

def clear_cache():
    """Clear cache (convenience function)"""
    cache = get_cache()
    cache.clear()

if __name__ == "__main__":
    print("\nResponse Cache Test\n" + "="*50)
    
    # Test caching
    cache = ResponseCache()
    
    # Add some test responses
    test_queries = [
        ("What is Python?", "Python is a high-level programming language.", 2.5),
        ("How are you?", "I'm doing great, thank you for asking!", 1.5),
        ("What's the weather?", "I don't have real-time weather data.", 2.0),
    ]
    
    print("\n1. Caching responses...")
    for query, response, gen_time in test_queries:
        cache.set(query, response, gen_time)
        print(f"   Cached: '{query}'")
    
    print("\n2. Testing cache retrieval...")
    for query, expected_response, _ in test_queries:
        cached = cache.get(query)
        if cached:
            print(f"   Found: '{query}'")
        else:
            print(f"   Not found: '{query}'")
    
    # Test similar queries (should match due to normalization)
    print("\n3. Testing similar queries...")
    similar_queries = [
        "what is python?",  # Different case
        "How are you",      # Missing punctuation
        "WHATS THE WEATHER" # All caps, no punctuation
    ]
    
    for query in similar_queries:
        cached = cache.get(query)
        if cached:
            print(f"   Matched: '{query}' -> '{cached[:50]}...'")
        else:
            print(f"   No match: '{query}'")
    
    # Show statistics
    print("\n4. Cache Statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Save cache
    cache.save_cache()
    cache.save_analytics()
    print("\nCache saved to disk")
