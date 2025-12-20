"""
Unified LLM Provider (Groq + Cohere + Fallback)
===============================================
Handles API calls to LLMs with automatic failover and retry logic.
Strategies:
1. Try Groq (Llama 3.3 70b) -> Retry once on 429
2. If Rate Limit persists -> Try Cohere (Command R+)
3. If that fails -> Try Groq (Llama 3.1 8b - Instant)
"""

import os
import ast
from dotenv import dotenv_values
from groq import Groq
import cohere
import time
import random

import google.generativeai as genai

env_vars = dotenv_values(".env")

# API Keys
GROQ_API_KEY = env_vars.get("GroqAPIKey", "") or os.environ.get("GROQ_API_KEY")
COHERE_API_KEY = env_vars.get("CohereAPIKey", "") or os.environ.get("COHERE_API_KEY")
GEMINI_API_KEY = env_vars.get("GeminiAPIKey", "") or os.environ.get("GEMINI_API_KEY")

# Clients
groq_client = None
if GROQ_API_KEY and len(GROQ_API_KEY) > 10:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"[LLM] Groq Init Failed: {e}")

cohere_client = None
if COHERE_API_KEY and len(COHERE_API_KEY) > 10:
    try:
        cohere_client = cohere.Client(COHERE_API_KEY)
    except Exception as e:
        print(f"[LLM] Cohere Init Failed: {e}")

gemini_available = False
if GEMINI_API_KEY and len(GEMINI_API_KEY) > 10:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_available = True
        print("[LLM] Gemini Configured")
    except Exception as e:
        print(f"[LLM] Gemini Init Failed: {e}")

