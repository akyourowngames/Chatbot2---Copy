"""
🌐 DYNAMIC BROWSER — The Phantom Navigator 👻
Advanced browser automation for JavaScript-heavy sites using Playwright and Selenium.
"""

import asyncio
import logging
import random
import time
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import json
import base64
from PIL import Image
import io

@dataclass
class BrowserConfig:
    """Configuration for browser automation"""
    browser_type: str = "chromium"  # chromium, firefox, webkit
    headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: str = None
    proxy: str = None
    timeout: int = 30
    wait_for_selector: str = None
    wait_for_load_state: str = "networkidle"  # load, domcontentloaded, networkidle
    screenshot: bool = False
    scroll_to_bottom: bool = False
    random_delay: bool = True
    delay_range: tuple = (1, 3)
    max_scroll_attempts: int = 5
    block_resources: List[str] = None  # ['image', 'stylesheet', 'font', 'media']
    javascript_enabled: bool = True
    cookies: List[Dict] = None
    extra_headers: Dict[str, str] = None

class DynamicBrowser:
    """
    🌐 Advanced browser automation with Playwright and Selenium support
    """
    
    def __init__(self, config: BrowserConfig = None):
        self.config = config or BrowserConfig()
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.selenium_driver = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_playwright()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def start_playwright(self):
        """Initialize Playwright browser"""
        try:
            self.playwright = await async_playwright().start()
            
            # Choose browser type
            if self.config.browser_type == "chromium":
                browser_launcher = self.playwright.chromium
            elif self.config.browser_type == "firefox":
                browser_launcher = self.playwright.firefox
            elif self.config.browser_type == "webkit":
                browser_launcher = self.playwright.webkit
            else:
                browser_launcher = self.playwright.chromium
            
            # Launch browser
            self.browser = await browser_launcher.launch(
                headless=self.config.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create context with stealth settings
            context_options = {
                'viewport': {
                    'width': self.config.viewport_width,
                    'height': self.config.viewport_height
                },
                'user_agent': self.config.user_agent or self._get_random_user_agent(),
                'java_script_enabled': self.config.javascript_enabled,
                'ignore_https_errors': True
            }
            
            if self.config.proxy:
                context_options['proxy'] = {'server': self.config.proxy}
            
            if self.config.extra_headers:
                context_options['extra_http_headers'] = self.config.extra_headers
            
            self.context = await self.browser.new_context(**context_options)
            
            # Add stealth scripts
            await self._add_stealth_scripts()
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set cookies if provided
            if self.config.cookies:
                await self.context.add_cookies(self.config.cookies)
            
            logging.info(f"🌐 Playwright browser started: {self.config.browser_type}")
            
        except Exception as e:
            logging.error(f"❌ Failed to start Playwright browser: {e}")
            raise
    
    def _get_random_user_agent(self) -> str:
        """Generate random user agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        return random.choice(user_agents)
    
    async def _add_stealth_scripts(self):
        """Add stealth scripts to avoid detection"""
        stealth_script = """
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // Mock permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """
        
        await self.context.add_init_script(stealth_script)
    
    async def navigate(self, url: str, wait_for: str = None) -> bool:
        """
        🚀 Navigate to URL with advanced waiting strategies
        """
        try:
            # Block resources if configured
            if self.config.block_resources:
                await self.page.route("**/*", self._block_resources)
            
            # Navigate to URL
            await self.page.goto(url, timeout=self.config.timeout * 1000)
            
            # Wait for specific conditions
            if wait_for:
                await self.page.wait_for_selector(wait_for, timeout=self.config.timeout * 1000)
            else:
                await self.page.wait_for_load_state(self.config.wait_for_load_state)
            
            # Random delay
            if self.config.random_delay:
                await asyncio.sleep(random.uniform(*self.config.delay_range))
            
            logging.info(f"🌐 Navigated to: {url}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to navigate to {url}: {e}")
            return False
    
    async def _block_resources(self, route):
        """Block specified resources"""
        if route.request.resource_type in self.config.block_resources:
            await route.abort()
        else:
            await route.continue_()
    
    async def scroll_to_bottom(self, max_attempts: int = None) -> bool:
        """
        📜 Scroll to bottom of page to load dynamic content
        """
        try:
            attempts = max_attempts or self.config.max_scroll_attempts
            
            for i in range(attempts):
                # Scroll down
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                
                # Wait for new content to load
                await asyncio.sleep(2)
                
                # Check if we've reached the bottom
                is_at_bottom = await self.page.evaluate("""
                    () => {
                        return window.innerHeight + window.scrollY >= document.body.scrollHeight - 100;
                    }
                """)
                
                if is_at_bottom:
                    break
            
            logging.info(f"📜 Scrolled to bottom after {attempts} attempts")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to scroll to bottom: {e}")
            return False
    
    async def wait_for_element(self, selector: str, timeout: int = None) -> bool:
        """Wait for element to appear"""
        try:
            timeout_ms = (timeout or self.config.timeout) * 1000
            await self.page.wait_for_selector(selector, timeout=timeout_ms)
            return True
        except TimeoutException:
            logging.warning(f"⏰ Timeout waiting for element: {selector}")
            return False
    
    async def click_element(self, selector: str) -> bool:
        """Click on element"""
        try:
            await self.page.click(selector)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            return True
        except Exception as e:
            logging.error(f"❌ Failed to click element {selector}: {e}")
            return False
    
    async def fill_input(self, selector: str, text: str) -> bool:
        """Fill input field"""
        try:
            await self.page.fill(selector, text)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            return True
        except Exception as e:
            logging.error(f"❌ Failed to fill input {selector}: {e}")
            return False
    
    async def get_content(self) -> str:
        """Get page content"""
        try:
            content = await self.page.content()
            return content
        except Exception as e:
            logging.error(f"❌ Failed to get page content: {e}")
            return ""
    
    async def get_text(self) -> str:
        """Get page text content"""
        try:
            text = await self.page.inner_text('body')
            return text
        except Exception as e:
            logging.error(f"❌ Failed to get page text: {e}")
            return ""
    
    async def take_screenshot(self, path: str = None) -> str:
        """Take screenshot"""
        try:
            if not path:
                timestamp = int(time.time())
                path = f"screenshot_{timestamp}.png"
            
            await self.page.screenshot(path=path, full_page=True)
            logging.info(f"📸 Screenshot saved: {path}")
            return path
        except Exception as e:
            logging.error(f"❌ Failed to take screenshot: {e}")
            return ""
    
    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript"""
        try:
            result = await self.page.evaluate(script)
            return result
        except Exception as e:
            logging.error(f"❌ Failed to execute script: {e}")
            return None
    
    async def get_network_requests(self) -> List[Dict]:
        """Get network requests made by the page"""
        try:
            requests = await self.page.evaluate("""
                () => {
                    return performance.getEntriesByType('resource').map(entry => ({
                        name: entry.name,
                        duration: entry.duration,
                        size: entry.transferSize,
                        type: entry.initiatorType
                    }));
                }
            """)
            return requests
        except Exception as e:
            logging.error(f"❌ Failed to get network requests: {e}")
            return []
    
    async def close(self):
        """Close browser and cleanup"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            logging.info("🌐 Browser closed successfully")
            
        except Exception as e:
            logging.error(f"❌ Error closing browser: {e}")

class SeleniumBrowser:
    """
    🔧 Selenium-based browser automation (fallback option)
    """
    
    def __init__(self, config: BrowserConfig = None):
        self.config = config or BrowserConfig()
        self.driver = None
    
    def start(self):
        """Start Selenium browser"""
        try:
            if self.config.browser_type == "chrome":
                options = ChromeOptions()
                if self.config.headless:
                    options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-blink-features=AutomationControlled")
                
                if self.config.user_agent:
                    options.add_argument(f"--user-agent={self.config.user_agent}")
                
                if self.config.proxy:
                    options.add_argument(f"--proxy-server={self.config.proxy}")
                
                self.driver = webdriver.Chrome(options=options)
                
            elif self.config.browser_type == "firefox":
                options = FirefoxOptions()
                if self.config.headless:
                    options.add_argument("--headless")
                
                if self.config.user_agent:
                    options.set_preference("general.useragent.override", self.config.user_agent)
                
                self.driver = webdriver.Firefox(options=options)
            
            self.driver.set_window_size(self.config.viewport_width, self.config.viewport_height)
            
            logging.info(f"🔧 Selenium browser started: {self.config.browser_type}")
            
        except Exception as e:
            logging.error(f"❌ Failed to start Selenium browser: {e}")
            raise
    
    def navigate(self, url: str) -> bool:
        """Navigate to URL"""
        try:
            self.driver.get(url)
            
            # Wait for page load
            WebDriverWait(self.driver, self.config.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            if self.config.random_delay:
                time.sleep(random.uniform(*self.config.delay_range))
            
            logging.info(f"🔧 Navigated to: {url}")
            return True
            
        except TimeoutException:
            logging.error(f"❌ Timeout navigating to {url}")
            return False
        except Exception as e:
            logging.error(f"❌ Failed to navigate to {url}: {e}")
            return False
    
    def scroll_to_bottom(self) -> bool:
        """Scroll to bottom"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            for i in range(self.config.max_scroll_attempts):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to scroll to bottom: {e}")
            return False
    
    def get_content(self) -> str:
        """Get page content"""
        try:
            return self.driver.page_source
        except Exception as e:
            logging.error(f"❌ Failed to get page content: {e}")
            return ""
    
    def get_text(self) -> str:
        """Get page text"""
        try:
            return self.driver.find_element(By.TAG_NAME, "body").text
        except Exception as e:
            logging.error(f"❌ Failed to get page text: {e}")
            return ""
    
    def take_screenshot(self, path: str = None) -> str:
        """Take screenshot"""
        try:
            if not path:
                timestamp = int(time.time())
                path = f"selenium_screenshot_{timestamp}.png"
            
            self.driver.save_screenshot(path)
            logging.info(f"📸 Screenshot saved: {path}")
            return path
        except Exception as e:
            logging.error(f"❌ Failed to take screenshot: {e}")
            return ""
    
    def close(self):
        """Close browser"""
        try:
            if self.driver:
                self.driver.quit()
            logging.info("🔧 Selenium browser closed")
        except Exception as e:
            logging.error(f"❌ Error closing Selenium browser: {e}")

# Convenience functions
async def scrape_dynamic_page(url: str, config: BrowserConfig = None) -> str:
    """Quick function to scrape dynamic page"""
    config = config or BrowserConfig()
    
    async with DynamicBrowser(config) as browser:
        success = await browser.navigate(url)
        if success:
            if config.scroll_to_bottom:
                await browser.scroll_to_bottom()
            return await browser.get_content()
        return ""

def scrape_with_selenium(url: str, config: BrowserConfig = None) -> str:
    """Quick function to scrape with Selenium"""
    config = config or BrowserConfig()
    browser = SeleniumBrowser(config)
    
    try:
        browser.start()
        success = browser.navigate(url)
        if success:
            if config.scroll_to_bottom:
                browser.scroll_to_bottom()
            return browser.get_content()
        return ""
    finally:
        browser.close()

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    async def test_playwright():
        """Test Playwright browser"""
        config = BrowserConfig(
            browser_type="chromium",
            headless=True,
            scroll_to_bottom=True,
            screenshot=True,
            block_resources=['image', 'font']
        )
        
        async with DynamicBrowser(config) as browser:
            success = await browser.navigate("https://httpbin.org/html")
            if success:
                content = await browser.get_content()
                print(f"🌐 Playwright content length: {len(content)}")
                
                screenshot_path = await browser.take_screenshot()
                print(f"📸 Screenshot: {screenshot_path}")
    
    def test_selenium():
        """Test Selenium browser"""
        config = BrowserConfig(
            browser_type="chrome",
            headless=True,
            scroll_to_bottom=True
        )
        
        browser = SeleniumBrowser(config)
        try:
            browser.start()
            success = browser.navigate("https://httpbin.org/html")
            if success:
                content = browser.get_content()
                print(f"🔧 Selenium content length: {len(content)}")
        finally:
            browser.close()
    
    # Run tests
    print("🌐 Testing Playwright...")
    asyncio.run(test_playwright())
    
    print("\n🔧 Testing Selenium...")
    test_selenium()
    
    print("\n🌐 Dynamic Browser initialized successfully!")
