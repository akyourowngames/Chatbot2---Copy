"""
Firebase Storage for Web Scraped Data with Auto-Cleanup
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import logging
import json
import os
from typing import Dict, List, Optional, Any
import threading
import time

class FirebaseStorage:
    """
    Firebase storage for scraped data with automatic cleanup
    Integrates Supabase for file storage
    """
    
    def __init__(self, project_id: str = None, credentials_path: str = None):
        """
        Initialize Firebase storage
        
        Args:
            project_id: Firebase project ID (optional, will use default if not provided)
            credentials_path: Path to Firebase service account JSON (optional)
        """
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.db = None
        self.supabase = None
        self.supabase_bucket = None
        self.cleanup_thread = None
        self.running = False
        
        # Initialize Firebase (for Firestore database)
        self._initialize_firebase()
        
        # Initialize Supabase (for file storage)
        self._initialize_supabase()
        
        # Start cleanup thread
        self._start_cleanup_thread()
        
        logging.info("Firebase Storage initialized")

    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Load environment variables
            from dotenv import load_dotenv
            load_dotenv()
            
            # Check if Firebase is already initialized by another module
            if firebase_admin._apps:
                self.db = firestore.client()
                logging.info("Firebase Storage: Using existing Firebase app")
                return
            
            # Get credentials from environment or parameters
            cred_path = self.credentials_path or os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
            project_id = self.project_id or os.getenv('FIREBASE_PROJECT_ID')
            
            # Try to find credentials file
            if not os.path.exists(cred_path):
                # Try alternative paths
                possible_paths = [
                    cred_path,
                    os.path.join(os.path.dirname(__file__), '..', cred_path),
                    os.path.join(os.path.dirname(__file__), '..', 'Config', 'firebase-credentials.json'),
                    os.path.join(os.path.dirname(__file__), '..', 'firebase-credentials.json'),
                ]
                
                found = False
                for path in possible_paths:
                    if os.path.exists(path):
                        cred_path = path
                        found = True
                        break
                
                if not found:
                    logging.warning(f"Firebase credentials not found, Firestore will not be available")
                    return
            
            # Initialize Firebase with credentials
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'projectId': project_id,
                'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
            })
            
            self.db = firestore.client()
            logging.info(f"Firebase initialized successfully (Project: {project_id})")
            
        except Exception as e:
            logging.error(f"Failed to initialize Firebase: {e}")
            # Try to use existing Firebase app as fallback
            try:
                if firebase_admin._apps:
                    self.db = firestore.client()
                    logging.info("Firebase Storage: Recovered using existing Firebase app")
                    return
            except:
                pass
            self.db = None
    
    def _initialize_supabase(self):
        """Initialize Supabase client for file storage"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                logging.warning("Supabase credentials not found in environment")
                return None
            
            try:
                from supabase import create_client
                self.supabase = create_client(supabase_url, supabase_key)
                self.supabase_bucket = os.getenv('SUPABASE_BUCKET', 'Flle')
                logging.info(f"Supabase initialized (Bucket: {self.supabase_bucket})")
                return self.supabase
            except ImportError:
                logging.warning("Supabase library not installed. Install with: pip install supabase")
                return None
                
        except Exception as e:
            logging.error(f"Failed to initialize Supabase: {e}")
            return None

            credentials_file = None
            possible_paths = [
                self.credentials_path,
                'kai-ai-32eab-firebase-adminsdk-fbsvc-580a75d2af.json',
                'firebase-credentials.json',
                'credentials.json'
            ]
            
            for path in possible_paths:
                if path and os.path.exists(path):
                    credentials_file = path
                    break
            
            # Initialize Firebase
            if credentials_file:
                # Use service account credentials
                cred = credentials.Certificate(credentials_file)
                project_id = self.project_id or 'kai-ai-32eab'  # Use your project ID
                firebase_admin.initialize_app(cred, {'projectId': project_id})
                logging.info(f"Firebase initialized with credentials: {credentials_file}")
            else:
                # Use default credentials (for local development or when running on GCP)
                firebase_admin.initialize_app()
                logging.info("Firebase initialized with default credentials")
            
            self.db = firestore.client()
            logging.info("Firebase client connected successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize Firebase: {e}")
            # Fallback to local storage if Firebase fails
            self.db = None
    
    def _start_cleanup_thread(self):
        """Start the cleanup thread for old data"""
        if self.cleanup_thread is None or not self.cleanup_thread.is_alive():
            self.running = True
            self.cleanup_thread = threading.Thread(target=self._cleanup_old_data, daemon=True)
            self.cleanup_thread.start()
            logging.info("Cleanup thread started")
    
    def _cleanup_old_data(self):
        """Clean up old scraped data (runs in background thread)"""
        while self.running:
            try:
                if self.db is None:
                    time.sleep(300)  # Wait 5 minutes if Firebase not available
                    continue
                
                # Clean up data older than 24 hours
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                # Get old documents
                old_docs = self.db.collection('scraped_data').where(
                    'created_at', '<', cutoff_time
                ).stream()
                
                deleted_count = 0
                for doc in old_docs:
                    doc.reference.delete()
                    deleted_count += 1
                
                if deleted_count > 0:
                    logging.info(f"Cleaned up {deleted_count} old scraped data entries")
                
                # Wait 1 hour before next cleanup
                time.sleep(3600)
                
            except Exception as e:
                logging.error(f"Error in cleanup thread: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def save_scraped_data(self, data: Dict[str, Any]) -> bool:
        """
        Save scraped data to Firebase
        
        Args:
            data: Dictionary containing scraped data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.db is None:
                logging.warning("Firebase not available, saving to local file")
                return self._save_to_local_file(data)
            
            # Add metadata
            data['created_at'] = datetime.utcnow()
            data['expires_at'] = datetime.utcnow() + timedelta(hours=24)
            
            # Save to Firebase
            doc_ref = self.db.collection('scraped_data').add(data)
            
            logging.info(f"Saved scraped data to Firebase: {doc_ref[1].id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save to Firebase: {e}")
            # Fallback to local storage
            return self._save_to_local_file(data)
    
    def _save_to_local_file(self, data: Dict[str, Any]) -> bool:
        """Fallback: Save to local JSON file"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs('Data', exist_ok=True)
            
            # Add timestamp
            data['created_at'] = datetime.utcnow().isoformat()
            data['expires_at'] = (datetime.utcnow() + timedelta(hours=24)).isoformat()
            
            # Save to JSON file
            filename = f"Data/scraped_data_{int(time.time())}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Saved scraped data to local file: {filename}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save to local file: {e}")
            return False
    
    def get_recent_data(self, url: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent scraped data
        
        Args:
            url: Filter by URL (optional)
            limit: Maximum number of results
            
        Returns:
            List of scraped data dictionaries
        """
        try:
            if self.db is None:
                return self._get_from_local_files(url, limit)
            
            # Query Firebase
            query = self.db.collection('scraped_data').order_by('created_at', direction=firestore.Query.DESCENDING)
            
            if url:
                query = query.where('url', '==', url)
            
            docs = query.limit(limit).stream()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logging.error(f"Failed to get data from Firebase: {e}")
            return self._get_from_local_files(url, limit)
    
    def _get_from_local_files(self, url: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Fallback: Get data from local JSON files"""
        try:
            if not os.path.exists('Data'):
                return []
            
            results = []
            files = [f for f in os.listdir('Data') if f.startswith('scraped_data_') and f.endswith('.json')]
            files.sort(reverse=True)  # Most recent first
            
            for filename in files[:limit]:
                try:
                    with open(os.path.join('Data', filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if url is None or data.get('url') == url:
                        results.append(data)
                        
                except Exception as e:
                    logging.warning(f"Failed to read file {filename}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logging.error(f"Failed to get data from local files: {e}")
            return []
    
    def cleanup_manual(self, hours_old: int = 24) -> int:
        """
        Manually clean up old data
        
        Args:
            hours_old: Delete data older than this many hours
            
        Returns:
            Number of documents deleted
        """
        try:
            if self.db is None:
                return self._cleanup_local_files(hours_old)
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
            
            # Get old documents
            old_docs = self.db.collection('scraped_data').where(
                'created_at', '<', cutoff_time
            ).stream()
            
            deleted_count = 0
            for doc in old_docs:
                doc.reference.delete()
                deleted_count += 1
            
            logging.info(f"Manually cleaned up {deleted_count} old entries")
            return deleted_count
            
        except Exception as e:
            logging.error(f"Failed to manually cleanup: {e}")
            return 0
    
    def _cleanup_local_files(self, hours_old: int = 24) -> int:
        """Clean up old local files"""
        try:
            if not os.path.exists('Data'):
                return 0
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
            deleted_count = 0
            
            files = [f for f in os.listdir('Data') if f.startswith('scraped_data_') and f.endswith('.json')]
            
            for filename in files:
                try:
                    filepath = os.path.join('Data', filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        deleted_count += 1
                        
                except Exception as e:
                    logging.warning(f"Failed to delete file {filename}: {e}")
                    continue
            
            logging.info(f"Cleaned up {deleted_count} old local files")
            return deleted_count
            
        except Exception as e:
            logging.error(f"Failed to cleanup local files: {e}")
            return 0
    
    def shutdown(self):
        """Shutdown the storage system"""
        self.running = False
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5)
        logging.info("Firebase Storage shutdown complete")

# Global storage instance
_storage_instance = None

def get_firebase_storage(project_id: str = None, credentials_path: str = None) -> FirebaseStorage:
    """Get or create Firebase storage instance"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = FirebaseStorage(project_id, credentials_path)
    return _storage_instance

# Example usage
if __name__ == "__main__":
    # Test Firebase storage
    storage = get_firebase_storage()
    
    # Test data
    test_data = {
        'url': 'https://example.com',
        'title': 'Example Page',
        'content': 'This is test content',
        'word_count': 4,
        'summary': 'Test summary'
    }
    
    # Save data
    success = storage.save_scraped_data(test_data)
    print(f"Save successful: {success}")
    
    # Get recent data
    recent_data = storage.get_recent_data(limit=5)
    print(f"Recent data count: {len(recent_data)}")
    
    # Manual cleanup
    deleted = storage.cleanup_manual(hours_old=1)
    print(f"Deleted {deleted} old entries")
    
    storage.shutdown()
    print("Firebase Storage test completed!")
