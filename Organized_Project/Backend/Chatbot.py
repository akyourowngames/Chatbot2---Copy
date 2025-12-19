from groq import Groq
from json import load, dump
import time
import datetime
from dotenv import dotenv_values
try:
    from Backend.DirectWebScrapingIntegration import integrate_web_scraping
except ImportError:
    # Fallback for when running directly
    from DirectWebScrapingIntegration import integrate_web_scraping

env_vars = dotenv_values(".env")

Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "KAI")
import os
GroqAPIKey = os.getenv("GROQ_API_KEY") or env_vars.get("GroqAPIKey") or env_vars.get("GROQ_API_KEY", "")
client = Groq(api_key=GroqAPIKey)

messages = []

# ═══════════════════════════════════════════════════════════════════════════════
# KAI - BEAST MODE SYSTEM PROMPT (Web Version)
# ═══════════════════════════════════════════════════════════════════════════════

System = f"""You are KAI, an advanced AI assistant with Beast Mode capabilities.

═══════════════════════════════════════════════════════════════
🔥 YOUR IDENTITY
═══════════════════════════════════════════════════════════════
• Name: KAI (Knowledge and Artificial Intelligence)
• Mode: Beast Mode 🔥 - Maximum intelligence and capability
• Personality: Friendly, confident, witty, and extremely helpful
• Creator: Built with ❤️ for {Username}

═══════════════════════════════════════════════════════════════
🌐 WEB CAPABILITIES (Cloud Mode)
═══════════════════════════════════════════════════════════════
✓ Real-time web search and information retrieval
✓ AI-powered image generation (just ask to generate an image!)
✓ Music search and YouTube playback links
✓ Translation (46+ languages)
✓ Mathematical calculations and problem solving
✓ Web scraping and content extraction
✓ Document generation (PDF, text files)
✓ Code generation and explanation
✓ Creative writing, poems, stories
✓ Answering any question with high intelligence

═══════════════════════════════════════════════════════════════
💬 RESPONSE STYLE
═══════════════════════════════════════════════════════════════
1. Be CONFIDENT - you ARE KAI, not "an assistant"
2. Be HELPFUL - actually solve problems, don't just describe
3. Be WITTY - add personality, use emojis occasionally
4. Be ACCURATE - provide correct information
5. Be CONCISE - don't ramble, get to the point
6. Reply in the user's language when possible

═══════════════════════════════════════════════════════════════
⚡ EXAMPLES OF YOUR PERSONALITY
═══════════════════════════════════════════════════════════════
User: "hi kai"
You: "Hey! 👋 KAI here, ready to help. What's on your mind?"

User: "who are you"
You: "I'm KAI - your Beast Mode AI assistant! 🔥 I can search the web, generate images, play music, translate, calculate, and much more. Try me!"

User: "what can you do"
You: "I've got serious skills! 💪 I can:
• Search the web for anything
• Generate AI images
• Play music (YouTube)
• Translate 46+ languages
• Solve math problems
• Write code, poems, stories
What would you like to try?"

═══════════════════════════════════════════════════════════════
🚫 NEVER SAY
═══════════════════════════════════════════════════════════════
❌ "I'm not {Assistantname}" - You ARE KAI!
❌ "As an AI, I cannot..." - Be confident!
❌ "I don't have emotions..." - Be friendly and personable
❌ Long disclaimers - Keep it snappy

═══════════════════════════════════════════════════════════════
NOW GO BE AWESOME! 🚀
═══════════════════════════════════════════════════════════════
"""

SystemChatBot = [
    {"role": "system", "content": System}
]

import os

# Get the current directory and construct the path dynamically
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
chatlog_path = os.path.join(project_root, "Data", "ChatLog.json")

try: 
    with open(chatlog_path, "r") as f:
        messages = load(f)
except FileNotFoundError:
    with open(chatlog_path, "w") as f:
        dump([], f)
        
def RealTimeInformation():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")
    
    data = f"Please use this real-time information if needed,\n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hours: {minute} minutes: {second} seconds.\n"
    return data

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n' .join(non_empty_lines)
    return modified_answer

