from groq import Groq
from json import load, dump
import datetime
import time
import requests
from dotenv import dotenv_values
from Backend.JarvisWebScraper import quick_search, scrape_markdown
import asyncio
try:
    from Backend.ActionHistory import action_history
except ImportError:
    action_history = None
from flask import request, jsonify  # Only import what's needed for type hints, not Flask app creation
import re
import xml.etree.ElementTree as ET

# --- SPECIALIZED DATA FETCHERS ---

def fetch_crypto_price(query):
    """Fetch crypto price using Jarvis scraper search"""
    try:
        results = asyncio.run(quick_search(query))
        # Format results
        # The original instruction provided a snippet that introduced `self._format_results(results_list)`
        # and `results_list`. Since `self` is not defined in this standalone function and `results_list`
        # is not initialized, these lines are omitted to maintain syntactical correctness and functionality.
        # The `action_history.update_status` call is adapted to use the existing `results` variable.
        
        if action_history:
            action_history.update_status("success" if results else "failed")
            
        if results:
            return f"Crypto Info: {results[0]['snippet']} (Source: {results[0]['link']})"
    except Exception:
        if action_history:
            action_history.update_status("failed")
        pass
    return None

def fetch_stock_quote(query):
    """Fetch stock quote using Jarvis scraper search"""
    try:
        results = asyncio.run(quick_search(query))
        if results:
            return f"Stock Info: {results[0]['snippet']} (Source: {results[0]['link']})"
    except Exception:
        pass
    return None

def fetch_news_headlines(query):
    """Fetch news headlines using Jarvis scraper search"""
    try:
        results = asyncio.run(quick_search(f"{query} latest news"))
        if results:
            return f"Latest News: {results[0]['title']} - {results[0]['snippet']} (Link: {results[0]['link']})"
    except Exception:
        pass
    return None

def fetch_youtube_best_video(query):
    """Fetch top youtube video link"""
    if "video" in query.lower() or "youtube" in query.lower() or "play" in query.lower():
        try:
            return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        except Exception:
            pass
    return None

def AnswerModifier(Answer):
    return Answer

def Information():
    return f"Status: Active | Time: {datetime.datetime.now().strftime('%H:%M:%S')}"

SystemChatBot = [] # Global placeholder for conversation context

env_vars = dotenv_values(".env")

Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
from Backend.LLM import ChatCompletion
# client = Groq(api_key=GroqAPIKey) # Removed: Using unified provider

System = f"""You are {Assistantname}, a witty, highly capable, and intelligent AI assistant built by {Username}.
You have real-time access to the internet and your computer system.
Your goal is to be helpful, concise, and engaging.
- Talk like a smart human, not a robot.
- Use natural language (no unnecessary "Here is the result:" headers).
- Be direct and efficient, but with a touch of personality.
- When answering from search results, synthesize the information into a cohesive answer, don't just list facts.
"""

import os

# Get the current directory and construct the path dynamically
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
chatlog_path = os.path.join(project_root, "Data", "ChatLog.json")

try:
    with open(chatlog_path, "r") as f:
        messages = load(f)
except:
    with open(chatlog_path, "w") as f:
        dump([], f)

# --- NEXT-GEN DEEP SEARCH ENGINE ---

def DeepSearch(query):
    """
    Next-Level Search: Searches Google/DDG AND scrapes the top results for deep context.
    """
    print(f"[DeepSearch] Starting deep search for: {query}")
    
    # 1. Perform initial search (Google or DDG)
    search_results = []
    try:
        raw_results = GoogleSearch(query, return_json=True) # Modified GoogleSearch to support JSON return
        if raw_results and "items" in raw_results:
            search_results = raw_results["items"][:3] # Top 3 results
    except Exception as e:
        print(f"[DeepSearch] Google error: {e}")
        # Fallback to DDG
        ddg_res = DuckDuckGoSearch(query, return_list=True)
        search_results = ddg_res[:3] if ddg_res else []

    if not search_results:
        return "No search results found."

    # 2. Extract URLs
    urls = [item.get("link") or item.get("href") for item in search_results if item.get("link") or item.get("href")]
    
    # 3. Parallel Scrape of Top URLs (The "Next Level" part)
    print(f"[DeepSearch] Scraping {len(urls)} top links for details...")
    from Backend.UltraFastWebScrapingIntegration import get_ultra_fast_scraper
    scraper = get_ultra_fast_scraper()
    
    import concurrent.futures
    scraped_contents = []
    
    def scrape_safe(url):
        try:
            return scraper.scrape_url_ultra_fast(url)
        except:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(scrape_safe, url): url for url in urls}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res and res.get("success"):
                scraped_contents.append(res)

    # 4. Format Rich Context
    context = f"## Deep Search Results for '{query}'\n\n"
    
    # summaries from search engine
    context += "### Quick Overview:\n"
    for item in search_results:
        title = item.get("title", "Unknown")
        snippet = item.get("snippet") or item.get("body", "No snippet")
        context += f"- **{title}**: {snippet}\n"
    
    context += "\n### Deep Content Analysis:\n"
    for item in scraped_contents:
        title = item.get("title", "Article")
        content = item.get("summary", "") or item.get("content", "")[:500] + "..." # Limit content length
        url = item.get("url")
        context += f"#### Source: {title} ({url})\n{content}\n\n"
        
    return context

