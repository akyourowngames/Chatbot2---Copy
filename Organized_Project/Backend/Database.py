"""
SQLite Database Manager for JARVIS
===================================
Handles conversation history, preferences, file metadata, and analytics
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Store in Data directory
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "jarvis.db")
        
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    
    def init_database(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                workspace TEXT DEFAULT 'default'
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)
        
        # User preferences
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # File uploads
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                filepath TEXT,
                file_type TEXT,
                size_bytes INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                analysis_result TEXT
            )
        """)
        
        # Analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                event_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics(event_type)")
        
        conn.commit()
        conn.close()
        
        print(f"[DATABASE] Initialized at {self.db_path}")
    
    # ==================== CONVERSATIONS ====================
    
    def create_conversation(self, title: str = "New Conversation", workspace: str = "default") -> int:
        """Create a new conversation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations (title, workspace)
            VALUES (?, ?)
        """, (title, workspace))
        
        conversation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return conversation_id
    
    def get_conversations(self, workspace: str = "default", limit: int = 50) -> List[Dict]:
        """Get all conversations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.*, COUNT(m.id) as message_count
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE c.workspace = ?
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            LIMIT ?
        """, (workspace, limit))
        
        conversations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return conversations
    
    def get_conversation(self, conversation_id: int) -> Optional[Dict]:
        """Get a specific conversation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def update_conversation(self, conversation_id: int, title: str = None):
        """Update conversation title"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if title:
            cursor.execute("""
                UPDATE conversations 
                SET title = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (title, conversation_id))
        
        conn.commit()
        conn.close()
    
    def delete_conversation(self, conversation_id: int):
        """Delete a conversation and its messages"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        
        conn.commit()
        conn.close()
    
    # ==================== MESSAGES ====================
    
    def add_message(self, conversation_id: int, role: str, content: str, metadata: Dict = None) -> int:
        """Add a message to a conversation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute("""
            INSERT INTO messages (conversation_id, role, content, metadata)
            VALUES (?, ?, ?, ?)
        """, (conversation_id, role, content, metadata_json))
        
        message_id = cursor.lastrowid
        
        # Update conversation timestamp
        cursor.execute("""
            UPDATE conversations 
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (conversation_id,))
        
        conn.commit()
        conn.close()
        
        return message_id
    
    def get_messages(self, conversation_id: int, limit: int = 100) -> List[Dict]:
        """Get messages for a conversation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM messages
            WHERE conversation_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        """, (conversation_id, limit))
        
        messages = []
        for row in cursor.fetchall():
            msg = dict(row)
            if msg['metadata']:
                msg['metadata'] = json.loads(msg['metadata'])
            messages.append(msg)
        
        conn.close()
        return messages
    
    def search_messages(self, query: str, workspace: str = "default", limit: int = 20) -> List[Dict]:
        """Search messages by content"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.*, c.title as conversation_title
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.workspace = ? AND m.content LIKE ?
            ORDER BY m.timestamp DESC
            LIMIT ?
        """, (workspace, f"%{query}%", limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    # ==================== PREFERENCES ====================
    
    def set_preference(self, key: str, value: Any):
        """Set a user preference"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        value_json = json.dumps(value)
        
        cursor.execute("""
            INSERT OR REPLACE INTO preferences (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value_json))
        
        conn.commit()
        conn.close()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row['value'])
        return default
    
    def get_all_preferences(self) -> Dict:
        """Get all preferences"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT key, value FROM preferences")
        prefs = {row['key']: json.loads(row['value']) for row in cursor.fetchall()}
        conn.close()
        
        return prefs
    
    # ==================== FILE UPLOADS ====================
    
    def add_file_upload(self, filename: str, filepath: str, file_type: str, 
                       size_bytes: int, analysis_result: Dict = None) -> int:
        """Record a file upload"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        analysis_json = json.dumps(analysis_result) if analysis_result else None
        
        cursor.execute("""
            INSERT INTO file_uploads (filename, filepath, file_type, size_bytes, analysis_result)
            VALUES (?, ?, ?, ?, ?)
        """, (filename, filepath, file_type, size_bytes, analysis_json))
        
        file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return file_id
    
    def get_file_uploads(self, limit: int = 50) -> List[Dict]:
        """Get recent file uploads"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM file_uploads
            ORDER BY uploaded_at DESC
            LIMIT ?
        """, (limit,))
        
        files = []
        for row in cursor.fetchall():
            file_data = dict(row)
            if file_data['analysis_result']:
                file_data['analysis_result'] = json.loads(file_data['analysis_result'])
            files.append(file_data)
        
        conn.close()
        return files
    
    # ==================== ANALYTICS ====================
    
    def track_event(self, event_type: str, event_data: Dict = None):
        """Track an analytics event"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        data_json = json.dumps(event_data) if event_data else None
        
        cursor.execute("""
            INSERT INTO analytics (event_type, event_data)
            VALUES (?, ?)
        """, (event_type, data_json))
        
        conn.commit()
        conn.close()
    
    def get_analytics(self, event_type: str = None, days: int = 7) -> List[Dict]:
        """Get analytics data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if event_type:
            cursor.execute("""
                SELECT * FROM analytics
                WHERE event_type = ? 
                AND timestamp >= datetime('now', '-' || ? || ' days')
                ORDER BY timestamp DESC
            """, (event_type, days))
        else:
            cursor.execute("""
                SELECT * FROM analytics
                WHERE timestamp >= datetime('now', '-' || ? || ' days')
                ORDER BY timestamp DESC
            """, (days,))
        
        events = []
        for row in cursor.fetchall():
            event = dict(row)
            if event['event_data']:
                event['event_data'] = json.loads(event['event_data'])
            events.append(event)
        
        conn.close()
        return events
    
    def get_analytics_summary(self, days: int = 7) -> Dict:
        """Get analytics summary"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                event_type,
                COUNT(*) as count
            FROM analytics
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY event_type
            ORDER BY count DESC
        """, (days,))
        
        summary = {row['event_type']: row['count'] for row in cursor.fetchall()}
        conn.close()
        
        return summary

# Global instance
db = Database()

if __name__ == "__main__":
    print("Testing Database...")
    
    # Test conversation
    conv_id = db.create_conversation("Test Conversation")
    print(f"Created conversation: {conv_id}")
    
    # Test messages
    db.add_message(conv_id, "user", "Hello JARVIS!")
    db.add_message(conv_id, "assistant", "Hello! How can I help?")
    
    messages = db.get_messages(conv_id)
    print(f"Messages: {len(messages)}")
    
    # Test preferences
    db.set_preference("theme", "dark")
    theme = db.get_preference("theme")
    print(f"Theme: {theme}")
    
    # Test analytics
    db.track_event("command_used", {"command": "test"})
    summary = db.get_analytics_summary()
    print(f"Analytics: {summary}")
    
    print("Database tests complete!")
