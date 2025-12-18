"""
🕸️ WEB SCRAPING INTEGRATION — Chatbot Web Intelligence 🧠
Integration module that adds web scraping capabilities to the existing chatbot system.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import asyncio
import threading
import time

# Import our web scraper modules
from web_scraper import (
    WebScrapingOrchestrator, OrchestratorConfig,
    StealthFetcher, ScrapingConfig,
    AIParser, ParserConfig,
    DynamicBrowser, BrowserConfig,
    DataStorage, StorageConfig,
    WebScrapingLogger, LogConfig
)

class ChatbotWebScraper:
    """
    🧠 Web scraping integration for the chatbot system
    """
    
    def __init__(self):
        # Initialize web scraper components
        self.orchestrator = WebScrapingOrchestrator(OrchestratorConfig(
            max_concurrent_jobs=5,
            log_level="INFO"
        ))
        
        self.fetcher = StealthFetcher(ScrapingConfig())
        self.parser = AIParser(ParserConfig())
        self.storage = DataStorage(StorageConfig())
        self.logger = WebScrapingLogger(LogConfig())
        
        # Start orchestrator
        self.orchestrator.start()
        
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
        
        # Known news and content sites
        self.news_sites = [
            'bbc.com', 'cnn.com', 'reuters.com', 'ap.org', 'npr.org',
            'techcrunch.com', 'wired.com', 'theverge.com', 'arstechnica.com',
            'hackernews.com', 'reddit.com', 'medium.com', 'dev.to'
        ]
        
        self.logger.log_info("Chatbot Web Scraper initialized")
    
    def detect_scraping_intent(self, query: str) -> Dict[str, Any]:
        """
        🔍 Detect if the user wants to scrape web content
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
    
    def scrape_url(self, url: str, use_browser: bool = False, extract_type: str = 'full') -> Dict[str, Any]:
        """
        🕸️ Scrape content from a URL
        """
        try:
            self.logger.log_info(f"Scraping URL: {url}")
            
            # Add job to orchestrator
            job_id = self.orchestrator.add_job(
                url=url,
                use_browser=use_browser,
                extract_images=True,
                extract_links=True
            )
            
            # Wait for job completion
            max_wait = 30  # 30 seconds timeout
            wait_time = 0
            
            while job_id in self.orchestrator.active_jobs and wait_time < max_wait:
                time.sleep(1)
                wait_time += 1
            
            if job_id in self.orchestrator.completed_jobs:
                # Get scraped content from storage
                search_results = self.storage.search_content("")
                
                if search_results:
                    latest_result = search_results[0]  # Get most recent
                    
                    # Format response based on extract_type
                    if extract_type == 'summary':
                        return {
                            'success': True,
                            'url': url,
                            'title': latest_result.get('title', ''),
                            'summary': latest_result.get('summary', ''),
                            'word_count': latest_result.get('word_count', 0),
                            'reading_time': latest_result.get('reading_time', 0),
                            'sentiment': latest_result.get('sentiment', ''),
                            'tags': latest_result.get('tags', [])
                        }
                    elif extract_type == 'headlines':
                        return {
                            'success': True,
                            'url': url,
                            'title': latest_result.get('title', ''),
                            'content_preview': latest_result.get('content', '')[:500] + '...',
                            'entities': latest_result.get('entities', {}),
                            'tags': latest_result.get('tags', [])
                        }
                    else:  # full
                        return {
                            'success': True,
                            'url': url,
                            'title': latest_result.get('title', ''),
                            'content': latest_result.get('content', ''),
                            'summary': latest_result.get('summary', ''),
                            'author': latest_result.get('author', ''),
                            'publish_date': latest_result.get('publish_date', ''),
                            'word_count': latest_result.get('word_count', 0),
                            'reading_time': latest_result.get('reading_time', 0),
                            'sentiment': latest_result.get('sentiment', ''),
                            'language': latest_result.get('language', ''),
                            'tags': latest_result.get('tags', []),
                            'entities': latest_result.get('entities', {}),
                            'images': latest_result.get('images', []),
                            'links': latest_result.get('links', [])
                        }
            
            return {
                'success': False,
                'url': url,
                'error': 'Failed to scrape content or timeout occurred'
            }
            
        except Exception as e:
            self.logger.log_error(f"Error scraping URL {url}", e)
            return {
                'success': False,
                'url': url,
                'error': str(e)
            }
    
    def scrape_multiple_urls(self, urls: List[str], extract_type: str = 'summary') -> List[Dict[str, Any]]:
        """
        🕸️ Scrape multiple URLs
        """
        results = []
        
        for url in urls:
            result = self.scrape_url(url, extract_type=extract_type)
            results.append(result)
            
            # Small delay between requests
            time.sleep(1)
        
        return results
    
    def get_news_headlines(self, url: str) -> Dict[str, Any]:
        """
        📰 Get news headlines from a URL
        """
        result = self.scrape_url(url, extract_type='headlines')
        
        if result['success']:
            # Extract headlines from content
            content = result.get('content_preview', '')
            
            # Simple headline extraction (can be improved with AI)
            lines = content.split('\n')
            headlines = []
            
            for line in lines:
                line = line.strip()
                if len(line) > 20 and len(line) < 200:  # Reasonable headline length
                    # Check if it looks like a headline
                    if any(keyword in line.lower() for keyword in ['news', 'report', 'update', 'breaking', 'latest']):
                        headlines.append(line)
            
            result['headlines'] = headlines[:10]  # Limit to 10 headlines
        
        return result
    
    def analyze_website(self, url: str) -> Dict[str, Any]:
        """
        🔍 Analyze a website and provide insights
        """
        result = self.scrape_url(url, extract_type='full')
        
        if result['success']:
            analysis = {
                'url': url,
                'title': result.get('title', ''),
                'content_type': self._detect_content_type(result),
                'quality_score': self._calculate_quality_score(result),
                'key_topics': result.get('tags', [])[:5],
                'sentiment': result.get('sentiment', 'neutral'),
                'reading_time': result.get('reading_time', 0),
                'word_count': result.get('word_count', 0),
                'entities': result.get('entities', {}),
                'has_images': len(result.get('images', [])) > 0,
                'has_links': len(result.get('links', [])) > 0,
                'language': result.get('language', 'unknown'),
                'recommendations': self._generate_recommendations(result)
            }
            
            return analysis
        
        return result
    
    def track_prices(self, url: str) -> Dict[str, Any]:
        """
        💰 Track prices from e-commerce sites
        """
        result = self.scrape_url(url, use_browser=True, extract_type='full')
        
        if result['success']:
            # Extract price information
            content = result.get('content', '')
            prices = self._extract_prices(content)
            
            return {
                'success': True,
                'url': url,
                'title': result.get('title', ''),
                'prices': prices,
                'currency': self._detect_currency(content),
                'availability': self._check_availability(content),
                'scraped_at': datetime.now().isoformat()
            }
        
        return result
    
    def generate_scraping_response(self, query: str, scraping_result: Dict[str, Any]) -> str:
        """
        💬 Generate a natural language response from scraping results
        """
        if not scraping_result.get('success', False):
            return f"I encountered an issue while scraping {scraping_result.get('url', 'the website')}. {scraping_result.get('error', 'Please try again later.')}"
        
        url = scraping_result.get('url', '')
        title = scraping_result.get('title', 'Untitled')
        
        # Generate response based on content type
        if 'headlines' in scraping_result:
            headlines = scraping_result['headlines']
            response = f"Here are the latest headlines from {url}:\n\n"
            for i, headline in enumerate(headlines, 1):
                response += f"{i}. {headline}\n"
            return response
        
        elif 'prices' in scraping_result:
            prices = scraping_result['prices']
            currency = scraping_result.get('currency', '$')
            response = f"Here's the pricing information from {title}:\n\n"
            for price in prices:
                response += f"• {currency}{price}\n"
            return response
        
        else:
            # General content response
            summary = scraping_result.get('summary', '')
            word_count = scraping_result.get('word_count', 0)
            reading_time = scraping_result.get('reading_time', 0)
            sentiment = scraping_result.get('sentiment', 'neutral')
            
            response = f"I've scraped content from {title}:\n\n"
            
            if summary:
                response += f"Summary: {summary}\n\n"
            
            response += f"Content Details:\n"
            response += f"• Word Count: {word_count}\n"
            response += f"• Reading Time: {reading_time} minutes\n"
            response += f"• Sentiment: {sentiment}\n"
            
            tags = scraping_result.get('tags', [])
            if tags:
                response += f"• Key Topics: {', '.join(tags[:5])}\n"
            
            return response
    
    def _detect_content_type(self, result: Dict[str, Any]) -> str:
        """Detect the type of content"""
        title = result.get('title', '').lower()
        content = result.get('content', '').lower()
        
        if any(keyword in title for keyword in ['news', 'breaking', 'update']):
            return 'news'
        elif any(keyword in title for keyword in ['blog', 'post', 'article']):
            return 'blog'
        elif any(keyword in title for keyword in ['price', 'buy', 'shop', 'store']):
            return 'ecommerce'
        elif any(keyword in title for keyword in ['tutorial', 'guide', 'how to']):
            return 'tutorial'
        else:
            return 'general'
    
    def _calculate_quality_score(self, result: Dict[str, Any]) -> float:
        """Calculate content quality score"""
        score = 0.0
        
        # Word count score
        word_count = result.get('word_count', 0)
        if word_count > 500:
            score += 0.3
        elif word_count > 200:
            score += 0.2
        elif word_count > 100:
            score += 0.1
        
        # Title quality
        title = result.get('title', '')
        if len(title) > 10 and len(title) < 100:
            score += 0.2
        
        # Summary quality
        summary = result.get('summary', '')
        if len(summary) > 50:
            score += 0.2
        
        # Tags quality
        tags = result.get('tags', [])
        if len(tags) >= 3:
            score += 0.1
        
        # Entities quality
        entities = result.get('entities', {})
        if entities:
            score += 0.1
        
        # Images and links
        if result.get('images'):
            score += 0.05
        if result.get('links'):
            score += 0.05
        
        return min(score, 1.0)
    
    def _generate_recommendations(self, result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on content analysis"""
        recommendations = []
        
        word_count = result.get('word_count', 0)
        if word_count < 200:
            recommendations.append("Content is quite short, consider adding more detail")
        
        if not result.get('summary'):
            recommendations.append("Consider adding a summary for better readability")
        
        if not result.get('tags'):
            recommendations.append("Adding relevant tags would improve discoverability")
        
        sentiment = result.get('sentiment', 'neutral')
        if sentiment == 'negative':
            recommendations.append("Content has negative sentiment, consider balancing with positive aspects")
        
        return recommendations
    
    def _extract_prices(self, content: str) -> List[str]:
        """Extract price information from content"""
        import re
        
        # Common price patterns
        price_patterns = [
            r'\$[\d,]+\.?\d*',  # $123.45
            r'€[\d,]+\.?\d*',   # €123.45
            r'£[\d,]+\.?\d*',   # £123.45
            r'₹[\d,]+\.?\d*',   # ₹123.45
            r'[\d,]+\.?\d*\s*(?:USD|EUR|GBP|INR)',  # 123.45 USD
        ]
        
        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, content)
            prices.extend(matches)
        
        return list(set(prices))  # Remove duplicates
    
    def _detect_currency(self, content: str) -> str:
        """Detect currency from content"""
        if '$' in content:
            return '$'
        elif '€' in content:
            return '€'
        elif '£' in content:
            return '£'
        elif '₹' in content:
            return '₹'
        else:
            return '$'  # Default
    
    def _check_availability(self, content: str) -> str:
        """Check product availability"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['out of stock', 'unavailable', 'sold out']):
            return 'out_of_stock'
        elif any(keyword in content_lower for keyword in ['in stock', 'available', 'buy now']):
            return 'in_stock'
        else:
            return 'unknown'
    
    def shutdown(self):
        """Shutdown the web scraper"""
        self.orchestrator.shutdown()
        self.logger.log_info("Chatbot Web Scraper shutdown complete")

# Integration function for the existing chatbot
def integrate_web_scraping(query: str) -> str:
    """
    🔗 Main integration function for the chatbot
    """
    scraper = ChatbotWebScraper()
    
    try:
        # Detect scraping intent
        intent = scraper.detect_scraping_intent(query)
        
        if intent['intent'] == 'scrape':
            url = intent['url']
            
            # Determine scraping type based on pattern
            pattern = intent['pattern']
            
            if pattern in ['get_news', 'get_headlines']:
                result = scraper.get_news_headlines(url)
            elif pattern == 'track_prices':
                result = scraper.track_prices(url)
            elif pattern == 'analyze_website':
                result = scraper.analyze_website(url)
            elif pattern == 'summarize_url':
                result = scraper.scrape_url(url, extract_type='summary')
            else:
                result = scraper.scrape_url(url)
            
            # Generate response
            response = scraper.generate_scraping_response(query, result)
            return response
        
        else:
            return ""  # No scraping intent detected
    
    except Exception as e:
        logging.error(f"Error in web scraping integration: {e}")
        return f"I encountered an error while trying to scrape web content: {str(e)}"
    
    finally:
        scraper.shutdown()

# Example usage and testing
if __name__ == "__main__":
    # Test the integration
    test_queries = [
        "Scrape the latest news from https://techcrunch.com",
        "Get headlines from https://bbc.com",
        "Analyze the website https://example.com",
        "Track prices from https://amazon.com/product",
        "Summarize the content from https://wikipedia.org"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        response = integrate_web_scraping(query)
        if response:
            print(f"Response: {response}")
        else:
            print("No scraping intent detected")
    
    print("\n🧠 Web Scraping Integration test completed!")
