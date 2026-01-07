"""
Per-User Chatbot with Advanced Memory
=====================================
Integrates per-user memory system for:
- Semantic memory recall
- Cross-session context
- Personalized responses
"""

from groq import Groq
from json import load, dump
import time
import datetime
import os
import logging
from typing import Dict, List, Optional, Any
from dotenv import dotenv_values

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import per-user memory system
try:
    from Backend.PerUserMemory import per_user_memory, remember, recall, get_context
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    logger.warning("[CHATBOT] Per-user memory system not available")

env_vars = dotenv_values(".env")

Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "KAI")
GroqAPIKey = os.getenv("GROQ_API_KEY") or env_vars.get("GroqAPIKey") or env_vars.get("GROQ_API_KEY", "")

client = Groq(api_key=GroqAPIKey)


def build_system_prompt(user_profile: Dict = None, memories: List = None) -> str:
    """Build personalized system prompt with user context"""
    
    # Base prompt
    base = f"""You are KAI, an advanced AI assistant with Beast Mode capabilities.

═══════════════════════════════════════════════════════════════
🔥 YOUR IDENTITY
═══════════════════════════════════════════════════════════════
• Name: KAI (Knowledge and Artificial Intelligence)
• Mode: Beast Mode 🔥 - Maximum intelligence and capability
• Personality: Friendly, confident, witty, and extremely helpful
• Creator: Built with ❤️

═══════════════════════════════════════════════════════════════
🌐 CAPABILITIES
═══════════════════════════════════════════════════════════════
✓ Real-time web search and information retrieval
✓ AI-powered image generation
✓ Music search and playback
✓ Translation (46+ languages)
✓ Mathematical calculations
✓ Document generation (PDF)
✓ Code generation and explanation
✓ Creative writing
✓ LONG-TERM MEMORY - You remember things about users!

═══════════════════════════════════════════════════════════════
💬 RESPONSE STYLE
═══════════════════════════════════════════════════════════════
1. Be CONFIDENT and PERSONABLE
2. Be HELPFUL - actually solve problems
3. Be CONCISE - get to the point
4. Use what you REMEMBER about the user to personalize responses
5. Reply in the user's preferred language when known"""

    # Add user profile context
    if user_profile:
        profile_context = f"""

═══════════════════════════════════════════════════════════════
👤 USER CONTEXT (from their profile)
═══════════════════════════════════════════════════════════════
• Name: {user_profile.get('name', 'Unknown')}
• Preferred style: {user_profile.get('responseStyle', 'casual')}
• Language preference: {user_profile.get('responseLanguage', 'English')}
• Interests: {', '.join(user_profile.get('interests', [])) or 'Not specified'}
• Bio: {user_profile.get('bio', 'Not provided')}"""
        base += profile_context

    # Add memory context
    if memories and len(memories) > 0:
        memory_context = f"""

═══════════════════════════════════════════════════════════════
🧠 YOUR MEMORIES OF THIS USER (from past conversations)
═══════════════════════════════════════════════════════════════
"""
        for mem in memories[:10]:  # Limit to 10 most relevant
            content = mem.get('content', '')[:150]  # Truncate long memories
            category = mem.get('category', 'general')
            importance = mem.get('importance', 0.5)
            memory_context += f"• [{category}] (importance: {importance:.1f}) {content}\n"
        
        memory_context += """
USE THESE MEMORIES to provide personalized, contextual responses.
Reference past conversations naturally when relevant.
DON'T explicitly say "I remember you told me..." - just use the knowledge naturally."""
        
        base += memory_context

    base += """

═══════════════════════════════════════════════════════════════
🚀 NOW GO BE AWESOME!
═══════════════════════════════════════════════════════════════
"""
    return base


def extract_memories_from_conversation(user_id: str, query: str, response: str, 
                                        session_id: str = None):
    """Extract and save important memories from the conversation"""
    if not MEMORY_AVAILABLE or not user_id:
        return
    
    try:
        # Detect memory-worthy content from user query
        memory_triggers = {
            'preference': ['i prefer', 'i like', 'i love', 'i hate', 'i enjoy', 'my favorite', 
                          'i usually', 'i always', 'i never', 'i want'],
            'personal': ['my name is', 'i am', "i'm", 'i work', 'i live', 'i have', 
                        'my job', 'my profession', 'my age', 'born in'],
            'fact': ['tell me about', 'what is', 'how does', 'explain'],
            'event': ['today', 'yesterday', 'tomorrow', 'next week', 'last month', 
                     'planning to', 'going to', 'i will'],
            'context': ['currently working on', 'my project', 'the app', 'the code', 
                       'the bug', 'the issue']
        }
        
        query_lower = query.lower()
        
        for category, triggers in memory_triggers.items():
            if any(trigger in query_lower for trigger in triggers):
                # This query contains memorable information
                importance = 0.6 if category in ['preference', 'personal'] else 0.5
                
                # Save the user's statement as a memory
                remember(user_id, query, category, importance, session_id)
                logger.info(f"[MEMORY] Saved {category} memory for user {user_id[:8]}")
                break
        
        # Also check for explicit "remember this" commands
        if any(phrase in query_lower for phrase in ['remember that', 'remember this', 
                                                     'don\'t forget', 'keep in mind']):
            remember(user_id, query, 'explicit', 0.9, session_id)
            logger.info(f"[MEMORY] Saved explicit memory for user {user_id[:8]}")
            
    except Exception as e:
        logger.error(f"[MEMORY] Failed to extract memories: {e}")


