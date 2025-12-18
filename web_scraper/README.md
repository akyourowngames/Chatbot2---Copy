# 🕸️ The Web Scraping Engine — *"Eyes of the Machine"* 👁️‍🕷️

> **An insane, stealth-grade web scraping system built for your AI Assistant.**
> Not just a scraper — this is an *autonomous data-hunting machine* that learns, extracts, understands, and evolves.

---

## ⚙️ OVERVIEW

This module gives your assistant the **power to read, understand, and dominate the web.**
It's the *data pipeline* that feeds your AI brain with real-time knowledge — from articles, prices, trends, to analytics.

It's engineered to:

* Bypass limits.
* Stay undetected.
* Scrape dynamic JavaScript sites.
* Auto-classify and summarize content using AI.
* Save, organize, and update data in real time.

---

## 🧩 FEATURES

| ⚔️ Capability                 | 🧠 Description                                               |
| ----------------------------- | ------------------------------------------------------------ |
| **Stealth Fetching**          | Randomized headers, rotating user-agents, proxy-ready.       |
| **Dynamic Page Rendering**    | Handles JavaScript with Playwright or Selenium.              |
| **AI-Powered Parsing**        | Uses Cohere / GPT to understand meaning, not just grab text. |
| **Multi-Domain Ready**        | Works on blogs, news, e-commerce, portals, or custom pages.  |
| **Data Storage Engine**       | Automatically organizes JSON, CSV, or local DB.              |
| **Error Resilience**          | Retries, logs, and continues on failure.                     |
| **Async Mode (Insane Speed)** | Scrapes hundreds of pages concurrently with `aiohttp`.       |
| **Assistant Integration**     | Accepts natural language commands like:                      |

> "Scrape the latest posts from TechCrunch and summarize the titles."

---

## 🧠 SYSTEM ARCHITECTURE

```
web_scraper/
 ┣━ core/
 ┃   ┣━ fetcher.py      → Handles all requests, proxies, headers
 ┃   ┣━ parser.py       → Extracts structured data
 ┃   ┣━ browser.py      → For dynamic (JS) pages using Playwright
 ┣━ utils/
 ┃   ┣━ storage.py      → Save data (JSON, CSV, SQLite)
 ┃   ┣━ logger.py       → Tracks operations, retries, errors
 ┗━ main.py             → Entry point / orchestration brain
```

---

## ⚡ INSTALLATION

### 1️⃣ Install Dependencies

```bash
pip install -r Requirements.txt
```

### 2️⃣ Install Playwright Browsers

```bash
python -m playwright install
```

### 3️⃣ Download spaCy Model

```bash
python -m spacy download en_core_web_sm
```

---

## 🧩 USAGE

### 🕶️ 1. Stealth Fetch

```python
from web_scraper import StealthFetcher, ScrapingConfig

config = ScrapingConfig(timeout=30, use_proxy=True)
fetcher = StealthFetcher(config)
response = fetcher.fetch("https://example.com/news")
```

### 🧬 2. Parse Extracted Data

```python
from web_scraper import AIParser, ParserConfig

parser = AIParser(ParserConfig(use_openai=True))
parsed_content = parser.parse_html(html_content, url)
```

### 💾 3. Store Data

```python
from web_scraper import DataStorage, StorageConfig

storage = DataStorage(StorageConfig(format="sqlite"))
storage.save_sqlite(parsed_content)
```

### 🚀 4. Automate Dynamic Sites

```python
from web_scraper import DynamicBrowser, BrowserConfig

config = BrowserConfig(scroll_to_bottom=True, screenshot=True)
async with DynamicBrowser(config) as browser:
    await browser.navigate("https://example.com")
    content = await browser.get_content()
```

### 🧠 5. Full Orchestration

```python
from web_scraper import WebScrapingOrchestrator, OrchestratorConfig

orchestrator = WebScrapingOrchestrator(OrchestratorConfig())
orchestrator.start()

# Add jobs
job_ids = orchestrator.add_jobs([
    "https://example.com/article1",
    "https://example.com/article2"
])

# Wait for completion
while orchestrator.active_jobs:
    time.sleep(1)

orchestrator.shutdown()
```

---

## 🤖 INTEGRATION WITH YOUR ASSISTANT

The web scraper is already integrated into your chatbot! Just use natural language commands:

### Example Commands:

> **"Scrape the latest headlines from TechCrunch"**
> **"Analyze the website https://example.com"**
> **"Get news from BBC"**
> **"Track prices from Amazon"**
> **"Summarize the content from https://wikipedia.org"**

### How It Works:

1. **Intent Detection**: The system detects when you want to scrape web content
2. **URL Extraction**: Automatically extracts URLs from your command
3. **Content Scraping**: Uses stealth techniques to fetch content
4. **AI Processing**: Analyzes and summarizes the content
5. **Response Generation**: Provides intelligent responses based on scraped data

---

## ⚔️ ADVANCED FEATURES

### 🔄 Proxy Rotation
```python
config = ScrapingConfig(
    use_proxy=True,
    proxy_list=["proxy1:port", "proxy2:port"]
)
```

### 🧠 AI-Powered Analysis
```python
config = ParserConfig(
    use_openai=True,
    openai_api_key="your-key",
    extract_entities=True,
    extract_sentiment=True,
    summarize_content=True
)
```

### 📊 Performance Monitoring
```python
from web_scraper.utils.logger import WebScrapingLogger

logger = WebScrapingLogger()
stats = logger.get_operation_stats()
```

### 💾 Multiple Storage Formats
```python
# JSON
storage.save_json(data, "articles.json")

# CSV
storage.save_csv(data, "articles.csv")

# SQLite Database
storage.save_sqlite(data)

# Parquet (for large datasets)
storage.save_parquet(data, "articles.parquet")
```

