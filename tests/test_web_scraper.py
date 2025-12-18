"""
🧪 WEB SCRAPER TEST SUITE — Testing the Beast Mode 🚀
Simple test script to verify the web scraping engine works correctly.
"""

import sys
import os
import time
import logging

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_basic_imports():
    """Test if all modules can be imported"""
    print("🧪 Testing basic imports...")
    
    try:
        from web_scraper import (
            StealthFetcher, ScrapingConfig,
            AIParser, ParserConfig,
            DynamicBrowser, BrowserConfig,
            DataStorage, StorageConfig,
            WebScrapingLogger, LogConfig,
            WebScrapingOrchestrator, OrchestratorConfig
        )
        print("✅ All modules imported successfully!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_fetcher():
    """Test the stealth fetcher"""
    print("\n🧪 Testing stealth fetcher...")
    
    try:
        from web_scraper import StealthFetcher, ScrapingConfig
        
        config = ScrapingConfig(timeout=10, max_retries=1)
        fetcher = StealthFetcher(config)
        
        # Test with a simple URL
        response = fetcher.fetch("https://httpbin.org/get")
        
        if response and fetcher.validate_response(response):
            print("✅ Fetcher test passed!")
            return True
        else:
            print("❌ Fetcher test failed - no valid response")
            return False
            
    except Exception as e:
        print(f"❌ Fetcher test error: {e}")
        return False

def test_parser():
    """Test the AI parser"""
    print("\n🧪 Testing AI parser...")
    
    try:
        from web_scraper import AIParser, ParserConfig
        
        config = ParserConfig(
            use_openai=False,  # Don't use OpenAI for testing
            use_local_models=False,  # Don't use local models for testing
            extract_entities=False,
            extract_sentiment=False,
            summarize_content=False
        )
        
        parser = AIParser(config)
        
        # Test HTML parsing
        test_html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Test Article</h1>
                <p>This is a test article for the web scraper.</p>
                <p>It contains multiple paragraphs of content.</p>
            </body>
        </html>
        """
        
        result = parser.parse_html(test_html, "https://example.com")
        
        if result and result.title == "Test Page":
            print("✅ Parser test passed!")
            return True
        else:
            print("❌ Parser test failed")
            return False
            
    except Exception as e:
        print(f"❌ Parser test error: {e}")
        return False

def test_storage():
    """Test the storage system"""
    print("\n🧪 Testing storage system...")
    
    try:
        from web_scraper import DataStorage, StorageConfig
        
        config = StorageConfig(base_path="test_data", format="json")
        storage = DataStorage(config)
        
        # Test data
        test_data = {
            "url": "https://example.com/test",
            "title": "Test Article",
            "content": "This is test content",
            "timestamp": time.time()
        }
        
        # Save JSON
        file_path = storage.save_json(test_data, "test.json")
        
        if file_path and os.path.exists(file_path):
            print("✅ Storage test passed!")
            return True
        else:
            print("❌ Storage test failed")
            return False
            
    except Exception as e:
        print(f"❌ Storage test error: {e}")
        return False

def test_logger():
    """Test the logging system"""
    print("\n🧪 Testing logging system...")
    
    try:
        from web_scraper import WebScrapingLogger, LogConfig
        
        config = LogConfig(log_level="INFO", console_output=True)
        logger = WebScrapingLogger(config)
        
        # Test logging
        logger.log_info("Test info message")
        logger.log_warning("Test warning message")
        
        # Test metrics
        stats = logger.get_operation_stats()
        
        print("✅ Logger test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Logger test error: {e}")
        return False

def test_integration():
    """Test the chatbot integration"""
    print("\n🧪 Testing chatbot integration...")
    
    try:
        from Backend.WebScrapingIntegration import ChatbotWebScraper
        
        scraper = ChatbotWebScraper()
        
        # Test intent detection
        intent = scraper.detect_scraping_intent("Scrape https://httpbin.org/html")
        
        if intent['intent'] == 'scrape' and intent['url'] == 'https://httpbin.org/html':
            print("✅ Integration test passed!")
            scraper.shutdown()
            return True
        else:
            print("❌ Integration test failed")
            scraper.shutdown()
            return False
            
    except Exception as e:
        print(f"❌ Integration test error: {e}")
        return False

def test_orchestrator():
    """Test the orchestrator (basic)"""
    print("\n🧪 Testing orchestrator...")
    
    try:
        from web_scraper import WebScrapingOrchestrator, OrchestratorConfig
        
        config = OrchestratorConfig(max_concurrent_jobs=2, log_level="WARNING")
        orchestrator = WebScrapingOrchestrator(config)
        
        # Start orchestrator
        orchestrator.start()
        
        # Add a test job
        job_id = orchestrator.add_job("https://httpbin.org/html")
        
        if job_id:
            print("✅ Orchestrator test passed!")
            orchestrator.shutdown()
            return True
        else:
            print("❌ Orchestrator test failed")
            orchestrator.shutdown()
            return False
            
    except Exception as e:
        print(f"❌ Orchestrator test error: {e}")
        return False

def cleanup_test_files():
    """Clean up test files"""
    print("\n🧹 Cleaning up test files...")
    
    try:
        import shutil
        
        # Remove test directories
        test_dirs = ["test_data", "logs", "scraped_data"]
        for dir_name in test_dirs:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
                print(f"✅ Removed {dir_name}")
        
        # Remove test files
        test_files = ["scraping_metrics.json", "active_sessions.json"]
        for file_name in test_files:
            if os.path.exists(file_name):
                os.remove(file_name)
                print(f"✅ Removed {file_name}")
                
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

def main():
    """Run all tests"""
    print("🕸️ WEB SCRAPER TEST SUITE 🧪")
    print("=" * 50)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Stealth Fetcher", test_fetcher),
        ("AI Parser", test_parser),
        ("Storage System", test_storage),
        ("Logging System", test_logger),
        ("Chatbot Integration", test_integration),
        ("Orchestrator", test_orchestrator)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print(f"\n{'='*50}")
    print(f"🧪 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Web Scraper is ready for beast mode! 🚀")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    
    # Cleanup
    cleanup_test_files()
    
    print("\n🕸️ Test suite completed!")

if __name__ == "__main__":
    main()
