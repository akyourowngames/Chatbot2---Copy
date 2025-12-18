"""
Firebase Data Access Layer (DAL)
=================================
Unified data access with schema validation, caching, and encryption
"""

from firebase_admin import firestore
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
import logging
from collections import OrderedDict
from Backend.SecurityManager import encrypt_field, decrypt_field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== PYDANTIC SCHEMAS ====================

class ConversationSchema(BaseModel):
    """Schema for conversation documents"""
    title: str = Field(..., min_length=1, max_length=200)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True


class MessageSchema(BaseModel):
    """Schema for message documents"""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    conversation_id: str = Field(..., min_length=1)
    
    class Config:
        arbitrary_types_allowed = True


class MemorySchema(BaseModel):
    """Schema for memory documents"""
    content: str = Field(..., min_length=1)
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


class WorkflowSchema(BaseModel):
    """Schema for workflow documents"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    steps: List[Dict[str, str]] = Field(..., min_items=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    enabled: bool = Field(default=True)
    
    class Config:
        arbitrary_types_allowed = True


class PreferenceSchema(BaseModel):
    """Schema for user preferences"""
    theme: str = Field(default="dark")
    language: str = Field(default="en")
    voice_settings: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


class ScreenshotSchema(BaseModel):
    """Schema for screenshot metadata"""
    filename: str = Field(..., min_length=1)
    storage_path: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True


class FileSchema(BaseModel):
    """Schema for file uploads"""
    filename: str = Field(..., min_length=1)
    file_type: str = Field(..., min_length=1)
    size_bytes: int = Field(..., gt=0)
    storage_path: str = Field(..., min_length=1)
    analysis: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True


class PluginSchema(BaseModel):
    """Schema for custom plugins"""
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1)
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True


class AnalyticsSchema(BaseModel):
    """Schema for analytics events"""
    event_type: str = Field(..., min_length=1)
    event_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True


class AutomationMacroSchema(BaseModel):
    """Schema for automation macros"""
    name: str = Field(..., min_length=1, max_length=100)
    triggers: List[str] = Field(..., min_items=1)
    actions: List[Dict[str, str]] = Field(..., min_items=1)
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True


# ==================== CACHING LAYER ====================

class LRUCache:
    """Simple LRU cache for Firestore data"""
    
    def __init__(self, max_size: int = 100):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any):
        """Set item in cache"""
        if key in self.cache:
            # Update existing
            self.cache.move_to_end(key)
        else:
            # Add new
            if len(self.cache) >= self.max_size:
                # Remove oldest
                self.cache.popitem(last=False)
        self.cache[key] = value
    
    def invalidate(self, key: str):
        """Remove item from cache"""
        if key in self.cache:
            del self.cache[key]
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        keys_to_remove = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self.cache[key]
    
    def clear(self):
        """Clear entire cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%"
        }


# ==================== FIREBASE DAL ====================

