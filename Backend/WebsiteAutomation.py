"""
Website Automation for JARVIS - Advanced Web Scraping & Automation
===================================================================
Automate website interactions, scraping, form filling, and monitoring
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import requests
import time
import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebsiteAutomation:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.headless = False
        logger.info("[Website] Automation module loaded")
    
    def start_browser(self, headless: bool = False, user_data_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Start Chrome browser with automation
        
        Args:
            headless: Run browser in headless mode (no UI)
            user_data_dir: Path to Chrome user data directory (for persistent sessions)
        """
        try:
            if self.driver:
                return {"status": "error", "message": "Browser already running"}
            
            logger.info(f"[Website] Starting browser (headless={headless})...")
            
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--disable-gpu')
            
            # Common options
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User data directory for persistent sessions
            if user_data_dir:
                chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
            
            # Start browser
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.maximize_window()
            self.wait = WebDriverWait(self.driver, 10)
            self.headless = headless
            
            logger.info("[Website] ✅ Browser started successfully")
            
            return {
                "status": "success",
                "message": "Browser started",
                "headless": headless
            }
        
        except Exception as e:
            logger.error(f"[Website] ❌ Start browser error: {e}")
            return {"status": "error", "message": str(e)}
    
    def close_browser(self) -> Dict[str, Any]:
        """Close the browser"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                logger.info("[Website] Browser closed")
                return {"status": "success", "message": "Browser closed"}
            return {"status": "error", "message": "Browser not running"}
        except Exception as e:
            logger.error(f"[Website] Close error: {e}")
            return {"status": "error", "message": str(e)}
    
    def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL"""
        try:
            if not self.driver:
                return {"status": "error", "message": "Browser not started"}
            
            if not url.startswith('http'):
                url = 'https://' + url
            
            logger.info(f"[Website] Navigating to {url}...")
            self.driver.get(url)
            time.sleep(2)  # Wait for page load
            
            return {
                "status": "success",
                "message": f"Navigated to {url}",
                "url": self.driver.current_url,
                "title": self.driver.title
            }
        
        except Exception as e:
            logger.error(f"[Website] Navigate error: {e}")
            return {"status": "error", "message": str(e)}
    
    def click_element(self, selector: str, by: str = "css") -> Dict[str, Any]:
        """
        Click an element on the page
        
        Args:
            selector: Element selector (CSS, XPath, ID, etc.)
            by: Selector type ('css', 'xpath', 'id', 'class', 'name')
        """
        try:
            if not self.driver:
                return {"status": "error", "message": "Browser not started"}
            
            by_map = {
                "css": By.CSS_SELECTOR,
                "xpath": By.XPATH,
                "id": By.ID,
                "class": By.CLASS_NAME,
                "name": By.NAME,
                "tag": By.TAG_NAME
            }
            
            by_type = by_map.get(by.lower(), By.CSS_SELECTOR)
            
            logger.info(f"[Website] Clicking element: {selector}")
            element = self.wait.until(EC.element_to_be_clickable((by_type, selector)))
            element.click()
            
            return {
                "status": "success",
                "message": f"Clicked element: {selector}"
            }
        
        except Exception as e:
            logger.error(f"[Website] Click error: {e}")
            return {"status": "error", "message": str(e)}
    
    def type_text(self, selector: str, text: str, by: str = "css", clear_first: bool = True) -> Dict[str, Any]:
        """
        Type text into an input field
        
        Args:
            selector: Element selector
            text: Text to type
            by: Selector type
            clear_first: Clear field before typing
        """
        try:
            if not self.driver:
                return {"status": "error", "message": "Browser not started"}
            
            by_map = {
                "css": By.CSS_SELECTOR,
                "xpath": By.XPATH,
                "id": By.ID,
                "class": By.CLASS_NAME,
                "name": By.NAME
            }
            
            by_type = by_map.get(by.lower(), By.CSS_SELECTOR)
            
            logger.info(f"[Website] Typing into element: {selector}")
            element = self.wait.until(EC.presence_of_element_located((by_type, selector)))
            
            if clear_first:
                element.clear()
            
            element.send_keys(text)
            
            return {
                "status": "success",
                "message": f"Typed text into: {selector}"
            }
        
        except Exception as e:
            logger.error(f"[Website] Type error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_text(self, selector: str, by: str = "css") -> Dict[str, Any]:
        """Get text from an element"""
        try:
            if not self.driver:
                return {"status": "error", "message": "Browser not started"}
            
            by_map = {
                "css": By.CSS_SELECTOR,
                "xpath": By.XPATH,
                "id": By.ID,
                "class": By.CLASS_NAME
            }
            
            by_type = by_map.get(by.lower(), By.CSS_SELECTOR)
            
            element = self.wait.until(EC.presence_of_element_located((by_type, selector)))
            text = element.text
            
            return {
                "status": "success",
                "text": text,
                "selector": selector
            }
        
        except Exception as e:
            logger.error(f"[Website] Get text error: {e}")
            return {"status": "error", "message": str(e)}
    
    def screenshot(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Take a screenshot of the current page"""
        try:
            if not self.driver:
                return {"status": "error", "message": "Browser not started"}
            
            if not filename:
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            screenshots_dir = os.path.join("Data", "Screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            
            filepath = os.path.join(screenshots_dir, filename)
            self.driver.save_screenshot(filepath)
            
            logger.info(f"[Website] Screenshot saved: {filepath}")
            
            return {
                "status": "success",
                "message": "Screenshot saved",
                "filepath": filepath
            }
        
        except Exception as e:
            logger.error(f"[Website] Screenshot error: {e}")
            return {"status": "error", "message": str(e)}
    
    def scrape_page(self, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape content from current page or specified URL
        
        Args:
            url: URL to scrape (if None, scrapes current page)
        """
        try:
            if url:
                nav_result = self.navigate(url)
                if nav_result.get("status") != "success":
                    return nav_result
            
            if not self.driver:
                return {"status": "error", "message": "Browser not started"}
            
            logger.info("[Website] Scraping page...")
            
            # Get page source
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract data
            data = {
                "url": self.driver.current_url,
                "title": self.driver.title,
                "headings": {
                    "h1": [h.get_text(strip=True) for h in soup.find_all('h1')],
                    "h2": [h.get_text(strip=True) for h in soup.find_all('h2')],
                    "h3": [h.get_text(strip=True) for h in soup.find_all('h3')]
                },
                "paragraphs": [p.get_text(strip=True) for p in soup.find_all('p')][:10],
                "links": [{"text": a.get_text(strip=True), "href": a.get('href')} 
                         for a in soup.find_all('a', href=True)][:20],
                "images": [{"alt": img.get('alt', ''), "src": img.get('src')} 
                          for img in soup.find_all('img')][:10],
                "meta": {
                    "description": soup.find('meta', attrs={'name': 'description'}),
                    "keywords": soup.find('meta', attrs={'name': 'keywords'})
                }
            }
            
            # Clean meta data
            if data['meta']['description']:
                data['meta']['description'] = data['meta']['description'].get('content', '')
            if data['meta']['keywords']:
                data['meta']['keywords'] = data['meta']['keywords'].get('content', '')
            
            logger.info(f"[Website] ✅ Scraped {len(data['paragraphs'])} paragraphs, {len(data['links'])} links")
            
            return {
                "status": "success",
                "data": data
            }
        
        except Exception as e:
            logger.error(f"[Website] Scrape error: {e}")
            return {"status": "error", "message": str(e)}
    
    def fill_form(self, form_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Fill a form with data
        
        Args:
            form_data: Dictionary of {selector: value} pairs
        """
        try:
            if not self.driver:
                return {"status": "error", "message": "Browser not started"}
            
            logger.info(f"[Website] Filling form with {len(form_data)} fields...")
            
            filled = 0
            for selector, value in form_data.items():
                try:
                    result = self.type_text(selector, value)
                    if result.get("status") == "success":
                        filled += 1
                except Exception as e:
                    logger.warning(f"[Website] Could not fill {selector}: {e}")
            
            return {
                "status": "success",
                "message": f"Filled {filled}/{len(form_data)} fields",
                "filled_count": filled,
                "total_count": len(form_data)
            }
        
        except Exception as e:
            logger.error(f"[Website] Fill form error: {e}")
            return {"status": "error", "message": str(e)}
    
    def execute_script(self, script: str) -> Dict[str, Any]:
        """Execute JavaScript on the page"""
        try:
            if not self.driver:
                return {"status": "error", "message": "Browser not started"}
            
            logger.info("[Website] Executing JavaScript...")
            result = self.driver.execute_script(script)
            
            return {
                "status": "success",
                "result": result
            }
        
        except Exception as e:
            logger.error(f"[Website] Execute script error: {e}")
            return {"status": "error", "message": str(e)}
    
    def monitor_element(self, selector: str, interval: int = 5, duration: int = 60) -> Dict[str, Any]:
        """
        Monitor an element for changes
        
        Args:
            selector: Element selector
            interval: Check interval in seconds
            duration: Total monitoring duration in seconds
        """
        try:
            if not self.driver:
                return {"status": "error", "message": "Browser not started"}
            
            logger.info(f"[Website] Monitoring element: {selector} for {duration}s...")
            
            changes = []
            start_time = time.time()
            last_text = None
            
            while time.time() - start_time < duration:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    current_text = element.text
                    
                    if last_text is not None and current_text != last_text:
                        changes.append({
                            "timestamp": datetime.now().isoformat(),
                            "old_value": last_text,
                            "new_value": current_text
                        })
                        logger.info(f"[Website] Change detected: {last_text} -> {current_text}")
                    
                    last_text = current_text
                except Exception as e:
                    logger.warning(f"[Website] Monitor check failed: {e}")
                
                time.sleep(interval)
            
            return {
                "status": "success",
                "message": f"Monitoring complete. {len(changes)} changes detected.",
                "changes": changes,
                "duration": duration
            }
        
        except Exception as e:
            logger.error(f"[Website] Monitor error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get website automation status"""
        return {
            "status": "ready" if self.driver else "browser_not_started",
            "module": "Website Automation",
            "browser_running": self.driver is not None,
            "headless": self.headless,
            "current_url": self.driver.current_url if self.driver else None,
            "features": [
                "Browser automation (Selenium)",
                "Web scraping (BeautifulSoup)",
                "Form filling",
                "Element clicking",
                "Screenshot capture",
                "JavaScript execution",
                "Element monitoring",
                "Page navigation"
            ]
        }

# Global instance
website_automation = WebsiteAutomation()

if __name__ == "__main__":
    print("Website Automation Test")
    print(website_automation.get_status())
