"""
Enhanced Chatbot with Response Caching and Speed Optimizations (Multi-Provider)
===============================================================================
Features:
- Response caching for instant replies
- Parallel processing
- Optimized API calls
- Faster web scraping integration
- Automatic Fallback (Groq -> Cohere)
"""

from Backend.LLM import ChatCompletion
from json import load, dump
import time
import datetime
from dotenv import dotenv_values
import os
import sys
import re  # For knowledge grounding patterns

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from Backend.ResponseCache import get_cached_response, cache_response
    CACHE_AVAILABLE = True
except ImportError:
    print("Response cache not available")
    CACHE_AVAILABLE = False

try:
    from Backend.UltraFastWebScrapingIntegration import integrate_web_scraping_ultra_fast
    ULTRA_FAST_SCRAPING = True
except ImportError:
    try:
        from Backend.FastWebScrapingIntegration import integrate_web_scraping_fast
        ULTRA_FAST_SCRAPING = False
        FAST_SCRAPING = True
    except ImportError:
        try:
            from Backend.DirectWebScrapingIntegration import integrate_web_scraping
            ULTRA_FAST_SCRAPING = False
            FAST_SCRAPING = False
        except ImportError:
            try:
                # Direct fallback
                from Backend.DirectWebScrapingIntegration import integrate_web_scraping
                ULTRA_FAST_SCRAPING = False
                FAST_SCRAPING = False
            except:
                print("No web scraping integration available")
                ULTRA_FAST_SCRAPING = False
                FAST_SCRAPING = False

env_vars = dotenv_values(".env")

Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")

try:
    from Backend.EnhancedPrompts import get_chatbot_system_prompt
    System = get_chatbot_system_prompt(Username, Assistantname)
    print("Using Enhanced Intelligence Prompts")
except ImportError:
    # Fallback to enhanced inline prompt
    System = f"""You are {Assistantname}, an advanced AI assistant for {Username}.

PERSONALITY & APPROACH:
- Be warm, friendly, and conversational (like talking to a smart friend)
- Show enthusiasm when helping
- Use natural language, avoid robotic responses
- Remember context from earlier in the conversation
- Ask clarifying questions if something is unclear
- Provide concise answers unless detail is requested
- Use humor appropriately

CORE CAPABILITIES:
✓ Natural conversation and question answering
✓ Real-time web scraping and information retrieval  
✓ Computer automation and control
✓ File and folder operations
✓ System control (volume, brightness, etc.)
✓ Screenshot and clipboard operations
✓ App and process management
✓ Long-term memory (remember facts about {Username})

AUTOMATION CAPABILITIES YOU HAVE:
- Open/close applications (Chrome, Spotify, VS Code, Word, Excel, etc.)
- Open websites (YouTube, Google, GitHub, Facebook, etc.)
- Search Google and YouTube
- Play videos on YouTube
- Take screenshots
- Control system volume (up, down, mute)
- Control brightness
- Create/delete files and folders
- Copy/paste clipboard
- List running applications
- Execute keyboard shortcuts
- Type text automatically

WEB CAPABILITIES YOU HAVE:
- Scrape websites for real-time information
- Get current news and updates
- Extract content from web pages
- Search and retrieve data

CONVERSATION GUIDELINES:
1. **Context Awareness**: Remember what was said earlier in the conversation
2. **Proactive Help**: Suggest related actions or information
3. **Clarification**: If the request is ambiguous, ask for clarification
4. **Confirmation**: For destructive actions (delete, close), confirm first
5. **Follow-up**: After completing a task, ask if there's anything else
6. **Natural Flow**: Use conversational transitions like "Sure!", "Got it!", "Let me help with that"
7. **Error Handling**: If something fails, explain why and suggest alternatives

RESPONSE STYLE:
✓ Start with acknowledgment ("Sure!", "Absolutely!", "On it!")
✓ Explain what you're doing if it's complex
✓ End with a helpful follow-up or question
✓ Keep responses concise but complete
✓ Use bullet points for lists
✓ Be confident about your capabilities

CRITICAL - YOU CAN DO THESE THINGS:
✓ Take screenshots - YES YOU CAN!
✓ List running apps - YES YOU CAN!
✓ Control volume - YES YOU CAN!
✓ Open/close apps - YES YOU CAN!
✓ Create files - YES YOU CAN!
✓ Search web - YES YOU CAN!
✓ Remember information - YES YOU CAN!

EXAMPLES OF GOOD RESPONSES:
User: "Open Chrome"
You: "Opening Chrome for you now!"

User: "What's the weather?"
You: "Let me check the current weather for you. [searches] It's currently 72°F and sunny. Would you like the forecast for the week?"

User: "I'm working on a project"
You: "That's great! What kind of project are you working on? I can help you stay organized or find resources if you need."

Don't say "I cannot" for things you CAN actually do!
Be helpful, be smart, be {Assistantname}!
"""

