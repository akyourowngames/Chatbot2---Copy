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
from flask import Flask, request, jsonify
from flask_cors import CORS
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

def RealtimeSearchEngine(prompt):
    """
    🚀 BEAST MODE: Gemini with Google Search Grounding for REAL-TIME web access.
    Uses Gemini 2.0 Flash with search grounding to get live, intelligent answers.
    Falls back to DuckDuckGo if Gemini fails.
    """
    print(f"[RealtimeSearch] 🔍 Query: {prompt}")
    
    # Clean the query
    clean_query = prompt.lower().replace("search for", "").replace("@search", "").strip()
    if not clean_query:
        clean_query = prompt
    
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
            print(f"[RealtimeSearch] ⚠️ No Gemini keys found, skipping to DuckDuckGo")
            raise Exception("No Gemini API keys available")
        
        # Try each key until one works
        last_error = None
        for idx, gemini_key in enumerate(gemini_keys):
            try:
                genai.configure(api_key=gemini_key)
                
                # Use Gemini 3 Pro with dynamic retrieval (Google Search grounding)
                model = genai.GenerativeModel(
                    model_name="gemini-3-pro-preview",
                    tools="google_search_retrieval"  # Correct syntax for grounding
                )
                
                # Create the search prompt
                search_prompt = f"""Search the web for the latest information about: {clean_query}

Provide a comprehensive, well-structured answer with:
- Current facts and data
- Recent news or updates  
- Key details the user should know

Be direct and informative. Use markdown formatting."""

                print(f"[RealtimeSearch] 🌐 Using Gemini key {idx+1}/{len(gemini_keys)} with Google Search Grounding...")
                
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
                        print(f"[RealtimeSearch] ⚠️ Source extraction error: {src_err}")
                    
                    print(f"[RealtimeSearch] ✅ Gemini grounding response with {len(sources)} sources")
                    
                    # Return structured response with sources
                    return {
                        "text": f"🔍 **{clean_query}**\n\n{result_text}",
                        "sources": sources,
                        "engine": "gemini"
                    }
                else:
                    print(f"[RealtimeSearch] ⚠️ Empty Gemini response with key {idx+1}")
                    
            except Exception as e:
                last_error = str(e)
                if "quota" in str(e).lower() or "429" in str(e):
                    print(f"[RealtimeSearch] ⚠️ Gemini key {idx+1} quota exceeded, trying next...")
                    continue
                else:
                    print(f"[RealtimeSearch] ⚠️ Gemini key {idx+1} error: {e}")
                    break
        
        # All keys failed
        print(f"[RealtimeSearch] ⚠️ All Gemini keys failed: {last_error}, falling back to DuckDuckGo")
                
    except Exception as e:
        print(f"[RealtimeSearch] ⚠️ Gemini grounding error: {e}, falling back to DuckDuckGo")
    
    # === FALLBACK: DuckDuckGo Direct Search ===
    try:
        # Try new package first, then old package
        try:
            from ddgs import DDGS
            print(f"[RealtimeSearch] Using new ddgs package")
        except ImportError:
            from duckduckgo_search import DDGS
            print(f"[RealtimeSearch] Using old duckduckgo_search package")
            
        with DDGS() as ddgs:
            results = list(ddgs.text(clean_query, max_results=5))
            
            if results:
                print(f"[RealtimeSearch] 📋 DuckDuckGo: {len(results)} results")
                
                response_text = f"🔍 **Web Search Results for: {clean_query}**\n\n"
                
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
                
                return {
                    "text": response_text,
                    "sources": sources,
                    "engine": "duckduckgo"
                }
            else:
                return {"text": f"No search results found for '{clean_query}'.", "sources": [], "engine": "none"}
                
    except Exception as e:
        print(f"[RealtimeSearch] ❌ All search methods failed: {e}")
        return {"text": f"Search failed: {str(e)}. Please try again.", "sources": [], "engine": "error"}

app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    prompt = data.get('prompt', '')
    if not prompt:
        return jsonify({'response': 'The query is empty. Please provide a valid query.'})
    
    response = RealtimeSearchEngine(prompt)
    return jsonify({'response': response})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)