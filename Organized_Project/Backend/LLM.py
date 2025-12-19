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

def ChatCompletion(messages, system_prompt=None, text_only=True, model="llama-3.3-70b-versatile"):
    """
    Unified chat completion function with robust error handling.
    """
    if not groq_client:
        return "System Error: Groq API Key is missing or invalid. Please check .env file."

    # Pre-process messages
    if system_prompt:
        if not any(m['role'] == 'system' for m in messages):
            messages.insert(0, {'role': 'system', 'content': system_prompt})
            
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
        response = ChatCompletion(messages, model="llama-3.3-70b-versatile")
        if "[" in response and "]" in response:
             return ast.literal_eval(response[response.find("["):response.rfind("]")+1])
    except:
        pass
    return ["general"]
