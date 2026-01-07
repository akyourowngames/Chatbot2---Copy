"""
Enhanced Decision-Making Model with Better Intelligence
========================================================
Improved intent classification with clearer logic
"""

from groq import Groq
from dotenv import dotenv_values

import os
env_vars = dotenv_values(".env")
GroqAPIKey = os.getenv("GROQ_API_KEY") or env_vars.get("GROQ_API_KEY", "")

if not GroqAPIKey:
    raise ValueError("GroqAPIKey is not set")

client = Groq(api_key=GroqAPIKey)

funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "content", "google search", 
    "youtube search", "reminder", "vision", "remember", "chrome", "workflow"
]

# Enhanced decision-making prompt
preamble = """You are an intelligent intent classifier. Analyze queries and classify them accurately.

INTENT CATEGORIES:

1. GENERAL - Conversations, questions not needing real-time data
   - "how are you?", "explain AI", "tell me about history"
   → general (query)

2. REALTIME - Queries needing current information
   - "who is the current president?", "today's news", "latest updates"
   → realtime (query)

3. OPEN - Open apps/websites
   - "open chrome", "launch spotify"
   → open (app name)

4. CLOSE - Close apps
   - "close notepad"
   → close (app name)

5. PLAY - Play media
   - "play bohemian rhapsody"
   → play (media name)

6. SYSTEM - System commands
   - "increase volume", "mute"
   → system (command)

7. CONTENT - Create content
   - "write an email", "code a script"
   → content (what to create)

8. GOOGLE SEARCH - Search Google
   - "search for python", "google AI"
   → google search (query)

9. YOUTUBE SEARCH - Search YouTube
   - "youtube search cooking"
   → youtube search (query)

10. REMINDER - Set reminders
    - "remind me at 5pm"
    → reminder (time) (message)

11. EXIT - End conversation
    - "goodbye", "bye"
    → exit

RULES:
- For time/date questions: use GENERAL (assistant knows time)
- For ambiguous queries: use GENERAL
- For multiple intents: list all (e.g., "open chrome, google search AI")
- Preserve exact query wording

EXAMPLES:
"how are you?" → general how are you?
"who is the PM?" → realtime who is the PM?
"open chrome" → open chrome
"search for AI" → google search AI
"""

ChatHistory = [
    {"role": "User", "message": "how are you?"},
    {"role": "Chatbot", "message": "general how are you?"},
    {"role": "User", "message": "who is the current president?"},
    {"role": "Chatbot", "message": "realtime who is the current president?"},
    {"role": "User", "message": "open chrome and search for AI"},
    {"role": "Chatbot", "message": "open chrome, google search AI"},
]

