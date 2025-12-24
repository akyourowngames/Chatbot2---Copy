"""
Supabase Database Wrapper for JARVIS
=====================================
Cloud database with real-time sync
"""

from supabase import create_client, Client
# Import realtime sync helper
from Backend.RealtimeSync import get_realtime_sync
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
        key = os.getenv("SUPABASE_KEY", "sb_secret_kT3r_lTsBYBLwpv313A0qQ_przZ-Q8v")
        
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
    
    def upload_pdf(self, file_path: str, folder: str = 'documents', user_id: str = None) -> str:
        """
        Upload PDF to Supabase Storage
        
        Args:
            file_path: Local PDF file path
            folder: Folder name in storage (documents/captures)
            user_id: Optional user ID for user-specific storage
            
        Returns:
            Public URL of uploaded PDF
        """
        filename = os.path.basename(file_path)
        # Use user-specific path if user_id provided
        if user_id:
            storage_path = f"{user_id}/{folder}/{filename}"
        else:
            storage_path = f"{folder}/{filename}"
        return self.upload_file(file_path, storage_path, bucket='kai-images', content_type='application/pdf')
    
    def upload_image(self, file_path: str, folder: str = 'generated', user_id: str = None) -> str:
        """
        Upload image to Supabase Storage
        
        Args:
            file_path: Local image file path
            folder: Folder name in storage
            user_id: Optional user ID for user-specific storage
            
        Returns:
            Public URL of uploaded image
        """
        filename = os.path.basename(file_path)
        # Use user-specific path if user_id provided
        if user_id:
            storage_path = f"{user_id}/{folder}/{filename}"
        else:
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
        
        return self.upload_file(file_path, storage_path, bucket='kai-images', content_type=content_type)
    
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
    
    # ==================== KAI MEMORIES (PERSISTENT) ====================
    
    def save_memory(self, content: str, category: str = "general", 
                    importance: float = 0.5, metadata: dict = None, 
                    user_id: str = "default") -> bool:
        """
        Save a memory to Supabase for persistence.
        
        Args:
            content: The memory content
            category: Category (personal, work, preference, etc.)
            importance: Importance score 0-1
            metadata: Additional metadata
            user_id: User identifier
            
        Returns:
            True if saved successfully
        """
        try:
            # Check for duplicate using content similarity
            existing = self.search_memories(content, user_id, limit=1)
            if existing and self._is_similar(existing[0].get('content', ''), content):
                # Update existing instead
                self.client.table('kai_memories').update({
                    'importance': max(existing[0].get('importance', 0.5), importance),
                    'access_count': existing[0].get('access_count', 0) + 1,
                    'last_accessed': datetime.now().isoformat()
                }).eq('id', existing[0]['id']).execute()
                logger.info(f"[MEMORY] Updated existing: {content[:50]}...")
                return True
            
            # Insert new memory
            self.client.table('kai_memories').insert({
                'user_id': user_id,
                'content': content,
                'category': category,
                'importance': importance,
                'metadata': json.dumps(metadata or {}),
                'access_count': 0,
                'last_accessed': datetime.now().isoformat()
            }).execute()
            
            logger.info(f"[MEMORY] Saved: {content[:50]}... (category: {category})")
            return True
            
        except Exception as e:
            error_str = str(e).lower()
            # Auto-create table if it doesn't exist
            if "relation" in error_str and "does not exist" in error_str:
                logger.info("[MEMORY] Table doesn't exist, creating kai_memories...")
                if self._create_memories_table():
                    return self.save_memory(content, category, importance, metadata, user_id)
            logger.error(f"[MEMORY] Save error: {e}")
            return False
    
    def _is_similar(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Check text similarity for deduplication"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return False
        overlap = len(words1.intersection(words2))
        max_len = max(len(words1), len(words2))
        return (overlap / max_len) >= threshold
    
    def _create_memories_table(self) -> bool:
        """Create kai_memories table via RPC or direct SQL"""
        try:
            # Try using Supabase RPC if available
            self.client.rpc('create_kai_memories_table', {}).execute()
            logger.info("[MEMORY] Created kai_memories table via RPC")
            return True
        except Exception as rpc_error:
            logger.warning(f"[MEMORY] RPC failed, table may need manual creation: {rpc_error}")
            # Return False - table needs to be created manually in Supabase dashboard
            return False
    
    def get_memories(self, user_id: str = "default", category: str = None, 
                     limit: int = 50) -> list:
        """
        Get memories for a user.
        
        Args:
            user_id: User identifier
            category: Optional category filter
            limit: Max memories to return
            
        Returns:
            List of memory dicts
        """
        try:
            query = self.client.table('kai_memories').select('*').eq('user_id', user_id)
            
            if category:
                query = query.eq('category', category)
            
            data = query.order('importance', desc=True).order('last_accessed', desc=True).limit(limit).execute()
            return data.data if data.data else []
            
        except Exception as e:
            logger.error(f"[MEMORY] Get memories error: {e}")
            return []
    
    def search_memories(self, query: str, user_id: str = "default", limit: int = 10) -> list:
        """
        Search memories by content.
        
        Args:
            query: Search query
            user_id: User identifier
            limit: Max results
            
        Returns:
            List of matching memories
        """
        try:
            data = self.client.table('kai_memories')\
                .select('*')\
                .eq('user_id', user_id)\
                .ilike('content', f'%{query}%')\
                .order('importance', desc=True)\
                .limit(limit)\
                .execute()
            
            # Update access count for found memories
            if data.data:
                for mem in data.data:
                    try:
                        self.client.table('kai_memories').update({
                            'access_count': mem.get('access_count', 0) + 1,
                            'last_accessed': datetime.now().isoformat()
                        }).eq('id', mem['id']).execute()
                    except:
                        pass
            
            return data.data if data.data else []
            
        except Exception as e:
            logger.error(f"[MEMORY] Search error: {e}")
            return []
    
    def get_memory_stats(self, user_id: str = "default") -> dict:
        """Get memory statistics for a user"""
        try:
            data = self.client.table('kai_memories')\
                .select('category')\
                .eq('user_id', user_id)\
                .execute()
            
            if not data.data:
                return {"total": 0, "categories": {}}
            
            categories = {}
            for mem in data.data:
                cat = mem.get('category', 'general')
                categories[cat] = categories.get(cat, 0) + 1
            
            return {
                "total": len(data.data),
                "categories": categories
            }
        except Exception as e:
            logger.error(f"[MEMORY] Stats error: {e}")
            return {"total": 0, "categories": {}}
    
    # ==================== USER SETTINGS ====================
    
    def save_user_settings(self, user_id: str, settings_data: dict) -> bool:
        """
        Save all user settings to Supabase.
        
        Args:
            user_id: Firebase/Auth user ID
            settings_data: Full settings object with profile, security, notifications, etc.
            
        Returns:
            True if saved successfully
        """
        try:
            # Prepare data for upsert
            record = {
                'user_id': user_id,
                'profile': json.dumps(settings_data.get('profile', {})),
                'security': json.dumps(settings_data.get('security', {})),
                'notifications': json.dumps(settings_data.get('notifications', {})),
                'model_preferences': json.dumps(settings_data.get('modelPreferences', {})),
                'language': json.dumps(settings_data.get('language', {})),
                'api_keys': json.dumps(settings_data.get('apiKeys', {})),  # Already base64 encoded from frontend
                'updated_at': datetime.now().isoformat()
            }
            
            # Upsert (insert or update)
            self.client.table('user_settings').upsert(record, on_conflict='user_id').execute()
            
            logger.info(f"[SETTINGS] Saved settings for user: {user_id[:8]}...")
            return True
            
        except Exception as e:
            error_str = str(e).lower()
            if "relation" in error_str and "does not exist" in error_str:
                logger.warning("[SETTINGS] Table doesn't exist. Please create 'user_settings' table in Supabase.")
            logger.error(f"[SETTINGS] Save error: {e}")
            return False
    
    def get_user_settings(self, user_id: str) -> dict:
        """
        Get all user settings from Supabase.
        
        Args:
            user_id: Firebase/Auth user ID
            
        Returns:
            Settings dict or empty dict if not found
        """
        try:
            data = self.client.table('user_settings')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()
            
            if not data.data:
                return {}
            
            record = data.data[0]
            
            # Parse JSON fields
            return {
                'profile': json.loads(record.get('profile', '{}') or '{}'),
                'security': json.loads(record.get('security', '{}') or '{}'),
                'notifications': json.loads(record.get('notifications', '{}') or '{}'),
                'modelPreferences': json.loads(record.get('model_preferences', '{}') or '{}'),
                'language': json.loads(record.get('language', '{}') or '{}'),
                'apiKeys': json.loads(record.get('api_keys', '{}') or '{}'),
                'updatedAt': record.get('updated_at'),
                'createdAt': record.get('created_at')
            }
            
        except Exception as e:
            logger.error(f"[SETTINGS] Get settings error: {e}")
            return {}
    
    def update_user_profile(self, user_id: str, profile_data: dict) -> bool:
        """
        Update user profile specifically.
        
        Args:
            user_id: Firebase/Auth user ID
            profile_data: Profile dict with name, email, bio, avatar_url, etc.
            
        Returns:
            True if updated successfully
        """
        try:
            # Get existing settings first
            existing = self.get_user_settings(user_id)
            
            # Merge profile data
            existing_profile = existing.get('profile', {})
            existing_profile.update(profile_data)
            
            # Calculate stats
            stats = self._calculate_user_stats(user_id)
            existing_profile['stats'] = stats
            existing_profile['lastSync'] = datetime.now().isoformat()
            
            # Update just the profile field
            if existing:
                self.client.table('user_settings').update({
                    'profile': json.dumps(existing_profile),
                    'updated_at': datetime.now().isoformat()
                }).eq('user_id', user_id).execute()
            else:
                # Create new record
                self.client.table('user_settings').insert({
                    'user_id': user_id,
                    'profile': json.dumps(existing_profile),
                    'updated_at': datetime.now().isoformat()
                }).execute()
            
            logger.info(f"[SETTINGS] Updated profile for user: {user_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"[SETTINGS] Update profile error: {e}")
            return False
    
    def get_user_profile(self, user_id: str) -> dict:
        """
        Get user profile with stats.
        
        Args:
            user_id: Firebase/Auth user ID
            
        Returns:
            Profile dict with stats, rank, achievements
        """
        try:
            settings = self.get_user_settings(user_id)
            profile = settings.get('profile', {})
            
            # Add computed stats
            stats = self._calculate_user_stats(user_id)
            profile['stats'] = stats
            
            # Calculate rank
            profile['rank'] = self._calculate_rank(stats)
            
            # Get achievements
            profile['achievements'] = self._get_achievements(stats, user_id)
            
            return profile
            
        except Exception as e:
            logger.error(f"[SETTINGS] Get profile error: {e}")
            return {}
    
    def _calculate_user_stats(self, user_id: str) -> dict:
        """Calculate user statistics for profile display"""
        try:
            # Count messages
            msg_data = self.client.table('messages').select('id', count='exact').execute()
            message_count = msg_data.count if hasattr(msg_data, 'count') else len(msg_data.data) if msg_data.data else 0
            
            # Count synced memories
            mem_stats = self.get_memory_stats(user_id)
            
            # Count conversations
            conv_data = self.client.table('conversations').select('id', count='exact').execute()
            conv_count = conv_data.count if hasattr(conv_data, 'count') else len(conv_data.data) if conv_data.data else 0
            
            # Calculate account age (mock - would need user creation date)
            account_age_days = 30  # Default
            
            return {
                'messageCount': message_count,
                'memoriesSynced': mem_stats.get('total', 0),
                'conversationCount': conv_count,
                'accountAgeDays': account_age_days,
                'weeklyActivity': [3, 5, 2, 7, 4, 6, 5]  # Mock activity data
            }
            
        except Exception as e:
            logger.error(f"[SETTINGS] Calculate stats error: {e}")
            return {
                'messageCount': 0,
                'memoriesSynced': 0,
                'conversationCount': 0,
                'accountAgeDays': 0,
                'weeklyActivity': [0, 0, 0, 0, 0, 0, 0]
            }
    
    def _calculate_rank(self, stats: dict) -> dict:
        """Calculate user rank based on usage"""
        messages = stats.get('messageCount', 0)
        memories = stats.get('memoriesSynced', 0)
        
        score = messages + (memories * 10)
        
        if score >= 1000:
            return {'title': 'DIRECTOR', 'level': 5, 'color': '#f59e0b'}
        elif score >= 500:
            return {'title': 'COMMANDER', 'level': 4, 'color': '#8b5cf6'}
        elif score >= 200:
            return {'title': 'CAPTAIN', 'level': 3, 'color': '#6366f1'}
        elif score >= 50:
            return {'title': 'LIEUTENANT', 'level': 2, 'color': '#10b981'}
        else:
            return {'title': 'OPERATIVE', 'level': 1, 'color': '#64748b'}
    
    def _get_achievements(self, stats: dict, user_id: str) -> list:
        """Get user achievements based on activity"""
        achievements = []
        
        # Early Adopter (always show for now)
        achievements.append({
            'id': 'early_adopter',
            'name': 'Early Adopter',
            'icon': '🏆',
            'description': 'Joined during alpha phase',
            'unlocked': True
        })
        
        # Power User
        if stats.get('messageCount', 0) >= 100:
            achievements.append({
                'id': 'power_user',
                'name': 'Power User',
                'icon': '⚡',
                'description': 'Sent 100+ messages',
                'unlocked': True
            })
        
        # Memory Master
        if stats.get('memoriesSynced', 0) >= 50:
            achievements.append({
                'id': 'memory_master',
                'name': 'Memory Master',
                'icon': '🧠',
                'description': 'Synced 50+ memories',
                'unlocked': True
            })
        
        # Security First
        achievements.append({
            'id': 'security_first',
            'name': 'Security First',
            'icon': '🔒',
            'description': 'Enabled TLS encryption',
            'unlocked': True
        })
        
        return achievements

# Import timedelta for analytics
from datetime import timedelta

# Global instance
try:
    supabase_db = SupabaseDB()
except Exception as e:
    logger.error(f"[SUPABASE] Failed to initialize: {e}")
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
