"""
Advanced Web Scraper - Beast Mode (Ultra Fast)
==============================================
Lightning-fast, parallelized web intelligence engine.
Features:
- Markdown-optimized extraction for LLMs
- Parallel batch processing
- Intelligent content filtering (De-cluttering)
- Deep metadata & SEO harvesting
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

class JarvisWebScraper:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1'
        }

    async def get_session(self):
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=15)
            self.session = aiohttp.ClientSession(headers=self.headers, timeout=timeout)
        return self.session

    async def fetch(self, url: str) -> Optional[str]:
        """Fetch raw HTML with resilience"""
        try:
            session = await self.get_session()
            async with session.get(url, allow_redirects=True) as response:
                if response.status == 200:
                    return await response.text()
                print(f"[Scraper] HTTP {response.status} for {url}")
        except Exception as e:
            print(f"[Scraper] Fetch Error: {e}")
        return None

    async def scrape_to_markdown(self, url: str) -> str:
        """Beast Mode: Convert page to clean Markdown for LLM consumption"""
        html = await self.fetch(url)
        if not html: return f"Error: Could not reach {url}"
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # De-clutter
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        title = soup.title.string if soup.title else "No Title"
        content = []
        content.append(f"# {title}\n")
        content.append(f"**URL:** {url}\n")
        
        # Smart Content Extraction
        main_content = soup.find('main') or soup.find('article') or soup.body
        if main_content:
            for tag in main_content.find_all(['h1', 'h2', 'h3', 'p', 'li']):
                text = tag.get_text().strip()
                if not text: continue
                
                if tag.name == 'h1': content.append(f"# {text}")
                elif tag.name == 'h2': content.append(f"## {text}")
                elif tag.name == 'h3': content.append(f"### {text}")
                elif tag.name == 'p': content.append(f"\n{text}\n")
                elif tag.name == 'li': content.append(f"- {text}")

        markdown = "\n".join(content)
        return markdown[:8000] # Limit to 8k chars

    async def search_quick(self, query: str):
        """Ultra-fast search results extraction"""
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        html = await self.fetch(url)
        if not html: return []
        
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Google result parsing (modern)
        for g in soup.select('.g'):
            link = g.select_one('a')
            title = g.select_one('h3')
            snippet = g.select_one('.VwiC3b')
            
            if link and title:
                results.append({
                    'title': title.get_text(),
                    'link': link['href'],
                    'snippet': snippet.get_text() if snippet else ""
                })
        return results[:5]

    async def close(self):
        if self.session: await self.session.close()

# Global instance
jarvis_scraper = JarvisWebScraper()

# Wrappers
async def scrape_markdown(url): return await jarvis_scraper.scrape_to_markdown(url)
async def quick_search(query): return await jarvis_scraper.search_quick(query)
