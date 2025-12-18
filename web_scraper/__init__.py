"""
🕸️ WEB SCRAPER — The Eyes of the Machine 👁️‍🕷️
Advanced web scraping system for AI assistants.
"""

from .core.fetcher import StealthFetcher, ScrapingConfig, fetch_url, fetch_multiple_urls
from .core.parser import AIParser, ParserConfig, ParsedContent, parse_html_content, parse_url
from .core.browser import DynamicBrowser, BrowserConfig, scrape_dynamic_page, scrape_with_selenium
from .utils.storage import DataStorage, StorageConfig, save_json, save_csv, save_sqlite
from .utils.logger import WebScrapingLogger, LogConfig, setup_logging
from .main import WebScrapingOrchestrator, OrchestratorConfig, create_orchestrator, quick_scrape

__version__ = "1.0.0"
__author__ = "Krish (AK CODING)"

__all__ = [
    # Core modules
    'StealthFetcher', 'ScrapingConfig', 'fetch_url', 'fetch_multiple_urls',
    'AIParser', 'ParserConfig', 'ParsedContent', 'parse_html_content', 'parse_url',
    'DynamicBrowser', 'BrowserConfig', 'scrape_dynamic_page', 'scrape_with_selenium',
    
    # Utils
    'DataStorage', 'StorageConfig', 'save_json', 'save_csv', 'save_sqlite',
    'WebScrapingLogger', 'LogConfig', 'setup_logging',
    
    # Main orchestrator
    'WebScrapingOrchestrator', 'OrchestratorConfig', 'create_orchestrator', 'quick_scrape'
]
