"""
Pro Web Scraper - Advanced Web Content Extraction
==================================================
Extract products, articles, prices, and structured data
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from datetime import datetime
import re
import json
from urllib.parse import urljoin, urlparse

class ProWebScraper:
    """Professional web scraper with specialized extractors"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.timeout = 15
    
    def scrape_smart(self, url: str, extract_type: str = "auto") -> Dict[str, Any]:
        """
        Smart scrape - auto-detect content type
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            domain = urlparse(url).netloc.lower()
            
            # Auto-detect based on URL/domain
            if extract_type == "auto":
                if any(shop in domain for shop in ['amazon', 'flipkart', 'ebay', 'walmart', 'myntra']):
                    extract_type = "product"
                elif any(news in domain for news in ['news', 'bbc', 'cnn', 'nytimes', 'guardian', 'reuters']):
                    extract_type = "article"
                elif 'wikipedia' in domain:
                    extract_type = "wiki"
                elif any(social in domain for social in ['twitter', 'x.com', 'reddit', 'linkedin']):
                    extract_type = "social"
                else:
                    extract_type = "general"
            
            # Route to specialized extractor
            if extract_type == "product":
                return self._extract_product(soup, url)
            elif extract_type == "article":
                return self._extract_article(soup, url)
            elif extract_type == "wiki":
                return self._extract_wiki(soup, url)
            else:
                return self._extract_general(soup, url)
                
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Request timed out"}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Scraping failed: {str(e)}"}
    
    def _extract_product(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract product information"""
        result = {
            "status": "success",
            "type": "product",
            "url": url,
            "scraped_at": datetime.now().isoformat()
        }
        
        # Try multiple selectors for different sites
        
        # Title
        title_selectors = [
            '#productTitle', '.product-title', 'h1.title', 
            '[data-testid="product-title"]', '.product-name', 'h1'
        ]
        for sel in title_selectors:
            elem = soup.select_one(sel)
            if elem:
                result["title"] = elem.get_text(strip=True)[:200]
                break
        
        # Price
        price_selectors = [
            '.a-price-whole', '.price', '#priceblock_ourprice', 
            '.product-price', '[data-testid="price"]', '.current-price',
            'span[class*="price"]', 'div[class*="price"]'
        ]
        for sel in price_selectors:
            elem = soup.select_one(sel)
            if elem:
                price_text = elem.get_text(strip=True)
                # Extract price with currency
                price_match = re.search(r'[\$₹€£]\s?[\d,]+\.?\d*', price_text)
                if price_match:
                    result["price"] = price_match.group(0)
                    break
                elif re.search(r'[\d,]+\.?\d*', price_text):
                    result["price"] = price_text
                    break
        
        # Rating
        rating_selectors = [
            '.a-icon-star', '[data-testid="rating"]', '.rating',
            '.stars', '.review-rating'
        ]
        for sel in rating_selectors:
            elem = soup.select_one(sel)
            if elem:
                rating_text = elem.get_text(strip=True)
                rating_match = re.search(r'(\d\.?\d?)\s*(?:/5|out of|stars)?', rating_text)
                if rating_match:
                    result["rating"] = rating_match.group(1)
                    break
        
        # Image
        img_selectors = ['#landingImage', '.product-image img', 'img.main-image', 'img[data-old-hires]']
        for sel in img_selectors:
            elem = soup.select_one(sel)
            if elem and elem.get('src'):
                result["image"] = elem.get('src')
                break
        
        # Description
        desc_selectors = ['#productDescription', '.product-description', '#feature-bullets']
        for sel in desc_selectors:
            elem = soup.select_one(sel)
            if elem:
                result["description"] = elem.get_text(strip=True)[:500]
                break
        
        return result
    
    def _extract_article(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract news/article content"""
        result = {
            "status": "success",
            "type": "article",
            "url": url,
            "scraped_at": datetime.now().isoformat()
        }
        
        # Remove unwanted elements
        for elem in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
            elem.decompose()
        
        # Title
        result["title"] = soup.title.string if soup.title else ""
        h1 = soup.find('h1')
        if h1:
            result["title"] = h1.get_text(strip=True)
        
        # Author
        author_selectors = ['[rel="author"]', '.author', '.byline', '[class*="author"]']
        for sel in author_selectors:
            elem = soup.select_one(sel)
            if elem:
                result["author"] = elem.get_text(strip=True)
                break
        
        # Date
        date_selectors = ['time', '[datetime]', '.date', '.published', '[class*="date"]']
        for sel in date_selectors:
            elem = soup.select_one(sel)
            if elem:
                result["date"] = elem.get('datetime') or elem.get_text(strip=True)
                break
        
        # Main content
        article_selectors = ['article', 'main', '.article-body', '.post-content', '.entry-content']
        for sel in article_selectors:
            elem = soup.select_one(sel)
            if elem:
                paragraphs = elem.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs[:15]])
                result["content"] = content[:2000]
                result["word_count"] = len(content.split())
                break
        
        if "content" not in result:
            # Fallback: get all paragraphs
            paragraphs = soup.find_all('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs[:10]])
            result["content"] = content[:1500]
            result["word_count"] = len(content.split())
        
        # Summary (first paragraph)
        first_p = soup.find('p')
        if first_p:
            result["summary"] = first_p.get_text(strip=True)[:300]
        
        return result
    
    def _extract_wiki(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract Wikipedia content"""
        result = {
            "status": "success",
            "type": "wikipedia",
            "url": url,
            "scraped_at": datetime.now().isoformat()
        }
        
        # Title
        title = soup.select_one('#firstHeading')
        result["title"] = title.get_text(strip=True) if title else ""
        
        # Summary (first paragraph)
        content_div = soup.select_one('#mw-content-text')
        if content_div:
            paragraphs = content_div.find_all('p', recursive=True)
            for p in paragraphs[:5]:
                text = p.get_text(strip=True)
                if len(text) > 50:  # Skip stub paragraphs
                    result["summary"] = text[:500]
                    break
            
            # Full content
            all_text = ' '.join([p.get_text(strip=True) for p in paragraphs[:20]])
            result["content"] = all_text[:3000]
        
        # Infobox data
        infobox = soup.select_one('.infobox')
        if infobox:
            info = {}
            rows = infobox.find_all('tr')
            for row in rows[:10]:
                th = row.find('th')
                td = row.find('td')
                if th and td:
                    key = th.get_text(strip=True)
                    value = td.get_text(strip=True)
                    if key and value:
                        info[key] = value[:100]
            result["infobox"] = info
        
        return result
    
    def _extract_general(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """General purpose extraction"""
        # Remove unwanted elements
        for elem in soup(['script', 'style', 'nav', 'header', 'footer', 'noscript']):
            elem.decompose()
        
        result = {
            "status": "success",
            "type": "general",
            "url": url,
            "scraped_at": datetime.now().isoformat()
        }
        
        # Title
        result["title"] = soup.title.string if soup.title else ""
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            result["description"] = meta_desc.get('content', '')[:300]
        
        # Main content
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        if main_content:
            paragraphs = main_content.find_all('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs[:15]])
            result["content"] = content[:2000]
        
        # Links count
        links = soup.find_all('a', href=True)
        result["links_count"] = len(links)
        
        # Images count
        images = soup.find_all('img')
        result["images_count"] = len(images)
        
        # Headings
        headings = []
        for h in soup.find_all(['h1', 'h2', 'h3'])[:10]:
            headings.append(h.get_text(strip=True)[:100])
        result["headings"] = headings
        
        return result
    
    def search_google(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Search Google and return results"""
        try:
            url = f"https://www.google.com/search?q={query}&num={num_results}"
            response = self.session.get(url, timeout=self.timeout)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            for div in soup.select('div.g')[:num_results]:
                link = div.find('a')
                title = div.find('h3')
                snippet = div.find('div', class_='VwiC3b')
                
                if link and title:
                    results.append({
                        "title": title.get_text(strip=True),
                        "url": link.get('href', ''),
                        "snippet": snippet.get_text(strip=True) if snippet else ""
                    })
            
            return {
                "status": "success",
                "query": query,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def batch_scrape(self, urls: List[str]) -> Dict[str, Any]:
        """Scrape multiple URLs"""
        results = []
        for url in urls[:5]:  # Limit to 5 URLs
            result = self.scrape_smart(url)
            results.append({"url": url, "data": result})
        
        return {
            "status": "success",
            "count": len(results),
            "results": results
        }


# Global instance
pro_scraper = ProWebScraper()


if __name__ == "__main__":
    # Test
    result = pro_scraper.scrape_smart("https://en.wikipedia.org/wiki/Python_(programming_language)")
    print(json.dumps(result, indent=2))
