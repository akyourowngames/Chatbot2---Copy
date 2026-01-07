"""
Security Manager - Encryption, Hashing, and JWT Token Management
=================================================================
Handles all security operations for the AI assistant
"""

import bcrypt
import secrets
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
from jose import JWTError, jwt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityManager:
    """Centralized security management for authentication and encryption"""
    
    def __init__(self):
        """Initialize security manager with encryption keys"""
        # JWT Configuration
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", self._generate_secret_key())
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_expire_days = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        # Encryption Configuration
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            # Generate a new key if not provided
            encryption_key = Fernet.generate_key().decode()
            logger.warning(f"[SECURITY] No ENCRYPTION_KEY found. Generated new key. Add to .env: ENCRYPTION_KEY={encryption_key}")
        
        self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        
        # Password hashing configuration
        self.bcrypt_rounds = 12  # Salt rounds for bcrypt
        
        logger.info("[SECURITY] Security Manager initialized")
    
    # ==================== PASSWORD HASHING ====================
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password as string
        """
        try:
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt(rounds=self.bcrypt_rounds)
            hashed = bcrypt.hashpw(password_bytes, salt)
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"[SECURITY] Password hashing error: {e}")
            raise
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            password_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            logger.error(f"[SECURITY] Password verification error: {e}")
            return False
    
    # ==================== FIELD ENCRYPTION ====================
    
    def encrypt_field(self, data: str) -> str:
        """
        Encrypt sensitive data (API keys, secrets, etc.)
        
        Args:
            data: Plain text data to encrypt
            
        Returns:
            Encrypted data as string
        """
        try:
            if not data:
                return ""
            data_bytes = data.encode('utf-8')
            encrypted = self.cipher.encrypt(data_bytes)
            return encrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"[SECURITY] Encryption error: {e}")
            raise
    
    def decrypt_field(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data
        
        Args:
            encrypted_data: Encrypted data string
            
        Returns:
            Decrypted plain text data
        """
        try:
            if not encrypted_data:
                return ""
            encrypted_bytes = encrypted_data.encode('utf-8')
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"[SECURITY] Decryption error: {e}")
            raise
    
    # ==================== JWT TOKEN MANAGEMENT ====================
    
    def create_access_token(self, user_id: str, email: str, role: str = "user") -> str:
        """
        Create a JWT access token
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            role: User's role (admin, user)
            
        Returns:
            JWT access token as string
        """
        try:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            
            payload = {
                "sub": user_id,  # Subject (user ID)
                "email": email,
                "role": role,
                "exp": expire,  # Expiration time
                "iat": datetime.utcnow(),  # Issued at
                "type": "access"
            }
            
            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            return token
        except Exception as e:
            logger.error(f"[SECURITY] Access token creation error: {e}")
            raise
    
    def create_refresh_token(self, user_id: str) -> str:
        """
        Create a JWT refresh token (longer expiration)
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            JWT refresh token as string
        """
        try:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
            
            payload = {
                "sub": user_id,
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "refresh"
            }
            
            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            return token
        except Exception as e:
            logger.error(f"[SECURITY] Refresh token creation error: {e}")
            raise
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token string
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Verify token type
            if payload.get("type") != token_type:
                logger.warning(f"[SECURITY] Token type mismatch. Expected {token_type}, got {payload.get('type')}")
                return None
            
            return payload
        except JWTError as e:
            logger.warning(f"[SECURITY] Token verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"[SECURITY] Token verification error: {e}")
            return None
    
    def extract_user_from_token(self, token: str) -> Optional[Dict[str, str]]:
        """
        Extract user information from a valid access token
        
        Args:
            token: JWT access token
            
        Returns:
            Dictionary with user_id, email, and role if valid, None otherwise
        """
        payload = self.verify_token(token, token_type="access")
        if not payload:
            return None
        
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "user")
        }
    
    # ==================== UTILITY FUNCTIONS ====================
    
    def _generate_secret_key(self, length: int = 64) -> str:
        """
        Generate a random secret key for JWT
        
        Args:
            length: Length of the secret key
            
        Returns:
            Random secret key as hex string
        """
        return secrets.token_hex(length)
    
    def generate_csrf_token(self) -> str:
        """
        Generate a CSRF token for web forms
        
        Returns:
            Random CSRF token
        """
        return secrets.token_urlsafe(32)
    
    def sanitize_input(self, input_string: str, max_length: int = 1000) -> str:
        """
        Sanitize user input to prevent injection attacks
        
        Args:
            input_string: User input to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not input_string:
            return ""
        
        # Truncate to max length
        sanitized = input_string[:max_length]
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Strip leading/trailing whitespace
        sanitized = sanitized.strip()
        
        return sanitized


# Global security manager instance
security_manager = SecurityManager()


# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    """Hash a password (convenience function)"""
    return security_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password (convenience function)"""
    return security_manager.verify_password(plain_password, hashed_password)


def encrypt_field(data: str) -> str:
    """Encrypt sensitive data (convenience function)"""
    return security_manager.encrypt_field(data)


def decrypt_field(encrypted_data: str) -> str:
    """Decrypt sensitive data (convenience function)"""
    return security_manager.decrypt_field(encrypted_data)


def create_access_token(user_id: str, email: str, role: str = "user") -> str:
    """Create JWT access token (convenience function)"""
    return security_manager.create_access_token(user_id, email, role)


def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token (convenience function)"""
    return security_manager.create_refresh_token(user_id)


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify JWT token (convenience function)"""
    return security_manager.verify_token(token, token_type)


def extract_user_from_token(token: str) -> Optional[Dict[str, str]]:
    """Extract user from JWT token (convenience function)"""
    return security_manager.extract_user_from_token(token)


# ==================== TESTING ====================

if __name__ == "__main__":
    print("🔒 Testing Security Manager\n")
    
    # Test password hashing
    print("1. Password Hashing:")
    password = "MySecurePassword123!"
    hashed = hash_password(password)
    print(f"   Original: {password}")
    print(f"   Hashed: {hashed[:50]}...")
    print(f"   Verification: {verify_password(password, hashed)}")
    print(f"   Wrong password: {verify_password('WrongPassword', hashed)}\n")
    
    # Test encryption
    print("2. Field Encryption:")
    secret_data = "sk-1234567890abcdef"
    encrypted = encrypt_field(secret_data)
    decrypted = decrypt_field(encrypted)
    print(f"   Original: {secret_data}")
    print(f"   Encrypted: {encrypted[:50]}...")
    print(f"   Decrypted: {decrypted}\n")
    
    # Test JWT tokens
    print("3. JWT Tokens:")
    user_id = "user_12345"
    email = "test@example.com"
    role = "admin"
    
    access_token = create_access_token(user_id, email, role)
    refresh_token = create_refresh_token(user_id)
    
    print(f"   Access Token: {access_token[:50]}...")
    print(f"   Refresh Token: {refresh_token[:50]}...")
    
    # Verify access token
    user_info = extract_user_from_token(access_token)
    print(f"   Extracted User: {user_info}\n")
    
    # Test token verification
    print("4. Token Verification:")
    valid_payload = verify_token(access_token, "access")
    print(f"   Valid access token: {valid_payload is not None}")
    print(f"   Invalid token: {verify_token('invalid_token', 'access') is None}")
    
    print("\n✅ Security Manager tests completed!")