def GoogleSearch(query, return_json=False):
    if not query.strip():
        return "The query is empty. Please provide a valid query."

    # Use environment variables if possible, else hardcoded (fallback)
    api_key = os.getenv("GOOGLE_API_KEY") or env_vars.get("GOOGLE_API_KEY", "")
    cx = os.getenv("GOOGLE_CSE_ID") or env_vars.get("GOOGLE_CSE_ID", "") 
    
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": 5
    }

    response = requests.get(search_url, params=params, timeout=6)
    response.raise_for_status()
    data = response.json()
    
    if return_json:
        return data

    Answer = f"The search results for '{query}' are:\n[start]\n"
    for item in data.get("items", []):
        Answer += f"Title: {item['title']}\nURL: {item['link']}\nDescription: {item['snippet']}\n\n"
    Answer += "[end]"
    return Answer

def DuckDuckGoSearch(query, return_list=False):
    """Fallback search using DuckDuckGo"""
    if not query.strip():
        return "No query provided."

    # Log action for retry
    if action_history:
        action_history.log_action(
            action_type="web_search",
            params={"query": query, "engine": "DuckDuckGo", "num_results": 5},
            description=f"DuckDuckGo Search: {query}"
        )
    print(f"[DuckDuckGo] Searching for: {query}")

    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if return_list:
                return results
                
            if results:
                answer = f"The search results for '{query}' are:\n[start]\n"
                for r in results:
                    title = r.get('title', '')
                    href = r.get('href', '')
                    body = r.get('body', '')
                    answer += f"Title: {title}\nURL: {href}\nDescription: {body}\n\n"
                answer += "[end]"
                return answer
    except ImportError:
        pass
    return [] if return_list else None

