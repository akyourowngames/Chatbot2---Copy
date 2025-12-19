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
        """Beast Mode: Convert page to ultra-rich Markdown for LLM consumption"""
        html = await self.fetch(url)
        if not html: return f"Error: Could not reach {url}"
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # De-clutter
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            element.decompose()

        title = soup.title.string if soup.title else "No Title"
        content = []
        content.append(f"# {title}\n")
        content.append(f"**URL:** {url}\n")
        
        # Extract metadata
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            content.append(f"**Description:** {meta_desc['content']}\n")
        
        meta_keywords = soup.find('meta', {'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            content.append(f"**Keywords:** {meta_keywords['content']}\n")
        
        content.append("\n---\n")
        
        # Smart Content Extraction - Enhanced for MAXIMUM data
        main_content = soup.find('main') or soup.find('article') or soup.find(class_=re.compile(r'content|article|post|entry|main')) or soup.body
        
        if main_content:
            # Track seen text to avoid duplicates
            seen_texts = set()
            
            # Extract all relevant elements
            for tag in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'blockquote', 'pre', 'code', 'span', 'div', 'td', 'th', 'a', 'strong', 'em']):
                # Skip nested divs that contain other tags we'll process
                if tag.name == 'div' and tag.find(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'table']):
                    continue
                    
                text = tag.get_text().strip()
                
                # Deduplication and length filter
                if not text or len(text) < 10 or text in seen_texts:
                    continue
                seen_texts.add(text)
                
                if tag.name == 'h1': content.append(f"\n# {text}\n")
                elif tag.name == 'h2': content.append(f"\n## {text}\n")
                elif tag.name == 'h3': content.append(f"\n### {text}\n")
                elif tag.name in ['h4', 'h5', 'h6']: content.append(f"\n#### {text}\n")
                elif tag.name == 'p': content.append(f"\n{text}\n")
                elif tag.name == 'li': content.append(f"- {text}")
                elif tag.name == 'blockquote': content.append(f"\n> {text}\n")
                elif tag.name in ['pre', 'code']: content.append(f"\n```\n{text}\n```\n")
                elif tag.name == 'a':
                    href = tag.get('href', '')
                    if href and href.startswith('http'):
                        content.append(f"[{text}]({href})")
                elif tag.name in ['strong', 'em'] and len(text) > 20:
                    content.append(f"**{text}**")
                elif tag.name in ['span', 'div', 'td', 'th'] and len(text) > 50:
                    content.append(f"\n{text}\n")
        
        # Extract tables
        tables = soup.find_all('table', limit=5)
        if tables:
            content.append("\n---\n## TABLES\n")
            for idx, table in enumerate(tables, 1):
                content.append(f"\n### Table {idx}\n")
                rows = table.find_all('tr')
                for row in rows[:10]:  # Limit rows
                    cells = [cell.get_text().strip() for cell in row.find_all(['td', 'th'])]
                    if cells:
                        content.append("| " + " | ".join(cells) + " |")
        
        # Extract images with alt text
        images = main_content.find_all('img', limit=10) if main_content else []
        if images:
            content.append("\n---\n## IMAGES\n")
            for img in images:
                alt = img.get('alt', 'No description')
                src = img.get('src', '')
                if alt or src:
                    content.append(f"- **{alt}** - `{src}`")
        
        # Extract important links
        links = main_content.find_all('a', limit=20) if main_content else []
        important_links = []
        for link in links:
            href = link.get('href', '')
            text = link.get_text().strip()
            if href and text and len(text) > 3:
                important_links.append(f"- [{text}]({urljoin(url, href)})")
        
        if important_links:
            content.append("\n---\n## IMPORTANT LINKS\n")
            content.extend(important_links[:15])
        
        # Extract structured data (JSON-LD)
        json_ld = soup.find('script', {'type': 'application/ld+json'})
        if json_ld:
            try:
                data = json.loads(json_ld.string)
                content.append("\n---\n## STRUCTURED DATA\n")
                content.append(f"```json\n{json.dumps(data, indent=2)[:1000]}\n```")
            except:
                pass

        markdown = "\n".join(content)
        return markdown[:18000]  # Increased limit to 18k chars for maximum data

    async def deep_scrape(self, url: str) -> str:
        """Deep Intelligence: Scrape main page + crawl related internal links for maximum context"""
        main_markdown = await self.scrape_to_markdown(url)
        if "Error:" in main_markdown: return main_markdown

        soup = BeautifulSoup(await self.fetch(url), 'html.parser')
        links = []
        domain = urlparse(url).netloc
        
        # Find 3-5 relevant internal links
        for a in soup.find_all('a', href=True):
            href = urljoin(url, a['href'])
            if urlparse(href).netloc == domain and href != url and len(links) < 4:
                if any(k in href.lower() for k in ['about', 'feature', 'product', 'guide', 'news', 'blog']):
                    links.append(href)

        # Scrape links in parallel
        tasks = [self.scrape_to_markdown(link) for link in links]
        sub_contents = await asyncio.gather(*tasks)

        # Assemble Master Intelligence Report
        deep_report = [
            f"# DEEP INTELLIGENCE REPORT: {url}\n",
            "## PRIMARY CONTENT",
            main_markdown,
            "\n---\n## KEY CONTEXT (CRAWLED DATA)",
        ]

        for i, sub_content in enumerate(sub_contents):
            title = sub_content.split('\n')[0].replace("# ", "")
            deep_report.append(f"### [Context {i+1}] {title}")
            # Take only the first 1000 chars of sub-pages
            snippet = sub_content.split('\n', 2)[-1][:1000]
            deep_report.append(f"{snippet}...\n")

        return "\n".join(deep_report)

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
async def scrape_markdown(url, deep=False): 
    if deep:
        return await jarvis_scraper.deep_scrape(url)
    return await jarvis_scraper.scrape_to_markdown(url)

async def quick_search(query): return await jarvis_scraper.search_quick(query)

