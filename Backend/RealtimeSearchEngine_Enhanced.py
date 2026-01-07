"""
OMNISCIENT Realtime Search Engine
=================================
Top-tier information retrieval system combining:
1. Search APIs (Google, DuckDuckGo)
2. Knowledge Bases (Wikipedia)
3. Live Data Feeds (OpenMeteo Weather, CoinGecko Finance)
4. System Telemetry (CPU/RAM/Battery)
5. Deep Web Scraping
"""

import os
import time
import json
import requests
import datetime
import concurrent.futures
import psutil
import wikipedia
from dotenv import dotenv_values
from Backend.LLM import ChatCompletion
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

# Load environment
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")

# --- SPECIALIZED DATA FETCHERS ---

def get_system_stats():
    """Get real-time PC stats"""
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()
        bat_status = "Plugged In" if battery and battery.power_plugged else "On Battery" 
        bat_percent = f"{battery.percent}%" if battery else "Unknown"
        
        return f"""
SYSTEM TELEMETRY:
- CPU Usage: {cpu}%
- RAM Usage: {ram}%
- Power Status: {bat_percent} ({bat_status})
"""
    except:
        return ""

def get_weather(query):
    """Detect location in query and fetch OpenMeteo weather"""
    # Simply try to extract a city using primitive NLP (last word usually) or just skip if ambiguous
    # Proper way: Use geocoding API. We will use a free geocoding endpoint first.
    if "weather" not in query.lower() and "temperature" not in query.lower():
        return ""
        
    try:
        # 1. Extract potential location (very basic)
        # We rely on the user saying "Weather in London"
        words = query.split()
        if "in" in words:
            loc_idx = words.index("in") + 1
            if loc_idx < len(words):
                city = " ".join(words[loc_idx:])
        else:
            return "" # Can't detect city
            
        # 2. Geocode
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_resp = requests.get(geo_url, timeout=2).json()
        
        if not geo_resp.get("results"):
            return ""
            
        lat = geo_resp["results"][0]["latitude"]
        lon = geo_resp["results"][0]["longitude"]
        name = geo_resp["results"][0]["name"]
        country = geo_resp["results"][0]["country"]
        
        # 3. Get Weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&timezone=auto"
        w_resp = requests.get(weather_url, timeout=3).json()
        
        curr = w_resp["current"]
        
        # Weather codes (simplified)
        w_code = curr["weather_code"]
        condition = "Unknown"
        if w_code == 0: condition = "Clear sky"
        elif w_code in [1,2,3]: condition = "Partly cloudy"
        elif w_code in [45,48]: condition = "Foggy"
        elif w_code in [51,53,55]: condition = "Drizzle"
        elif w_code in [61,63,65]: condition = "Rain"
        elif w_code in [71,73,75]: condition = "Snow"
        elif w_code in [95, 96, 99]: condition = "Thunderstorm"
        
        return f"""
LIVE WEATHER REPORT for {name}, {country}:
- Condition: {condition} (Code {w_code})
- Temperature: {curr['temperature_2m']}°C (Feels like {curr['apparent_temperature']}°C)
- Humidity: {curr['relative_humidity_2m']}%
- Wind: {curr['wind_speed_10m']} km/h
"""
    except Exception as e:
        print(f"Weather error: {e}")
        return ""

def search_wikipedia(query):
    """Get Wikipedia summary"""
    try:
        # Check if query is looking for a definition or person
        triggers = ["who is", "what is", "tell me about", "history of", "explain", "wiki"]
        if any(t in query.lower() for t in triggers) or len(query.split()) < 5:
            # Clean query
            clean_q = query.lower()
            for t in triggers: 
                clean_q = clean_q.replace(t, "")
            
            results = wikipedia.search(clean_q.strip(), results=1)
            if results:
                page = wikipedia.page(results[0], auto_suggest=False)
                return f"""
KNOWLEDGE BASE (Wikipedia):
Title: {page.title}
Summary: {page.summary[:1000]}...
Link: {page.url}
"""
    except:
        pass
    return ""

