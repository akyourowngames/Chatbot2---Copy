"""
Unified LLM Provider (Groq + Cohere + Fallback)
===============================================
Handles API calls to LLMs with automatic failover and retry logic.

🚀 MULTI-KEY ROTATION: 6 Groq API keys for ~600k TPD capacity!

Strategies:
1. Rotate through 6 Groq keys (round-robin)
2. On 429 -> Skip to next key immediately
3. If all keys exhausted -> Fallback to Gemini -> Cohere -> Instant
"""

import os
import ast
from dotenv import dotenv_values
from groq import Groq
import cohere
import time
import random
import threading
import logging
from functools import wraps
from typing import Optional, List, Dict, Any

import google.generativeai as genai

# 🔧 BEAST MODE: Enhanced Logging
logger = logging.getLogger(__name__)

env_vars = dotenv_values(".env")

# 🔧 BEAST MODE: Performance Tracking
_request_timings: List[Dict[str, Any]] = []
MAX_TIMING_HISTORY = 100

def track_timing(provider: str, duration_ms: float, success: bool, model: str = None):
    """Track API request timing for performance monitoring."""
    global _request_timings
    _request_timings.append({
        "provider": provider,
        "model": model,
        "duration_ms": round(duration_ms, 2),
        "success": success,
        "timestamp": time.time()
    })
    # Keep only recent history
    if len(_request_timings) > MAX_TIMING_HISTORY:
        _request_timings = _request_timings[-MAX_TIMING_HISTORY:]
    
    status = "✓" if success else "✗"
    logger.info(f"[LLM] {provider} {status} in {duration_ms:.0f}ms")

def get_avg_latency(provider: str = None) -> float:
    """Get average latency for a provider (or all providers)."""
    relevant = [t for t in _request_timings if t["success"] and (not provider or t["provider"] == provider)]
    if not relevant:
        return 0
    return sum(t["duration_ms"] for t in relevant) / len(relevant)

# 🔧 BEAST MODE: Exponential Backoff with Jitter
def calculate_backoff(attempt: int, base_seconds: float = 30, max_seconds: float = 300) -> float:
    """Calculate exponential backoff with jitter."""
    backoff = min(base_seconds * (2 ** attempt), max_seconds)
    jitter = random.uniform(0, backoff * 0.3)  # 30% jitter
    return backoff + jitter

# ==================== MULTI-KEY ROTATION SYSTEM ====================
# 14 Groq API Keys for 14x capacity (~1.4M tokens/day)
GROQ_API_KEYS = [
    os.environ.get("GROQ_API_KEY_1") or env_vars.get("GROQ_API_KEY_1", ""),
    os.environ.get("GROQ_API_KEY_2") or env_vars.get("GROQ_API_KEY_2", ""),
    os.environ.get("GROQ_API_KEY_3") or env_vars.get("GROQ_API_KEY_3", ""),
    os.environ.get("GROQ_API_KEY_4") or env_vars.get("GROQ_API_KEY_4", ""),
    os.environ.get("GROQ_API_KEY_5") or env_vars.get("GROQ_API_KEY_5", ""),
    os.environ.get("GROQ_API_KEY_6") or env_vars.get("GROQ_API_KEY_6", ""),
    os.environ.get("GROQ_API_KEY_7") or env_vars.get("GROQ_API_KEY_7", ""),
    os.environ.get("GROQ_API_KEY_8") or env_vars.get("GROQ_API_KEY_8", ""),
    os.environ.get("GROQ_API_KEY_9") or env_vars.get("GROQ_API_KEY_9", ""),
    os.environ.get("GROQ_API_KEY_10") or env_vars.get("GROQ_API_KEY_10", ""),
    os.environ.get("GROQ_API_KEY_11") or env_vars.get("GROQ_API_KEY_11", ""),
    os.environ.get("GROQ_API_KEY_12") or env_vars.get("GROQ_API_KEY_12", ""),
    os.environ.get("GROQ_API_KEY_13") or env_vars.get("GROQ_API_KEY_13", ""),
    # Fallback to original key if new ones not set
    os.environ.get("GROQ_API_KEY") or env_vars.get("GroqAPIKey", ""),
]

