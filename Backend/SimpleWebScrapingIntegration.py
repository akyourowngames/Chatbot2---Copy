"""
Simplified Web Scraping Integration - No Complex Orchestrator
This version avoids threading issues and signal handler conflicts
"""

import re
import time
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

# Import our web scraper modules directly
from web_scraper import (
    StealthFetcher, ScrapingConfig,
    AIParser, ParserConfig
)
from Backend.FirebaseStorage import get_firebase_storage

class SimpleWebScraper:
    """
    Simplified web scraper without complex orchestrator
    """
    
    def __init__(self):
        # Initialize components directly with better configuration
        self.fetcher = StealthFetcher(ScrapingConfig(
            timeout=30,  # Increased timeout for complex sites
            max_retries=3  # More retries for reliability
        ))
        self.parser = AIParser(ParserConfig(
            use_openai=False,
            use_local_models=False,
            extract_entities=True,  # Enable entity extraction
            extract_sentiment=False,
            summarize_content=True  # Enable summarization
        ))
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
        
        logging.info("Simple Web Scraper initialized")
    
    def detect_scraping_intent(self, query: str) -> Dict[str, Any]:
        """
        Detect if the user wants to scrape web content
        """
        query_lower = query.lower()
        
        # Check for scraping patterns
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
        
        # Check for general web-related queries
        web_keywords = ['website', 'url', 'link', 'page', 'article', 'news', 'blog', 'site']
        url_pattern = r'https?://[^\s]+'
        
        if any(keyword in query_lower for keyword in web_keywords):
            url_match = re.search(url_pattern, query)
            if url_match:
                return {
                    'intent': 'scrape',
                    'pattern': 'general_web',
                    'url': url_match.group(0),
                    'confidence': 0.7
                }
        
        return {'intent': 'none', 'confidence': 0.0}
    
    def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from a URL with improved error handling and retry logic
        """
        try:
            logging.info(f"Scraping URL: {url}")
            
            # Clean and validate URL
            url = self._clean_url(url)
            
            # Try multiple approaches for difficult sites
            for attempt in range(3):
                try:
                    # Fetch content
                    response = self.fetcher.fetch(url)
                    
                    if response and self.fetcher.validate_response(response):
                        # Parse content
                        parsed_content = self.parser.parse_html(response.text, url)
                        
                        # Validate parsed content
                        if parsed_content and (parsed_content.content or parsed_content.title):
                            # Store result in Firebase
                            try:
                                storage_data = {
                                    'url': url,
                                    'title': parsed_content.title or 'Untitled',
                                    'content': parsed_content.content or '',
                                    'summary': parsed_content.summary or '',
                                    'word_count': parsed_content.word_count or 0,
                                    'reading_time': parsed_content.reading_time or 1,
                                    'tags': parsed_content.tags or [],
                                    'extracted_at': parsed_content.extracted_at.isoformat() if hasattr(parsed_content.extracted_at, 'isoformat') else datetime.now().isoformat()
                                }
                                self.storage.save_scraped_data(storage_data)
                            except Exception as e:
                                logging.warning(f"Failed to save to Firebase: {e}")
                            
                            return {
                                'success': True,
                                'url': url,
                                'title': parsed_content.title or 'Untitled',
                                'content': parsed_content.content or '',
                                'summary': parsed_content.summary or '',
                                'word_count': parsed_content.word_count or 0,
                                'reading_time': parsed_content.reading_time or 1,
                                'tags': parsed_content.tags or [],
                                'extracted_at': parsed_content.extracted_at
                            }
                        else:
                            logging.warning(f"Empty content from {url}, attempt {attempt + 1}")
                            if attempt < 2:
                                time.sleep(2)  # Wait before retry
                                continue
                    else:
                        logging.warning(f"Invalid response from {url}, attempt {attempt + 1}")
                        if attempt < 2:
                            time.sleep(2)  # Wait before retry
                            continue
                            
                except Exception as e:
                    logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                    if attempt < 2:
                        time.sleep(2)  # Wait before retry
                        continue
            
            # All attempts failed
            return {
                'success': False,
                'url': url,
                'error': 'Failed to fetch or parse content after multiple attempts'
            }
                
        except Exception as e:
            logging.error(f"Error scraping URL {url}: {e}")
            return {
                'success': False,
                'url': url,
                'error': str(e)
            }
    
    def _clean_url(self, url: str) -> str:
        """
        Clean and validate URL
        """
        # Remove extra whitespace
        url = url.strip()
        
        # Fix common URL issues
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Fix Wikipedia URL encoding issues
        if 'wikipedia.org' in url and '%28' in url:
            url = url.replace('%28', '(').replace('%29', ')')
        
        return url
    
    def generate_response(self, query: str, scraping_result: Dict[str, Any]) -> str:
        """
        Generate a natural language response from scraping results
        """
        if not scraping_result.get('success', False):
            return f"I encountered an issue while scraping {scraping_result.get('url', 'the website')}. {scraping_result.get('error', 'Please try again later.')}"
        
        url = scraping_result.get('url', '')
        title = scraping_result.get('title', 'Untitled')
        summary = scraping_result.get('summary', '')
        word_count = scraping_result.get('word_count', 0)
        reading_time = scraping_result.get('reading_time', 0)
        tags = scraping_result.get('tags', [])
        
        response = f"I've successfully scraped content from {title}:\n\n"
        
        if summary:
            response += f"Summary: {summary}\n\n"
        
        response += f"Content Details:\n"
        response += f"• Word Count: {word_count}\n"
        response += f"• Reading Time: {reading_time} minutes\n"
        
        if tags:
            response += f"• Key Topics: {', '.join(tags[:5])}\n"
        
        response += f"• Source: {url}\n"
        
        return response

# Global scraper instance
_scraper_instance = None

def get_scraper():
    """Get or create scraper instance"""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = SimpleWebScraper()
    return _scraper_instance

def integrate_web_scraping(query: str) -> str:
    """
    Main integration function for the chatbot - simplified version
    """
    try:
        scraper = get_scraper()
        
        # Detect scraping intent
        intent = scraper.detect_scraping_intent(query)
        
        if intent['intent'] == 'scrape':
            url = intent['url']
            
            # Scrape the URL
            result = scraper.scrape_url(url)
            
            # Generate response
            response = scraper.generate_response(query, result)
            return response
        
        else:
            return ""  # No scraping intent detected
    
    except Exception as e:
        logging.error(f"Error in web scraping integration: {e}")
        return f"I encountered an error while trying to scrape web content: {str(e)}"

# Example usage and testing
if __name__ == "__main__":
    # Test the integration
    test_queries = [
        "Scrape the latest news from https://httpbin.org/html",
        "Get content from https://example.com",
        "Analyze the website https://httpbin.org/json"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        response = integrate_web_scraping(query)
        if response:
            print(f"Response: {response}")
        else:
            print("No scraping intent detected")
    
    print("\nSimple Web Scraping Integration test completed!")
