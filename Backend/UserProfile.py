"""
User Profile - Firebase Storage
================================
Store and retrieve user details for auto-fill capabilities.
Syncs with Firebase for cross-device access.
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Firebase imports (lazy load)
firebase_db = None

def get_firebase():
    """Lazy load Firebase"""
    global firebase_db
    if firebase_db is None:
        try:
            from Backend.FirebaseStorage import get_firebase_storage
            fs = get_firebase_storage()
            firebase_db = fs.db
        except Exception as e:
            print(f"[PROFILE] Firebase not available: {e}")
    return firebase_db


class UserProfile:
    """
    Manages user profile data for automation features.
    
    Usage:
    - profile.get("name") → "Krish"
    - profile.set("phone", "+91 12345")
    - profile.auto_fill_data() → Dict for form filling
    """
    
    # Standard fields for form auto-fill
    STANDARD_FIELDS = [
        "name", "first_name", "last_name",
        "email", "phone", "mobile",
        "address", "city", "state", "country", "zip", "pincode",
        "company", "job_title", "website",
        "date_of_birth", "gender"
    ]
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.local_cache: Dict[str, Any] = {}
        self.cache_file = os.path.join(
            os.path.dirname(__file__), "..", "data", "user_profile.json"
        )
        
        # Load from local cache first
        self._load_local()
        
        # Sync with Firebase
        self._sync_from_firebase()
        
        print(f"[PROFILE] Loaded for user: {user_id}")
    
    def _load_local(self):
        """Load from local cache file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r") as f:
                    self.local_cache = json.load(f)
        except Exception as e:
            print(f"[PROFILE] Local load error: {e}")
    
    def _save_local(self):
        """Save to local cache file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, "w") as f:
                json.dump(self.local_cache, f, indent=2)
        except Exception as e:
            print(f"[PROFILE] Local save error: {e}")
    
    def _sync_from_firebase(self):
        """Sync profile from Firebase"""
        db = get_firebase()
        if not db:
            return
        
        try:
            doc = db.collection("user_profiles").document(self.user_id).get()
            if doc.exists:
                firebase_data = doc.to_dict()
                # Merge with local (Firebase takes priority)
                self.local_cache.update(firebase_data)
                self._save_local()
        except Exception as e:
            print(f"[PROFILE] Firebase sync error: {e}")
    
    def _sync_to_firebase(self):
        """Sync profile to Firebase"""
        db = get_firebase()
        if not db:
            return
        
        try:
            db.collection("user_profiles").document(self.user_id).set(
                self.local_cache, merge=True
            )
        except Exception as e:
            print(f"[PROFILE] Firebase save error: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a profile field"""
        return self.local_cache.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set a profile field"""
        self.local_cache[key] = value
        self.local_cache["updated_at"] = datetime.now().isoformat()
        
        self._save_local()
        self._sync_to_firebase()
        
        return True
    
    def update(self, data: Dict[str, Any]) -> bool:
        """Bulk update profile fields"""
        self.local_cache.update(data)
        self.local_cache["updated_at"] = datetime.now().isoformat()
        
        self._save_local()
        self._sync_to_firebase()
        
        return True
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire profile"""
        return self.local_cache.copy()
    
    def auto_fill_data(self) -> Dict[str, str]:
        """
        Get data formatted for form auto-fill.
        Maps common form field names to profile values.
        """
        mappings = {
            # Name variations
            "name": self.get("name", ""),
            "full_name": self.get("name", ""),
            "fullname": self.get("name", ""),
            "first_name": self.get("first_name", self.get("name", "").split()[0] if self.get("name") else ""),
            "firstname": self.get("first_name", ""),
            "last_name": self.get("last_name", self.get("name", "").split()[-1] if self.get("name") else ""),
            "lastname": self.get("last_name", ""),
            
            # Contact
            "email": self.get("email", ""),
            "email_address": self.get("email", ""),
            "phone": self.get("phone", ""),
            "phone_number": self.get("phone", ""),
            "mobile": self.get("mobile", self.get("phone", "")),
            "telephone": self.get("phone", ""),
            
            # Address
            "address": self.get("address", ""),
            "street": self.get("address", ""),
            "street_address": self.get("address", ""),
            "city": self.get("city", ""),
            "state": self.get("state", ""),
            "country": self.get("country", ""),
            "zip": self.get("zip", self.get("pincode", "")),
            "zipcode": self.get("zip", self.get("pincode", "")),
            "postal_code": self.get("zip", self.get("pincode", "")),
            "pincode": self.get("pincode", ""),
            
            # Professional
            "company": self.get("company", ""),
            "organization": self.get("company", ""),
            "job_title": self.get("job_title", ""),
            "title": self.get("job_title", ""),
            "website": self.get("website", ""),
            "url": self.get("website", ""),
        }
        
        # Filter out empty values
        return {k: v for k, v in mappings.items() if v}
    
    def get_summary(self) -> str:
        """Get human-readable profile summary"""
        name = self.get("name", "Not set")
        email = self.get("email", "Not set")
        phone = self.get("phone", "Not set")
        
        return f"👤 {name} | 📧 {email} | 📱 {phone}"


# Singleton instance
user_profile = UserProfile()


# Quick access
def get_profile() -> UserProfile:
    """Get the user profile instance"""
    return user_profile

def set_profile_field(key: str, value: Any) -> bool:
    """Set a profile field"""
    return user_profile.set(key, value)

def get_auto_fill() -> Dict[str, str]:
    """Get auto-fill data"""
    return user_profile.auto_fill_data()


if __name__ == "__main__":
    print("User Profile Test")
    print(f"Summary: {user_profile.get_summary()}")
    print(f"Auto-fill fields: {len(user_profile.auto_fill_data())}")