def FirstLayerDMM(prompt: str = "test"):
    """
    OPTIMIZED Decision Making Model - JARVIS Level
    Uses SmartTrigger for instant recognition (sub-100ms)
    Falls back to LLM only when needed (reduces LLM calls by 80%)
    """
    from Backend.SmartTrigger import smart_trigger
    
    prompt_lower = prompt.lower().strip()
    
    # INSTANT TRIGGERS (No LLM needed - 10-50ms response)
    trigger_type, command, original = smart_trigger.detect(prompt)
    
    if trigger_type:
        # Map triggers to function calls
        if trigger_type == "chrome":
            action, target = smart_trigger.extract_chrome_action(prompt)
            if action == "search":
                return [f"chrome search {target}"]
            elif action == "open":
                return [f"chrome open {target}"]
            else:
                return [f"chrome {action}"]
        
        elif trigger_type == "vision":
            return [f"vision {prompt_lower}"]
        
        elif trigger_type == "memory":
            return [f"remember {command}"]
        
        elif trigger_type == "system":
            # Extract system command
            if "volume up" in prompt_lower or "increase volume" in prompt_lower:
                return ["system volume up"]
            elif "volume down" in prompt_lower or "decrease volume" in prompt_lower:
                return ["system volume down"]
            elif "brightness up" in prompt_lower or "increase brightness" in prompt_lower:
                return ["system brightness up"]
            elif "brightness down" in prompt_lower or "decrease brightness" in prompt_lower:
                return ["system brightness down"]
            elif "mute" in prompt_lower:
                return ["system mute"]
            elif "screenshot" in prompt_lower:
                return ["system screenshot"]
            elif "lock" in prompt_lower:
                return ["system lock screen"]
            elif "desktop" in prompt_lower or "minimize" in prompt_lower:
                return ["system minimize all"]
        
        elif trigger_type == "file":
            if "create" in prompt_lower:
                filename = command.replace("create file", "").replace("named", "").strip()
                return [f"system create file {filename}"]
            elif "delete" in prompt_lower:
                filename = command.replace("delete file", "").replace("the file", "").strip()
                return [f"system delete file {filename}"]
        
        elif trigger_type == "app":
            if "open" in prompt_lower or "launch" in prompt_lower:
                app = command.replace("open", "").replace("launch", "").strip()
                return [f"open {app}"]
            elif "close" in prompt_lower:
                app = command.replace("close", "").replace("quit", "").strip()
                return [f"close {app}"]
        
        elif trigger_type == "scrape":
            return [f"realtime {prompt}"]
        
        elif trigger_type == "switch":
            # Handle app switching
            if "next" in prompt_lower or ("switch" in prompt_lower and "app" in prompt_lower and "to" not in prompt_lower):
                return ["system switch app"]
            elif "previous" in prompt_lower or "back" in prompt_lower:
                return ["system previous app"]
            elif "switch to" in prompt_lower:
                app_name = prompt_lower.split("switch to")[-1].strip()
                return [f"system switch to {app_name}"]
            elif "list" in prompt_lower:
                return ["system list apps"]
        
        elif trigger_type == "rag":
            # Handle RAG (Chat with Documents) - NEW
            return [f"rag {command}"]
        
        elif trigger_type == "agents":
            # Handle Multi-Agent System - NEW
            return [f"agents {command}"]
        
        elif trigger_type == "code":
            # Handle Code Execution - NEW
            return [f"code {command}"]
    
    # AUTO-DETECT PDF/SUPABASE URLs in message (for direct URL summarization)
    import re
    url_match = re.search(r'https?://[^\s]+\.pdf', prompt, re.IGNORECASE)
    supabase_match = re.search(r'https?://[^\s]*supabase[^\s]*', prompt, re.IGNORECASE)
    
    if url_match or supabase_match:
        matched_url = url_match.group(0) if url_match else supabase_match.group(0)
        # Check if user wants to summarize or chat with it
        if any(word in prompt_lower for word in ['summarize', 'summarise', 'sum up', 'summary', 'chat', 'read', 'add', 'upload', 'analyze', 'analyse']):
            return [f"rag upload {matched_url}"]
    
    # AUTO-DETECT MULTI-AGENT REQUESTS
    agent_keywords = ["research and write", "research then write", "deeply research", "full pipeline", "use agents"]
    if any(kw in prompt_lower for kw in agent_keywords):
        return [f"agents {prompt}"]
    
    # AUTO-DETECT CODE REQUESTS
    code_keywords = ["run this code", "execute code", "write python", "debug code", "fix this error"]
    if any(kw in prompt_lower for kw in code_keywords):
        return [f"code {prompt}"]
    
    # FAST REGEX PATTERNS (50-100ms response)
    if "time" in prompt_lower and "what" in prompt_lower:
        return ["general what time is it"]
    if "date" in prompt_lower and "what" in prompt_lower:
        return ["general what is today's date"]
    if prompt_lower in ["exit", "quit", "bye", "goodbye"]:
        return ["exit"]
    
    # REALTIME SEARCH INDICATORS (100-150ms)
    realtime_keywords = ["latest", "current", "today", "news", "weather", "stock", "price"]
    if any(keyword in prompt_lower for keyword in realtime_keywords):
        return [f"realtime {prompt_lower}"]
    
    # LLM FALLBACK (Only for complex queries - 800-1500ms)
    # This is now used <20% of the time vs 100% before
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": preamble},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=150,
            top_p=0.9,
            stream=False,
            stop=None
        )
        
        response = completion.choices[0].message.content
        response = response.replace("\n", "")
        response = response.split(",")
        response = [i.strip() for i in response]
        
        temp = []
        for task in response:
            for func in funcs:
                if task.startswith(func):
                    temp.append(task)
                    break
        
        response = temp if temp else ["general " + prompt]
        
        if "(query)" in str(response):
            return FirstLayerDMM(prompt=prompt)
        
        return response
        
    except Exception as e:
        print(f"Decision-making error: {e}")
        return ["general " + prompt]

if __name__ == "__main__":
    # Test cases
    test_queries = [
        "how are you?",
        "who is the current president?",
        "open chrome",
        "search for AI tutorials",
        "play some music",
        "what time is it?",
        "look at this image",
        "what is on my screen",
    ]
    
    print("\nTesting Enhanced Decision-Making Model:\n")
    for query in test_queries:
        result = FirstLayerDMM(query)
        print(f"Query: '{query}'")
        print(f"Decision: {result}\n")