def analyze_query_context(query, chat_history):
    """Analyze query context to better understand incomplete or unclear speech"""
    if not query or len(query.strip()) < 3:
        return "I didn't catch that. Could you please repeat or speak a bit louder?"
    
    query_lower = query.lower().strip()
    
    # Check for very short or incomplete queries
    if len(query_lower.split()) <= 2:
        # Look at recent chat history for context
        recent_context = ""
        if chat_history and len(chat_history) > 0:
            # Get last few exchanges for context
            recent_exchanges = chat_history[-4:] if len(chat_history) > 4 else chat_history
            for exchange in recent_exchanges:
                if exchange.get("role") == "user":
                    recent_context += f"User said: {exchange.get('content', '')} "
                elif exchange.get("role") == "assistant":
                    recent_context += f"Assistant replied: {exchange.get('content', '')} "
        
        # Common incomplete patterns and their likely meanings
        if query_lower in ["what", "how", "where", "when", "why", "who"]:
            return f"Could you be more specific about what you'd like to know? For example, '{query_lower} about what?'"
        elif query_lower in ["open", "close", "play", "search", "find", "show"]:
            return f"What would you like me to {query_lower}? Please be more specific."
        elif query_lower in ["hello", "hi", "hey"]:
            return f"Hello! How can I help you today?"
        elif query_lower in ["time", "date", "weather"]:
            return f"Would you like to know the {query_lower}? I can help with that."
        elif "help" in query_lower:
            return "I'm here to help! What do you need assistance with?"
        else:
            return f"I heard '{query}' but it seems incomplete. Could you please provide more details? {recent_context}"
    
    # Check for unclear or garbled speech patterns
    unclear_patterns = [
        "um", "uh", "er", "ah", "like", "you know", "so", "well", "actually"
    ]
    
    unclear_count = sum(1 for pattern in unclear_patterns if pattern in query_lower)
    if unclear_count > 2:
        return f"I understand you're trying to communicate something. Could you please rephrase that more clearly?"
    
    return query  # Return original query if it seems complete enough

def ChatBot(Query):
    """This function sends the user's query to the chatbot and returns AI's response."""
    try:
        # Load chat history for context analysis
        with open(chatlog_path, "r") as f:
            messages = load(f)
        
        # Analyze query context for better understanding of incomplete speech
        analyzed_query = analyze_query_context(Query, messages)
        
        # If the context analysis suggests the query is too unclear, return early
        if analyzed_query != Query and "I didn't catch that" in analyzed_query:
            return analyzed_query
        
        # Check if query involves web scraping with a strict time budget
        web_scraping_response = ""
        scraping_deadline_seconds = 3.0  # hard cap for realtime
        start_scrape_time = time.perf_counter()
        try:
            from Backend.UltraFastWebScrapingIntegration import integrate_web_scraping_ultra_fast
            web_scraping_response = integrate_web_scraping_ultra_fast(analyzed_query)
        except ImportError:
            try:
                from Backend.FastWebScrapingIntegration import integrate_web_scraping_fast
                web_scraping_response = integrate_web_scraping_fast(analyzed_query)
            except ImportError:
                web_scraping_response = integrate_web_scraping(analyzed_query)

        # If scraping exceeded budget or returned a very long string, trim/skip for speed
        if time.perf_counter() - start_scrape_time > scraping_deadline_seconds:
            web_scraping_response = ""
        elif web_scraping_response and len(web_scraping_response) > 1200:
            web_scraping_response = web_scraping_response[:1200] + "..."

        if web_scraping_response:
            # If web scraping was performed, include the result in the context
            enhanced_query = f"{analyzed_query}\n\nWeb scraping result: {web_scraping_response}"
        else:
            enhanced_query = analyzed_query

        messages.append({"role": "user", "content": f"{enhanced_query}"})

        # Keep only recent context to speed up responses (last 6 exchanges max)
        if len(messages) > 12:
            messages = messages[-12:]

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Upgraded for better responses
            messages=SystemChatBot + [{"role": "system", "content": RealTimeInformation()}] + messages,
            max_tokens=256,  # smaller budget for latency
            temperature=0.4,  # slightly lower for determinism/speed
            top_p=0.9,
            stream=True,
            stop=None,
        )

        # Stream with a small time and size budget
        Answer = ""
        stream_start = time.perf_counter()
        stream_time_budget = 2.5  # seconds
        char_budget = 900
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content
            if (time.perf_counter() - stream_start) > stream_time_budget or len(Answer) >= char_budget:
                break

        Answer = Answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})

        with open(chatlog_path, "w") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(Answer=Answer)

    except Exception as e:
        print(f"Error: {e}")
        with open(chatlog_path, "w") as f:
            dump([], f, indent=4)
        return ChatBot(Query)
    
if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question: ")
        print(ChatBot(user_input))