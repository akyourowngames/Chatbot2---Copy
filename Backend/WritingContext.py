"""
Writing Context - Per-User Writing Memory for Continuity
=========================================================
Lightweight in-memory storage to track the most recent writing output
per user session, enabling natural continuation and refinement.

Features:
- Save what Kai wrote (content, type, destination)
- Retrieve context for continuation requests
- Auto-expire old context (configurable TTL)
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import threading

# ==================== CONFIGURATION ====================

# How long to keep writing context (default: 30 minutes)
CONTEXT_TTL_MINUTES = 30

# Maximum content length to store (prevents memory bloat)
MAX_CONTENT_LENGTH = 50000

# ==================== STORAGE ====================

# Thread-safe in-memory storage
_writing_contexts: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()


# ==================== PUBLIC API ====================

def save_writing(
    user_id: str,
    content: str,
    content_type: str = "direct",
    destination: str = "chat",
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Save the most recent writing output for a user.
    
    Args:
        user_id: The user's ID (or "anonymous")
        content: The full text that was generated/written
        content_type: Type of content ("poem", "letter", "paragraph", "story", "reflection", "direct")
        destination: Where it was sent ("chat" or "notepad")
        metadata: Optional extra info (topic, title, etc.)
    
    Returns:
        True if saved successfully
    """
    if not user_id or not content:
        return False
    
    # Truncate if too long
    if len(content) > MAX_CONTENT_LENGTH:
        content = content[:MAX_CONTENT_LENGTH]
    
    context = {
        "content": content,
        "content_type": content_type,
        "destination": destination,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {}
    }
    
    with _lock:
        _writing_contexts[user_id] = context
        _cleanup_expired()
    
    print(f"[WRITING_CONTEXT] Saved {len(content)} chars ({content_type}) for user {user_id[:8] if len(user_id) > 8 else user_id}...")
    return True


def get_last_writing(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the most recent writing context for a user.
    
    Args:
        user_id: The user's ID
    
    Returns:
        Dict with content, content_type, destination, timestamp, metadata
        or None if no context exists or it's expired
    """
    if not user_id:
        return None
    
    with _lock:
        context = _writing_contexts.get(user_id)
        
        if not context:
            return None
        
        # Check if expired
        timestamp = datetime.fromisoformat(context["timestamp"])
        if datetime.now() - timestamp > timedelta(minutes=CONTEXT_TTL_MINUTES):
            # Expired, remove it
            del _writing_contexts[user_id]
            return None
        
        return context.copy()


def clear_writing(user_id: str) -> bool:
    """
    Clear writing context for a user (privacy/reset).
    
    Args:
        user_id: The user's ID
    
    Returns:
        True if context was cleared
    """
    with _lock:
        if user_id in _writing_contexts:
            del _writing_contexts[user_id]
            print(f"[WRITING_CONTEXT] Cleared context for user {user_id[:8] if len(user_id) > 8 else user_id}...")
            return True
    return False


def get_context_summary(user_id: str) -> Optional[str]:
    """
    Get a brief summary of what was last written (for debugging/display).
    
    Returns:
        A short description like "poem (256 chars, 5 min ago)"
    """
    context = get_last_writing(user_id)
    if not context:
        return None
    
    timestamp = datetime.fromisoformat(context["timestamp"])
    age_minutes = int((datetime.now() - timestamp).total_seconds() / 60)
    
    content_preview = context["content"][:50].replace("\n", " ")
    if len(context["content"]) > 50:
        content_preview += "..."
    
    return f"{context['content_type']} ({len(context['content'])} chars, {age_minutes}m ago): \"{content_preview}\""


# ==================== INTERNAL HELPERS ====================

def _cleanup_expired():
    """Remove expired contexts (called within lock)."""
    now = datetime.now()
    expired_users = []
    
    for user_id, context in _writing_contexts.items():
        timestamp = datetime.fromisoformat(context["timestamp"])
        if now - timestamp > timedelta(minutes=CONTEXT_TTL_MINUTES):
            expired_users.append(user_id)
    
    for user_id in expired_users:
        del _writing_contexts[user_id]
    
    if expired_users:
        print(f"[WRITING_CONTEXT] Cleaned up {len(expired_users)} expired contexts")


# ==================== DEBUG ====================

def get_all_contexts_debug() -> Dict[str, Any]:
    """Get all contexts (for debugging only)."""
    with _lock:
        return {
            user_id: {
                "content_type": ctx["content_type"],
                "destination": ctx["destination"],
                "content_length": len(ctx["content"]),
                "timestamp": ctx["timestamp"],
                "topic": ctx.get("metadata", {}).get("topic", "N/A")
            }
            for user_id, ctx in _writing_contexts.items()
        }


if __name__ == "__main__":
    # Quick test
    save_writing("test-user", "Roses are red\nViolets are blue", "poem", "chat", {"topic": "love"})
    print(get_context_summary("test-user"))
    print(get_last_writing("test-user"))
