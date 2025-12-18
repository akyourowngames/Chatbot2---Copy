"""
KAI OS - Production Configuration
================================
Secure settings for production deployment.
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==================== ENVIRONMENT ====================
ENV = os.getenv("FLASK_ENV", "development")
IS_PRODUCTION = ENV == "production"
DEBUG = not IS_PRODUCTION

# ==================== SERVER CONFIGURATION ====================
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
WORKERS = int(os.getenv("WORKERS", 4))  # For Gunicorn

# ==================== SECURITY CONFIGURATION ====================

# CORS Configuration - Restrict in production!
CORS_ALLOWED_ORIGINS: List[str] = []

if IS_PRODUCTION:
    # Production: Only allow specific origins
    _origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if _origins:
        CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _origins.split(",")]
    else:
        # Default to Electron app and localhost only
        CORS_ALLOWED_ORIGINS = [
            "file://",  # Electron app
            "http://localhost:5000",
            "http://127.0.0.1:5000",
        ]
else:
    # Development: Allow all origins for easier testing
    CORS_ALLOWED_ORIGINS = ["*"]

# CORS Settings
CORS_SETTINGS = {
    "origins": CORS_ALLOWED_ORIGINS,
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "X-API-Key", "X-Requested-With"],
    "supports_credentials": True,
    "max_age": 600,  # 10 minutes preflight cache
}

# API Keys - NEVER use defaults in production!
API_KEY = os.getenv("API_KEY")
DEVELOPER_API_KEY = os.getenv("DEVELOPER_API_KEY")

if IS_PRODUCTION:
    if not API_KEY or API_KEY == "demo_key_12345":
        raise ValueError("❌ CRITICAL: Set a secure API_KEY in production!")
    if not DEVELOPER_API_KEY or DEVELOPER_API_KEY == "demo_key_12345":
        raise ValueError("❌ CRITICAL: Set a secure DEVELOPER_API_KEY in production!")

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7))

if IS_PRODUCTION and (not JWT_SECRET_KEY or len(JWT_SECRET_KEY) < 32):
    raise ValueError("❌ CRITICAL: Set a secure JWT_SECRET_KEY (min 32 chars) in production!")

# Encryption Key
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if IS_PRODUCTION and not ENCRYPTION_KEY:
    raise ValueError("❌ CRITICAL: Set ENCRYPTION_KEY in production!")

# ==================== RATE LIMITING ====================
RATE_LIMIT_ENABLED = IS_PRODUCTION or os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"

# Requests per minute
RATE_LIMITS = {
    "default": 60,        # 60 requests per minute
    "chat": 30,           # 30 chat requests per minute
    "auth": 10,           # 10 auth attempts per minute
    "image_gen": 5,       # 5 image generations per minute
    "heavy": 10,          # Heavy operations (scraping, automation)
}

# ==================== SECURITY HEADERS ====================
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

if IS_PRODUCTION:
    SECURITY_HEADERS["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

# ==================== LOGGING ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if IS_PRODUCTION else "DEBUG")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.getenv("LOG_FILE", "logs/kai_os.log")

# ==================== DATABASE ====================
# Firebase
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")

# Supabase (optional)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ==================== EXTERNAL APIS ====================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# Features APIs
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ==================== FEATURE FLAGS ====================
FEATURES = {
    "voice_enabled": os.getenv("FEATURE_VOICE", "true").lower() == "true",
    "gesture_enabled": os.getenv("FEATURE_GESTURE", "true").lower() == "true",
    "automation_enabled": os.getenv("FEATURE_AUTOMATION", "true").lower() == "true",
    "image_gen_enabled": os.getenv("FEATURE_IMAGE_GEN", "true").lower() == "true",
    "websocket_enabled": os.getenv("FEATURE_WEBSOCKET", "true").lower() == "true",
}

# ==================== VALIDATION ====================
def validate_config():
    """Validate critical configuration for production."""
    errors = []
    warnings = []
    
    if IS_PRODUCTION:
        # Check API Keys
        if not GEMINI_API_KEY and not GROQ_API_KEY and not OPENAI_API_KEY:
            errors.append("At least one AI API key must be set (GEMINI, GROQ, or OPENAI)")
        
        # Check Firebase (if using)
        if FIREBASE_PROJECT_ID and not FIREBASE_CREDENTIALS_PATH:
            warnings.append("FIREBASE_PROJECT_ID set but no FIREBASE_CREDENTIALS_PATH")
        
        # Check CORS
        if "*" in CORS_ALLOWED_ORIGINS:
            errors.append("CORS allows all origins (*) - this is insecure in production!")
    
    if errors:
        print("\n❌ CONFIGURATION ERRORS:")
        for err in errors:
            print(f"   • {err}")
        raise ValueError("Configuration validation failed. Fix the above errors.")
    
    if warnings:
        print("\n⚠️ CONFIGURATION WARNINGS:")
        for warn in warnings:
            print(f"   • {warn}")
    
    print(f"\n✅ Configuration validated for {ENV} environment")

# ==================== HELPER FUNCTIONS ====================
def get_cors_origins() -> List[str]:
    """Get CORS origins for current environment."""
    return CORS_ALLOWED_ORIGINS

def is_origin_allowed(origin: Optional[str]) -> bool:
    """Check if an origin is allowed."""
    if "*" in CORS_ALLOWED_ORIGINS:
        return True
    if not origin:
        return False
    return any(
        origin.startswith(allowed) or origin == allowed
        for allowed in CORS_ALLOWED_ORIGINS
    )

# Export configuration summary
def print_config_summary():
    """Print current configuration (safe values only)."""
    print("\n" + "=" * 50)
    print("🚀 KAI OS - Configuration Summary")
    print("=" * 50)
    print(f"Environment: {ENV}")
    print(f"Debug Mode: {DEBUG}")
    print(f"Host: {HOST}:{PORT}")
    print(f"CORS Origins: {len(CORS_ALLOWED_ORIGINS)} allowed")
    print(f"Rate Limiting: {'Enabled' if RATE_LIMIT_ENABLED else 'Disabled'}")
    print(f"Features: {sum(FEATURES.values())}/{len(FEATURES)} enabled")
    print("=" * 50 + "\n")


# Validate on import in production
if IS_PRODUCTION:
    validate_config()