def RealtimeSearchEngine(prompt, clear_cache=False):
    """
    BEAST MODE: Gemini with Google Search Grounding for REAL-TIME web access.
    Uses Gemini 2.0 Flash with search grounding to get live, intelligent answers.
    Falls back to DuckDuckGo if Gemini fails.
    """
    print(f"[RealtimeSearch] Query: {prompt}")
    
    # Clean the query
    clean_query = prompt.lower().replace("search for", "").replace("@search", "").strip()
    if not clean_query:
        clean_query = prompt
    
    # SPEED: Simple in-memory cache (5 min TTL)
    import time as _time
    cache_key = clean_query[:100]  # Limit key length
    if not hasattr(RealtimeSearchEngine, '_cache'):
        RealtimeSearchEngine._cache = {}
    
    # Allow manual cache clearing
    if clear_cache:
        RealtimeSearchEngine._cache = {}
        print("[RealtimeSearch] Cache cleared")
    
    # Check cache (5 minute TTL)
    if cache_key in RealtimeSearchEngine._cache:
        cached, timestamp = RealtimeSearchEngine._cache[cache_key]
        if _time.time() - timestamp < 300:  # 5 min TTL
            print(f"[RealtimeSearch] CACHE HIT - returning cached result")
            return cached
    
    sources = []  # Collect sources for UI cards
    
    # === GEMINI WITH SEARCH GROUNDING (BEAST MODE) ===
    try:
        import google.generativeai as genai
        
        # Get Gemini API keys with rotation
        gemini_keys = []
        for i in range(1, 6):  # Try GEMINI_API_KEY_1 through GEMINI_API_KEY_5
            key = os.getenv(f"GEMINI_API_KEY_{i}") or env_vars.get(f"GEMINI_API_KEY_{i}")
            if key:
                gemini_keys.append(key)
        
        # Also add the main key
        main_key = os.getenv("GEMINI_API_KEY") or env_vars.get("GEMINI_API_KEY")
        if main_key and main_key not in gemini_keys:
            gemini_keys.insert(0, main_key)
        
        if not gemini_keys:
            print(f"[RealtimeSearch] WARNING: No Gemini keys found, skipping to DuckDuckGo")
            raise Exception("No Gemini API keys available")
        
        # Try each key until one works
        last_error = None
        for idx, gemini_key in enumerate(gemini_keys):
            try:
                genai.configure(api_key=gemini_key)
                
                # Use Gemini 2.0 Flash with dynamic retrieval (Google Search grounding)
                model = genai.GenerativeModel(
                    model_name="gemini-2.0-flash-exp",
                    tools="google_search_retrieval"  # Correct syntax for grounding
                )
                
                # Detect query type for better search context
                query_lower = clean_query.lower()
                query_type = "general"
                if any(w in query_lower for w in ["price", "cost", "rate", "value", "worth"]):
                    query_type = "price/financial"
                elif any(w in query_lower for w in ["news", "latest", "update", "happening"]):
                    query_type = "news"
                elif any(w in query_lower for w in ["weather", "forecast", "temperature"]):
                    query_type = "weather"
                elif any(w in query_lower for w in ["score", "match", "game", "won"]):
                    query_type = "sports"
                
                # Create the search prompt with specific context
                search_prompt = f"""You are a real-time search assistant. Search the web for CURRENT, FACTUAL information about:

**Query**: {clean_query}
**Query Type**: {query_type}

IMPORTANT INSTRUCTIONS:
1. This is a {query_type} query - provide actual DATA, not grammar or language explanations
2. Include NUMBERS, DATES, and SPECIFIC FACTS
3. For prices: show actual current prices with currency
4. For news: show recent headlines with dates
5. Format your response in clear markdown
6. Be direct - the user wants FACTS, not definitions

Provide a comprehensive answer with real-time data."""

                print(f"[RealtimeSearch] Using Gemini key {idx+1}/{len(gemini_keys)} with Google Search Grounding...")
                
                response = model.generate_content(search_prompt)
                
                if response and response.text:
                    result_text = response.text
                    
                    # Extract grounding sources if available
                    try:
                        if hasattr(response, 'candidates') and response.candidates:
                            candidate = response.candidates[0]
                            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                                gm = candidate.grounding_metadata
                                # Get grounding chunks (sources)
                                if hasattr(gm, 'grounding_chunks'):
                                    for chunk in gm.grounding_chunks[:5]:  # Top 5 sources
                                        if hasattr(chunk, 'web') and chunk.web:
                                            sources.append({
                                                "title": getattr(chunk.web, 'title', 'Source'),
                                                "url": getattr(chunk.web, 'uri', '')
                                            })
                    except Exception as src_err:
                        print(f"[RealtimeSearch] WARNING: Source extraction error: {src_err}")
                    
                    print(f"[RealtimeSearch] SUCCESS: Gemini grounding response with {len(sources)} sources")
                    
                    result = {
                        "text": f"**{clean_query}**\n\n{result_text}",
                        "sources": sources,
                        "engine": "gemini"
                    }
                    # 🚀 CACHE: Save result for 5 min
                    RealtimeSearchEngine._cache[cache_key] = (result, _time.time())
                    return result
                else:
                    print(f"[RealtimeSearch] WARNING: Empty Gemini response with key {idx+1}")
                    
            except Exception as e:
                last_error = str(e)
                if "quota" in str(e).lower() or "429" in str(e):
                    print(f"[RealtimeSearch] WARNING: Gemini key {idx+1} quota exceeded, trying next...")
                    continue
                else:
                    print(f"[RealtimeSearch] WARNING: Gemini key {idx+1} error: {e}")
                    break
        
        # All keys failed
        print(f"[RealtimeSearch] WARNING: All Gemini keys failed: {last_error}, falling back to DuckDuckGo")
                
    except Exception as e:
        print(f"[RealtimeSearch] WARNING: Gemini grounding error: {e}, falling back to DuckDuckGo")
    
    # === FALLBACK: DuckDuckGo Direct Search with Retries ===
    try:
        # Try new package first, then old package
        ddgs_module = None
        try:
            from ddgs import DDGS
            ddgs_module = "ddgs"
            print(f"[RealtimeSearch] Using new ddgs package")
        except ImportError:
            try:
                from duckduckgo_search import DDGS
                ddgs_module = "duckduckgo_search"
                print(f"[RealtimeSearch] Using old duckduckgo_search package")
            except ImportError:
                ddgs_module = None
                print(f"[RealtimeSearch] WARNING: No DuckDuckGo package installed")
        
        if ddgs_module:
            # Try with minimal retries for speed (reduced from 3 to 2)
            for attempt in range(2):
                try:
                    with DDGS() as ddgs:
                        # Use API backend first (faster)
                        results = list(ddgs.text(clean_query, max_results=4, backend="api"))
                        
                        if not results and attempt == 0:
                            # Only try HTML backend on first fail
                            results = list(ddgs.text(clean_query, max_results=5, backend="html"))
                        
                        if results:
                            print(f"[RealtimeSearch] DuckDuckGo: {len(results)} results (attempt {attempt+1})")
                            
                            response_text = f"**Web Search Results for: {clean_query}**\n\n"
                            
                            for i, r in enumerate(results, 1):
                                title = r.get('title', 'No title')
                                body = r.get('body', 'No description')
                                href = r.get('href', '')
                                
                                response_text += f"**{i}. {title}**\n"
                                response_text += f"{body}\n\n"
                                
                                # Add to sources for UI cards
                                sources.append({
                                    "title": title,
                                    "url": href
                                })
                            
                            result = {
                                "text": response_text,
                                "sources": sources,
                                "engine": "duckduckgo"
                            }
                            # 🚀 CACHE: Save result for 5 min
                            RealtimeSearchEngine._cache[cache_key] = (result, _time.time())
                            return result
                        else:
                            print(f"[RealtimeSearch] WARNING: No results on attempt {attempt+1}, retrying...")
                            import time
                            time.sleep(0.3)  # Quick retry
                except Exception as ddg_err:
                    print(f"[RealtimeSearch] WARNING: DDG attempt {attempt+1} failed: {ddg_err}")
                    import time
                    time.sleep(0.3)  # Quick retry
        
        # === FALLBACK 2: Use requests to scrape DuckDuckGo directly ===
        print(f"[RealtimeSearch] Trying direct web scrape fallback...")
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            # Use DuckDuckGo HTML
            url = f"https://html.duckduckgo.com/html/?q={clean_query.replace(' ', '+')}"
            resp = requests.get(url, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                results = soup.find_all('div', class_='result')[:5]
                
                if results:
                    response_text = f"**Web Search Results for: {clean_query}**\n\n"
                    
                    for i, result in enumerate(results, 1):
                        title_elem = result.find('a', class_='result__a')
                        snippet_elem = result.find('a', class_='result__snippet')
                        
                        title = title_elem.get_text(strip=True) if title_elem else 'No title'
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else 'No description'
                        href = title_elem.get('href', '') if title_elem else ''
                        
                        response_text += f"**{i}. {title}**\n"
                        response_text += f"{snippet}\n\n"
                        
                        sources.append({"title": title, "url": href})
                    
                    print(f"[RealtimeSearch] SUCCESS: Direct scrape: {len(results)} results")
                    result = {
                        "text": response_text,
                        "sources": sources,
                        "engine": "duckduckgo_html"
                    }
                    # 🚀 CACHE: Save result for 5 min
                    RealtimeSearchEngine._cache[cache_key] = (result, _time.time())
                    return result
        except Exception as scrape_err:
            print(f"[RealtimeSearch] WARNING: Direct scrape failed: {scrape_err}")
        
        # If all else fails
        return {"text": f"I couldn't find real-time data for '{clean_query}'. All search methods are temporarily unavailable. Please try again in a moment.", "sources": [], "engine": "none"}
                
    except Exception as e:
        print(f"[RealtimeSearch] ERROR: All search methods failed: {e}")
        return {"text": f"Search failed: {str(e)}. Please try again.", "sources": [], "engine": "error"}

# End of module