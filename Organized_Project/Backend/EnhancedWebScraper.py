"""
Enhanced Web Scraping - Advanced Data Extraction
================================================
Intelligent web scraping with AI-powered content extraction
"""

import requests
from bs4 import BeautifulSoup
import json
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urljoin
import re
from datetime import datetime

class EnhancedWebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_url(self, url: str, extract_type: str = "all") -> Dict[str, Any]:
        """
        Scrape a URL with intelligent content extraction
        
        Args:
            url: URL to scrape
            extract_type: Type of content to extract (all, text, links, images, tables, metadata)
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            result = {
                "status": "success",
                "url": url,
                "scraped_at": datetime.now().isoformat()
            }
            
            if extract_type in ["all", "text"]:
                result["text"] = self._extract_text(soup)
            
            if extract_type in ["all", "links"]:
                result["links"] = self._extract_links(soup, url)
            
            if extract_type in ["all", "images"]:
                result["images"] = self._extract_images(soup, url)
            
            if extract_type in ["all", "tables"]:
                result["tables"] = self._extract_tables(soup)
            
            if extract_type in ["all", "metadata"]:
                result["metadata"] = self._extract_metadata(soup)
            
            if extract_type in ["all", "articles"]:
                result["articles"] = self._extract_articles(soup)
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Failed to fetch URL: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Scraping failed: {str(e)}"
            }
    
    def _extract_text(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract main text content"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Extract headings
        headings = []
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                headings.append({
                    "level": i,
                    "text": heading.get_text().strip()
                })
        
        # Extract paragraphs
        paragraphs = [p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip()]
        
        return {
            "full_text": text[:5000],  # Limit to 5000 chars
            "word_count": len(text.split()),
            "char_count": len(text),
            "headings": headings[:20],
            "paragraphs": paragraphs[:10]
        }
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Extract all links"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            
            links.append({
                "text": link.get_text().strip(),
                "url": absolute_url,
                "is_external": urlparse(absolute_url).netloc != urlparse(base_url).netloc
            })
        
        return {
            "total": len(links),
            "internal": len([l for l in links if not l["is_external"]]),
            "external": len([l for l in links if l["is_external"]]),
            "links": links[:50]  # Limit to 50 links
        }
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Extract all images"""
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src:
                absolute_url = urljoin(base_url, src)
                images.append({
                    "url": absolute_url,
                    "alt": img.get('alt', ''),
                    "title": img.get('title', '')
                })
        
        return {
            "total": len(images),
            "images": images[:30]  # Limit to 30 images
        }
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract tables"""
        tables = []
        
        for table in soup.find_all('table')[:5]:  # Limit to 5 tables
            rows = []
            for tr in table.find_all('tr'):
                cells = [td.get_text().strip() for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            
            if rows:
                tables.append({
                    "rows": len(rows),
                    "columns": len(rows[0]) if rows else 0,
                    "data": rows[:20]  # Limit to 20 rows
                })
        
        return tables
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract page metadata"""
        metadata = {
            "title": soup.title.string if soup.title else None,
            "description": None,
            "keywords": None,
            "author": None,
            "og_data": {}
        }
        
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', '').lower()
            property_name = meta.get('property', '').lower()
            content = meta.get('content', '')
            
            if name == 'description':
                metadata["description"] = content
            elif name == 'keywords':
                metadata["keywords"] = content
            elif name == 'author':
                metadata["author"] = content
            elif property_name.startswith('og:'):
                metadata["og_data"][property_name] = content
        
        return metadata
    
    def _extract_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract article-like content"""
        articles = []
        
        # Look for article tags
        for article in soup.find_all('article')[:10]:
            title = article.find(['h1', 'h2', 'h3'])
            content = article.get_text().strip()
            
            articles.append({
                "title": title.get_text().strip() if title else "Untitled",
                "content": content[:500],  # First 500 chars
                "word_count": len(content.split())
            })
        
        return articles
    
    def scrape_multiple(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape multiple URLs"""
        results = []
        
        for url in urls[:10]:  # Limit to 10 URLs
            result = self.scrape_url(url)
            results.append(result)
        
        return results
    
    def extract_emails(self, url: str) -> Dict[str, Any]:
        """Extract email addresses from a page"""
        try:
            result = self.scrape_url(url, extract_type="text")
            
            if result["status"] == "success":
                text = result["text"]["full_text"]
                
                # Email regex
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = list(set(re.findall(email_pattern, text)))
                
                return {
                    "status": "success",
                    "count": len(emails),
                    "emails": emails
                }
            else:
                return result
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def extract_phone_numbers(self, url: str) -> Dict[str, Any]:
        """Extract phone numbers from a page"""
        try:
            result = self.scrape_url(url, extract_type="text")
            
            if result["status"] == "success":
                text = result["text"]["full_text"]
                
                # Phone number patterns
                patterns = [
                    r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US format
                    r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b',  # (123) 456-7890
                    r'\b\+\d{1,3}\s*\d{1,14}\b'  # International
                ]
                
                phones = []
                for pattern in patterns:
                    phones.extend(re.findall(pattern, text))
                
                phones = list(set(phones))
                
                return {
                    "status": "success",
                    "count": len(phones),
                    "phone_numbers": phones
                }
            else:
                return result
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_page_summary(self, url: str) -> Dict[str, Any]:
        """Get a comprehensive summary of a page"""
        try:
            result = self.scrape_url(url, extract_type="all")
            
            if result["status"] == "success":
                summary = {
                    "status": "success",
                    "url": url,
                    "title": result.get("metadata", {}).get("title", "Unknown"),
                    "description": result.get("metadata", {}).get("description", ""),
                    "word_count": result.get("text", {}).get("word_count", 0),
                    "link_count": result.get("links", {}).get("total", 0),
                    "image_count": result.get("images", {}).get("total", 0),
                    "table_count": len(result.get("tables", [])),
                    "headings": result.get("text", {}).get("headings", [])[:5],
                    "preview": result.get("text", {}).get("paragraphs", [])[:2]
                }
                
                return summary
            else:
                return result
                
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Global instance
enhanced_scraper = EnhancedWebScraper()

if __name__ == "__main__":
    print("Enhanced Web Scraper initialized!")