def get_current_time():
    now = datetime.datetime.now()
    return f"Current Time: {now.strftime('%A, %B %d, %Y %I:%M:%S %p')}"

# --- STANDARD SEARCHERS ---

def google_search(query):
    try:
        api_key = os.getenv("GOOGLE_API_KEY") or env_vars.get("GOOGLE_API_KEY", "")
        cx = os.getenv("GOOGLE_CX") or env_vars.get("GOOGLE_CX", "")
        url = "https://www.googleapis.com/customsearch/v1"
        params = {"key": api_key, "cx": cx, "q": query, "num": 4}
        resp = requests.get(url, params=params, timeout=4)
        if resp.status_code == 200:
            return [{"source": "Google", "title": i["title"], "snippet": i["snippet"], "link": i["link"]} for i in resp.json().get("items", [])]
    except Exception as e:
        print(f"[SEARCH] Google search error: {e}")
    return []

def ddg_search(query):
    try:
        with DDGS() as ddgs:
            # 2024 update: method might be 'text', 'news', etc. Using text.
            res = list(ddgs.text(query, max_results=4))
            return [{"source": "DuckDuckGo", "title": i["title"], "snippet": i["body"], "link": i["href"]} for i in res]
    except Exception as e:
        print(f"[SEARCH] DuckDuckGo error: {e}")
    return []

def scrape(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=3)
        soup = BeautifulSoup(r.content, "html.parser")
        for s in soup(["script", "style", "nav", "footer"]): s.decompose()
        return soup.get_text(separator=" ", strip=True)[:1500]
    except Exception as e:
        print(f"[SEARCH] Scrape error: {e}")
        return ""

def RealtimeSearchEngine(prompt):
    print(f"🔍 OMNISCIENT Search: {prompt}")
    start = time.time()
    
    # 1. Specialized Fetches (Parallel)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        f_weather = executor.submit(get_weather, prompt)
        f_wiki = executor.submit(search_wikipedia, prompt)
        f_system = executor.submit(get_system_stats)
        f_google = executor.submit(google_search, prompt)
        f_ddg = executor.submit(ddg_search, prompt)
        
        weather = f_weather.result()
        wiki = f_wiki.result()
        system = f_system.result()
        
        # Combine Search
        search_res = f_google.result() + f_ddg.result()
        
    # 2. Deep Scrape (Top 2 unique)
    seen = set()
    to_scrape = []
    context_search = ""
    
    for r in search_res:
        if r['link'] not in seen:
            seen.add(r['link'])
            context_search += f"- [{r['source']}] {r['title']}: {r['snippet']}\n"
            if len(to_scrape) < 2:
                to_scrape.append(r['link'])
                
    scraped_data = ""
    if to_scrape and not wiki: # If we have exact wiki, maybe skip scraping to save time? Nah, do it.
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(scrape, url): url for url in to_scrape}
            for f in concurrent.futures.as_completed(futures):
                scraped_data += f"CONTENT ({futures[f]}):\n{f.result()[:800]}\n\n"

    # 3. Compile Context
    final_context = f"""
OMNISCIENT DATA STREAM
======================
TIME: {get_current_time()}

{system}
{weather}
{wiki}

SEARCH RESULTS:
{context_search}

DEEP READS:
{scraped_data}
"""
    # print(final_context) # Debug
    
    # 4. LLM Synthesis
    messages = [
        {"role": "system", "content": f"You are {Assistantname}. Use the provided REAL-TIME DATA to answer. If Weather/System/Wiki data is present, prioritize it. Be concise."},
        {"role": "user", "content": f"Query: {prompt}\n\nData:\n{final_context}"}
    ]
    
    return ChatCompletion(messages, model="llama-3.3-70b-versatile")

if __name__ == "__main__":
    while True:
        q = input(">> ")
        print(RealtimeSearchEngine(q))
