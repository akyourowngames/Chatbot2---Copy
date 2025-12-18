"""
Chrome Automation - Beast Mode
==============================
Advanced Chrome control with focus on stealth, tab management, and smart interaction.
"""

import time
import os
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from typing import List, Dict, Optional, Union

class ChromeAutomation:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.last_closed_urls = []

    def start_chrome(self, headless=False, incognito=False):
        """Start Chrome with Beast Mode configurations"""
        try:
            options = Options()
            if headless:
                options.add_argument('--headless=new')
            if incognito:
                options.add_argument('--incognito')
            
            options.add_argument('--start-maximized')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            
            # Stealth: Avoid Bot Detection
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Basic User Agent Spoofing for stealth
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 15)
            
            # Remove navigator.webdriver property
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
            
            return True
        except Exception as e:
            print(f"[Chrome] Launch Error: {e}")
            return False

    def ensure_started(self):
        if not self.driver:
            self.start_chrome()

    def open_url(self, url):
        self.ensure_started()
        if not url.startswith('http'):
            url = 'https://' + url
        self.driver.get(url)
        return f"Opened: {url}"

    # ==================== TAB MANAGEMENT (BEAST) ====================

    def new_tab(self, url=None):
        self.ensure_started()
        self.driver.execute_script("window.open('about:blank', '_blank');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        if url:
            self.open_url(url)
        return "Opened new tab"

    def close_tab(self):
        if not self.driver or len(self.driver.window_handles) == 0:
            return "No tabs to close"
        
        self.last_closed_urls.append(self.driver.current_url)
        self.driver.close()
        
        if len(self.driver.window_handles) > 0:
            self.driver.switch_to.window(self.driver.window_handles[-1])
        else:
            self.driver = None # All tabs closed
        return "Closed tab"

    def revert_closed_tab(self):
        """Reopen last closed tab"""
        if self.last_closed_urls:
            url = self.last_closed_urls.pop()
            return self.new_tab(url)
        return "No tabs in history"

    def close_other_tabs(self):
        """Close all tabs except the current one"""
        current = self.driver.current_window_handle
        for handle in self.driver.window_handles:
            if handle != current:
                self.driver.switch_to.window(handle)
                self.driver.close()
        self.driver.switch_to.window(current)
        return "Closed all other tabs"

    def switch_to_tab(self, query: str):
        """Switch tab by title or index"""
        self.ensure_started()
        if query.isdigit():
            idx = int(query)
            if idx < len(self.driver.window_handles):
                self.driver.switch_to.window(self.driver.window_handles[idx])
                return f"Switched to tab {idx}"
        
        # Search by Title
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if query.lower() in self.driver.title.lower():
                return f"Switched to tab: {self.driver.title}"
        
        return f"Tab '{query}' not found"

    # ==================== SMART INTERACTION ====================

    def search_google(self, query):
        """Search on Google"""
        self.open_url(f'https://www.google.com/search?q={query.replace(" ", "+")}')
        return f"Searching Google for: {query}"

    def search_youtube(self, query):
        """Search on YouTube"""
        self.open_url(f'https://www.youtube.com/results?search_query={query.replace(" ", "+")}')
        return f"Searching YouTube for: {query}"

    def click_text(self, text: str):
        """Click an element that contains specific text (Smart & Case-Insensitive)"""
        try:
            # Using XPath with translate for case-insensitive match
            xpath = (
                f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}') "
                f"or contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"
            )
            elements = self.driver.find_elements(By.XPATH, xpath)
            for el in elements:
                if el.is_displayed():
                    webdriver.ActionChains(self.driver).move_to_element(el).click().perform()
                    return f"Clicked '{text}'"
            return f"Found '{text}' but it was not clickable/visible"
        except Exception as e:
            return f"Click error: {e}"

    def type_and_enter(self, text: str):
        """Type into focused element and press enter"""
        action = webdriver.ActionChains(self.driver)
        action.send_keys(text)
        action.send_keys(Keys.RETURN)
        action.perform()
        return f"Typed and entered: {text}"

    def extract_page_text(self):
        """Get all visible text from the page (for LLM context)"""
        if not self.driver: return "No browser active"
        return self.driver.find_element(By.TAG_NAME, "body").text[:5000] # Limit to 5k chars

    def screenshot(self, name="chrome_capture", full_page=False):
        """Advanced Browser Screenshot"""
        if not self.driver: return False
        try:
            filename = f"{name}_{int(time.time())}.png"
            if full_page:
                # Set window size to match body height for full-page
                height = self.driver.execute_script("return document.body.scrollHeight")
                width = self.driver.execute_script("return document.body.scrollWidth")
                self.driver.set_window_size(width, height)
                time.sleep(1)
            
            self.driver.save_screenshot(filename)
            
            # Reset window size if it was a full-page capture
            if full_page:
                self.driver.maximize_window()
            
            from Backend.ExecutionState import set_state
            set_state("last_screenshot", filename)
            return filename
        except Exception as e:
            print(f"[Chrome] Screenshot Error: {e}")
            return False

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            return "Browser closed"
        return "No browser running"

# Global instance
chrome_bot = ChromeAutomation()

# Quick wrappers for external use
def chrome_open(url): return chrome_bot.open_url(url)
def chrome_close_tab(): return chrome_bot.close_tab()
def chrome_new_tab(url=None): return chrome_bot.new_tab(url)
def chrome_screenshot(name=None, full_page=False): return chrome_bot.screenshot(name, full_page)

def chrome_search(query, engine="google"):
    """Search query on Google or YouTube"""
    if engine.lower() == "youtube":
        return chrome_bot.search_youtube(query)
    else:
        return chrome_bot.search_google(query)

# Backward compatibility alias
chrome_automation = chrome_bot

def chrome_command(command):
    """Integrated command handler for the dispatcher/automation bridge"""
    cmd = command.lower().strip()
    
    if "new tab" in cmd:
        return chrome_bot.new_tab()
    elif "close tab" in cmd:
        return chrome_bot.close_tab()
    elif "revert" in cmd or "undo close" in cmd:
        return chrome_bot.revert_closed_tab()
    elif "close others" in cmd:
        return chrome_bot.close_other_tabs()
    elif cmd.startswith("switch to "):
        target = cmd.replace("switch to ", "").strip()
        return chrome_bot.switch_to_tab(target)
    elif cmd.startswith("search "):
        query = cmd.replace("search ", "").strip()
        return chrome_bot.search_google(query)
    elif cmd.startswith("youtube "):
        query = cmd.replace("youtube ", "").strip()
        return chrome_bot.search_youtube(query)
    elif cmd.startswith("open "):
        url = cmd.replace("open ", "").strip()
        return chrome_bot.open_url(url)
    elif "screenshot" in cmd:
        full = "full" in cmd
        res = chrome_bot.screenshot(full_page=full)
        return f"Screenshot saved: {res}. Do you want to open it?" if res else "Failed to take screenshot"
    elif cmd.startswith("click "):
        target = cmd.replace("click ", "").strip()
        return chrome_bot.click_text(target)
    elif cmd.startswith("type "):
        text = cmd.replace("type ", "").strip()
        return chrome_bot.type_and_enter(text)
    elif "scroll" in cmd:
        if "bottom" in cmd:
             chrome_bot.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
             return "Scrolled to bottom"
        chrome_bot.driver.execute_script("window.scrollBy(0, 500);")
        return "Scrolled down"
    elif "close browser" in cmd or "quit chrome" in cmd:
        return chrome_bot.close()
    
    return "Unknown chrome command"