class FirebaseDAL:
    """Data Access Layer for Firebase Firestore"""
    
    # Schema mapping
    SCHEMAS = {
        "conversations": ConversationSchema,
        "messages": MessageSchema,
        "memory": MemorySchema,
        "workflows": WorkflowSchema,
        "preferences": PreferenceSchema,
        "screenshots": ScreenshotSchema,
        "files": FileSchema,
        "plugins": PluginSchema,
        "analytics": AnalyticsSchema,
        "automation_macros": AutomationMacroSchema
    }
    
    # Fields to encrypt
    ENCRYPTED_FIELDS = {
        "plugins": ["code"],  # Encrypt plugin code
        "preferences": []  # Add any sensitive preference fields
    }
    
    def __init__(self, db: firestore.Client, cache_size: int = 200):
        """
        Initialize Firebase DAL
        
        Args:
            db: Firestore database client
            cache_size: Maximum number of cached items
        """
        self.db = db
        self.cache = LRUCache(max_size=cache_size)
        logger.info(f"[DAL] Firebase DAL initialized with cache size: {cache_size}")
    
    # ==================== CREATE ====================
    
    def create(self, collection: str, user_id: str, data: Dict[str, Any], doc_id: Optional[str] = None) -> Optional[str]:
        """
        Create a new document
        
        Args:
            collection: Collection name
            user_id: User ID (for user-scoped collections)
            data: Document data
            doc_id: Optional document ID (auto-generated if not provided)
            
        Returns:
            Document ID if successful, None otherwise
        """
        try:
            # Validate schema
            if collection in self.SCHEMAS:
                schema = self.SCHEMAS[collection]
                validated_data = schema(**data).dict()
            else:
                validated_data = data
            
            # Encrypt sensitive fields
            validated_data = self._encrypt_fields(collection, validated_data)
            
            # Get collection reference
            col_ref = self.db.collection(collection).document(user_id).collection(collection)
            
            # Create document
            if doc_id:
                col_ref.document(doc_id).set(validated_data)
                created_id = doc_id
            else:
                doc_ref = col_ref.add(validated_data)
                created_id = doc_ref[1].id
            
            # Invalidate cache for this user's collection
            self.cache.invalidate_pattern(f"{collection}:{user_id}")
            
            logger.info(f"[DAL] Created {collection} document: {created_id} for user: {user_id}")
            return created_id
            
        except Exception as e:
            logger.error(f"[DAL] Create error in {collection}: {e}")
            return None
    
    # ==================== READ ====================
    
    def get(self, collection: str, user_id: str, doc_id: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get a single document
        
        Args:
            collection: Collection name
            user_id: User ID
            doc_id: Document ID
            use_cache: Whether to use cache
            
        Returns:
            Document data if found, None otherwise
        """
        try:
            cache_key = f"{collection}:{user_id}:{doc_id}"
            
            # Check cache first
            if use_cache:
                cached = self.cache.get(cache_key)
                if cached:
                    logger.debug(f"[DAL] Cache hit: {cache_key}")
                    return cached
            
            # Get from Firestore
            doc_ref = self.db.collection(collection).document(user_id).collection(collection).document(doc_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            data["id"] = doc.id
            
            # Decrypt sensitive fields
            data = self._decrypt_fields(collection, data)
            
            # Cache the result
            if use_cache:
                self.cache.set(cache_key, data)
            
            return data
            
        except Exception as e:
            logger.error(f"[DAL] Get error in {collection}: {e}")
            return None
    
    def list(self, collection: str, user_id: str, limit: int = 50, order_by: Optional[str] = None, 
             descending: bool = True, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        List documents in a collection
        
        Args:
            collection: Collection name
            user_id: User ID
            limit: Maximum number of documents
            order_by: Field to order by
            descending: Sort order
            filters: Optional filters (field: value)
            
        Returns:
            List of documents
        """
        try:
            # Build query
            query = self.db.collection(collection).document(user_id).collection(collection)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    query = query.where(field, "==", value)
            
            # Apply ordering
            if order_by:
                direction = firestore.Query.DESCENDING if descending else firestore.Query.ASCENDING
                query = query.order_by(order_by, direction=direction)
            
            # Apply limit
            query = query.limit(limit)
            
            # Execute query
            docs = query.stream()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                # Decrypt sensitive fields
                data = self._decrypt_fields(collection, data)
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"[DAL] List error in {collection}: {e}")
            return []
    
    # ==================== UPDATE ====================
    
    def update(self, collection: str, user_id: str, doc_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a document
        
        Args:
            collection: Collection name
            user_id: User ID
            doc_id: Document ID
            updates: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Encrypt sensitive fields in updates
            updates = self._encrypt_fields(collection, updates)
            
            # Add updated_at timestamp if not present
            if "updated_at" not in updates:
                updates["updated_at"] = datetime.utcnow()
            
            # Update document
            doc_ref = self.db.collection(collection).document(user_id).collection(collection).document(doc_id)
            doc_ref.update(updates)
            
            # Invalidate cache
            cache_key = f"{collection}:{user_id}:{doc_id}"
            self.cache.invalidate(cache_key)
            self.cache.invalidate_pattern(f"{collection}:{user_id}")
            
            logger.info(f"[DAL] Updated {collection} document: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"[DAL] Update error in {collection}: {e}")
            return False
    
    # ==================== DELETE ====================
    
    def delete(self, collection: str, user_id: str, doc_id: str) -> bool:
        """
        Delete a document
        
        Args:
            collection: Collection name
            user_id: User ID
            doc_id: Document ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete document
            doc_ref = self.db.collection(collection).document(user_id).collection(collection).document(doc_id)
            doc_ref.delete()
            
            # Invalidate cache
            cache_key = f"{collection}:{user_id}:{doc_id}"
            self.cache.invalidate(cache_key)
            self.cache.invalidate_pattern(f"{collection}:{user_id}")
            
            logger.info(f"[DAL] Deleted {collection} document: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"[DAL] Delete error in {collection}: {e}")
            return False
    
    # ==================== BATCH OPERATIONS ====================
    
    def batch_create(self, collection: str, user_id: str, items: List[Dict[str, Any]]) -> List[str]:
        """
        Create multiple documents in a batch
        
        Args:
            collection: Collection name
            user_id: User ID
            items: List of document data
            
        Returns:
            List of created document IDs
        """
        try:
            batch = self.db.batch()
            col_ref = self.db.collection(collection).document(user_id).collection(collection)
            
            doc_ids = []
            for item in items:
                # Validate and encrypt
                if collection in self.SCHEMAS:
                    validated = self.SCHEMAS[collection](**item).dict()
                else:
                    validated = item
                validated = self._encrypt_fields(collection, validated)
                
                # Add to batch
                doc_ref = col_ref.document()
                batch.set(doc_ref, validated)
                doc_ids.append(doc_ref.id)
            
            # Commit batch
            batch.commit()
            
            # Invalidate cache
            self.cache.invalidate_pattern(f"{collection}:{user_id}")
            
            logger.info(f"[DAL] Batch created {len(doc_ids)} documents in {collection}")
            return doc_ids
            
        except Exception as e:
            logger.error(f"[DAL] Batch create error in {collection}: {e}")
            return []
    
    # ==================== HELPER METHODS ====================
    
    def _encrypt_fields(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in document data"""
        if collection not in self.ENCRYPTED_FIELDS:
            return data
        
        encrypted_data = data.copy()
        for field in self.ENCRYPTED_FIELDS[collection]:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = encrypt_field(str(encrypted_data[field]))
        
        return encrypted_data
    
    def _decrypt_fields(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in document data"""
        if collection not in self.ENCRYPTED_FIELDS:
            return data
        
        decrypted_data = data.copy()
        for field in self.ENCRYPTED_FIELDS[collection]:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = decrypt_field(decrypted_data[field])
                except:
                    # If decryption fails, field might not be encrypted
                    pass
        
        return decrypted_data
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache.get_stats()
    
    def clear_cache(self):
        """Clear the entire cache"""
        self.cache.clear()
        logger.info("[DAL] Cache cleared")


# ==================== TESTING ====================

if __name__ == "__main__":
    print("📊 Testing Firebase DAL\n")
    
    # Test schema validation
    print("1. Testing Schema Validation:")
    
    try:
        # Valid conversation
        conv = ConversationSchema(title="Test Conversation")
        print(f"   ✅ Valid conversation: {conv.title}")
    except Exception as e:
        print(f"   ❌ Validation error: {e}")
    
    try:
        # Invalid conversation (title too short)
        conv = ConversationSchema(title="")
        print(f"   ❌ Should have failed validation")
    except Exception as e:
        print(f"   ✅ Correctly rejected invalid data")
    
    # Test cache
    print("\n2. Testing LRU Cache:")
    cache = LRUCache(max_size=3)
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    print(f"   Cache size: {len(cache.cache)}")
    print(f"   Get key1: {cache.get('key1')}")
    print(f"   Get key4 (miss): {cache.get('key4')}")
    
    # Add one more (should evict oldest)
    cache.set("key4", "value4")
    print(f"   After adding key4, key2 exists: {'key2' in cache.cache}")
    
    stats = cache.get_stats()
    print(f"   Cache stats: {stats}")
    
    print("\n✅ Firebase DAL tests completed!")
