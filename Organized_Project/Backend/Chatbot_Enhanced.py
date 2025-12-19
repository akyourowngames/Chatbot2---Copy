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


def ChatBot(Query: str, use_cache: bool = True) -> str:
    start_time = time.time()
    
    try:
        # Load chat history
        with open(chatlog_path, "r") as f:
            messages = load(f)
        
        # Keep only recent context (last 12 exchanges)
        if len(messages) > 12:
            messages = messages[-12:]
            
        # Get Long-Term Memory
        from Backend.Memory import Recall
        MemoryContext = Recall()
        
        # Get Contextual Memory
        from Backend.ContextualMemory import contextual_memory
        ConversationContext = contextual_memory.get_context(Query)
        
        # Build System Prompt
        full_context = System + "\n" + RealTimeInformation() + "\n\n" + MemoryContext
        if ConversationContext:
            full_context += "\n\nConversation Context:\n" + ConversationContext

        # --- DIRECT LLM CALL (LEGACY RESTORED) ---
        # Build messages for LLM
        conversation_messages = SystemChatBot.copy()
        conversation_messages.append({"role": "system", "content": full_context})
        conversation_messages.extend(messages)
        conversation_messages.append({"role": "user", "content": Query})
        
        # Call unified LLM provider
        Answer = ChatCompletion(
            messages=conversation_messages,
            model="llama-3.3-70b-versatile",
            text_only=True
        )
        # ----------------------------

        # Prepare message for history
        messages.append({"role": "user", "content": Query})
        messages.append({"role": "assistant", "content": Answer})
        
        # Save chat history
        with open(chatlog_path, "w") as f:
            dump(messages, f, indent=4)
        
        # Save to contextual memory
        contextual_memory.add_conversation(Query, Answer)
        
        # Cache the response
        generation_time = time.time() - start_time
        if use_cache and CACHE_AVAILABLE:
            cache_response(Query, Answer, generation_time)
        
        print(f"Response generated in {generation_time:.2f}s")
        
        return AnswerModifier(Answer=Answer)
    
    except Exception as e:
        print(f"Error: {e}")
        return "I encountered an error. Please try again."

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
