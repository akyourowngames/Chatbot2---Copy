"""
🕸️ STEALTH FETCHER — The Eyes of the Machine 👁️‍🕷️
Advanced web scraping fetcher with stealth capabilities, proxy rotation, and anti-detection measures.
"""

import requests
import random
import time
import json
from typing import Dict, List, Optional, Union
from fake_useragent import UserAgent
from urllib.parse import urljoin, urlparse
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import aiohttp
import asyncio
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

@dataclass
class ScrapingConfig:
    """Configuration for scraping behavior"""
    timeout: int = 30
    max_retries: int = 3
    delay_range: tuple = (1, 3)
    use_proxy: bool = False
    proxy_list: List[str] = None
    user_agent_rotation: bool = True
    respect_robots: bool = True
    max_concurrent: int = 10

class StealthFetcher:
    """
    🕶️ Stealth-grade web fetcher with advanced anti-detection capabilities
    """
    
    def __init__(self, config: ScrapingConfig = None):
        self.config = config or ScrapingConfig()
        self.ua = UserAgent()
        self.session = requests.Session()
        self.proxy_index = 0
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Load proxy list if provided
        if self.config.proxy_list:
            self.proxies = self.config.proxy_list
        else:
            self.proxies = self._load_free_proxies()
    
    def _load_free_proxies(self) -> List[str]:
        """Load free proxy list from various sources"""
        proxies = []
        try:
            # Free proxy sources (you can add more)
            proxy_sources = [
                "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
                "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt"
            ]
            
            for source in proxy_sources:
                try:
                    response = requests.get(source, timeout=10)
                    if response.status_code == 200:
                        proxies.extend([f"http://{proxy.strip()}" for proxy in response.text.split('\n') if proxy.strip()])
                except:
                    continue
                    
        except Exception as e:
            logging.warning(f"Failed to load free proxies: {e}")
            
        return proxies[:50]  # Limit to 50 proxies
    
    def _get_random_headers(self) -> Dict[str, str]:
        """Generate randomized headers for stealth"""
        headers = {
            'User-Agent': self.ua.random if self.config.user_agent_rotation else self.ua.chrome,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice([
                'en-US,en;q=0.5',
                'en-GB,en;q=0.5',
                'en-CA,en;q=0.5',
                'es-ES,es;q=0.5',
                'fr-FR,fr;q=0.5',
                'de-DE,de;q=0.5'
            ]),
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        # Randomly add some optional headers
        if random.random() > 0.5:
            headers['Sec-Fetch-User'] = '?1'
        
        return headers
    
    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """Get next proxy in rotation"""
        if not self.config.use_proxy or not self.proxies:
            return None
            
        proxy = self.proxies[self.proxy_index % len(self.proxies)]
        self.proxy_index += 1
        
        return {
            'http': proxy,
            'https': proxy
        }
    
    def _random_delay(self):
        """Add random delay between requests"""
        delay = random.uniform(*self.config.delay_range)
        time.sleep(delay)
    
    def fetch(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        🕶️ Stealth fetch a single URL with anti-detection measures
        """
        try:
            # Prepare request parameters
            params = {
                'timeout': self.config.timeout,
                'headers': self._get_random_headers(),
                'proxies': self._get_proxy(),
                'allow_redirects': True,
                'verify': False  # For development - enable in production
            }
            
            # Merge with custom kwargs
            params.update(kwargs)
            
            # Add random delay
            self._random_delay()
            
            # Make the request
            response = self.session.get(url, **params)
            
            # Log the request
            logging.info(f"🕸️ Fetched: {url} | Status: {response.status_code} | Size: {len(response.content)} bytes")
            
            return response
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Failed to fetch {url}: {e}")
            return None
    
    def fetch_multiple(self, urls: List[str], **kwargs) -> Dict[str, Optional[requests.Response]]:
        """
        🚀 Fetch multiple URLs concurrently with thread pool
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.config.max_concurrent) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(self.fetch, url, **kwargs): url 
                for url in urls
            }
            
            # Collect results
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    results[url] = future.result()
                except Exception as e:
                    logging.error(f"❌ Error fetching {url}: {e}")
                    results[url] = None
        
        return results
    
    async def fetch_async(self, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """
        ⚡ Async fetch for maximum speed
        """
        try:
            headers = self._get_random_headers()
            proxy = self._get_proxy()
            
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            async with aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                connector=aiohttp.TCPConnector(verify_ssl=False)
            ) as session:
                
                # Add random delay
                await asyncio.sleep(random.uniform(*self.config.delay_range))
                
                async with session.get(url, proxy=proxy.get('http') if proxy else None, **kwargs) as response:
                    logging.info(f"🕸️ Async fetched: {url} | Status: {response.status} | Size: {len(await response.read())} bytes")
                    return response
                    
        except Exception as e:
            logging.error(f"❌ Async fetch failed for {url}: {e}")
            return None
    
    async def fetch_multiple_async(self, urls: List[str], **kwargs) -> Dict[str, Optional[aiohttp.ClientResponse]]:
        """
        🚀⚡ Fetch multiple URLs asynchronously for insane speed
        """
        tasks = [self.fetch_async(url, **kwargs) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        return dict(zip(urls, responses))
    
    def validate_response(self, response: requests.Response) -> bool:
        """
        🔍 Validate if response is valid and not blocked
        """
        if not response:
            return False
            
        # Check status code
        if response.status_code not in [200, 201, 202]:
            return False
            
        # Check content length
        if len(response.content) < 100:
            return False
            
        # Check for common blocking indicators
        blocking_indicators = [
            'access denied',
            'blocked',
            'captcha',
            'cloudflare',
            'rate limit',
            'too many requests'
        ]
        
        content_lower = response.text.lower()
        for indicator in blocking_indicators:
            if indicator in content_lower:
                logging.warning(f"🚫 Possible blocking detected: {indicator}")
                return False
                
        return True
    
    def get_page_info(self, url: str) -> Dict[str, Union[str, int]]:
        """
        📊 Get basic page information without full content
        """
        try:
            response = self.session.head(url, headers=self._get_random_headers(), timeout=10)
            
            return {
                'url': url,
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'content_length': response.headers.get('content-length', 0),
                'last_modified': response.headers.get('last-modified', ''),
                'server': response.headers.get('server', ''),
                'accessible': response.status_code == 200
            }
            
        except Exception as e:
            logging.error(f"❌ Failed to get page info for {url}: {e}")
            return {'url': url, 'accessible': False, 'error': str(e)}

# Convenience functions for easy usage
def fetch_url(url: str, config: ScrapingConfig = None) -> Optional[str]:
    """Quick fetch function for single URL"""
    fetcher = StealthFetcher(config)
    response = fetcher.fetch(url)
    return response.text if response and fetcher.validate_response(response) else None

def fetch_multiple_urls(urls: List[str], config: ScrapingConfig = None) -> Dict[str, Optional[str]]:
    """Quick fetch function for multiple URLs"""
    fetcher = StealthFetcher(config)
    responses = fetcher.fetch_multiple(urls)
    
    results = {}
    for url, response in responses.items():
        if response and fetcher.validate_response(response):
            results[url] = response.text
        else:
            results[url] = None
            
    return results

async def fetch_url_async(url: str, config: ScrapingConfig = None) -> Optional[str]:
    """Quick async fetch function"""
    fetcher = StealthFetcher(config)
    response = await fetcher.fetch_async(url)
    return await response.text() if response else None

# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Test the fetcher
    config = ScrapingConfig(
        timeout=15,
        max_retries=2,
        delay_range=(0.5, 1.5),
        use_proxy=False,
        user_agent_rotation=True
    )
    
    fetcher = StealthFetcher(config)
    
    # Test single fetch
    print("🕸️ Testing single fetch...")
    response = fetcher.fetch("https://httpbin.org/get")
    if response:
        print(f"✅ Success: {response.status_code}")
    else:
        print("❌ Failed")
    
    # Test multiple fetches
    print("\n🚀 Testing multiple fetches...")
    urls = [
        "https://httpbin.org/get",
        "https://httpbin.org/user-agent",
        "https://httpbin.org/headers"
    ]
    
    results = fetcher.fetch_multiple(urls)
    for url, response in results.items():
        if response:
            print(f"✅ {url}: {response.status_code}")
        else:
            print(f"❌ {url}: Failed")
    
    print("\n🕸️ Stealth Fetcher initialized successfully!")