---

## 🔥 POWER COMMANDS (when connected to your assistant)

| Command                                  | What It Does                                     |
| ---------------------------------------- | ------------------------------------------------ |
| "Scrape tech news and summarize top 5."  | Fetches latest tech headlines & summarizes them. |
| "Track iPhone 16 prices across sites."   | Multi-source e-commerce scraping.                |
| "Get me trending projects on GitHub."    | Fetches live repo data & ranks them.             |
| "Find motivational blogs updated today." | Filters and fetches only new entries.            |
| "Analyze competitor websites."           | Comprehensive website analysis.                   |
| "Monitor news about AI developments."    | Continuous news monitoring.                       |

---

## 🛡️ STEALTH FEATURES

### Anti-Detection Measures:
- **Randomized User Agents**: Rotates between different browsers
- **Request Delays**: Random delays between requests
- **Header Randomization**: Varies headers to avoid detection
- **Proxy Support**: Built-in proxy rotation
- **Browser Automation**: Uses real browsers for JavaScript sites
- **Error Handling**: Graceful handling of blocks and errors

### Rate Limiting Protection:
- **Automatic Retries**: Smart retry logic with exponential backoff
- **Request Throttling**: Configurable delays between requests
- **Queue Management**: Priority-based job queuing
- **Resource Blocking**: Can block images, CSS, fonts to save bandwidth

---

## 📊 MONITORING & ANALYTICS

### Real-time Metrics:
- **Success Rate**: Track scraping success percentage
- **Performance**: Monitor response times and throughput
- **Error Tracking**: Detailed error logging and analysis
- **Resource Usage**: Memory and CPU monitoring
- **Data Quality**: Content quality scoring

### Logging System:
- **Structured Logging**: JSON-formatted logs for analysis
- **Performance Tracking**: Detailed performance metrics
- **Error Analysis**: Comprehensive error tracking
- **Operation History**: Complete operation audit trail

---

## 🔧 CONFIGURATION

### ScrapingConfig Options:
```python
ScrapingConfig(
    timeout=30,                    # Request timeout
    max_retries=3,                 # Max retry attempts
    delay_range=(1, 3),           # Random delay range
    use_proxy=False,              # Enable proxy rotation
    user_agent_rotation=True,     # Rotate user agents
    respect_robots=True,          # Respect robots.txt
    max_concurrent=10            # Max concurrent requests
)
```

### BrowserConfig Options:
```python
BrowserConfig(
    browser_type="chromium",       # chromium, firefox, webkit
    headless=True,                # Run headless
    viewport_width=1920,          # Browser width
    viewport_height=1080,         # Browser height
    scroll_to_bottom=True,        # Auto-scroll for dynamic content
    screenshot=True,              # Take screenshots
    block_resources=['image']     # Block resource types
)
```

### ParserConfig Options:
```python
ParserConfig(
    use_openai=True,              # Use OpenAI for analysis
    use_cohere=False,            # Use Cohere API
    use_local_models=True,       # Use local NLP models
    extract_entities=True,       # Extract named entities
    extract_sentiment=True,      # Analyze sentiment
    extract_language=True,       # Detect language
    summarize_content=True,      # Generate summaries
    chunk_size=4000             # Text chunk size for processing
)
```

---

## 🚀 PERFORMANCE OPTIMIZATION

### Async Processing:
```python
# Concurrent scraping
urls = ["url1", "url2", "url3"]
results = await fetcher.fetch_multiple_async(urls)
```

### Batch Operations:
```python
# Batch processing
orchestrator.add_jobs(urls, priority=5)
```

### Resource Management:
```python
# Memory-efficient processing
config = ParserConfig(max_content_length=10000)
```

---

## 🧱 FUTURE UPGRADES

* [ ] Voice-triggered scraping
* [ ] Real-time visual web capture (screenshots of content)
* [ ] Semantic search in scraped data
* [ ] Sentiment-based filtering (positive/negative articles)
* [ ] Integration with the "Automation Brain" for automatic task chaining
* [ ] Machine learning-based content classification
* [ ] Real-time data streaming
* [ ] Advanced anti-detection techniques
* [ ] Distributed scraping across multiple machines

---

## 🔍 TROUBLESHOOTING

### Common Issues:

1. **Import Errors**: Make sure all dependencies are installed
   ```bash
   pip install -r Requirements.txt
   ```

2. **Playwright Issues**: Install browser binaries
   ```bash
   python -m playwright install
   ```

3. **spaCy Model Missing**: Download the English model
   ```bash
   python -m spacy download en_core_web_sm
   ```

4. **Memory Issues**: Reduce concurrent jobs or content length
   ```python
   config = OrchestratorConfig(max_concurrent_jobs=3)
   ```

5. **Rate Limiting**: Increase delays or use proxies
   ```python
   config = ScrapingConfig(delay_range=(2, 5), use_proxy=True)
   ```

---

## 👑 AUTHOR

**Developed by:** *Krish (AK CODING)*
**Project Type:** Core module for KaiAI / Ankita Assistant
**Motto:** *"If the web hides it, my machine will find it."*

---

## 🧠 FINAL WORD

This isn't a script.
This is a **cyber-organism** that feeds your assistant live internet intelligence.
You built not a bot — but an *entity that watches, learns, and automates*.

> "When humans sleep, my assistant keeps reading." 🌙

---

## 📞 SUPPORT

For issues, questions, or feature requests:
- Check the troubleshooting section above
- Review the logs in the `logs/` directory
- Monitor system metrics with `orchestrator.get_stats()`

**Happy Scraping! 🕸️👁️‍🕷️**
