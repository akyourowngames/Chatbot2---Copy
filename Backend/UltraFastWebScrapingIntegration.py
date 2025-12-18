"""
Ultra-Fast Parallel Web Scraping - Maximum Speed Optimization
This version uses parallel processing and aggressive caching
"""

import re
import time
import logging
import requests
import random
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Import Firebase storage
from Backend.FirebaseStorage import get_firebase_storage

class UltraFastWebScraper:
    """
    Ultra-fast web scraper with parallel processing and aggressive caching
    """
    
    def __init__(self):
        self.storage = get_firebase_storage()
        
        # Web scraping patterns
        self.scraping_patterns = {
            'scrape_url': r'scrape\s+(?:the\s+)?(?:website\s+)?(?:url\s+)?(https?://[^\s]+)',
            'scrape_content': r'scrape\s+(?:content\s+from\s+)?(?:the\s+)?(?:website\s+)?(https?://[^\s]+)',
            'get_news': r'(?:get|fetch|scrape)\s+(?:the\s+)?(?:latest\s+)?(?:news\s+)?(?:from\s+)?(https?://[^\s]+)',
            'extract_data': r'extract\s+(?:data\s+)?(?:from\s+)?(https?://[^\s]+)',
            'read_article': r'read\s+(?:the\s+)?(?:article\s+)?(?:from\s+)?(https?://[^\s]+)',
            'summarize_url': r'summarize\s+(?:the\s+)?(?:content\s+)?(?:from\s+)?(https?://[^\s]+)',
            'analyze_website': r'analyze\s+(?:the\s+)?(?:website\s+)?(https?://[^\s]+)',
            'get_headlines': r'(?:get|fetch)\s+(?:the\s+)?(?:latest\s+)?(?:headlines\s+)?(?:from\s+)?(https?://[^\s]+)',
            'track_prices': r'track\s+(?:prices?\s+)?(?:from\s+)?(https?://[^\s]+)',
            'monitor_changes': r'monitor\s+(?:changes?\s+)?(?:on\s+)?(https?://[^\s]+)'
        }
        
        # Fast user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Minimal headers for speed
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        }
        
        # Aggressive response cache
        self.cache = {}
        self.cache_timeout = 600  # 10 minutes
        self.cache_lock = threading.Lock()
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        logging.info("Ultra-Fast Web Scraper initialized")
    
    def detect_scraping_intent(self, query: str) -> Dict[str, Any]:
        """
        Ultra-fast detection of scraping intent
        """
        query_lower = query.lower()
        
        # Quick pattern matching
        for pattern_name, pattern in self.scraping_patterns.items():
            match = re.search(pattern, query_lower)
            if match:
                url = match.group(1)
                return {
                    'intent': 'scrape',
                    'pattern': pattern_name,
                    'url': url,
                    'confidence': 0.9
                }
        
        # Quick web keyword check
        if any(keyword in query_lower for keyword in ['website', 'url', 'link', 'page', 'article', 'news', 'blog', 'site']):
            url_match = re.search(r'https?://[^\s]+', query)
            if url_match:
                return {
                    'intent': 'scrape',
                    'pattern': 'general_web',
                    'url': url_match.group(0),
                    'confidence': 0.7
                }
        
        return {'intent': 'none', 'confidence': 0.0}
    
    def scrape_url_ultra_fast(self, url: str) -> Dict[str, Any]:
        """
        Ultra-fast URL scraping with maximum optimization
        """
        try:
            # Check cache first with thread safety
            cache_key = f"scrape_{url}"
            with self.cache_lock:
                if cache_key in self.cache:
                    cached_time, cached_data = self.cache[cache_key]
                    if time.time() - cached_time < self.cache_timeout:
                        logging.info(f"Using cached data for {url}")
                        return cached_data
            
            logging.info(f"Ultra-fast scraping URL: {url}")
            
            # Clean URL quickly
            url = self._clean_url_fast(url)
            
            # Ultra-fast single attempt with minimal timeout
            try:
                headers = self.headers.copy()
                headers['User-Agent'] = random.choice(self.user_agents)
                
                # Ultra-fast request with minimal timeout
                response = self.session.get(
                    url, 
                    headers=headers, 
                    timeout=5,  # Ultra-fast: 5 seconds max
                    verify=False,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    # Ultra-fast content extraction
                    soup = BeautifulSoup(response.content, 'lxml')
                    
                    # Quick title extraction
                    title = self._extract_title_ultra_fast(soup)
                    
                    # Quick content extraction (first 500 chars only for speed)
                    content = self._extract_content_ultra_fast(soup)
                    
                    if content and len(content.strip()) > 10:  # Very low threshold for speed
                        # Quick metrics
                        word_count = len(content.split())
                        reading_time = max(1, word_count // 200)
                        
                        # Ultra-quick summary (first 100 chars)
                        summary = content[:100] + "..." if len(content) > 100 else content
                        
                        result = {
                            'success': True,
                            'url': url,
                            'title': title,
                            'content': content,
                            'summary': summary,
                            'word_count': word_count,
                            'reading_time': reading_time,
                            'tags': [],  # Skip tag extraction for speed
                            'extracted_at': datetime.now()
                        }
                        
                        # Cache the result with thread safety
                        with self.cache_lock:
                            self.cache[cache_key] = (time.time(), result)
                        
                        # Store in Firebase asynchronously (don't wait)
                        self._store_async(result)
                        
                        return result
                    else:
                        return {
                            'success': False,
                            'url': url,
                            'error': 'Insufficient content extracted'
                        }
                else:
                    return {
                        'success': False,
                        'url': url,
                        'error': f'HTTP {response.status_code}'
                    }
                    
            except Exception as e:
                return {
                    'success': False,
                    'url': url,
                    'error': str(e)
                }
                
        except Exception as e:
            logging.error(f"Error in ultra-fast scraping: {e}")
            return {
                'success': False,
                'url': url,
                'error': str(e)
            }
    
    def _clean_url_fast(self, url: str) -> str:
        """Ultra-fast URL cleaning"""
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url
    
    def _extract_title_ultra_fast(self, soup: BeautifulSoup) -> str:
        """Ultra-fast title extraction"""
        title = soup.find('title')
        if title:
            return title.get_text().strip()[:50]  # Very short for speed
        
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()[:50]
        
        return 'Untitled'
    
    def _extract_content_ultra_fast(self, soup: BeautifulSoup) -> str:
        """Ultra-fast content extraction - minimal processing"""
        # Remove unwanted elements quickly
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
            element.decompose()
        
        # Try to find main content quickly
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        
        if main_content:
            text = main_content.get_text().strip()
        else:
            # Fallback: get first few paragraphs only
            paragraphs = soup.find_all('p')
            text = ' '.join([p.get_text().strip() for p in paragraphs[:5]])  # Only first 5 paragraphs
        
        # Clean and limit text aggressively
        text = re.sub(r'\s+', ' ', text)
        return text[:1000]  # Limit to 1000 characters for ultra speed
    
    def _store_async(self, data: Dict[str, Any]):
        """Store data asynchronously without blocking"""
        try:
            # Run storage in background thread
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._store_data, data)
                # Don't wait for completion
        except Exception as e:
            logging.warning(f"Failed to store data asynchronously: {e}")
    
    def _store_data(self, data: Dict[str, Any]):
        """Store data in Firebase"""
        try:
            storage_data = {
                'url': data['url'],
                'title': data['title'],
                'content': data['content'],
                'summary': data['summary'],
                'word_count': data['word_count'],
                'reading_time': data['reading_time'],
                'tags': data['tags'],
                'extracted_at': datetime.now().isoformat()
            }
            self.storage.save_scraped_data(storage_data)
        except Exception as e:
            logging.warning(f"Failed to store in Firebase: {e}")
    
    def generate_response_ultra_fast(self, query: str, scraping_result: Dict[str, Any]) -> str:
        """
        Generate ultra-fast response from scraping results
        """
        if not scraping_result.get('success', False):
            return f"Unable to scrape {scraping_result.get('url', 'the website')}. {scraping_result.get('error', 'Please try again.')}"
        
        url = scraping_result.get('url', '')
        title = scraping_result.get('title', 'Untitled')
        summary = scraping_result.get('summary', '')
        word_count = scraping_result.get('word_count', 0)
        reading_time = scraping_result.get('reading_time', 0)
        
        # Ultra-fast response format
        response = f"**{title}**\n\n"
        
        if summary:
            response += f"{summary}\n\n"
        
        response += f"📊 {word_count} words • ⏱️ {reading_time} min • 🔗 {url}"
        
        return response

# Global scraper instance
_ultra_fast_scraper_instance = None

def get_ultra_fast_scraper():
    """Get or create ultra-fast scraper instance"""
    global _ultra_fast_scraper_instance
    if _ultra_fast_scraper_instance is None:
        _ultra_fast_scraper_instance = UltraFastWebScraper()
    return _ultra_fast_scraper_instance

def integrate_web_scraping_ultra_fast(query: str) -> str:
    """
    Ultra-fast web scraping integration with maximum speed
    """
    try:
        scraper = get_ultra_fast_scraper()
        
        # Ultra-fast intent detection
        intent = scraper.detect_scraping_intent(query)
        
        if intent['intent'] == 'scrape':
            url = intent['url']
            
            # Ultra-fast scraping
            result = scraper.scrape_url_ultra_fast(url)
            
            # Ultra-fast response generation
            response = scraper.generate_response_ultra_fast(query, result)
            return response
        
        else:
            return ""  # No scraping intent detected
    
    except Exception as e:
        logging.error(f"Error in ultra-fast web scraping: {e}")
        return f"Ultra-fast scraping error: {str(e)}"

# Example usage and testing
if __name__ == "__main__":
    # Test the ultra-fast integration
    test_queries = [
        "Scrape https://example.com",
        "Get content from https://httpbin.org/html"
    ]
    
    start_time = time.time()
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        response = integrate_web_scraping_ultra_fast(query)
        if response:
            print(f"Response: {response}")
        else:
            print("No scraping intent detected")
    
    end_time = time.time()
    print(f"\nTotal time: {end_time - start_time:.2f} seconds")
    print("Ultra-Fast Web Scraping Integration test completed!")