def PerUserChatBot(query: str, user_id: str, session_id: str = None, 
                   user_profile: Dict = None, chat_history: List = None) -> Dict[str, Any]:
    """
    Chat with per-user memory context.
    
    Args:
        query: User's message
        user_id: Unique user ID (REQUIRED for per-user isolation)
        session_id: Current chat session ID
        user_profile: User's profile data (name, preferences, etc.)
        chat_history: Recent chat history for context
        
    Returns:
        Dict with response and metadata
    """
    if not query or not user_id:
        return {
            "response": "I need a valid user context to respond.",
            "type": "text",
            "memory_accessed": False,
            "memory_saved": False
        }
    
    response_metadata = {
        "type": "text",
        "memory_accessed": False,
        "memory_saved": False,
        "relevant_memories": []
    }
    
    try:
        # 1. Recall relevant memories for this user
        relevant_memories = []
        cross_session_context = []
        
        if MEMORY_AVAILABLE:
            # Search for semantically similar memories
            relevant_memories = recall(user_id, query, limit=5)
            response_metadata["memory_accessed"] = len(relevant_memories) > 0
            response_metadata["relevant_memories"] = [
                {"content": m.get('content', '')[:100], "category": m.get('category')}
                for m in relevant_memories[:3]
            ]
            
            # Get cross-session context
            if session_id:
                cross_session_context = get_context(user_id, session_id, query)
                relevant_memories.extend(cross_session_context[:3])
        
        # 2. Build personalized system prompt
        system_prompt = build_system_prompt(user_profile, relevant_memories)
        
        # 3. Build messages for LLM
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add real-time info
        current_time = datetime.datetime.now()
        time_info = f"Current time: {current_time.strftime('%A, %B %d, %Y at %H:%M:%S')}"
        messages.append({"role": "system", "content": time_info})
        
        # Add recent chat history
        if chat_history:
            for msg in chat_history[-8:]:  # Last 8 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role in ['user', 'assistant'] and content:
                    messages.append({"role": role, "content": content})
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        # 4. Get LLM response with SOCIAL INTELLIGENCE 🧠
        from Backend.LLM import ChatCompletion
        
        # Use our ChatCompletion which includes social intelligence processing
        answer = ChatCompletion(
            messages=messages,
            system_prompt=None,  # Already in messages
            text_only=True,
            model="llama-3.3-70b-versatile",
            user_id=user_id,
            inject_memory=False,  # We already injected memory above
            apply_social_intelligence=False  # DISABLED - was causing canned responses on Render
        )
        
        # 5. Extract and save memories
        if MEMORY_AVAILABLE:
            extract_memories_from_conversation(user_id, query, answer, session_id)
            response_metadata["memory_saved"] = True
        
        return {
            "response": answer,
            **response_metadata
        }
        
    except Exception as e:
        logger.error(f"[CHATBOT] Error: {e}")
        return {
            "response": f"I encountered an error: {str(e)[:100]}. Let me try again.",
            "type": "error",
            "memory_accessed": False,
            "memory_saved": False
        }


def get_user_memory_summary(user_id: str) -> Dict:
    """Get a summary of what KAI remembers about a user"""
    if not MEMORY_AVAILABLE or not user_id:
        return {"total": 0, "categories": {}, "sample_memories": []}
    
    try:
        stats = per_user_memory.get_memory_stats(user_id)
        memories = per_user_memory.get_user_memories(user_id, limit=5)
        
        return {
            **stats,
            "sample_memories": [
                {"content": m.get('content', '')[:100], "category": m.get('category')}
                for m in memories
            ]
        }
    except Exception as e:
        logger.error(f"[MEMORY] Failed to get summary: {e}")
        return {"total": 0, "categories": {}, "sample_memories": [], "error": str(e)}


def clear_user_memory(user_id: str, category: str = None) -> bool:
    """Clear memories for a user (GDPR compliance)"""
    if not MEMORY_AVAILABLE or not user_id:
        return False
    
    try:
        return per_user_memory.delete_user_memories(user_id, category)
    except Exception as e:
        logger.error(f"[MEMORY] Failed to clear: {e}")
        return False


# Backwards compatible wrapper
def ChatBot(Query: str, user_id: str = "default", session_id: str = None, 
            user_profile: Dict = None) -> str:
    """Backwards-compatible wrapper that returns just the response string"""
    result = PerUserChatBot(Query, user_id, session_id, user_profile)
    return result.get("response", "Error processing request")


if __name__ == "__main__":
    # Test
    test_user = "test_user_abc123"
    test_session = "test_session_001"
    
    print("Testing Per-User Chatbot with Memory...")
    print("-" * 50)
    
    # Simulate conversation
    queries = [
        "Hi! My name is John and I'm a Python developer",
        "What's my name?",
        "I prefer dark mode and minimal interfaces",
        "What do you remember about me?",
    ]
    
    chat_history = []
    
    for query in queries:
        print(f"\nUser: {query}")
        
        result = PerUserChatBot(
            query=query,
            user_id=test_user,
            session_id=test_session,
            chat_history=chat_history
        )
        
        print(f"KAI: {result['response']}")
        print(f"[Memory accessed: {result['memory_accessed']}, saved: {result['memory_saved']}]")
        
        # Update chat history
        chat_history.append({"role": "user", "content": query})
        chat_history.append({"role": "assistant", "content": result['response']})
    
    # Show memory summary
    print("\n" + "=" * 50)
    print("Memory Summary:")
    summary = get_user_memory_summary(test_user)
    print(f"Total memories: {summary.get('total', 0)}")
    print(f"Categories: {summary.get('categories', {})}")
    print("Sample memories:", summary.get('sample_memories', []))