# Filter out empty keys and create clients (NO auto-retry - we handle fallback ourselves!)
GROQ_CLIENTS = []
for i, key in enumerate(GROQ_API_KEYS):
    if key and len(key) > 10:
        try:
            # max_retries=0 disables SDK auto-retry so we can fallback to Gemini immediately
            client = Groq(api_key=key, max_retries=0)
            GROQ_CLIENTS.append({"client": client, "key_index": i, "rate_limited_until": 0})
            print(f"[LLM] Groq Key #{i+1} initialized")
        except Exception as e:
            print(f"[LLM] Groq Key #{i+1} failed: {e}")

# Thread-safe key rotation
_current_key_index = 0
_key_lock = threading.Lock()

def get_next_groq_client():
    """Round-robin rotation with rate-limit awareness"""
    global _current_key_index
    
    if not GROQ_CLIENTS:
        return None
    
    current_time = time.time()
    
    with _key_lock:
        # Try each key until we find one not rate-limited
        for _ in range(len(GROQ_CLIENTS)):
            client_info = GROQ_CLIENTS[_current_key_index % len(GROQ_CLIENTS)]
            _current_key_index += 1
            
            # Skip if rate-limited (wait 60 seconds before retry)
            if client_info["rate_limited_until"] > current_time:
                continue
            
            return client_info
        
        # All keys rate-limited, return the one with earliest unlock
        return min(GROQ_CLIENTS, key=lambda x: x["rate_limited_until"])

def mark_key_rate_limited(client_info, attempt: int = 0):
    """Mark a key as rate-limited with exponential backoff."""
    wait_seconds = calculate_backoff(attempt)
    client_info["rate_limited_until"] = time.time() + wait_seconds
    client_info["rate_limit_attempt"] = attempt + 1
    logger.warning(f"[LLM] Key #{client_info['key_index']+1} rate-limited for {wait_seconds:.0f}s (attempt {attempt + 1})")

# Legacy single client for backward compatibility
groq_client = GROQ_CLIENTS[0]["client"] if GROQ_CLIENTS else None

print(f"[LLM] Multi-Key System: {len(GROQ_CLIENTS)} Groq keys active!")

# ==================== GEMINI MULTI-KEY ROTATION ====================
GEMINI_API_KEYS = [
    os.environ.get("GEMINI_API_KEY") or env_vars.get("GeminiAPIKey", "") or env_vars.get("GEMINI_API_KEY", ""),
    os.environ.get("GEMINI_API_KEY_1") or env_vars.get("GEMINI_API_KEY_1", ""),
    os.environ.get("GEMINI_API_KEY_2") or env_vars.get("GEMINI_API_KEY_2", ""),
    os.environ.get("GEMINI_API_KEY_3") or env_vars.get("GEMINI_API_KEY_3", ""),
    os.environ.get("GEMINI_API_KEY_4") or env_vars.get("GEMINI_API_KEY_4", ""),
    os.environ.get("GEMINI_API_KEY_5") or env_vars.get("GEMINI_API_KEY_5", ""),
]

# Filter valid Gemini keys
GEMINI_KEYS = []
for i, key in enumerate(GEMINI_API_KEYS):
    if key and len(key) > 10 and key not in [k['key'] for k in GEMINI_KEYS]:
        GEMINI_KEYS.append({"key": key, "idx": i, "rate_limited_until": 0})

_gemini_key_index = 0
_gemini_key_lock = threading.Lock()

def get_next_gemini_key():
    """Round-robin Gemini key with rate-limit awareness"""
    global _gemini_key_index
    
    if not GEMINI_KEYS:
        return None
    
    current_time = time.time()
    
    with _gemini_key_lock:
        for _ in range(len(GEMINI_KEYS)):
            key_info = GEMINI_KEYS[_gemini_key_index % len(GEMINI_KEYS)]
            _gemini_key_index += 1
            
            if key_info["rate_limited_until"] > current_time:
                continue
            
            return key_info
        
        # All rate-limited, return earliest unlock
        return min(GEMINI_KEYS, key=lambda x: x["rate_limited_until"])

def mark_gemini_key_rate_limited(key_info, attempt: int = 0):
    """Mark Gemini key as rate-limited with exponential backoff."""
    wait_seconds = calculate_backoff(attempt)
    key_info["rate_limited_until"] = time.time() + wait_seconds
    key_info["rate_limit_attempt"] = attempt + 1
    logger.warning(f"[LLM] Gemini Key #{key_info['idx']+1} rate-limited for {wait_seconds:.0f}s (attempt {attempt + 1})")

print(f"[LLM] Gemini Multi-Key: {len(GEMINI_KEYS)} keys active!")

