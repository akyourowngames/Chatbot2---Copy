"""
SharedFileManager - Multi-User File Sharing System
=====================================================
Enables users to share files with teammates and chat with KAI about them collaboratively.

Features:
- Upload files (local or Google Drive)
- Share with multiple users
- Permission management
- Cross-chatroom context injection
- Activity tracking
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import firebase_admin
from firebase_admin import credentials, firestore, storage
from dataclasses import dataclass, asdict

# Initialize Firebase (if not already initialized)
try:
    firebase_admin.get_app()
except ValueError:
    # Load Firebase credentials
    FIREBASE_CREDENTIALS = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
    if os.path.exists(FIREBASE_CREDENTIALS):
        cred = credentials.Certificate(FIREBASE_CREDENTIALS)
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'kai-g-80f9c.appspot.com'
        })

db = firestore.client()
bucket = storage.bucket()


@dataclass
class FileMetadata:
    """Extracted file metadata"""
    extracted_text: str
    summary: str
    keywords: List[str]
    page_count: Optional[int] = None
    drive_id: Optional[str] = None  # Google Drive file ID if imported from Drive


@dataclass
class SharedFile:
    """Shared file model"""
    file_id: str
    name: str
    type: str  # pdf, docx, txt, etc.
    size: int
    storage_url: str
    drive_id: Optional[str]
    owner_id: str
    created_at: datetime
    metadata: FileMetadata
    permissions: Dict[str, Dict]  # {user_id: {access: "read", granted_at: timestamp}}
    analytics: Dict[str, int]  # {total_questions: 0, unique_users: 0}


class SharedFileManager:
    """Manages shared file operations"""
    
    def __init__(self):
        self.files_collection = db.collection('shared_files')
        self.activity_collection = db.collection('file_activity')
    
    def upload_file(self, user_id: str, file_data: bytes, filename: str, 
                   file_type: str, metadata: Optional[FileMetadata] = None) -> str:
        """
        Upload a file to Firebase Storage and create Firestore document.
        
        Args:
            user_id: ID of user uploading
            file_data: Binary file data
            filename: Name of file
            file_type: File extension (pdf, docx, etc.)
            metadata: Optional extracted metadata
            
        Returns:
            file_id: Unique file identifier
        """
        try:
            # Generate unique file ID
            file_id = self.files_collection.document().id
            
            # Upload to Firebase Storage
            blob = bucket.blob(f'shared_files/{user_id}/{file_id}/{filename}')
            blob.upload_from_string(file_data, content_type=f'application/{file_type}')
            blob.make_public()
            storage_url = blob.public_url
            
            # Create Firestore document
            file_doc = {
                'file_id': file_id,
                'name': filename,
                'type': file_type,
                'size': len(file_data),
                'storage_url': storage_url,
                'drive_id': None,
                'owner_id': user_id,
                'created_at': firestore.SERVER_TIMESTAMP,
                'metadata': asdict(metadata) if metadata else {
                    'extracted_text': '',
                    'summary': '',
                    'keywords': []
                },
                'permissions': {
                    user_id: {
                        'access': 'owner',
                        'granted_at': firestore.SERVER_TIMESTAMP,
                        'granted_by': user_id
                    }
                },
                'analytics': {
                    'total_questions': 0,
                    'unique_users': 0,
                    'last_accessed': firestore.SERVER_TIMESTAMP
                }
            }
            
            self.files_collection.document(file_id).set(file_doc)
            
            # Track activity
            self.track_activity(file_id, user_id, 'uploaded', {'filename': filename})
            
            print(f"[SharedFileManager] ✅ Uploaded {filename} (ID: {file_id})")
            return file_id
            
        except Exception as e:
            print(f"[SharedFileManager] ❌ Upload failed: {e}")
            raise
    
    def share_file(self, file_id: str, user_id: str, share_with: List[str], 
                   permission: str = 'read') -> bool:
        """
        Share a file with other users.
        
        Args:
            file_id: File to share
            user_id: User sharing the file (must be owner)
            share_with: List of user IDs to share with
            permission: Access level ('read' or 'write')
            
        Returns:
            bool: Success status
        """
        try:
            file_ref = self.files_collection.document(file_id)
            file_doc = file_ref.get()
            
            if not file_doc.exists:
                print(f"[SharedFileManager] ❌ File {file_id} not found")
                return False
            
            file_data = file_doc.to_dict()
            
            # Verify user is owner
            if file_data['owner_id'] != user_id:
                print(f"[SharedFileManager] ❌ User {user_id} not authorized to share")
                return False
            
            # Add permissions for each user
            permissions = file_data.get('permissions', {})
            for target_user in share_with:
                permissions[target_user] = {
                    'access': permission,
                    'granted_at': firestore.SERVER_TIMESTAMP,
                    'granted_by': user_id
                }
            
            # Update document
            file_ref.update({'permissions': permissions})
            
            # Track activity
            self.track_activity(file_id, user_id, 'shared', {
                'shared_with': share_with,
                'permission': permission
            })
            
            print(f"[SharedFileManager] ✅ Shared {file_id} with {len(share_with)} users")
            return True
            
        except Exception as e:
            print(f"[SharedFileManager] ❌ Share failed: {e}")
            return False
    
    def revoke_access(self, file_id: str, user_id: str, revoke_user: str) -> bool:
        """
        Revoke file access from a user.
        
        Args:
            file_id: File ID
            user_id: User revoking access (must be owner)
            revoke_user: User to revoke access from
            
        Returns:
            bool: Success status
        """
        try:
            file_ref = self.files_collection.document(file_id)
            file_doc = file_ref.get()
            
            if not file_doc.exists:
                return False
            
            file_data = file_doc.to_dict()
            
            # Verify user is owner
            if file_data['owner_id'] != user_id:
                return False
            
            # Remove permission
            permissions = file_data.get('permissions', {})
            if revoke_user in permissions:
                del permissions[revoke_user]
                file_ref.update({'permissions': permissions})
                
                self.track_activity(file_id, user_id, 'revoked', {'revoked_user': revoke_user})
                print(f"[SharedFileManager] ✅ Revoked access for {revoke_user}")
                return True
            
            return False
            
        except Exception as e:
            print(f"[SharedFileManager] ❌ Revoke failed: {e}")
            return False
    
    def get_shared_files(self, user_id: str) -> List[Dict]:
        """
        Get all files accessible to a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of file dictionaries
        """
        try:
            # Query files where user has permission
            files = []
            all_files = self.files_collection.stream()
            
            for doc in all_files:
                file_data = doc.to_dict()
                permissions = file_data.get('permissions', {})
                
                # Check if user has access
                if user_id in permissions or file_data['owner_id'] == user_id:
                    files.append(file_data)
            
            print(f"[SharedFileManager] Found {len(files)} accessible files for {user_id}")
            return files
            
        except Exception as e:
            print(f"[SharedFileManager] ❌ Get files failed: {e}")
            return []
    
    def get_file_content(self, file_id: str, user_id: str) -> Optional[str]:
        """
        Get file content (with permission check).
        
        Args:
            file_id: File ID
            user_id: Requesting user
            
        Returns:
            Extracted text content or None
        """
        try:
            file_doc = self.files_collection.document(file_id).get()
            
            if not file_doc.exists:
                return None
            
            file_data = file_doc.to_dict()
            permissions = file_data.get('permissions', {})
            
            # Check permission
            if user_id not in permissions and file_data['owner_id'] != user_id:
                print(f"[SharedFileManager] ❌ User {user_id} has no access to {file_id}")
                return None
            
            # Return cached extracted text
            content = file_data.get('metadata', {}).get('extracted_text', '')
            
            # Update analytics
            self.files_collection.document(file_id).update({
                'analytics.last_accessed': firestore.SERVER_TIMESTAMP
            })
            
            return content
            
        except Exception as e:
            print(f"[SharedFileManager] ❌ Get content failed: {e}")
            return None
    
    def track_activity(self, file_id: str, user_id: str, action: str, details: Dict = None):
        """Track file activity"""
        try:
            activity_doc = {
                'file_id': file_id,
                'user_id': user_id,
                'action': action,
                'details': details or {},
                'timestamp': firestore.SERVER_TIMESTAMP
            }
            self.activity_collection.add(activity_doc)
        except Exception as e:
            print(f"[SharedFileManager] Activity tracking failed: {e}")
    
    def update_file_metadata(self, file_id: str, metadata: FileMetadata) -> bool:
        """Update file metadata after extraction"""
        try:
            self.files_collection.document(file_id).update({
                'metadata': asdict(metadata)
            })
            return True
        except Exception as e:
            print(f"[SharedFileManager] Metadata update failed: {e}")
            return False


# Global instance
shared_file_manager = SharedFileManager()

def get_shared_file_manager() -> SharedFileManager:
    """Get the global SharedFileManager instance."""
    return shared_file_manager


if __name__ == "__main__":
    print("SharedFileManager initialized ✅")
    print("Features:")
    print("  - Multi-user file sharing")
    print("  - Permission management")
    print("  - Firebase Storage integration")
    print("  - Activity tracking")
    print("  - Google Drive import support")