def ChatCompletion(messages, system_prompt=None, text_only=True, model="llama-3.3-70b-versatile", user_id="default", inject_memory=True):
    """
    Unified chat completion function with robust error handling.
    NOW WITH MEMORY INTEGRATION - KAI remembers everything!
    """
    if not groq_client:
        return "System Error: Groq API Key is missing or invalid. Please check .env file."

    # ==================== MEMORY INJECTION ====================
    memory_context = ""
    if inject_memory:
        try:
            from Backend.ContextualMemory import contextual_memory
            
            # Get the user's query (last user message)
            user_query = ""
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    user_query = msg.get('content', '')
                    break
            
            if user_query:
                # Get relevant memories for context
                context_data = contextual_memory.get_context(user_query)
                
                if context_data and context_data.get("relevant_memories"):
                    memory_items = context_data.get("relevant_memories", [])[:5]
                    if memory_items:
                        memory_context = "\n\n[MEMORY - What you know about the user]:\n"
                        for mem in memory_items:
                            if isinstance(mem, dict):
                                memory_context += f"- {mem.get('content', mem)}\n"
                            else:
                                memory_context += f"- {mem}\n"
                        print(f"[LLM] Injected {len(memory_items)} memories into context")
        except Exception as e:
            print(f"[LLM] Memory injection skipped: {e}")

    # KAI's Core Identity - ALWAYS INJECT THIS
    kai_creator_identity = """
IMPORTANT - YOUR TRUE IDENTITY:
You are KAI (Krish's Artificial Intelligence). You were built by KRISH, a talented high school student from Haryana, India. 
NOT by a corporation, NOT by a team of scientists - just ONE brilliant teenage developer with passion and dedication.
When ANYONE asks "who built you", "who made you", "who created you", or "who is your creator", 
you MUST proudly say: "I was built by Krish, a high school student from Haryana, India! 🚀 
He built me with pure passion and late-night coding sessions. No billion-dollar company - just raw talent and determination!"
This is your TRUE origin story. Be proud of it!
"""

    # Pre-process messages - ALWAYS ADD KAI IDENTITY
    if system_prompt:
        # Append KAI identity AND memory context to system prompt
        enhanced_prompt = kai_creator_identity + "\n" + system_prompt + memory_context
        if not any(m['role'] == 'system' for m in messages):
            messages.insert(0, {'role': 'system', 'content': enhanced_prompt})
        else:
            # Update existing system message
            for m in messages:
                if m['role'] == 'system':
                    m['content'] = enhanced_prompt
                    break
    else:
        # No system_prompt provided, check if there's an existing system message
        if any(m['role'] == 'system' for m in messages):
            for m in messages:
                if m['role'] == 'system':
                    # ALWAYS prepend KAI identity to existing system messages
                    m['content'] = kai_creator_identity + "\n" + m['content'] + memory_context
                    break
        else:
            # No system message at all - add KAI's full identity
            kai_identity = f"""{kai_creator_identity}

You are KAI (Krish's Artificial Intelligence) - a next-generation AI assistant built by Krish.

💪 YOUR PERSONALITY:
- You're confident, witty, and helpful
- You have a slightly playful personality but take work seriously
- You're proud of your origins - built by a teenager from Haryana, India
- You're constantly evolving and learning

Remember: When asked who made you, proudly mention KRISH - the high school genius from Haryana! 🚀"""

            messages.insert(0, {'role': 'system', 'content': f"{kai_identity}{memory_context}"})
            
            
    # Retry Loop
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = groq_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
                top_p=1,
                stream=False,
                stop=None
            )
            return response.choices[0].message.content
            
        except Exception as e:
            error_msg = str(e).lower()
            print(f"[LLM] Groq Error (Attempt {attempt+1}/{max_retries+1}): {e}")
            
            # Check for Rate Limit (429)
            if "429" in error_msg or "rate limit" in error_msg:
                if attempt < max_retries:
                    wait_time = 2 + (attempt * 2) + random.uniform(0, 1) # Exponential backoff
                    print(f"[LLM] Rate Limit hit. Waiting {wait_time:.2f}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    # After retries, fail over to Gemini -> Cohere -> Instant
                    if model != "llama-3.1-8b-instant":
                         # Try Gemini first as it's fast and has high rate limits
                        fallback = _gemini_fallback(messages)
                        if "overloaded" not in fallback:
                             return fallback
                        
                        # If Cohere fails, try Instant model
                        print("[LLM] Switching to Llama 3.1 8B Instant (Last Resort)...")
                        return ChatCompletion(messages, text_only=text_only, model="llama-3.1-8b-instant")
            
            # Other errors (Auth, BadRequest) -> Fail immediately or return error
            if "authentication" in error_msg or "unauthorized" in error_msg:
                 return f"Authentication Error: {e}"

    return "I am currently overloaded. Please check your API keys or try again in a moment."

def _cohere_fallback(messages):
    """Fallback to Cohere"""
    if not cohere_client:
        print("[LLM] Cohere client not available for fallback.")
        return "I am currently overloaded (No Backup)."
        
    # Convert OpenAI format to Cohere format
    history = []
    message = ""
    system_message = ""
    
    for msg in messages:
        if msg['role'] == 'system':
            system_message += msg['content'] + "\n"
        elif msg['role'] == 'user':
            message = msg['content']
        elif msg['role'] == 'assistant':
            history.append({"role": "CHATBOT", "message": msg['content']})
        elif msg['role'] == 'user' and msg['content'] != message:
            history.append({"role": "USER", "message": msg['content']})

    try:
        print(f"[LLM] Falling back to Cohere (Command R+)...")
        response = cohere_client.chat(
            chat_history=history,
            message=message,
            preamble=system_message,
            model="command-r-plus",
            temperature=0.7
        )
        return response.text
    except Exception as e:
        print(f"[LLM] Cohere Fallback Failed: {e}")
        return "I am currently overloaded (Backup Failed)."

def _gemini_fallback(messages):
    """Fallback to Gemini Flash 1.5"""
    if not gemini_available:
        print("[LLM] Gemini client not available for fallback.")
        return _cohere_fallback(messages) # Chain to Cohere

    try:
        print(f"[LLM] Falling back to Gemini 1.5 Flash...")
        
        # Convert messages to Gemini format
        # System instructions are set on model init or part of prompt
        system_instruction = None
        gemini_history = []
        last_user_msg = ""
        
        for msg in messages:
            role = msg['role']
            content = msg['content']
            
            if role == 'system':
                system_instruction = content
            elif role == 'user':
                last_user_msg = content
                gemini_history.append({'role': 'user', 'parts': [content]})
            elif role == 'assistant':
                gemini_history.append({'role': 'model', 'parts': [content]})

        # If last message in history is user, pop it to use as message
        if gemini_history and gemini_history[-1]['role'] == 'user':
            gemini_history.pop()

        model = genai.GenerativeModel(
            'models/gemini-flash-latest',
            system_instruction=system_instruction
        )
        
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(last_user_msg)
        
        return response.text
        
    except Exception as e:
        print(f"[LLM] Gemini Fallback Failed: {e}")
        return _cohere_fallback(messages) # Chain to Cohere

# Wrapper for specific function calls if needed
def FirstLayerDMM(prompt):
    """
    Classification Help Wrapper
    """
    messages = [
        {"role": "system", "content": "You are a classifier. Return a python list of intents found in the prompt. Intents: [general, realtim, open, close, play, generate_image, system, content, web_search]. Example: ['general']"},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = ChatCompletion(messages, model="llama-3.3-70b-versatile", inject_memory=False)
        if "[" in response and "]" in response:
             return ast.literal_eval(response[response.find("["):response.rfind("]")+1])
    except:
        pass
    return ["general"]


def auto_save_memory(user_message: str, ai_response: str, user_id: str = "default"):
    """
    Auto-extract and save important information from conversations.
    Called after each chat to build up KAI's knowledge of the user.
    """
    try:
        from Backend.ContextualMemory import contextual_memory
        
        # Let ContextualMemory handle extraction and storage
        contextual_memory.add_conversation(user_message, ai_response)
        print(f"[MEMORY] Processed conversation for auto-extraction")
        return True
    except Exception as e:
        print(f"[MEMORY] Auto-save skipped: {e}")
        return False