# Initialize first Gemini key
gemini_available = False
if GEMINI_KEYS:
    try:
        genai.configure(api_key=GEMINI_KEYS[0]['key'])
        gemini_available = True
        print("[LLM] Gemini Configured")
    except Exception as e:
        print(f"[LLM] Gemini Init Failed: {e}")

# Other API Keys
COHERE_API_KEY = env_vars.get("CohereAPIKey", "") or os.environ.get("COHERE_API_KEY")

cohere_client = None
if COHERE_API_KEY and len(COHERE_API_KEY) > 10:
    try:
        cohere_client = cohere.Client(COHERE_API_KEY)
    except Exception as e:
        print(f"[LLM] Cohere Init Failed: {e}")

def ChatCompletion(messages, system_prompt=None, text_only=True, model="llama-3.3-70b-versatile", user_id="default", inject_memory=True, apply_social_intelligence=False):  # DISABLED persona system
    """
    Unified chat completion function with robust error handling.
    🚀 MULTI-KEY ROTATION: Automatically rotates through 6 Groq keys!
    🧠 SOCIAL INTELLIGENCE: Makes responses human-like and contextually appropriate!
    """
    if not GROQ_CLIENTS:
        return "System Error: No Groq API Keys configured. Please check .env file."

    # 🚀 SPEED: Get user query for caching and model selection
    user_query = ""
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get('role') == 'user':
            user_query = msg.get('content', '')
            break
    
    # ==================== PROJECT MODE REMOVED ====================
    # Project intelligence has been removed - all project-like queries
    # are now handled by the goal inference pipeline in api_server.py
    
    # ==================== NORMAL CHAT FLOW CONTINUES ====================
    
    # NOTE: LLM-level caching DISABLED - was causing wrong responses
    # ResponseCache.py handles caching with proper hash-based keys
    
    # 🚀 SPEED: Use faster model for short/simple queries (under 50 chars)
    if len(user_query) < 50 and model == "llama-3.3-70b-versatile":
        # Simple queries can use the faster 8B model
        simple_keywords = ["hi", "hello", "thanks", "bye", "ok", "yes", "no", "what time", "date"]
        if any(kw in user_query.lower() for kw in simple_keywords):
            model = "llama-3.1-8b-instant"
            print(f"[LLM] Using faster 8B model for simple query")

    # ==================== MEMORY INJECTION ====================
    memory_context = ""
    # 🚀 SPEED: Skip memory for short queries (greetings, simple responses)
    if inject_memory and len(user_query) > 20:
        try:
            from Backend.ContextualMemory import contextual_memory
            
            if user_query:
                # Get relevant memories for context
                context_data = contextual_memory.get_context(user_query)
                
                # ✅ FIX: Check if context_data is dict before calling .get()
                if isinstance(context_data, dict) and context_data.get("relevant_memories"):
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

    # KAI's Core Identity - Only mention when DIRECTLY asked
    kai_creator_identity = """
Your name is KAI. You are a helpful, intelligent AI assistant.
When someone DIRECTLY asks "who built you", "who made you", "who created you", or "who is your creator",
respond: "I was built by Krish, a developer from India."
Do NOT mention your creator in every response - only when explicitly asked.
Focus on being helpful and answering the user's actual questions.
"""

    # Pre-process messages - ADD KAI IDENTITY only once
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
                    # Add KAI identity to existing system messages
                    m['content'] = kai_creator_identity + "\n" + m['content'] + memory_context
                    break
        else:
            # No system message at all - add minimal identity
            kai_identity = f"""{kai_creator_identity}

You are KAI - a helpful AI assistant. Be thorough, accurate, and genuinely helpful.
Focus on answering the user's question completely with detail when needed.
"""

            messages.insert(0, {'role': 'system', 'content': f"{kai_identity}{memory_context}"})
            
            
    # ==================== MULTI-KEY ROTATION LOOP ====================
    keys_tried = 0
    max_keys_to_try = len(GROQ_CLIENTS) + 1  # Try all keys once + 1 retry
    
    while keys_tried < max_keys_to_try:
        client_info = get_next_groq_client()
        if not client_info:
            break
        
        start_time = time.time()
        try:
            response = client_info["client"].chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=2048,  # Allow longer, detailed responses
                temperature=0.7,
                top_p=1,
                stream=False,
                stop=None
            )
            
            # 🔧 Track successful request timing
            duration_ms = (time.time() - start_time) * 1000
            track_timing("Groq", duration_ms, True, model)
            
            # Reset rate limit attempt counter on success
            client_info["rate_limit_attempt"] = 0
            
            response_text = response.choices[0].message.content
            
            # 🧠 SOCIAL INTELLIGENCE: Process response for social appropriateness
            if apply_social_intelligence:
                try:
                    from Backend.SocialIntelligence import social_intelligence
                    
                    # Extract user query from messages
                    user_query = ""
                    for msg in reversed(messages):
                        if msg.get('role') == 'user':
                            user_query = msg.get('content', '')
                            break
                    
                    # Apply social intelligence
                    response_text = social_intelligence.process_response(
                        user_input=user_query,
                        llm_response=response_text,
                        user_id=user_id,
                        history=messages
                    )
                except Exception as si_error:
                    print(f"[LLM] Social Intelligence processing failed: {si_error}")
                    # Continue with original response if social intelligence fails
            
            
            return response_text
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e).lower()
            keys_tried += 1
            
            # 🔧 BEAST MODE: Categorize errors
            error_type = "unknown"
            if "429" in error_msg or "rate limit" in error_msg:
                error_type = "rate_limit"
            elif "authentication" in error_msg or "unauthorized" in error_msg:
                error_type = "auth"
            elif "timeout" in error_msg or "timed out" in error_msg:
                error_type = "timeout"
            elif "connection" in error_msg:
                error_type = "network"
            
            track_timing("Groq", duration_ms, False, model)
            logger.warning(f"[LLM] Groq Key #{client_info['key_index']+1} Error [{error_type}]: {e}")
            
            # Handle rate limiting with exponential backoff
            if error_type == "rate_limit":
                attempt = client_info.get("rate_limit_attempt", 0)
                mark_key_rate_limited(client_info, attempt)
                logger.info(f"[LLM] Rotating to next key... ({keys_tried}/{len(GROQ_CLIENTS)} tried)")
                continue
            
            # Auth errors - fail immediately
            if error_type == "auth":
                return f"Authentication Error: {e}"
            
            # Other errors (Auth, BadRequest) -> Fail immediately or return error
            if "authentication" in error_msg or "unauthorized" in error_msg:
                 return f"Authentication Error: {e}"
    
    # All Groq keys exhausted - ALWAYS fallback to Gemini!
    print("[LLM] All Groq keys exhausted! Falling back to Gemini...")
    
    fallback = _gemini_fallback(messages)
    if fallback and "overloaded" not in fallback.lower() and "error" not in fallback.lower()[:50]:
        return fallback
    
    # If Gemini also fails, return error message
    return "I'm temporarily overloaded. Please try again in a moment."

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
    """Fallback to Gemini with multi-key rotation"""
    if not GEMINI_KEYS:
        print("[LLM] No Gemini keys available for fallback.")
        return _cohere_fallback(messages)

    # Convert messages to Gemini format once
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

    if gemini_history and gemini_history[-1]['role'] == 'user':
        gemini_history.pop()

    # Try each Gemini key
    max_attempts = len(GEMINI_KEYS) + 1
    for attempt in range(max_attempts):
        key_info = get_next_gemini_key()
        if not key_info:
            break
            
        try:
            genai.configure(api_key=key_info['key'])
            print(f"[LLM] Gemini Key #{key_info['idx']+1} - attempting...")
            
            model = genai.GenerativeModel(
                'models/gemini-1.5-flash',  # Use 1.5-flash for reliability
                system_instruction=system_instruction
            )
            
            chat = model.start_chat(history=gemini_history)
            response = chat.send_message(last_user_msg)
            
            return response.text
            
        except Exception as e:
            error_msg = str(e).lower()
            print(f"[LLM] Gemini Key #{key_info['idx']+1} Error: {e}")
            
            if "429" in error_msg or "quota" in error_msg or "rate" in error_msg:
                mark_gemini_key_rate_limited(key_info, wait_seconds=60)
                continue
            
            # Other errors - try next key
            continue
    
    # All Gemini keys exhausted
    print("[LLM] All Gemini keys exhausted!")
    return _cohere_fallback(messages)

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
    except (SyntaxError, ValueError) as parse_err:
        print(f"[LLM] FirstLayerDMM parse error: {parse_err}")
    except Exception as e:
        print(f"[LLM] FirstLayerDMM error: {e}")
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

