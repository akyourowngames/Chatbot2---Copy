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
    logger.info(f"Searching DuckDuckGo for: {query}")

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
    global SystemChatBot, messages
    
    with open(chatlog_path, "r") as f:
        messages = load(f)
    
    if not any(msg['role'] == 'system' for msg in messages):
        messages.insert(0, {"role": "system", "content": System})
    
    messages.append({"role": "user", "content": f"{prompt}"})

    # 1) Specialized Intents
    yt = fetch_youtube_best_video(prompt)
    if yt:
        messages.append({"role": "assistant", "content": yt})
        with open(chatlog_path, "w") as f: dump(messages, f, indent=4)
        try:
            from pywhatkit import playonyt
            playonyt(yt)
        except Exception:
            pass
        return AnswerModifier(Answer=f"Playing: {yt}")

    crypto = fetch_crypto_price(prompt)
    if crypto:
        messages.append({"role": "assistant", "content": crypto})
        with open(chatlog_path, "w") as f: dump(messages, f, indent=4)
        return AnswerModifier(Answer=crypto)

    stock = fetch_stock_quote(prompt)
    if stock:
        messages.append({"role": "assistant", "content": stock})
        with open(chatlog_path, "w") as f: dump(messages, f, indent=4)
        return AnswerModifier(Answer=stock)

    news = fetch_news_headlines(prompt)
    if news:
        messages.append({"role": "assistant", "content": news})
        with open(chatlog_path, "w") as f: dump(messages, f, indent=4)
        return AnswerModifier(Answer=news)
    
    # 2) Deep Research (The Upgrade)
    print(f"[RealtimeSearch] Initiating Next-Gen Deep Search for: {prompt}")
    search_context = DeepSearch(prompt)
    
    SystemChatBot.append({"role": "system", "content": search_context})
    
    # 3) LLM Synthesis
    Answer = ChatCompletion(
        model="llama-3.3-70b-versatile",
        messages=SystemChatBot + [{"role": "system", "content": Information()}] + messages,
        text_only=True
    )
    
    Answer = Answer.strip().replace("</s>", "")
    messages.append({"role": "assistant", "content": Answer})
    
    with open(chatlog_path, "w") as f:
        dump(messages, f, indent=4)
        
    SystemChatBot.pop()
    return AnswerModifier(Answer=Answer)

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