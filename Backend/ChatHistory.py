"""
Chat History Manager - Firebase-Backed Persistent Storage
==========================================================
Saves and loads chat history with Firebase persistence
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Import Firebase DAL
try:
    from Backend.FirebaseDAL import FirebaseDAL
    from Backend.FirebaseStorage import get_firebase_storage
    firebase_available = True
except ImportError:
    firebase_available = False
    logging.warning("[CHAT HISTORY] Firebase not available, using fallback mode")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatHistoryManager:
    """Firebase-backed chat history manager"""
    
    def __init__(self):
        """Initialize chat history manager"""
        if firebase_available:
            storage = get_firebase_storage()
            self.dal = FirebaseDAL(storage.db) if storage.db else None
        else:
            self.dal = None
        
        self.conversations_collection = "conversations"
        self.messages_collection = "messages"
        logger.info("[CHAT HISTORY] Chat history manager initialized")
    
    # ==================== CONVERSATION MANAGEMENT ====================
    
    def create_conversation(self, user_id: str, title: str = "New Conversation") -> Optional[str]:
        """
        Create a new conversation
        
        Args:
            user_id: User's unique identifier
            title: Conversation title
            
        Returns:
            Conversation ID if successful, None otherwise
        """
        try:
            if not self.dal:
                return None
            
            conversation_data = {
                "title": title,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            conv_id = self.dal.create(self.conversations_collection, user_id, conversation_data)
            
            if conv_id:
                logger.info(f"[CHAT HISTORY] Created conversation {conv_id} for user {user_id}")
            
            return conv_id
            
        except Exception as e:
            logger.error(f"[CHAT HISTORY] Create conversation error: {e}")
            return None
    
    def get_conversations(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all conversations for a user
        
        Args:
            user_id: User's unique identifier
            limit: Maximum number of conversations
            
        Returns:
            List of conversation dictionaries
        """
        try:
            if not self.dal:
                return []
            
            conversations = self.dal.list(
                self.conversations_collection,
                user_id,
                limit=limit,
                order_by="updated_at",
                descending=True
            )
            
            return conversations
            
        except Exception as e:
            logger.error(f"[CHAT HISTORY] Get conversations error: {e}")
            return []
    
    def get_conversation(self, user_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific conversation with its messages
        
        Args:
            user_id: User's unique identifier
            conversation_id: Conversation ID
            
        Returns:
            Conversation dictionary with messages
        """
        try:
            if not self.dal:
                return None
            
            # Get conversation
            conversation = self.dal.get(self.conversations_collection, user_id, conversation_id)
            
            if not conversation:
                return None
            
            # Get messages for this conversation
            messages = self.get_messages(user_id, conversation_id)
            conversation["messages"] = messages
            
            return conversation
            
        except Exception as e:
            logger.error(f"[CHAT HISTORY] Get conversation error: {e}")
            return None
    
    def update_conversation_title(self, user_id: str, conversation_id: str, title: str) -> bool:
        """
        Update conversation title
        
        Args:
            user_id: User's unique identifier
            conversation_id: Conversation ID
            title: New title
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.dal:
                return False
            
            return self.dal.update(
                self.conversations_collection,
                user_id,
                conversation_id,
                {"title": title, "updated_at": datetime.utcnow()}
            )
            
        except Exception as e:
            logger.error(f"[CHAT HISTORY] Update conversation error: {e}")
            return False
    
    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """
        Delete a conversation and all its messages safely
        
        Args:
            user_id: User's unique identifier
            conversation_id: Conversation ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.dal:
                return False
            
            # 1. Delete all messages first (to avoid orphans)
            messages = self.get_messages(user_id, conversation_id, limit=1000)
            for msg in messages:
                self.dal.delete(self.messages_collection, user_id, msg["id"])
            
            # 2. Delete conversation document
            success = self.dal.delete(self.conversations_collection, user_id, conversation_id)
            
            if success:
                logger.info(f"[CHAT HISTORY] Deleted conversation {conversation_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"[CHAT HISTORY] Delete conversation error: {e}")
            return False

    def delete_all_conversations(self, user_id: str) -> bool:
        """
        Delete ALL conversations for a user (Bulk Delete)
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.dal:
                return False
            
            # 1. Get all conversations
            conversations = self.get_conversations(user_id, limit=1000)
            
            success_count = 0
            for conv in conversations:
                if self.delete_conversation(user_id, conv["id"]):
                    success_count += 1
            
            logger.info(f"[CHAT HISTORY] Bulk deleted {success_count} conversations for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"[CHAT HISTORY] Bulk delete error: {e}")
            return False
    
    # ==================== MESSAGE MANAGEMENT ====================
    
    def add_message(self, user_id: str, conversation_id: str, role: str, content: str, 
                   metadata: Optional[Dict] = None) -> bool:
        """
        Add a message to a conversation
        
        Args:
            user_id: User's unique identifier
            conversation_id: Conversation ID
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.dal:
                return False
            
            message_data = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow(),
                "metadata": metadata or {},
                "conversation_id": conversation_id
            }
            
            message_id = self.dal.create(self.messages_collection, user_id, message_data)
            
            if message_id:
                # Update conversation's updated_at timestamp
                self.dal.update(
                    self.conversations_collection,
                    user_id,
                    conversation_id,
                    {"updated_at": datetime.utcnow()}
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"[CHAT HISTORY] Add message error: {e}")
            return False
    
    def get_messages(self, user_id: str, conversation_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all messages for a conversation
        
        Args:
            user_id: User's unique identifier
            conversation_id: Conversation ID
            limit: Maximum number of messages
            
        Returns:
            List of message dictionaries
        """
        try:
            if not self.dal:
                return []
            
            # Retrieve messages with filter but WITHOUT ordering (to avoid composite index requirement)
            messages = self.dal.list(
                self.messages_collection,
                user_id,
                limit=limit,
                # order_by="timestamp",  <-- Removed to avoid index error
                # descending=False,      <-- Removed
                filters={"conversation_id": conversation_id}
            )
            
            # Sort in-memory
            messages.sort(key=lambda x: x.get("timestamp", ""))
            
            return messages
            
        except Exception as e:
            logger.error(f"[CHAT HISTORY] Get messages error: {e}")
            return []
    
    # ==================== BACKWARD COMPATIBILITY ====================
    
    def load_history(self):
        """Backward compatibility - no-op for Firebase"""
        logger.info("[CHAT HISTORY] Using Firebase - no local file to load")
    
    def save_history(self):
        """Backward compatibility - no-op for Firebase"""
        logger.info("[CHAT HISTORY] Using Firebase - auto-saved")
    
    def get_session(self, session_id: str, user_id: str = "default") -> Dict:
        """
        Get session (backward compatible)
        
        Args:
            session_id: Session/conversation ID
            user_id: User ID
            
        Returns:
            Session dictionary with messages
        """
        conversation = self.get_conversation(user_id, session_id)
        if not conversation:
            return {"messages": []}
        return conversation
    
    def get_all_sessions(self, user_id: str = "default") -> Dict:
        """
        Get all sessions (backward compatible)
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary of sessions
        """
        conversations = self.get_conversations(user_id)
        sessions = {}
        for conv in conversations:
            sessions[conv["id"]] = conv
        return sessions
    
    def clear_all(self, user_id: str = "default"):
        """
        Clear all history for a user
        
        Args:
            user_id: User ID
        """
        conversations = self.get_conversations(user_id, limit=1000)
        for conv in conversations:
            self.delete_conversation(user_id, conv["id"])
        logger.info(f"[CHAT HISTORY] Cleared all history for user {user_id}")


# Global instance
chat_history = ChatHistoryManager()


# ==================== TESTING ====================

if __name__ == "__main__":
    print("💬 Testing Chat History Manager\n")
    
    test_user_id = "test_user_123"
    
    # Test create conversation
    print("1. Creating conversation:")
    conv_id = chat_history.create_conversation(test_user_id, "Test Chat")
    print(f"   Created conversation: {conv_id}")
    
    # Test add messages
    print("\n2. Adding messages:")
    chat_history.add_message(test_user_id, conv_id, "user", "Hello!")
    chat_history.add_message(test_user_id, conv_id, "assistant", "Hi there!")
    print("   Added 2 messages")
    
    # Test get conversation
    print("\n3. Getting conversation:")
    conversation = chat_history.get_conversation(test_user_id, conv_id)
    if conversation:
        print(f"   Title: {conversation['title']}")
        print(f"   Messages: {len(conversation['messages'])}")
    
    print("\n✅ Chat history tests completed!")

