"""
Firebase Authentication System
===============================
Complete authentication with email/password and Google OAuth
"""

import firebase_admin
from firebase_admin import auth, firestore
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
import logging
import re
from Backend.SecurityManager import hash_password, verify_password, create_access_token, create_refresh_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FirebaseAuth:
    """Firebase-based authentication system with JWT tokens"""
    
    def __init__(self, db):
        """
        Initialize Firebase Auth
        
        Args:
            db: Firestore database client
        """
        self.db = db
        self.users_collection = "users"
        logger.info("[AUTH] Firebase Auth initialized")
    
    # ==================== USER REGISTRATION ====================
    
    def register_user(self, email: str, password: str, role: str = "user") -> Tuple[bool, str, Optional[Dict]]:
        """
        Register a new user with email and password
        
        Args:
            email: User's email address
            password: User's password (will be hashed)
            role: User role (default: "user", can be "admin")
            
        Returns:
            Tuple of (success, message, user_data)
        """
        try:
            # Validate email format
            if not self._is_valid_email(email):
                return False, "Invalid email format", None
            
            # Validate password strength
            is_strong, msg = self._is_strong_password(password)
            if not is_strong:
                return False, msg, None
            
            # Check if user already exists
            existing_user = self._get_user_by_email(email)
            if existing_user:
                return False, "Email already registered", None
            
            # Hash password
            password_hash = hash_password(password)
            
            # Create user document
            user_data = {
                "email": email,
                "password_hash": password_hash,
                "role": role,
                "created_at": datetime.utcnow(),
                "last_login": None,
                "email_verified": False,
                "google_oauth_id": None
            }
            
            # Add to Firestore
            user_ref = self.db.collection(self.users_collection).add(user_data)
            user_id = user_ref[1].id
            
            logger.info(f"[AUTH] User registered: {email} (ID: {user_id})")
            
            # Return user data without password hash
            user_data_safe = {
                "user_id": user_id,
                "email": email,
                "role": role,
                "created_at": user_data["created_at"].isoformat()
            }
            
            return True, "User registered successfully", user_data_safe
            
        except Exception as e:
            logger.error(f"[AUTH] Registration error: {e}")
            return False, f"Registration failed: {str(e)}", None
    
    # ==================== USER LOGIN ====================
    
    def login_user(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Login user with email and password
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Tuple of (success, message, auth_data with tokens)
        """
        try:
            # Get user from database
            user_doc = self._get_user_by_email(email)
            if not user_doc:
                return False, "Invalid email or password", None
            
            user_id = user_doc["user_id"]
            user_data = user_doc["data"]
            
            # Verify password
            if not verify_password(password, user_data["password_hash"]):
                return False, "Invalid email or password", None
            
            # Update last login
            self.db.collection(self.users_collection).document(user_id).update({
                "last_login": datetime.utcnow()
            })
            
            # Generate JWT tokens
            access_token = create_access_token(user_id, email, user_data["role"])
            refresh_token = create_refresh_token(user_id)
            
            logger.info(f"[AUTH] User logged in: {email}")
            
            auth_data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "user": {
                    "user_id": user_id,
                    "email": email,
                    "role": user_data["role"]
                }
            }
            
            return True, "Login successful", auth_data
            
        except Exception as e:
            logger.error(f"[AUTH] Login error: {e}")
            return False, f"Login failed: {str(e)}", None
    
    # ==================== GOOGLE OAUTH ====================
    
    def login_with_google(self, google_id_token: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Login or register user with Google OAuth
        
        Args:
            google_id_token: Google ID token from OAuth flow
            
        Returns:
            Tuple of (success, message, auth_data with tokens)
        """
        try:
            # Verify Google ID token
            decoded_token = auth.verify_id_token(google_id_token)
            google_user_id = decoded_token['uid']
            email = decoded_token.get('email')
            
            if not email:
                return False, "Email not provided by Google", None
            
            # Check if user exists
            user_doc = self._get_user_by_email(email)
            
            if user_doc:
                # Existing user - update Google OAuth ID if not set
                user_id = user_doc["user_id"]
                user_data = user_doc["data"]
                
                if not user_data.get("google_oauth_id"):
                    self.db.collection(self.users_collection).document(user_id).update({
                        "google_oauth_id": google_user_id
                    })
                
            else:
                # New user - create account
                user_data = {
                    "email": email,
                    "password_hash": "",  # No password for OAuth users
                    "role": "user",
                    "created_at": datetime.utcnow(),
                    "last_login": None,
                    "email_verified": True,  # Google verifies emails
                    "google_oauth_id": google_user_id
                }
                
                user_ref = self.db.collection(self.users_collection).add(user_data)
                user_id = user_ref[1].id
                
                logger.info(f"[AUTH] New Google user registered: {email}")
            
            # Update last login
            self.db.collection(self.users_collection).document(user_id).update({
                "last_login": datetime.utcnow()
            })
            
            # Generate JWT tokens
            access_token = create_access_token(user_id, email, user_data["role"])
            refresh_token = create_refresh_token(user_id)
            
            logger.info(f"[AUTH] Google login successful: {email}")
            
            auth_data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "user": {
                    "user_id": user_id,
                    "email": email,
                    "role": user_data["role"]
                }
            }
            
            return True, "Google login successful", auth_data
            
        except Exception as e:
            logger.error(f"[AUTH] Google login error: {e}")
            return False, f"Google login failed: {str(e)}", None
    
    # ==================== USER MANAGEMENT ====================
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """
        Get user profile information
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            User profile data (without password hash)
        """
        try:
            user_doc = self.db.collection(self.users_collection).document(user_id).get()
            
            if not user_doc.exists:
                return None
            
            user_data = user_doc.to_dict()
            
            # Remove sensitive data
            return {
                "user_id": user_id,
                "email": user_data["email"],
                "role": user_data["role"],
                "created_at": user_data["created_at"].isoformat() if user_data.get("created_at") else None,
                "last_login": user_data["last_login"].isoformat() if user_data.get("last_login") else None,
                "email_verified": user_data.get("email_verified", False)
            }
            
        except Exception as e:
            logger.error(f"[AUTH] Get user profile error: {e}")
            return None
    
    def update_user_profile(self, user_id: str, updates: Dict) -> Tuple[bool, str]:
        """
        Update user profile (limited fields)
        
        Args:
            user_id: User's unique identifier
            updates: Dictionary of fields to update
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Only allow updating specific fields
            allowed_fields = ["email_verified"]
            filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
            
            if not filtered_updates:
                return False, "No valid fields to update"
            
            self.db.collection(self.users_collection).document(user_id).update(filtered_updates)
            
            logger.info(f"[AUTH] User profile updated: {user_id}")
            return True, "Profile updated successfully"
            
        except Exception as e:
            logger.error(f"[AUTH] Update profile error: {e}")
            return False, f"Update failed: {str(e)}"
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Change user password
        
        Args:
            user_id: User's unique identifier
            old_password: Current password
            new_password: New password
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get user
            user_doc = self.db.collection(self.users_collection).document(user_id).get()
            if not user_doc.exists:
                return False, "User not found"
            
            user_data = user_doc.to_dict()
            
            # Verify old password
            if not verify_password(old_password, user_data["password_hash"]):
                return False, "Current password is incorrect"
            
            # Validate new password
            is_strong, msg = self._is_strong_password(new_password)
            if not is_strong:
                return False, msg
            
            # Hash new password
            new_password_hash = hash_password(new_password)
            
            # Update password
            self.db.collection(self.users_collection).document(user_id).update({
                "password_hash": new_password_hash
            })
            
            logger.info(f"[AUTH] Password changed for user: {user_id}")
            return True, "Password changed successfully"
            
        except Exception as e:
            logger.error(f"[AUTH] Change password error: {e}")
            return False, f"Password change failed: {str(e)}"
    
    def delete_user(self, user_id: str) -> Tuple[bool, str]:
        """
        Delete user account and all associated data
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Delete user document
            self.db.collection(self.users_collection).document(user_id).delete()
            
            # Note: In production, you should also delete all user's data from other collections
            # This would be done in a background task to avoid timeout
            
            logger.info(f"[AUTH] User deleted: {user_id}")
            return True, "Account deleted successfully"
            
        except Exception as e:
            logger.error(f"[AUTH] Delete user error: {e}")
            return False, f"Account deletion failed: {str(e)}"
    
    # ==================== HELPER FUNCTIONS ====================
    
    def _get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user document by email"""
        try:
            users = self.db.collection(self.users_collection).where("email", "==", email).limit(1).stream()
            
            for user in users:
                return {
                    "user_id": user.id,
                    "data": user.to_dict()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"[AUTH] Get user by email error: {e}")
            return None
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_strong_password(self, password: str) -> Tuple[bool, str]:
        """
        Validate password strength
        
        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        return True, "Password is strong"


# ==================== TESTING ====================

if __name__ == "__main__":
    print("🔐 Testing Firebase Auth\n")
    
    # Note: This requires Firebase to be initialized
    # For testing, we'll just validate the password strength function
    
    auth_system = FirebaseAuth(None)
    
    print("Testing password strength validation:")
    test_passwords = [
        ("weak", False),
        ("Weak123", True),
        ("StrongPassword123", True),
        ("short1A", False),
        ("nouppercase123", False),
        ("NOLOWERCASE123", False),
        ("NoDigitsHere", False)
    ]
    
    for password, should_pass in test_passwords:
        is_strong, msg = auth_system._is_strong_password(password)
        status = "✅" if is_strong == should_pass else "❌"
        print(f"{status} '{password}': {msg}")
    
    print("\n✅ Firebase Auth tests completed!")
