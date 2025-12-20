"""
Supabase Database Wrapper for JARVIS
=====================================
Cloud database with real-time sync
"""

from supabase import create_client, Client
# Import realtime sync helper (optional - may not be available on all deployments)
try:
    from Backend.RealtimeSync import get_realtime_sync
except ImportError:
    get_realtime_sync = None
import os
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseDB:
    def __init__(self):
        """Initialize Supabase connection"""
        url = os.getenv("SUPABASE_URL", "https://skbfmcwrshxnmaxfqyaw.supabase.co")
        # Check both possible env var names for the key
        key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "sb_secret_kT3r_lTsBYBLwpv313A0qQ_przZ-Q8v"
        
        if not url or not key:
            raise ValueError("Supabase credentials missing in environment")
        
        try:
            self.client: Client = create_client(url, key)
            logger.info("[SUPABASE] Connected successfully")
        except Exception as e:
            logger.error(f"[SUPABASE] Connection failed: {e}")
            raise
    
    # ==================== CONVERSATIONS ====================
    
    def create_conversation(self, title, workspace='default'):
        """Create a new conversation"""
        try:
            data = self.client.table('conversations').insert({
                'title': title,
                'workspace': workspace
            }).execute()
            
            if data.data:
                logger.info(f"[SUPABASE] Created conversation: {data.data[0]['id']}")
                return data.data[0]['id']
            return None
        except Exception as e:
            logger.error(f"[SUPABASE] Create conversation error: {e}")
            return None
    
    def get_conversations(self, workspace='default', limit=50):
        """Get all conversations for a workspace"""
        try:
            data = self.client.table('conversations')\
                .select('*')\
                .eq('workspace', workspace)\
                .order('updated_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return data.data if data.data else []
        except Exception as e:
            logger.error(f"[SUPABASE] Get conversations error: {e}")
            return []
    
    def get_conversation(self, conversation_id):
        """Get a specific conversation with messages"""
        try:
            # Get conversation
            conv_data = self.client.table('conversations')\
                .select('*')\
                .eq('id', conversation_id)\
                .execute()
            
            if not conv_data.data:
                return None
            
            conversation = conv_data.data[0]
            
            # Get messages
            messages = self.get_messages(conversation_id)
            conversation['messages'] = messages
            
            return conversation
        except Exception as e:
            logger.error(f"[SUPABASE] Get conversation error: {e}")
            return None
    
    def update_conversation(self, conversation_id, title):
        """Update conversation title"""
        try:
            self.client.table('conversations')\
                .update({'title': title, 'updated_at': datetime.now().isoformat()})\
                .eq('id', conversation_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"[SUPABASE] Update conversation error: {e}")
            return False
    
    def delete_conversation(self, conversation_id):
        """Delete a conversation (cascades to messages)"""
        try:
            self.client.table('conversations')\
                .delete()\
                .eq('id', conversation_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"[SUPABASE] Delete conversation error: {e}")
            return False
    
    # ==================== MESSAGES ====================
    
    def add_message(self, conversation_id, role, content, metadata=None):
        """Add a message to a conversation"""
        try:
            self.client.table('messages').insert({
                'conversation_id': conversation_id,
                'role': role,
                'content': content,
                'metadata': json.dumps(metadata or {})
            }).execute()
            
            # Update conversation timestamp
            self.client.table('conversations')\
                .update({'updated_at': datetime.now().isoformat()})\
                .eq('id', conversation_id)\
                .execute()
            
            # Broadcast the new message via realtime sync to all connected clients
            realtime = get_realtime_sync()
            if realtime:
                try:
                    data = {
                        "type": "added",
                        "collection": "messages",
                        "conversation_id": conversation_id,
                        "role": role,
                        "content": content,
                        "metadata": metadata or {}
                    }
                    # Send to all users currently connected
                    for uid in list(realtime.connected_clients.keys()):
                        realtime._broadcast_to_user(user_id=uid, data=data)
                except Exception as e:
                    logger.error(f"[SUPABASE] Realtime broadcast error: {e}")

            return True
        except Exception as e:
            logger.error(f"[SUPABASE] Add message error: {e}")
            return False
    
    def get_messages(self, conversation_id, limit=100):
        """Get messages for a conversation"""
        try:
            data = self.client.table('messages')\
                .select('*')\
                .eq('conversation_id', conversation_id)\
                .order('created_at', desc=False)\
                .limit(limit)\
                .execute()
            
            return data.data if data.data else []
        except Exception as e:
            logger.error(f"[SUPABASE] Get messages error: {e}")
            return []
    
    def search_messages(self, query, limit=20):
        """Search messages by content"""
        try:
            data = self.client.table('messages')\
                .select('*, conversations(*)')\
                .ilike('content', f'%{query}%')\
                .limit(limit)\
                .execute()
            
            return data.data if data.data else []
        except Exception as e:
            logger.error(f"[SUPABASE] Search messages error: {e}")
            return []
    
    # ==================== PREFERENCES ====================
    
    def set_preference(self, key, value):
        """Set a user preference"""
        try:
            # Upsert (insert or update)
            self.client.table('preferences').upsert({
                'key': key,
                'value': str(value),
                'updated_at': datetime.now().isoformat()
            }).execute()
            return True
        except Exception as e:
            logger.error(f"[SUPABASE] Set preference error: {e}")
            return False
    
    def get_preference(self, key, default=None):
        """Get a user preference"""
        try:
            data = self.client.table('preferences')\
                .select('value')\
                .eq('key', key)\
                .execute()
            
            if data.data:
                return data.data[0]['value']
            return default
        except Exception as e:
            logger.error(f"[SUPABASE] Get preference error: {e}")
            return default
    
    def get_all_preferences(self):
        """Get all preferences"""
        try:
            data = self.client.table('preferences').select('*').execute()
            return {item['key']: item['value'] for item in data.data} if data.data else {}
        except Exception as e:
            logger.error(f"[SUPABASE] Get all preferences error: {e}")
            return {}
    
    # ==================== FILE UPLOADS ====================
    
    def log_file_upload(self, filename, filepath, file_type, size_bytes, analysis_result=None):
        """Log a file upload"""
        try:
            self.client.table('file_uploads').insert({
                'filename': filename,
                'filepath': filepath,
                'file_type': file_type,
                'size_bytes': size_bytes,
                'analysis_result': json.dumps(analysis_result or {})
            }).execute()
            return True
        except Exception as e:
            logger.error(f"[SUPABASE] Log file upload error: {e}")
            return False
    
    def get_file_history(self, limit=20):
        """Get file upload history"""
        try:
            data = self.client.table('file_uploads')\
                .select('*')\
                .order('uploaded_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return data.data if data.data else []
        except Exception as e:
            logger.error(f"[SUPABASE] Get file history error: {e}")
            return []
    
    # ==================== SUPABASE STORAGE ====================
    
    def upload_file(self, file_path: str, storage_path: str, bucket: str = 'kai-files', content_type: str = None) -> str:
        """
        Upload a file to Supabase Storage
        
        Args:
            file_path: Local file path to upload
            storage_path: Path in storage bucket (e.g., 'documents/report.pdf')
            bucket: Storage bucket name (default: 'kai-files')
            content_type: MIME type (auto-detected if None)
            
        Returns:
            Public URL of uploaded file, or None if failed
        """
        try:
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Auto-detect content type if not provided
            if not content_type:
                ext = os.path.splitext(file_path)[1].lower()
                content_type_map = {
                    '.pdf': 'application/pdf',
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp',
                    '.mp4': 'video/mp4',
                    '.txt': 'text/plain',
                    '.json': 'application/json'
                }
                content_type = content_type_map.get(ext, 'application/octet-stream')
            
            # Upload to storage
            try:
                response = self.client.storage.from_(bucket).upload(
                    path=storage_path,
                    file=file_data,
                    file_options={"content-type": content_type, "upsert": "true"}
                )
                
                # Get public URL
                public_url = self.client.storage.from_(bucket).get_public_url(storage_path)
                
                logger.info(f"[SUPABASE] Uploaded file to: {public_url}")
                return public_url
                
            except Exception as storage_error:
                # If bucket doesn't exist, try to create it
                if "not found" in str(storage_error).lower() or "does not exist" in str(storage_error).lower():
                    logger.info(f"[SUPABASE] Bucket '{bucket}' doesn't exist, creating...")
                    try:
                        self.client.storage.create_bucket(bucket, public=True)
                        logger.info(f"[SUPABASE] Created bucket: {bucket}")
                        
                        # Retry upload
                        response = self.client.storage.from_(bucket).upload(
                            path=storage_path,
                            file=file_data,
                            file_options={"content-type": content_type, "upsert": "true"}
                        )
                        public_url = self.client.storage.from_(bucket).get_public_url(storage_path)
                        logger.info(f"[SUPABASE] Uploaded file to: {public_url}")
                        return public_url
                    except Exception as create_error:
                        logger.error(f"[SUPABASE] Bucket creation failed: {create_error}")
                        raise
                else:
                    raise
                    
        except Exception as e:
            logger.error(f"[SUPABASE] File upload error: {e}")
            return None
    
    def upload_pdf(self, file_path: str, folder: str = 'documents') -> str:
        """
        Upload PDF to Supabase Storage
        
        Args:
            file_path: Local PDF file path
            folder: Folder name in storage (documents/captures)
            
        Returns:
            Public URL of uploaded PDF
        """
        filename = os.path.basename(file_path)
        storage_path = f"{folder}/{filename}"
        # detailed: Use 'kai-files' bucket instead of 'kai-pdfs'
        return self.upload_file(file_path, storage_path, bucket='kai-files', content_type='application/pdf')
    
    def upload_image(self, file_path: str, folder: str = 'generated') -> str:
        """
        Upload image to Supabase Storage
        
        Args:
            file_path: Local image file path
            folder: Folder name in storage
            
        Returns:
            Public URL of uploaded image
        """
        filename = os.path.basename(file_path)
        storage_path = f"{folder}/{filename}"
        
        # Auto-detect image type
        ext = os.path.splitext(file_path)[1].lower()
        content_type = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }.get(ext, 'image/png')
        
        # detailed: Use 'kai-files' bucket instead of 'kai-images'
        return self.upload_file(file_path, storage_path, bucket='kai-files', content_type=content_type)
    
    # ==================== ANALYTICS ====================
    
    def track_event(self, event_type, event_data=None):
        """Track an analytics event"""
        try:
            self.client.table('analytics').insert({
                'event_type': event_type,
                'event_data': json.dumps(event_data or {})
            }).execute()
            return True
        except Exception as e:
            logger.error(f"[SUPABASE] Track event error: {e}")
            return False
    
    def get_analytics(self, event_type=None, days=7):
        """Get analytics data"""
        try:
            query = self.client.table('analytics').select('*')
            
            if event_type:
                query = query.eq('event_type', event_type)
            
            # Filter by date
            from_date = (datetime.now() - timedelta(days=days)).isoformat()
            query = query.gte('created_at', from_date)
            
            data = query.order('created_at', desc=True).execute()
            return data.data if data.data else []
        except Exception as e:
            logger.error(f"[SUPABASE] Get analytics error: {e}")
            return []
    
    def get_analytics_summary(self, days=7):
        """Get analytics summary"""
        try:
            from_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            data = self.client.table('analytics')\
                .select('event_type')\
                .gte('created_at', from_date)\
                .execute()
            
            if not data.data:
                return {}
            
            # Count events by type
            summary = {}
            for item in data.data:
                event_type = item['event_type']
                summary[event_type] = summary.get(event_type, 0) + 1
            
            return summary
        except Exception as e:
            logger.error(f"[SUPABASE] Get analytics summary error: {e}")
            return {}
    
    # ==================== WHATSAPP CONTACTS ====================
    
    def add_contact(self, name, phone):
        """Add a WhatsApp contact"""
        try:
            self.client.table('whatsapp_contacts').insert({
                'name': name,
                'phone': phone
            }).execute()
            logger.info(f"[SUPABASE] Added contact: {name}")
            return True
        except Exception as e:
            logger.error(f"[SUPABASE] Add contact error: {e}")
            return False
    
    def get_contact_by_name(self, name):
        """Get contact by name (case-insensitive)"""
        try:
            data = self.client.table('whatsapp_contacts')\
                .select('*')\
                .ilike('name', f'%{name}%')\
                .limit(1)\
                .execute()
            
            return data.data[0] if data.data else None
        except Exception as e:
            logger.error(f"[SUPABASE] Get contact error: {e}")
            return None
    
    def get_all_contacts(self):
        """Get all WhatsApp contacts"""
        try:
            data = self.client.table('whatsapp_contacts')\
                .select('*')\
                .order('name')\
                .execute()
            
            return data.data if data.data else []
        except Exception as e:
            logger.error(f"[SUPABASE] Get all contacts error: {e}")
            return []
    
    # ==================== WHATSAPP MESSAGES ====================
    
    def log_whatsapp_message(self, phone, message, contact_id=None, message_type='text', status='sent'):
        """Log a WhatsApp message"""
        try:
            self.client.table('whatsapp_messages').insert({
                'contact_id': contact_id,
                'phone': phone,
                'message': message,
                'message_type': message_type,
                'status': status
            }).execute()
            return True
        except Exception as e:
            logger.error(f"[SUPABASE] Log WhatsApp message error: {e}")
            return False
    
    def get_whatsapp_history(self, phone=None, limit=50):
        """Get WhatsApp message history"""
        try:
            query = self.client.table('whatsapp_messages').select('*, whatsapp_contacts(*)')
            
            if phone:
                query = query.eq('phone', phone)
            
            data = query.order('sent_at', desc=True).limit(limit).execute()
            return data.data if data.data else []
        except Exception as e:
            logger.error(f"[SUPABASE] Get WhatsApp history error: {e}")
            return []

# Import timedelta for analytics
from datetime import timedelta

# Global instance
try:
    supabase_db = SupabaseDB()
except Exception as e:
    logger.error(f"[SUPABASE] Failed to initialize: {e}")
    with open("debug_supabase_init.txt", "a") as f:
        f.write(f"[Init Fail] {e}\n")
    supabase_db = None

if __name__ == "__main__":
    # Test connection
    if supabase_db:
        print("✅ Supabase connected!")
        
        # Test conversation
        conv_id = supabase_db.create_conversation("Test Conversation")
        if conv_id:
            print(f"✅ Created conversation: {conv_id}")
            
            # Test message
            supabase_db.add_message(conv_id, "user", "Hello Supabase!")
            print("✅ Added message")
            
            # Test preference
            supabase_db.set_preference("theme", "dark")
            theme = supabase_db.get_preference("theme")
            print(f"✅ Preference: {theme}")
    else:
        print("❌ Supabase connection failed")