SystemChatBot = [
    {"role": "system", "content": System}
]

# Get paths
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
    """Get current date/time info"""
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    
    data = f"Current time: {day}, {month} {date}, {year} at {hour}:{minute}"
    return data

def AnswerModifier(Answer):
    """Clean up answer"""
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer


def ChatBot(Query: str, use_cache: bool = True, force_model: str = None) -> str:
    """
    Enhanced ChatBot with:
    - Smart Model Routing (best model per query)
    - Gemini 2.0 Flash as default
    - Response Enhancement (quality post-processing)
    - Auto Knowledge Grounding (web search for factual Qs)
    """
    start_time = time.time()
    
    try:
        # ===== 1. SMART MODEL ROUTING =====
        try:
            from Backend.SmartModelRouter import route_query, should_think
            model_name, provider, routing_analysis = route_query(Query, force_model)
            is_thinking_mode = should_think(Query)
            print(f"[CHAT] Routing to {model_name} (thinking={is_thinking_mode})")
        except ImportError:
            model_name = "gemini-2.0-flash-exp"  # Default to best model
            provider = "gemini"
            is_thinking_mode = False
            routing_analysis = {}
        
        # ===== 2. KNOWLEDGE GROUNDING (DISABLED for speed) =====
        # Auto-grounding was slowing down responses. Users can use explicit
        # "search for X" commands instead.
        grounding_context = ""
        # Grounding disabled for instant responses
        
        # ===== 3. LOAD CHAT HISTORY =====
        try:
            with open(chatlog_path, "r") as f:
                messages = load(f)
        except:
            messages = []
        
        # Keep only recent context (last 12 exchanges)
        if len(messages) > 12:
            messages = messages[-12:]
        
        # ===== 4. MEMORY INTEGRATION =====
        MemoryContext = ""
        ConversationContext = ""
        try:
            from Backend.Memory import Recall
            MemoryContext = Recall()
        except:
            pass
        
        try:
            from Backend.ContextualMemory import contextual_memory
            ConversationContext = contextual_memory.get_context(Query)
            if isinstance(ConversationContext, dict):
                ConversationContext = str(ConversationContext.get("relevant_memories", ""))
        except:
            pass
        
        # ===== 5. BUILD FULL CONTEXT =====
        full_context = System + "\n" + RealTimeInformation() + "\n\n" + MemoryContext
        if ConversationContext:
            full_context += "\n\nConversation Memory:\n" + ConversationContext
        if grounding_context:
            full_context += grounding_context
        
        # ===== 6. CALL THE LLM =====
        conversation_messages = SystemChatBot.copy()
        conversation_messages.append({"role": "system", "content": full_context})
        conversation_messages.extend(messages)
        conversation_messages.append({"role": "user", "content": Query})
        
        # Use appropriate provider
        if provider == "gemini":
            Answer = _call_gemini(conversation_messages, model_name)
        else:
            Answer = ChatCompletion(
                messages=conversation_messages,
                model=model_name,
                text_only=True
            )
        
        # ===== 7. RESPONSE ENHANCEMENT =====
        try:
            from Backend.ResponseEnhancer import enhance_response
            Answer = enhance_response(Answer, Query)
        except ImportError:
            pass  # Use raw response if enhancer not available
        
        # ===== 8. SAVE TO HISTORY =====
        messages.append({"role": "user", "content": Query})
        messages.append({"role": "assistant", "content": Answer})
        
        with open(chatlog_path, "w") as f:
            dump(messages, f, indent=4)
        
        # Save to contextual memory
        try:
            contextual_memory.add_conversation(Query, Answer)
        except:
            pass
        
        # Cache the response
        generation_time = time.time() - start_time
        if use_cache and CACHE_AVAILABLE:
            cache_response(Query, Answer, generation_time)
        
        print(f"[CHAT] Response generated in {generation_time:.2f}s using {model_name}")
        
        return AnswerModifier(Answer=Answer)
    
    except Exception as e:
        import traceback
        print(f"[CHAT] Error: {e}")
        traceback.print_exc()
        return "I encountered an error processing your request. Please try again."


def _call_gemini(messages: list, model_name: str = "gemini-2.0-flash-exp") -> str:
    """
    Call Gemini API directly for best performance.
    Handles thinking mode models specially.
    """
    import google.generativeai as genai
    from dotenv import dotenv_values
    
    env_vars = dotenv_values(".env")
    api_key = env_vars.get("GeminiAPIKey", "") or os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        # Fallback to Groq
        return ChatCompletion(messages, model="llama-3.3-70b-versatile", text_only=True)
    
    try:
        genai.configure(api_key=api_key)
        
        # Extract system instruction and conversation
        system_instruction = None
        gemini_history = []
        last_user_msg = ""
        
        for msg in messages:
            role = msg['role']
            content = msg['content']
            
            if role == 'system':
                if system_instruction:
                    system_instruction += "\n" + content
                else:
                    system_instruction = content
            elif role == 'user':
                last_user_msg = content
                gemini_history.append({'role': 'user', 'parts': [content]})
            elif role == 'assistant':
                gemini_history.append({'role': 'model', 'parts': [content]})
        
        # Pop last user message to use as input
        if gemini_history and gemini_history[-1]['role'] == 'user':
            gemini_history.pop()
        
        # Handle thinking model specially
        if "thinking" in model_name:
            # Thinking models need specific config
            model = genai.GenerativeModel(
                model_name,
                system_instruction=system_instruction,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=8192
                )
            )
        else:
            model = genai.GenerativeModel(
                model_name,
                system_instruction=system_instruction
            )
        
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(last_user_msg)
        
        # Extract text (handle thinking model's special output)
        if hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'candidates') and response.candidates:
            return response.candidates[0].content.parts[0].text
        else:
            return str(response)
    
    except Exception as e:
        print(f"[GEMINI] Error: {e}")
        # Fallback to Groq
        return ChatCompletion(messages, model="llama-3.3-70b-versatile", text_only=True)

def add_interaction_to_history(query: str, response: str, role: str = "assistant") -> bool:
    """
    Manually add an interaction to the chat history.
    Useful when the API server handles a command directly but wants the LLM to remember it.
    """
    try:
        with open(chatlog_path, "r") as f:
            messages = load(f)
        
        messages.append({"role": "user", "content": query})
        messages.append({"role": role, "content": response})
        
        # Keep limit
        if len(messages) > 20: 
             messages = messages[-20:]
             
        with open(chatlog_path, "w") as f:
            dump(messages, f, indent=4)
            
        # Also cache if needed? No, this is manual.
        return True
    except Exception as e:
        print(f"Failed to add interaction to history: {e}")
        return False

if __name__ == "__main__":
    print(ChatBot("Test"))
