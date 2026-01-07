"""
JARVIS API Server - The Brain of the Desktop Assistant
======================================================
Serving all AI capabilities via REST API

PRODUCTION-READY with secure CORS, rate limiting, and security headers.
"""

from flask import Flask, request, jsonify, send_from_directory, redirect
# from flask_cors import CORS  # DISABLED - using manual cors_sanitizer instead
import threading
import json
import os
import base64
import time
import asyncio
from typing import Dict, Any, List
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
# Explicitly define path to .env file relative to this script
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
load_dotenv(env_path)
from Backend.YouTubePlayer import youtube_player

app = Flask(__name__)

# Register Local Agent API blueprint for device management endpoints
try:
    from Backend.LocalAgentAPI import local_agent_bp
    app.register_blueprint(local_agent_bp)
    print("[INIT] ✅ Local Agent API endpoints registered (/agent/*)")
except Exception as e:
    print(f"[INIT] ⚠️ Local Agent API not loaded: {e}")

# ==================== CORS SANITIZER (ONLY CORS HANDLER) ====================
# Allowed origins for CORS (add more as needed)
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.1.104:3000",  # LAN IP
    # Production origins
    "https://kai2010.netlify.app",
    "https://kai-frontend.onrender.com",
    "https://kai-api-nxxv.onrender.com",
]

@app.after_request
def cors_sanitizer(response):
    """
    Complete CORS handler - Flask-CORS is DISABLED.
    This is now the ONLY source of CORS headers.
    Dynamically allows the request's origin if it's in the allowed list.
    """
    if request.path.startswith('/agent/') or request.path.startswith('/api/'):
        # Get the request's origin
        origin = request.headers.get('Origin', '')
        
        # Check if origin is allowed (dev + production patterns)
        if origin in ALLOWED_ORIGINS or origin.startswith('http://localhost:') or origin.startswith('http://192.168.') or origin.endswith('.netlify.app') or origin.endswith('.onrender.com'):
            allowed_origin = origin
        else:
            allowed_origin = "https://kai2010.netlify.app"  # fallback to production
        
        print(f"[CORS_SANITIZER] {request.method} {request.path} -> Origin: {origin} -> Allowed: {allowed_origin}")
        
        # DELETE any existing CORS headers first (safety)
        for header in ['Access-Control-Allow-Origin', 'Access-Control-Allow-Credentials', 
                       'Access-Control-Allow-Methods', 'Access-Control-Allow-Headers']:
            if header in response.headers:
                del response.headers[header]
        
        # Set all required CORS headers with the correct origin
        response.headers['Access-Control-Allow-Origin'] = allowed_origin
        response.headers['Access-Control-Allow-Credentials'] = "true"
        response.headers['Access-Control-Allow-Methods'] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers['Access-Control-Allow-Headers'] = "Content-Type, Authorization, X-API-Key, X-Requested-With, X-Drive-Token, X-User-Id, X-User-ID"
        response.headers['Access-Control-Max-Age'] = "600"
            
    return response

# ==================== SECURE CORS CONFIGURATION ====================
# Determine environment
FLASK_ENV = os.getenv("FLASK_ENV", "development")
IS_PRODUCTION = FLASK_ENV == "production"

# Get allowed origins from environment or use defaults
def get_cors_origins() -> List[str]:
    """Get CORS allowed origins based on environment."""
    if IS_PRODUCTION:
        # Production: Only allow specific origins
        origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "")
        if origins_str:
            return [origin.strip() for origin in origins_str.split(",")]
        # Default production origins (Electron app + localhost)
        return [
            "file://",  # Electron app
            "http://localhost:5000",
            "http://127.0.0.1:5000",
            "https://localhost:5000",
        ]
    else:
        # Development: Allow all for easier testing
        return ["*"]

CORS_ORIGINS = get_cors_origins()
print(f"[CORS] Environment: {FLASK_ENV}, Allowed origins: {CORS_ORIGINS[:3]}{'...' if len(CORS_ORIGINS) > 3 else ''}")

# Configure CORS - Explicit origin required when using Authorization headers
# Browser rejects wildcard (*) when auth headers are present
FRONTEND_ORIGIN = "http://localhost:3000"

# DISABLED: Flask-CORS was causing duplicate headers. Using cors_sanitizer instead.
# CORS(app, resources={
#     r"/api/*": {
#         "origins": FRONTEND_ORIGIN,
#         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#         "allow_headers": ["Content-Type", "Authorization", "X-API-Key", "X-Requested-With", "X-Drive-Token", "X-User-Id"],
#         "supports_credentials": True,
#         "max_age": 600,
#     },
#     r"/agent/*": {
#         "origins": FRONTEND_ORIGIN,
#         "methods": ["GET", "POST", "OPTIONS"],
#         "allow_headers": ["Content-Type", "Authorization", "X-User-ID"],
#         "supports_credentials": True,
#         "max_age": 600,
#     },
#     # STRICT MODE: No wildcards anywhere
#     r"/health": {"origins": FRONTEND_ORIGIN},
#     r"/data/*": {"origins": FRONTEND_ORIGIN},
# })

# ==================== SECURITY MIDDLEWARE ====================
try:
    from Backend.SecurityMiddleware import setup_security_middleware, add_security_headers
    from Backend.RateLimiter import rate_limit, add_rate_limit_headers, configure_rate_limits
    
    # Set up security middleware (headers, IP blocking, request validation)
    setup_security_middleware(app)
    
    # Add rate limit headers to all responses
    app.after_request(add_rate_limit_headers)
    
    # Configure rate limits based on environment
    if IS_PRODUCTION:
        configure_rate_limits({
            "default": 60,    # 60 requests/minute
            "chat": 30,       # 30 chat requests/minute
            "auth": 10,       # 10 auth attempts/minute
            "image_gen": 5,   # 5 image generations/minute
            "heavy": 10,      # 10 heavy operations/minute
        })
    else:
        # More lenient for development
        configure_rate_limits({
            "default": 200,
            "chat": 100,
            "auth": 50,
            "image_gen": 20,
            "heavy": 50,
        })
    

    
    SECURITY_ENABLED = True
    print("[OK] Security middleware loaded")
except ImportError as e:
    print(f"[WARN] Security middleware not available: {e}")
    SECURITY_ENABLED = False
    rate_limit = lambda *args, **kwargs: lambda f: f  # No-op decorator

# NOTE: LocalAgentAPI blueprint registered at app creation (line 32-37)

# Imports for Vision + File Upload (Optional - may not be available in cloud deployment)
try:
    from Backend.api.upload import upload_endpoint
    from Backend.api.list import list_endpoint
    from Backend.api.download import download_endpoint
    from Backend.api.delete import delete_endpoint
    from Backend.api.analyze import analyze_endpoint 
    from Backend.api.analyze_image import analyze_image_endpoint
    VISION_AVAILABLE = True
    print("[OK] Vision + File Upload modules loaded")
except ImportError as e:
    print(f"[WARN] Vision + File Upload not available (expected in cloud): {e}")
    VISION_AVAILABLE = False
    upload_endpoint = list_endpoint = download_endpoint = delete_endpoint = None
    analyze_endpoint = analyze_image_endpoint = None

# ==================== PRELOAD MEMORY SYSTEM ====================
# Load all memory systems at startup so first message is fast
try:
    from Backend.ContextualMemory import contextual_memory
    print(f"[OK] ContextualMemory preloaded: {len(contextual_memory.memory.get('facts', []))} facts synced from Supabase")
except Exception as e:
    print(f"[WARN] ContextualMemory preload failed: {e}")
    contextual_memory = None

# Preload SemanticMemory (SentenceTransformer model takes 1-2s to load)
try:
    from Backend.SemanticMemory import SemanticMemory
    _semantic_memory = SemanticMemory()  # This loads the all-MiniLM-L6-v2 model
    print(f"[OK] SemanticMemory preloaded: {len(_semantic_memory.memories)} memories loaded")
except Exception as e:
    print(f"[WARN] SemanticMemory preload failed: {e}")
    _semantic_memory = None

# Preload MemoryIntelligence 
try:
    from Backend.MemoryIntelligence import MemoryIntelligence
    _memory_intelligence = MemoryIntelligence()
    print(f"[OK] MemoryIntelligence preloaded")
except Exception as e:
    print(f"[WARN] MemoryIntelligence preload failed: {e}")
    _memory_intelligence = None

# Preload Per-User Memory System (NEW - Beast Mode)
try:
    from Backend.PerUserMemory import per_user_memory, remember, recall, get_context
    from Backend.PerUserChatbot import PerUserChatBot, get_user_memory_summary
    _per_user_memory = per_user_memory
    PER_USER_MEMORY_ENABLED = True
    print(f"[OK] Per-User Memory System preloaded (Beast Mode)")
except Exception as e:
    print(f"[WARN] Per-User Memory System preload failed: {e}")
    _per_user_memory = None
    PER_USER_MEMORY_ENABLED = False
    def remember(*args, **kwargs): return False
    def recall(*args, **kwargs): return []
    def get_context(*args, **kwargs): return []

# ==================== WRITING CONTEXT (CONTINUITY) ====================
try:
    from Backend.WritingContext import save_writing, get_last_writing, clear_writing
    WRITING_CONTEXT_ENABLED = True
    print("[OK] WritingContext loaded (writing continuity enabled)")
except Exception as e:
    print(f"[WARN] WritingContext not available: {e}")
    WRITING_CONTEXT_ENABLED = False
    def save_writing(*args, **kwargs): return False
    def get_last_writing(*args, **kwargs): return None
    def clear_writing(*args, **kwargs): return False
    def PerUserChatBot(*args, **kwargs): return {"response": "Memory system unavailable", "type": "error"}
    def get_user_memory_summary(*args, **kwargs): return {}

# from Backend.Dispatcher import dispatcher # KAI Intelligence Engine (Bypassed)

# ==================== HEALTH CHECK (CRITICAL) ====================
@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200

# ==================== CACHE CLEAR ENDPOINT ====================
@app.route("/api/v1/cache/clear", methods=["POST"])
def clear_cache_endpoint():
    """Clear the response cache - use when responses are broken"""
    try:
        from Backend.ResponseCache import clear_cache, get_cache_stats
        stats_before = get_cache_stats()
        clear_cache()
        return {
            "success": True,
            "message": "Cache cleared successfully",
            "cache_before": stats_before
        }, 200
    except Exception as e:
        return {"error": str(e)}, 500

# ==================== GOOGLE DRIVE INTEGRATION ====================
# NOTE: Drive feature temporarily disabled for hackathon polish
# Will be re-enabled after polishing is complete
# Uncomment the code below to restore Drive functionality

# # Session storage for OAuth state (in production, use Redis/DB)
# _oauth_states = {}

# @app.route("/api/v1/drive/auth", methods=["GET"])
# def drive_auth():
#     """Get Google Drive OAuth authorization URL"""
#     try:
#         from Backend.GoogleDriveAPI import get_drive_api
#         api = get_drive_api()
#         
#         if not api.is_available():
#             return {"error": "Google Drive not configured. Set GOOGLE_DRIVE_CLIENT_ID and GOOGLE_DRIVE_CLIENT_SECRET"}, 503
#         
#         auth_url, state = api.get_auth_url()
#         _oauth_states[state] = {"created": datetime.now().isoformat()}
#         
#         return {
#             "auth_url": auth_url,
#             "state": state
#         }, 200
#     except Exception as e:
#         return {"error": str(e)}, 500

# @app.route("/api/v1/drive/callback", methods=["GET"])
# def drive_callback():
#     """OAuth callback - exchange code for tokens and redirect to frontend"""
#     try:
#         from Backend.GoogleDriveAPI import get_drive_api
#         import json
#         import urllib.parse
#         
#         code = request.args.get('code')
#         state = request.args.get('state')
#         error = request.args.get('error')
#         
#         # Frontend URL - redirect there with tokens
#         frontend_url = "http://localhost:3000"
#         
#         if error:
#             return redirect(f"{frontend_url}/drive-callback.html?error={urllib.parse.quote(error)}")
#         
#         if not code or not state:
#             return redirect(f"{frontend_url}/drive-callback.html?error=missing_params")
#         
#         # Verify state
#         if state not in _oauth_states:
#             return redirect(f"{frontend_url}/drive-callback.html?error=invalid_state")
#         
#         del _oauth_states[state]  # Consume state
#         
#         api = get_drive_api()
#         tokens = api.exchange_code(code, state)
#         
#         # Encode tokens as base64 to pass in URL
#         import base64
#         tokens_json = json.dumps(tokens)
#         tokens_b64 = base64.urlsafe_b64encode(tokens_json.encode()).decode()
#         
#         # Redirect to frontend callback page with tokens in URL
#         return redirect(f"{frontend_url}/drive-callback.html?success=true&tokens={tokens_b64}")
#         
#     except Exception as e:
#         import urllib.parse
#         frontend_url = "http://localhost:3000"
#         return redirect(f"{frontend_url}/drive-callback.html?error={urllib.parse.quote(str(e))}")


# @app.route("/api/v1/drive/files", methods=["GET"])
# def drive_list_files():
#     """List user's Google Drive files"""
#     try:
#         from Backend.GoogleDriveAPI import get_drive_api
#         
#         access_token = request.headers.get('X-Drive-Token') or request.args.get('access_token')
#         if not access_token:
#             return {"error": "Access token required (X-Drive-Token header or access_token param)"}, 401
#         
#         page_token = request.args.get('page_token')
#         query = request.args.get('q')
#         
#         api = get_drive_api()
#         result = api.list_files(access_token, page_token=page_token, query=query)
#         
#         return {
#             "files": result['files'],
#             "next_page_token": result.get('next_page_token')
#         }, 200
#     except Exception as e:
#         return {"error": str(e)}, 500

# @app.route("/api/v1/drive/import", methods=["POST"])
# def drive_import_file():
#     """Import a file from Google Drive and extract its content"""
#     try:
#         from Backend.GoogleDriveAPI import get_drive_api
#         
#         data = request.get_json()
#         file_id = data.get('drive_file_id')
#         access_token = data.get('access_token') or request.headers.get('X-Drive-Token')
#         
#         if not file_id:
#             return {"error": "drive_file_id required"}, 400
#         if not access_token:
#             return {"error": "access_token required"}, 401
#         
#         # Download from Drive
#         drive_api = get_drive_api()
#         file_bytes, mime_type, filename = drive_api.download_file(file_id, access_token)
#         
#         # Determine file type
#         ext_map = {
#             'application/pdf': 'pdf',
#             'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
#             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
#             'text/plain': 'txt',
#             'text/csv': 'csv',
#             'application/json': 'json'
#         }
#         file_type = ext_map.get(mime_type, 'unknown')
#         
#         # Extract text content
#         extracted_text = ""
#         try:
#             from Backend.TextExtractor import extract_text_from_file
#             extracted_text = extract_text_from_file(file_bytes, file_type)
#         except Exception as e:
#             print(f"[DRIVE] Text extraction warning: {e}")
#             extracted_text = f"[Unable to extract text from {file_type} file]"
#         
#         # For now, just return the extracted content
#         # In future, could save to SharedFileManager when Firebase is available
#         return {
#             "success": True,
#             "filename": filename,
#             "file_type": file_type,
#             "size": len(file_bytes),
#             "mime_type": mime_type,
#             "extracted_text": extracted_text[:10000] if extracted_text else "",  # Limit to 10k chars
#             "text_length": len(extracted_text) if extracted_text else 0,
#             "message": f"Successfully imported '{filename}' from Google Drive"
#         }, 200
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return {"error": str(e)}, 500

# @app.route("/api/v1/drive/refresh", methods=["POST"])
# def drive_refresh_token():
#     """Refresh an expired access token"""
#     try:
#         from Backend.GoogleDriveAPI import get_drive_api
#         
#         data = request.get_json()
#         refresh_token = data.get('refresh_token')
#         
#         if not refresh_token:
#             return {"error": "refresh_token required"}, 400
#         
#         api = get_drive_api()
#         new_tokens = api.refresh_token(refresh_token)
#         
#         return {
#             "success": True,
#             "access_token": new_tokens['access_token'],
#             "expiry": new_tokens.get('expiry')
#         }, 200
#     except Exception as e:
#         return {"error": str(e)}, 500

# @app.route("/api/v1/vision/analyze", methods=["POST"])
# def vision_analyze_drive_image():
#     """Analyze a Drive image using Vision API"""
#     try:
#         data = request.get_json()
#         drive_file_id = data.get('drive_file_id')
#         access_token = data.get('access_token')
#         prompt = data.get('prompt', 'Describe this image in detail. Extract any visible text.')
#         
#         if not drive_file_id or not access_token:
#             return {"error": "drive_file_id and access_token required"}, 400
#         
#         # Download image from Drive
#         from Backend.GoogleDriveAPI import get_drive_api
#         drive_api = get_drive_api()
#         file_bytes, mime_type, filename = drive_api.download_file(drive_file_id, access_token)
#         
#         if not mime_type.startswith('image/'):
#             return {"error": f"File is not an image: {mime_type}"}, 400
#         
#         # Use Gemini Vision for analysis
#         import google.generativeai as genai
#         import base64
#         
#         # Get Gemini API key
#         gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
#         if not gemini_key:
#             return {"error": "Gemini API key not configured"}, 503
#         
#         genai.configure(api_key=gemini_key)
#         model = genai.GenerativeModel('gemini-1.5-flash')
#         
#         # Create image part
#         image_data = base64.standard_b64encode(file_bytes).decode('utf-8')
#         
#         response = model.generate_content([
#             {
#                 "mime_type": mime_type,
#                 "data": image_data
#             },
#             prompt
#         ])
#         
#         analysis = response.text if response.text else "No analysis generated"
#         
#         return {
#             "success": True,
#             "filename": filename,
#             "analysis": analysis,
#             "mime_type": mime_type
#         }, 200
#         
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return {"error": str(e)}, 500

# ==================== FILE SERVING ====================
@app.route('/data/<path:filename>')
@app.route('/Data/<path:filename>')  # Also handle uppercase for frontend
def serve_files(filename):
    """Serve generic files from Data directory"""
    try:
        return send_from_directory(DATA_DIR, filename)
    except Exception as e:
        return {"error": str(e)}, 404 

# ==================== CONFIGURATION ====================

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data")
os.makedirs(DATA_DIR, exist_ok=True)

# API Key authentication - Load from environment for security
from dotenv import dotenv_values
_env = dotenv_values(".env")
API_KEYS = {}
# Add API keys from .env if configured (format: API_KEY_1=key:name:tier)
for key, value in _env.items():
    if key.startswith("API_KEY_"):
        parts = value.split(":")
        if len(parts) >= 2:
            API_KEYS[parts[0]] = {"name": parts[1], "tier": parts[2] if len(parts) > 2 else "free"}

# ==================== BACKEND IMPORTS ====================
# Importing backend modules with error handling to avoid server crash

# ==================== LAZY LOADING SYSTEM ====================
class LazyModule:
    """Proxy to load modules only when accessed"""
    def __init__(self, module_name, import_path, class_name=None):
        self.module_name = module_name
        self.import_path = import_path
        self.class_name = class_name
        self._module = None
        self._instance = None

    def _load(self):
        if self._module is None:
            try:
                import importlib
                self._module = importlib.import_module(self.import_path)
                print(f"[LAZY] Loaded {self.module_name}")
            except ImportError as e:
                print(f"[WARN] Failed to load {self.module_name}: {e}")
                self._module = False
        return self._module

    def __getattr__(self, name):
        module = self._load()
        if not module: return None
        
        # If wrapped class/instance
        if self.class_name:
            if not self._instance:
                cls = getattr(module, self.class_name)
                # If it's a singleton already instantiated in module (like 'audio_player')
                if not callable(cls): 
                    self._instance = cls
                else:
                    self._instance = cls() # Instantiate
            return getattr(self._instance, name)
        
        return getattr(module, name)

    def __call__(self, *args, **kwargs):
        # Allow calling the module proxy directly if it represents a function/class
        module = self._load()
        if not module: return None
        if self.class_name:
             cls = getattr(module, self.class_name)
             return cls(*args, **kwargs)
        return module(*args, **kwargs)

# ==================== LAZY MODULES ====================

# We keep simple global variables but they are now proxies or handled differently
# For simplicity in this existing codebase, we will replace the direct imports with
# function calls or just load them on demand in the endpoints. 
# However, to keep code changes minimal elsewhere, we'll keep the variables but set them to None
# and re-import inside the specific routes/functions where used.

# Global Placeholders (Populated on first use inside endpoints)
ChatBot = None
Automation = None
workflow_engine = None
file_manager = None
Remember = None
Recall = None
# ultimate_pc removed - using psutil directly
ai_predictor = None
performance_optimizer = None
window_manager = None
enhanced_speech = None
TextToAudioFile = None
TTS = None
search_engine = None
db = None
supabase_db = None
GenerateImages = None
set_reminder = None
RealtimeSearchEngine = None
JarvisWebScraper = None
chrome_bot = None
YoutubeAutomation = None
ultra_smooth_gesture = None
visualizer = None
PORCUPINE_AVAILABLE = False
contextual_memory = None
get_cache = None
integrations = None
whatsapp = None
instagram = None
Listen = None
document_generator = None
enhanced_image_gen = None
chat_parser = None
file_analyzer = None
vqa_service = None
enhanced_automation = None

# Initialize file_analyzer for file uploads
try:
    from Backend.FileAnalyzer import FileAnalyzer
    file_analyzer = FileAnalyzer()
    print("[OK] FileAnalyzer loaded")
except Exception as e:
    print(f"[WARN] FileAnalyzer not available: {e}")
    file_analyzer = None

class SystemStatus:
    def __init__(self):
        self.status = "Available"
        self.wake_word_detected = False

system_status = SystemStatus()

def load_critical_modules():
    """Load core modules needed for basic functionality immediately if desired, or lazily"""
    pass

# Helper to import on demand
def get_module(name):
    global ChatBot, Automation, search_engine, firebase_auth
    
    if name == 'ChatBot':
        if not ChatBot:
            from Backend.Chatbot_Enhanced import ChatBot as CB
            ChatBot = CB
        return ChatBot
        
    if name == 'Automation':
        if not Automation:
            from Backend.Automation import Automation as Aut
            Automation = Aut
        return Automation

    if name == 'firebase_auth':
        if not firebase_auth:
             try: 
                from Backend.FirebaseAuth import FirebaseAuth
                from Backend.FirebaseStorage import get_firebase_storage
                fs = get_firebase_storage()
                firebase_auth = FirebaseAuth(fs.db) if fs.db else None
             except Exception as firebase_err:
                 print(f"[AUTH] Firebase init error: {firebase_err}")
        return firebase_auth

# ... (We will use local imports in endpoints instead of global loading)


# ==================== FIREBASE AUTHENTICATION & DAL ====================

try:
    from Backend.FirebaseAuth import FirebaseAuth
    from Backend.FirebaseDAL import FirebaseDAL
    from Backend.FirebaseStorage import get_firebase_storage
    from Backend.SecurityManager import extract_user_from_token, verify_token
    
    # Initialize Firebase
    firebase_storage = get_firebase_storage()
    firebase_auth = FirebaseAuth(firebase_storage.db) if firebase_storage.db else None
    firebase_dal = FirebaseDAL(firebase_storage.db) if firebase_storage.db else None
    
    print("[OK] Firebase Auth & DAL loaded")
except Exception as e:
    print(f"[WARN] Firebase Auth/DAL import failed: {e}")
    firebase_auth = None
    firebase_dal = None

# ==================== AUTHENTICATION MIDDLEWARE ====================

def require_auth(f):
    """Require JWT authentication for endpoint"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header required"}), 401
        
        # Extract token (format: "Bearer <token>")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({"error": "Invalid authorization header format"}), 401
        
        token = parts[1]
        
        # Verify token
        user_info = extract_user_from_token(token)
        if not user_info:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Attach user info to request
        request.current_user = user_info
        return f(*args, **kwargs)
    
    return decorated_function

def require_role(role: str):
    """Require specific role for endpoint"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({"error": "Authentication required"}), 401
            
            user_role = request.current_user.get('role', 'user')
            if user_role != role and user_role != 'admin':  # Admins can access everything
                return jsonify({"error": f"Requires {role} role"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """Get current authenticated user from request"""
    if hasattr(request, 'current_user'):
        return request.current_user
    return None

# Legacy API key authentication (for backward compatibility)
# HACKATHON MODE: Skip auth if no API keys configured
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Try JWT Auth first (Priority for user isolation)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                token = auth_header.split()[1]
                # Check if extract_user_from_token is available (imported above)
                if 'extract_user_from_token' in globals():
                    user_info = extract_user_from_token(token)
                    if user_info:
                        request.current_user = user_info
                        # Legacy support
                        request.user = {"name": user_info.get("email"), "tier": "pro"} 
                        return f(*args, **kwargs)
            except Exception:
                pass # Fallback to normal flow if token invalid

        # Skip authentication in development mode (any key accepted)
        if not IS_PRODUCTION:
            request.user = {"name": "dev", "tier": "free"}
            request.current_user = {"user_id": "dev", "email": "dev@localhost.com", "role": "user"}
            return f(*args, **kwargs)
        
        # Skip authentication if no API keys configured (demo mode)
        if not API_KEYS:
            request.user = {"name": "demo", "tier": "free"}
            request.current_user = {"user_id": "demo", "email": "demo@hackathon.com", "role": "user"}
            return f(*args, **kwargs)
        
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "API key required"}), 401
        if api_key not in API_KEYS:
            return jsonify({"error": "Invalid API key"}), 403
        request.user = API_KEYS[api_key]
        request.current_user = {"user_id": "default", "email": "legacy@user.com", "role": "user"}
        return f(*args, **kwargs)
    return decorated_function


# ==================== ENDPOINTS ====================

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "version": "13.0",
        "name": "KAI API - Production Ready",
        "modules": {
            "chat": ChatBot is not None,
            "automation": Automation is not None,
            "firebase_auth": firebase_auth is not None,
            "firebase_dal": firebase_dal is not None
        }
    })

# ==================== STATIC FILE SERVING ====================

@app.route('/data/<path:filename>')
def serve_data_files(filename):
    """Serve static files from Data directory (images, PDFs, etc.)"""
    try:
        data_dir = os.path.join(os.path.dirname(__file__), 'Data')
        return send_from_directory(data_dir, filename)
    except Exception as e:
        print(f"[ERROR] 404 GET /data/{filename} from {request.remote_addr}")
        return jsonify({"error": "File not found"}), 404

# ==================== AUTHENTICATION ENDPOINTS ====================

@app.route('/api/v1/auth/signup', methods=['POST'])
@rate_limit("auth")
def auth_signup():
    """Register a new user"""
    if not firebase_auth:
        return jsonify({"error": "Firebase authentication not available"}), 503
    
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        success, message, user_data = firebase_auth.register_user(email, password)
        
        if success:
            return jsonify({
                "success": True,
                "message": message,
                "user": user_data
            }), 201
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/auth/login', methods=['POST'])
@rate_limit("auth")
def auth_login():
    """Login with email and password"""
    if not firebase_auth:
        return jsonify({"error": "Firebase authentication not available"}), 503
    
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        success, message, auth_data = firebase_auth.login_user(email, password)
        
        if success:
            return jsonify({
                "success": True,
                "message": message,
                **auth_data
            }), 200
        else:
            return jsonify({"error": message}), 401
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/auth/google', methods=['POST'])
@rate_limit("auth")
def auth_google():
    """Login with Google OAuth"""
    if not firebase_auth:
        return jsonify({"error": "Firebase authentication not available"}), 503
    
    try:
        data = request.json
        google_id_token = data.get('google_id_token')
        
        if not google_id_token:
            return jsonify({"error": "Google ID token required"}), 400
        
        success, message, auth_data = firebase_auth.login_with_google(google_id_token)
        
        if success:
            return jsonify({
                "success": True,
                "message": message,
                **auth_data
            }), 200
        else:
            return jsonify({"error": message}), 401
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/auth/logout', methods=['POST'])
@require_auth
def auth_logout():
    """Logout (client should delete token)"""
    return jsonify({
        "success": True,
        "message": "Logged out successfully. Please delete your access token."
    }), 200

@app.route('/api/v1/auth/session', methods=['GET'])
@require_auth
def auth_session():
    """Get current session info"""
    user = get_current_user()
    return jsonify({
        "success": True,
        "user": user
    }), 200

@app.route('/api/v1/auth/refresh', methods=['POST'])
def auth_refresh():
    """Refresh access token using refresh token"""
    try:
        data = request.json
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({"error": "Refresh token required"}), 400
        
        # Verify refresh token
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            return jsonify({"error": "Invalid or expired refresh token"}), 401
        
        user_id = payload.get('sub')
        
        # Get user profile
        if not firebase_auth:
            return jsonify({"error": "Firebase authentication not available"}), 503
        
        user_profile = firebase_auth.get_user_profile(user_id)
        if not user_profile:
            return jsonify({"error": "User not found"}), 404
        
        # Generate new access token
        from Backend.SecurityManager import create_access_token
        new_access_token = create_access_token(
            user_id,
            user_profile['email'],
            user_profile['role']
        )
        
        return jsonify({
            "success": True,
            "access_token": new_access_token,
            "token_type": "Bearer"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== DOCUMENT UPLOAD ENDPOINT ====================

@app.route('/api/v1/upload-document', methods=['POST'])
@rate_limit("default")
def upload_document():
    """
    Upload a document (PDF, DOCX, TXT) for text extraction and summarization.
    Returns extracted text for AI context injection.
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if not file.filename:
            return jsonify({"error": "Empty filename"}), 400
        
        # Check extension
        allowed_extensions = ['.pdf', '.docx', '.txt', '.md']
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            return jsonify({"error": f"Unsupported format: {ext}. Allowed: {allowed_extensions}"}), 400
        
        # Save to temp location
        temp_dir = os.path.join(current_dir, 'temp_uploads')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{int(time.time())}_{file.filename}")
        file.save(temp_path)
        
        # Extract text using DocumentReader
        try:
            from Backend.DocumentReader import document_reader
            result = document_reader.read_document(temp_path)
        except ImportError:
            # Fallback: basic text reading
            with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            result = {
                "status": "success",
                "filename": file.filename,
                "text": text,
                "word_count": len(text.split()),
                "preview": text[:500]
            }
        
        # Cleanup temp file
        try:
            os.remove(temp_path)
        except OSError as cleanup_err:
            print(f"[UPLOAD] Warning: Could not cleanup temp file: {cleanup_err}")
        
        if result.get('status') == 'success':
            return jsonify({
                "success": True,
                "filename": result['filename'],
                "word_count": result['word_count'],
                "preview": result.get('preview', ''),
                "text": result['text'],
                "type": "document_upload"
            }), 200
        else:
            return jsonify({"error": result.get('message', 'Failed to extract text')}), 400
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

# ==================== USER MANAGEMENT ENDPOINTS ====================

@app.route('/api/v1/users/me', methods=['GET'])
@require_auth
def get_user_profile():
    """Get current user profile"""
    if not firebase_auth:
        return jsonify({"error": "Firebase authentication not available"}), 503
    
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        profile = firebase_auth.get_user_profile(user_id)
        if not profile:
            return jsonify({"error": "User profile not found"}), 404
        
        return jsonify({
            "success": True,
            "user": profile
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/users/me', methods=['PUT'])
@require_auth
def update_user_profile():
    """Update current user profile"""
    if not firebase_auth:
        return jsonify({"error": "Firebase authentication not available"}), 503
    
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        data = request.json
        success, message = firebase_auth.update_user_profile(user_id, data)
        
        if success:
            return jsonify({
                "success": True,
                "message": message
            }), 200
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/users/me/password', methods=['PUT'])
@require_auth
def change_password():
    """Change user password"""
    if not firebase_auth:
        return jsonify({"error": "Firebase authentication not available"}), 503
    
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        data = request.json
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({"error": "Old and new passwords required"}), 400
        
        success, message = firebase_auth.change_password(user_id, old_password, new_password)
        
        if success:
            return jsonify({
                "success": True,
                "message": message
            }), 200
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/users/me', methods=['DELETE'])
@require_auth
def delete_user_account():
    """Delete user account"""
    if not firebase_auth:
        return jsonify({"error": "Firebase authentication not available"}), 503
    
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        success, message = firebase_auth.delete_user(user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": message
            }), 200
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/users/profile', methods=['GET', 'OPTIONS'])
def get_autofill_profile():
    """Get user profile data for form autofill"""
    # Flask-CORS handles OPTIONS preflight automatically
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # Get user_id from query parameter
        user_id = request.args.get('user_id')
        
        if not user_id or user_id == 'default':
            print('[PROFILE] ⚠️ No user_id provided, returning empty')
            return jsonify({"success": True, "profile": {}})
        
        print(f'[PROFILE] Fetching profile for user: {user_id}')
        
        # Load from Firestore using REST API (no credentials file needed!)
        try:
            import requests
            
            # Firestore REST API endpoint
            project_id = "kai-g-80f9c"
            api_key = "AIzaSyAVv4EhUiVZSf54iZlB-ud05pxIlO8zBWk"
            
            # Path: users/{userId}/data/profile
            url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/users/{user_id}/data/profile?key={api_key}"
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse Firestore document format
                # Fields are in format: {"fieldName": {"stringValue": "value"}}
                fields = data.get('fields', {})
                
                def get_field(field_name):
                    """Extract value from Firestore field"""
                    field = fields.get(field_name, {})
                    # Handle string values
                    if 'stringValue' in field:
                        return field['stringValue']
                    # Handle integers
                    if 'integerValue' in field:
                        return field['integerValue']
                    # Handle arrays
                    if 'arrayValue' in field:
                        arr = field['arrayValue'].get('values', [])
                        return [item.get('stringValue', '') for item in arr]
                    return ''
                
                user_profile = {
                    'name': get_field('name'),
                    'email': get_field('email'),
                    'nickname': get_field('nickname'),
                    'bio': get_field('bio'),
                    'phone': get_field('phone'),
                    'address': get_field('address'),
                    'city': get_field('city'),
                    'state': get_field('state'),
                    'zip': get_field('zip') or get_field('zipCode'),
                    'country': get_field('country'),
                    'avatarUrl': get_field('avatarUrl'),
                    'responseStyle': get_field('responseStyle'),
                    'responseLanguage': get_field('responseLanguage'),
                    'interests': get_field('interests')  # Array field
                }
                
                print(f'[PROFILE] ✅ Loaded from Firestore REST API:', user_profile.get('name'))
                
                # Map to autofill format
                profile = {
                    "success": True,
                    "profile": {
                        "name": user_profile['name'],
                        "firstName": user_profile['name'].split()[0] if user_profile['name'] else '',
                        "lastName": user_profile['name'].split()[-1] if user_profile['name'] and len(user_profile['name'].split()) > 1 else '',
                        "email": user_profile['email'],
                        "phone": user_profile['phone'],
                        "address": user_profile['address'],
                        "city": user_profile['city'],
                        "state": user_profile['state'],
                        "zip": user_profile['zip'],
                        "country": user_profile['country']
                    }
                }
                
                return jsonify(profile)
            
            elif response.status_code == 404:
                print('[PROFILE] ⚠️ No profile document found in Firestore')
            else:
                print(f'[PROFILE] Firestore API error: {response.status_code} - {response.text}')
                
        except Exception as e:
            print(f'[PROFILE] Firestore REST API error: {e}')
            import traceback
            traceback.print_exc()
        
        # Fallback to empty profile
        print('[PROFILE] ⚠️ Using empty fallback')
        profile = {
            "success": True,
            "profile": {
                "name": "",
                "firstName": "",
                "lastName": "",
                "email": "",
                "phone": "",
                "address": "",
                "city": "",
                "state": "",
                "zip": "",
                "country": ""
            }
        }
        
        return jsonify(profile)
    except Exception as e:
        print(f'[PROFILE] Error: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "success": False}), 500

# PROJECT MODE ENDPOINTS REMOVED - Migrated to goal-based architecture

# NOTE: Data serving routes already defined above (serve_files function handles /data/<path:filename> and /Data/<path:filename>)

# ==================== BROWSER AUTOMATION ENDPOINTS ====================

@app.route('/api/v1/automation/analyze-page', methods=['POST', 'OPTIONS'])
def automation_analyze_page():
    """Analyze webpage content and structure"""
    # Flask-CORS handles OPTIONS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.json
        url = data.get('url', '')
        forms = data.get('forms', [])
        text = data.get('text', '')[:500]
        
        from Backend.LLM import ChatCompletion
        prompt = f'Analyze this page briefly:\nURL: {url}\nForms: {len(forms)}\nText: {text}\n\nQuick analysis:'
        
        analysis = ChatCompletion(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            text_only=True
        )
        
        return jsonify({"success": True, "analysis": analysis, "forms_detected": len(forms)})
    except Exception as e:
        print(f'[AUTOMATION] Analyze error: {e}')
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/automation/fill-form-smart', methods=['POST', 'OPTIONS'])
def automation_fill_form():
    """Fill form intelligently using AI"""
    # Flask-CORS handles OPTIONS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        forms = request.json.get('forms', [])
        if not forms:
            return jsonify({"error": "No forms detected"}), 400
        
        # Get user data (TODO: Load from Firebase user profile)
        user_data = {
            "firstName": "John",
            "lastName": "Doe", 
            "fullName": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "address": "123 Main St",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94102",
            "country": "USA"
        }
        
        # Use AI to intelligently map fields
        form = forms[0]
        fields = form.get('fields', [])
        
        from Backend.LLM import ChatCompletion
        
        # Create field descriptions for AI
        field_list = "\n".join([
            f"- Field: name='{f.get('name')}', type='{f.get('type')}', label='{f.get('label')}'"
            for f in fields
        ])
        
        prompt = f"""Map user data to form fields. Return ONLY valid JSON.

Form Fields:
{field_list}

User Data:
{json.dumps(user_data)}

Return JSON mapping field names to values. Use exact field names from above.
Example: {{"firstName": "John", "email": "john@example.com"}}
"""
        
        try:
            mapping_text = ChatCompletion(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                text_only=True
            )
            
            # Extract JSON
            if "```json" in mapping_text:
                mapping_text = mapping_text.split("```json")[1].split("```")[0]
            elif "```" in mapping_text:
                mapping_text = mapping_text.split("```")[1].split("```")[0]
            
            mappings = json.loads(mapping_text.strip())
            
        except:
            # Fallback: rule-based mapping
            mappings = {}
            for field in fields:
                name = field.get('name', '').lower()
                label = field.get('label', '').lower()
                
                # Smart matching
                if 'email' in name or 'email' in label:
                    mappings[field.get('name')] = user_data['email']
                elif ('first' in name or 'first' in label) and 'name' in (name + label):
                    mappings[field.get('name')] = user_data['firstName']
                elif ('last' in name or 'last' in label) and 'name' in (name + label):
                    mappings[field.get('name')] = user_data['lastName']
                elif 'name' in name or 'name' in label:
                    mappings[field.get('name')] = user_data['fullName']
                elif 'phone' in name or 'phone' in label:
                    mappings[field.get('name')] = user_data['phone']
                elif 'address' in name or 'address' in label:
                    mappings[field.get('name')] = user_data['address']
                elif 'city' in name or 'city' in label:
                    mappings[field.get('name')] = user_data['city']
                elif 'state' in name or 'state' in label:
                    mappings[field.get('name')] = user_data['state']
                elif 'zip' in name or 'zip' in label or 'postal' in name:
                    mappings[field.get('name')] = user_data['zip']
        
        return jsonify({
            "success": True,
            "mappings": mappings,
            "fields_filled": len(mappings)
        })
    except Exception as e:
        print(f'[AUTOMATION] Fill error: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ==================== MEMORY ENDPOINTS ====================

@app.route('/api/v1/memory/save', methods=['POST'])
@require_auth
def save_memory():
    """Save a memory for the current user"""
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        data = request.json
        content = data.get('content')
        tags = data.get('tags', [])
        
        if not content:
            return jsonify({"error": "Content required"}), 400
        
        from Backend.Memory import memory_system
        success = memory_system.remember(user_id, content, tags)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Memory saved successfully"
            }), 201
        else:
            return jsonify({"error": "Failed to save memory"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/memory/list', methods=['GET'])
@require_auth
def list_memories():
    """List all memories for the current user"""
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        limit = request.args.get('limit', 50, type=int)
        
        from Backend.Memory import memory_system
        memories_text = memory_system.recall(user_id, limit)
        
        return jsonify({
            "success": True,
            "memories": memories_text
        }), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/memory/search', methods=['GET'])
@require_auth
def search_memories():
    """Search memories for the current user"""
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        query = request.args.get('query', '')
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return jsonify({"error": "Query required"}), 400
        
        from Backend.Memory import memory_system
        results = memory_system.search_memories(user_id, query, limit)
        
        return jsonify({
            "success": True,
            "results": results
        }), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/memory/<memory_id>', methods=['DELETE'])
@require_auth
def delete_memory(memory_id):
    """Delete a specific memory"""
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        from Backend.Memory import memory_system
        success = memory_system.delete_memory(user_id, memory_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Memory deleted successfully"
            }), 200
        else:
            return jsonify({"error": "Failed to delete memory"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== CHAT HISTORY ENDPOINTS ====================

@app.route('/api/v1/chat/history', methods=['GET'])
@require_auth
def get_chat_history():
    """Get all conversations for the current user"""
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        limit = request.args.get('limit', 50, type=int)
        
        from Backend.ChatHistory import chat_history
        conversations = chat_history.get_conversations(user_id, limit)
        
        return jsonify({
            "success": True,
            "conversations": conversations
        }), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/chat/history', methods=['POST'])
@require_auth
def create_conversation():
    """Create a new conversation"""
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        data = request.json
        title = data.get('title', 'New Conversation')
        
        from Backend.ChatHistory import chat_history
        conv_id = chat_history.create_conversation(user_id, title)
        
        if conv_id:
            return jsonify({
                "success": True,
                "conversation_id": conv_id
            }), 201
        else:
            return jsonify({"error": "Failed to create conversation"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Helper for Firestore serialization
def serialize_firestore_data(data):
    if isinstance(data, dict):
        return {k: serialize_firestore_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_firestore_data(v) for v in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data

@app.route('/api/v1/chat/history/<conversation_id>', methods=['GET'])
@require_auth
def get_conversation(conversation_id):
    """Get a specific conversation with messages"""
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        from Backend.ChatHistory import chat_history
        conversation = chat_history.get_conversation(user_id, conversation_id)
        
        if conversation:
            print(f"[DEBUG] Conversation found: {conversation.get('title')}")
            print(f"[DEBUG] Message count: {len(conversation.get('messages', []))}")
            return jsonify({
                "success": True,
                "conversation": serialize_firestore_data(conversation)
            }), 200
        else:
            return jsonify({"error": "Conversation not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/chat/history/<conversation_id>', methods=['DELETE'])
@require_auth
def delete_conversation(conversation_id):
    """Delete a conversation"""
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        from Backend.ChatHistory import chat_history
        success = chat_history.delete_conversation(user_id, conversation_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Conversation deleted successfully"
            }), 200
        else:
            return jsonify({"error": "Failed to delete conversation"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/chat/history/<conversation_id>/messages', methods=['POST'])
@require_auth
def add_message(conversation_id):
    """Add a message to a conversation"""
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        data = request.json
        role = data.get('role')
        content = data.get('content')
        metadata = data.get('metadata')
        
        if not role or not content:
            return jsonify({"error": "Role and content required"}), 400
        
        from Backend.ChatHistory import chat_history
        success = chat_history.add_message(user_id, conversation_id, role, content, metadata)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Message added successfully"
            }), 201
        else:
            return jsonify({"error": "Failed to add message"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== WORKFLOW ENDPOINTS ====================

@app.route('/api/v1/workflows/save', methods=['POST'])
@require_auth
def save_workflow():
    """Create a new workflow"""
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        data = request.json
        name = data.get('name')
        description = data.get('description', '')
        steps = data.get('steps', [])
        
        if not name or not steps:
            return jsonify({"error": "Name and steps required"}), 400
        
        from Backend.WorkflowEngine import workflow_engine
        success = workflow_engine.create_workflow(name, description, steps, user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Workflow created successfully"
            }), 201
        else:
            return jsonify({"error": "Failed to create workflow"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/workflows/list', methods=['GET'])
@require_auth
def list_workflows():
    """List all workflows for the current user"""
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        from Backend.WorkflowEngine import workflow_engine
        workflows = workflow_engine.list_workflows(user_id)
        
        return jsonify({
            "success": True,
            "workflows": workflows
        }), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/workflows/run', methods=['POST'])
@require_auth
async def run_workflow():
    """Execute a workflow"""
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        data = request.json
        workflow_name = data.get('workflow_name')
        parameters = data.get('parameters', {})
        
        if not workflow_name:
            return jsonify({"error": "Workflow name required"}), 400
        
        from Backend.WorkflowEngine import workflow_engine
        results = await workflow_engine.execute_workflow(workflow_name, user_id, parameters)
        
        return jsonify({
            "success": True,
            "results": results
        }), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/workflows/<workflow_id>', methods=['GET'])
@require_auth
def get_workflow(workflow_id):
    """Get workflow details"""
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        from Backend.WorkflowEngine import workflow_engine
        workflow = workflow_engine.get_workflow(workflow_id, user_id)
        
        if workflow:
            return jsonify({
                "success": True,
                "workflow": workflow
            }), 200
        else:
            return jsonify({"error": "Workflow not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/workflows/<workflow_id>', methods=['PUT'])
@require_auth
def update_workflow(workflow_id):
    """Update a workflow"""
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        data = request.json
        
        from Backend.WorkflowEngine import workflow_engine
        success = workflow_engine.update_workflow(workflow_id, data, user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Workflow updated successfully"
            }), 200
        else:
            return jsonify({"error": "Failed to update workflow"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/workflows/<workflow_id>', methods=['DELETE'])
@require_auth
def delete_workflow(workflow_id):
    """Delete a workflow"""
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        from Backend.WorkflowEngine import workflow_engine
        success = workflow_engine.delete_workflow(workflow_id, user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Workflow deleted successfully"
            }), 200
        else:
            return jsonify({"error": "Failed to delete workflow"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== WEB MUSIC PLAYER ENDPOINT ====================

@app.route('/api/v1/music/play', methods=['POST'])
@require_api_key
def web_music_play():
    """
    Web-based music player - searches YouTube and returns embed URL.
    The frontend handles actual playback in the browser.
    """
    try:
        from Backend.WebMusicPlayer import get_music_response
        
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "Query required"}), 400
        
        result = get_music_response(query)
        return jsonify(result), 200
        
    except ImportError:
        # Fallback: Just return a YouTube search URL
        from urllib.parse import quote_plus
        query = request.json.get('query', 'music')
        search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        return jsonify({
            "status": "fallback",
            "message": f"🎵 Search for: {query}",
            "search_url": search_url,
            "type": "music_link"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== NEW FEATURE ENDPOINTS ====================

@app.route('/api/v1/image/generate', methods=['POST'])
@require_auth
@rate_limit("image_gen")
def generate_image_api():
    """Generate an image from prompt"""
    try:
        data = request.json
        prompt = data.get('prompt')
        style = data.get('style', 'realistic')
        
        if not prompt:
            return jsonify({"error": "Prompt required"}), 400
        
        # Using Enhanced Image Gen if available
            user_id = request.current_user.get('user_id') if hasattr(request, 'current_user') else None
            images = enhanced_image_gen.generate_with_style(prompt, style, num_images=1, user_id=user_id)
            if images:
                # Convert local path to URL if needed, or if it returns URL
                # enhanced_image_gen usually returns absolute path or relative?
                # Let's assume absolute path for now and let frontend handle it or serve it
                # If it's a file path, we need to ensure it's in Data directory
                
                image_url = images[0]
                # Fix path for serving
                if "Data" in image_url:
                     image_url = image_url[image_url.find("Data"):] # keep Data/...
                     image_url = "/" + image_url.replace("\\", "/")
                
                return jsonify({
                    "status": "success",
                    "images": [image_url]
                }), 200
        
        # Fallback
        if GenerateImages:
            GenerateImages(prompt)
            # Naive return
            safe_prompt = prompt.replace(" ", "_")
            return jsonify({
                "status": "success", 
                "images": [f"/data/{safe_prompt}1.jpg"]
            }), 200
            
        return jsonify({"error": "Image generation not available"}), 503
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== SMART WORKFLOWS API ====================

@app.route('/api/v1/workflows/smart', methods=['GET'])
@require_api_key
def list_smart_workflows():
    """List all available smart workflows"""
    try:
        from Backend.SmartWorkflows import smart_workflows
        workflows = smart_workflows.list_workflows()
        return jsonify({
            "status": "success",
            "workflows": workflows,
            "count": len(workflows)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== MODE SWITCHING ====================

@app.route('/api/v1/switch/speech', methods=['POST'])
@require_api_key
def switch_to_speech_mode():
    """Launch the GUI for speech-to-speech interaction"""
    try:
        import subprocess
        import os
        import sys
        
        # Path to GUI script - prioritize Futuristic GUI
        gui_path = os.path.join(os.path.dirname(__file__), "Frontend", "GUI_Futuristic.py")
        
        if not os.path.exists(gui_path):
            # Try GUI_Ultimate
            gui_path = os.path.join(os.path.dirname(__file__), "Frontend", "GUI_Ultimate.py")
        
        if not os.path.exists(gui_path):
            # Try GUI_Modern as fallback
            gui_path = os.path.join(os.path.dirname(__file__), "Frontend", "GUI_Modern.py")

        
        if not os.path.exists(gui_path):
            return jsonify({
                "status": "error",
                "message": "GUI script not found"
            }), 404
        
        # Launch in new process (non-blocking)
        subprocess.Popen(
            [sys.executable, gui_path],
            cwd=os.path.dirname(__file__),
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        
        return jsonify({
            "status": "success",
            "message": "Speech Mode GUI launched"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/v1/workflows/smart/execute', methods=['POST'])
@require_api_key
def execute_smart_workflow():
    """Execute a smart workflow by name"""
    try:
        data = request.json
        workflow_name = data.get('workflow', data.get('name', ''))
        
        if not workflow_name:
            return jsonify({"error": "Workflow name required"}), 400
        
        from Backend.SmartWorkflows import smart_workflows
        
        # Find and execute
        workflow_key = smart_workflows.find_workflow(workflow_name)
        if not workflow_key:
            return jsonify({
                "error": f"Workflow '{workflow_name}' not found",
                "available": smart_workflows.get_workflow_names()
            }), 404
        
        result = asyncio.run(smart_workflows.execute_workflow(workflow_key))
        
        return jsonify({
            "status": result.get("status", "unknown"),
            "workflow": result.get("workflow", workflow_key),
            "steps_completed": result.get("steps_completed", 0),
            "total_steps": result.get("total_steps", 0),
            "details": result.get("results", [])
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/data/live', methods=['GET'])
@require_auth
def get_live_data():
    """Get live data like crypto and weather"""
    try:
        # We could use the integration modules, but for speed let's just return basic info
        # Or fetch real data if modules are available
        
        data = {
            "bitcoin": "Loading...",
            "weather": "Loading..."
        }
        
        # Bitcoin
        try:
            # Quick fetch or use integration
             import requests
             # This is blocking, but okay for now
             # r = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json")
             # data["bitcoin"] = "$" + r.json()["bpi"]["USD"]["rate"]
             pass
        except Exception as btc_err:
            print(f"[DASHBOARD] Bitcoin fetch skipped: {btc_err}")
        
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/memory/summary', methods=['GET'])
@require_auth
def get_memory_summary():
    """Get a summary of stored memories"""
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        from Backend.Memory import memory_system
        # Assuming memory_system has a summary or count method, or we count manually
        if hasattr(memory_system, 'get_stats'):
            summary = memory_system.get_stats(user_id)
        else:
            # Fallback
            memories_list = memory_system.recall(user_id, 10)
            # memories_list returns a string usually "Here are relevant memories..."
            summary = f"Recent memories active: {memories_list[:100]}..."
            
        return jsonify({
            "status": "success",
            "summary": summary
        }), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/chat/history/delete_all', methods=['DELETE'])
@require_auth
def delete_all_conversations():
    """Delete ALL conversations for the current user"""
    try:
        user = get_current_user()
        user_id = user['user_id']
        
        from Backend.ChatHistory import chat_history
        success = chat_history.delete_all_conversations(user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "All conversations deleted successfully"
            }), 200
        else:
            return jsonify({"error": "Failed to delete all conversations"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- CHAT & CORE ---

# ==================== SMART REALTIME DETECTION ====================
def needs_realtime_search(query: str) -> bool:
    """
    Detect if a query needs real-time data instead of LLM knowledge.
    Triggers RealtimeSearchEngine for time-sensitive queries like:
    - "What is the price of gold today?"
    - "Current bitcoin value"
    - "Latest news about India"
    """
    query_lower = query.lower()
    
    # Time indicators that suggest current/live data needed
    time_indicators = [
        "today", "now", "current", "currently", "latest", "live", "right now", 
        "at the moment", "this week", "this month", "2024", "2025",
        "yesterday", "tomorrow", "recent", "recently", "happening"
    ]
    
    # Topics that typically need real-time data when combined with time indicators
    realtime_topics = [
        # Financial
        "price", "rate", "value", "cost", "worth", "trading",
        "gold", "silver", "platinum", "bitcoin", "btc", "ethereum", "eth", 
        "crypto", "cryptocurrency", "stock", "share", "nifty", "sensex",
        "dollar", "rupee", "euro", "forex", "exchange rate",
        # Weather
        "weather", "temperature", "forecast", "rain", "humidity",
        # News & Events
        "news", "update", "headline", "breaking",
        # Sports
        "score", "match", "game", "ipl", "cricket", "football",
        "who won", "who is winning", "results"
    ]
    
    has_time_indicator = any(t in query_lower for t in time_indicators)
    has_realtime_topic = any(t in query_lower for t in realtime_topics)
    
    # Explicit phrases that ALWAYS need realtime search
    explicit_realtime_phrases = [
        "what is the price", "current price", "today's price", "price of",
        "what's happening", "latest news", "live score", "current value",
        "how much is", "what is the rate", "exchange rate",
        "weather in", "temperature in", "forecast for",
        "who is the current", "who is the prime minister", "who is the president"
    ]
    
    # Check explicit phrases first (highest priority)
    if any(phrase in query_lower for phrase in explicit_realtime_phrases):
        return True
    
    # Check combination of time indicator + realtime topic
    if has_time_indicator and has_realtime_topic:
        return True
    
    return False

@app.route('/api/v1/chat', methods=['POST'])
@require_api_key
@rate_limit("chat")
def chat():
    global ChatBot
    
    # Robust loading of ChatBot
    if not ChatBot:
        print("[DEBUG] ChatBot not loaded, attempting to load...")
        try:
            from Backend.Chatbot_Enhanced import ChatBot as CB
            ChatBot = CB
            print("[SUCCESS] ChatBot module loaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load ChatBot module: {e}")
            import traceback
            traceback.print_exc()
            # Try get_module as fallback
            ChatBot = get_module('ChatBot')

    data = request.json
    query = data.get('query', '')
    image_path = data.get('image_path')  # Legacy support
    attachments = data.get('attachments', [])  # New: array of {name, url, type}
    user_preferences = data.get('user_preferences')  # User profile settings
    style_hint = data.get('style_hint', 'neutral')  # 🎭 BEAST MODE: Adaptive Personality (concise/detailed/neutral)
    
    # === PER-USER MEMORY SYSTEM (NEW - Beast Mode) ===
    user_id = data.get('uid', 'anonymous')  # Firebase UID from frontend
    session_id = data.get('session_id', 'default')  # Chat session ID
    
    # Inject relevant memories into context
    memory_context = ""
    memory_accessed = False
    memory_saved = False
    
    if PER_USER_MEMORY_ENABLED and user_id != 'anonymous':
        try:
            # 1. Recall semantically similar memories for this user
            relevant_memories = recall(user_id, query, limit=5)
            
            if relevant_memories:
                memory_accessed = True
                memory_context = "\n[🧠 MEMORY CONTEXT - What you remember about this user]:\n"
                for mem in relevant_memories[:5]:
                    content = mem.get('content', '')[:150]
                    category = mem.get('category', 'general')
                    memory_context += f"• [{category}] {content}\n"
                memory_context += "\nUse these memories to personalize your response naturally.\n"
                print(f"[MEMORY] Recalled {len(relevant_memories)} memories for user {user_id[:8]}")
            
            # 2. Get cross-session context
            cross_context = get_context(user_id, session_id, query)
            if cross_context:
                memory_context += f"\n[Previous sessions context: {len(cross_context)} relevant items]\n"
                
        except Exception as mem_error:
            print(f"[MEMORY] Recall error: {mem_error}")
    
    # === USER PREFERENCES CONTEXT (NEW) ===
    # Build personalized context from user settings
    user_context = ""
    if user_preferences:
        name = user_preferences.get('name', '')
        nickname = user_preferences.get('nickname', '')
        bio = user_preferences.get('bio', '')
        response_style = user_preferences.get('responseStyle', 'casual')
        response_language = user_preferences.get('responseLanguage', 'english')
        interests = user_preferences.get('interests', [])
        
        # Build context string
        user_context_parts = []
        if name or nickname:
            display_name = nickname or name
            user_context_parts.append(f"The user's name is {name}." + (f" Call them '{nickname}' casually." if nickname else ""))
        if bio:
            user_context_parts.append(f"About the user: {bio}")
        if interests:
            user_context_parts.append(f"User's interests: {', '.join(interests)}")
        
        # Response style preferences
        style_instructions = {
            'professional': "Respond in a professional and formal manner.",
            'casual': "Be casual and friendly in your responses.",
            'brief': "Keep responses brief and concise.",
            'detailed': "Provide detailed and thorough explanations.",
            'technical': "Be technical and precise in explanations."
        }
        if response_style in style_instructions:
            user_context_parts.append(style_instructions[response_style])
        
        # Language preference - ALWAYS add explicit instruction to override chat history
        # Support ANY language dynamically
        lang_lower = response_language.lower() if response_language else 'english'
        
        language_instructions = {
            'hindi': "IMPORTANT: Respond primarily in Hindi (हिंदी में जवाब दें).",
            'hinglish': "IMPORTANT: Respond in Hinglish (mix of Hindi and English).",
            'english': "IMPORTANT: Respond in English only.",
            'spanish': "IMPORTANT: Respond in Spanish (Responde en español).",
            'french': "IMPORTANT: Respond in French (Répondez en français).",
            'german': "IMPORTANT: Respond in German (Antworten Sie auf Deutsch).",
            'japanese': "IMPORTANT: Respond in Japanese (日本語で答えてください).",
            'chinese': "IMPORTANT: Respond in Chinese (请用中文回答).",
            'korean': "IMPORTANT: Respond in Korean (한국어로 대답해 주세요).",
            'portuguese': "IMPORTANT: Respond in Portuguese (Responda em português).",
            'italian': "IMPORTANT: Respond in Italian (Rispondi in italiano).",
            'russian': "IMPORTANT: Respond in Russian (Отвечайте на русском).",
            'arabic': "IMPORTANT: Respond in Arabic (أجب بالعربية).",
        }
        
        if lang_lower in language_instructions:
            user_context_parts.append(language_instructions[lang_lower])
        elif lang_lower != 'auto':
            # For any other language, generate dynamic instruction
            user_context_parts.append(f"IMPORTANT: Respond in {response_language}.")
        
        if user_context_parts:
            user_context = "[USER CONTEXT: " + " ".join(user_context_parts) + "]\n\n"
            print(f"[CHAT] User preferences loaded: {name or 'Anonymous'}, style={response_style}, lang={response_language}")
    
    # 🎭 BEAST MODE: Adaptive Style Based on Input Length
    adaptive_style_instructions = {
        'concise': "The user sent a SHORT message. Keep your response brief and direct (1-3 sentences max unless critical info is needed).",
        'detailed': "The user sent a DETAILED question. Provide a thorough, comprehensive response with explanations.",
        'neutral': ""  # No special instruction
    }
    if style_hint in adaptive_style_instructions and adaptive_style_instructions[style_hint]:
        user_context += f"[ADAPTIVE STYLE: {adaptive_style_instructions[style_hint]}]\n\n"
    
    # === ATTACHMENT HANDLING (NEW) ===
    # Process any attached files (images get vision analysis)
    import os as _os  # Use _os to avoid scoping issues with later imports
    attachment_context = ""
    for attachment in attachments:
        file_name = attachment.get('name', '')
        file_url = attachment.get('url', '')
        # Fallback type from frontend, but we'll prefer extension
        file_type_api = attachment.get('type', 'unknown')
        
        # Robust extension detection
        ext = _os.path.splitext(file_name)[1].lower().lstrip('.')
        
        print(f"[ATTACHMENT] Processing: {file_name} (type: {file_type_api}, ext: {ext})")
        
        

        # --- PDF PROCESSING (Smart OCR) ---
        if ext == 'pdf':
            try:
                import pdfplumber
                full_path = _os.path.join(DATA_DIR, 'Uploads', file_name)
                pdf_text = ""
                has_images = False
                
                with pdfplumber.open(full_path) as pdf:
                    # Limit to first 15 pages to prevent context overflow
                    for i, page in enumerate(pdf.pages[:15]):
                        text = page.extract_text()
                        if text and text.strip():
                            pdf_text += f"\n--- Page {i+1} ---\n{text}"
                        # Check if page has images (indicates scanned PDF)
                        if page.images:
                            has_images = True
                
                if pdf_text and len(pdf_text.strip()) > 50:
                    # Text-based PDF - use pdfplumber text
                    attachment_context += f"\n\n[PDF CONTENT - {file_name}]:\n{pdf_text[:8000]}"
                    print(f"[PDF] ✅ Extracted {len(pdf_text)} chars from text PDF")
                else:
                    # Scanned PDF - Use Gemini Vision OCR
                    print(f"[PDF] 📸 No text found, attempting OCR with Gemini Vision...")
                    try:
                        import pypdfium2 as pdfium
                        from PIL import Image
                        from Backend.VisionService import get_vision_service
                        
                        # Open PDF with pypdfium2 (already installed with pdfplumber - no Poppler needed!)
                        pdf_doc = pdfium.PdfDocument(full_path)
                        vision = get_vision_service()
                        ocr_text = ""
                        
                        # Limit to first 5 pages for OCR
                        max_pages = min(len(pdf_doc), 5)
                        
                        for i in range(max_pages):
                            page = pdf_doc[i]
                            # Render page to image (scale=2 for 150 DPI equivalent)
                            bitmap = page.render(scale=2)
                            pil_image = bitmap.to_pil()
                            
                            # Save temp image
                            temp_img_path = os.path.join(DATA_DIR, 'Uploads', f'_ocr_temp_{i}.png')
                            pil_image.save(temp_img_path, 'PNG')
                            
                            # Use Gemini Vision for OCR
                            result = vision.analyze(temp_img_path, "Extract ALL text from this image. Return only the text content, preserving formatting.")
                            
                            if result.get('success'):
                                page_text = result.get('description', '')
                                if page_text:
                                    ocr_text += f"\n--- Page {i+1} (OCR) ---\n{page_text}"
                            
                            # Clean up temp file
                            try:
                                _os.remove(temp_img_path)
                            except:
                                pass
                        
                        pdf_doc.close()
                        
                        if ocr_text:
                            attachment_context += f"\n\n[PDF OCR CONTENT - {file_name}]:\n{ocr_text[:8000]}"
                            print(f"[PDF] ✅ OCR extracted {len(ocr_text)} chars from scanned PDF")
                        else:
                            attachment_context += f"\n\n[PDF - {file_name}]: (Scanned PDF - OCR found no readable text)"
                            
                    except ImportError as ie:
                        print(f"[PDF] ⚠️ OCR dependency missing: {ie}")
                        attachment_context += f"\n\n[PDF - {file_name}]: (Scanned PDF - OCR not available)"
                    except Exception as ocr_e:
                        print(f"[PDF] ⚠️ OCR Error: {ocr_e}")
                        attachment_context += f"\n\n[PDF - {file_name}]: (Scanned PDF - OCR failed)"
                        
            except Exception as e:
                print(f"[ATTACHMENT] PDF Error: {e}")
                attachment_context += f"\n\n[PDF - {file_name}]: Error reading PDF."

        # --- TEXT/CODE/DATA PROCESSING ---
        elif ext in ['txt', 'md', 'py', 'js', 'html', 'css', 'json', 'csv', 'cpp', 'c', 'java', 'xml', 'yaml', 'yml']:
            try:
                full_path = _os.path.join(DATA_DIR, 'Uploads', file_name)
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    attachment_context += f"\n\n[FILE CONTENT - {file_name}]:\n{content[:8000]}"
                    print(f"[ATTACHMENT] Read {len(content)} chars from {ext} file")
            except Exception as e:
                print(f"[ATTACHMENT] File Read Read Error: {e}")

        # --- IMAGE PROCESSING ---
        elif file_type_api == 'image' or ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
            try:
                import os as _os  # Explicit import to avoid scoping issues
                from Backend.VisionService import get_vision_service
                vision = get_vision_service()
                
                # Build full file path - try local first, then fall back to URL
                full_path = _os.path.join(DATA_DIR, 'Uploads', file_name)
                image_source = None
                
                if _os.path.exists(full_path):
                    # Local file exists (development mode)
                    image_source = full_path
                    print(f"[VISION] Using local file: {full_path}")
                elif file_url and file_url.startswith(('http://', 'https://')):
                    # Use Firebase Storage URL directly (cloud/Render mode)
                    image_source = file_url
                    print(f"[VISION] Using URL: {file_url[:80]}...")
                
                if image_source:
                    # Improved prompt for comprehensive, detailed analysis
                    base_query = query or "Describe this image"
                    vision_prompt = f"""{base_query}

Provide a COMPREHENSIVE and DETAILED analysis of this image. Include:

1. **Main Subject/Focus**: What is the primary subject or focus of this image?
2. **Visual Elements**: Describe colors, composition, style, lighting, and artistic techniques
3. **Details & Objects**: List all notable objects, text, symbols, or elements visible
4. **Context & Setting**: Describe the environment, background, or setting
5. **Mood & Atmosphere**: What emotions or atmosphere does this image convey?
6. **Purpose/Intent**: What appears to be the purpose of this image? (e.g., advertisement, art, logo, infographic, etc.)

Format your response with **Bold Headers** and clear sections. Be thorough and descriptive - aim for 150-300 words."""
                    
                    result = vision.analyze(image_source, vision_prompt)
                    if result.get('success'):
                        attachment_context += f"\n\n[IMAGE ANALYSIS - {file_name}]:\n{result.get('description', 'Image analyzed.')}"
                        print(f"[VISION] Analyzed {file_name}: {result.get('description', '')[:100]}...")
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        attachment_context += f"\n\n[IMAGE: {file_name}] - Analysis failed: {error_msg}"
                        print(f"[VISION] Analysis failed for {file_name}: {error_msg}")
                else:
                    print(f"[VISION] No valid image source for: {file_name} (local: {full_path}, url: {file_url})")
                    attachment_context += f"\n\n[IMAGE: {file_name}] - File attached but could not be analyzed."
            except Exception as ve:
                print(f"[VISION] Error processing {file_name}: {ve}")
                import traceback
                traceback.print_exc()
                attachment_context += f"\n\n[IMAGE: {file_name}] - Attached (analysis failed)."
        else:
            # Non-image attachments
            attachment_context += f"\n\n[ATTACHED FILE: {file_name} (type: {file_type_api})]"
    
    # Save original query for trigger detection (before attachment context injection)
    original_query = query
    original_query_lower = query.lower().strip()
    
    # Inject attachment context into query
    if attachment_context:
        query = f"{query}\n\n[CONTEXT FROM ATTACHMENTS]{attachment_context}"
    
    # === LEGACY VISION AWARENESS (for backward compatibility) ===
    if image_path and not attachments:
        print(f"[VISION] Received legacy image path: {image_path}")
        try:
            from Backend.VisionService import get_vision_service
            vision = get_vision_service()
            result = vision.analyze(image_path, query or "Describe this image in detail.")
            
            if result.get('success'):
                description = result.get('description', '')
                query += f"\n\n[SYSTEM: I have analyzed the uploaded image. Here is what I see:]\n{description}"
                print(f"[VISION] Context injected into query.")
        except Exception as ve:
            print(f"[VISION] Failed to process legacy image: {ve}")

    if not query: return jsonify({"error": "Query required"}), 400
    
    query_lower = query.lower().strip()
    chat_metadata = {} # Initialize metadata container
    
    # === SMART REALTIME DETECTION (NEW - Beast Mode) ===
    # Detect time-sensitive queries and route to RealtimeSearchEngine
    if needs_realtime_search(original_query):
        print(f"[SMART] 🔍 Detected time-sensitive query, using RealtimeSearchEngine: '{original_query[:50]}...'")
        try:
            from Backend.RealtimeSearchEngine import RealtimeSearchEngine
            realtime_result = RealtimeSearchEngine(original_query)
            
            # Handle dict or string response from RealtimeSearchEngine
            if isinstance(realtime_result, dict):
                response_text = realtime_result.get('text', '')
                sources = realtime_result.get('sources', [])
                engine = realtime_result.get('engine', 'unknown')
            else:
                response_text = str(realtime_result)
                sources = []
                engine = 'unknown'
            
            # Return realtime response with sources for UI cards
            print(f"[SMART] ✅ Realtime search complete via {engine}, {len(sources)} sources")
            return jsonify({
                "response": response_text,
                "sources": sources,
                "metadata": {
                    "type": "realtime_search",
                    "engine": engine,
                    "memory_accessed": False,
                    "memory_saved": False
                }
            })
        except Exception as rt_error:
            print(f"[SMART] ⚠️ Realtime search failed: {rt_error}, falling back to LLM")
            # Fall through to normal LLM flow
    
    # === SPOTIFY MUSIC PLAYER (Cloud Ready - No YouTube Fallback) ===
    # Music requests are now routed through SmartTrigger to use Spotify only
    
    try:
        # === INITIALIZE RESPONSE METADATA ===
        # Must be initialized early to prevent NameError in return statement
        chat_metadata = {}
        
        # === CHAT CONTEXT FOR CONTINUOUS FLOW ===
        # Load recent chat history for LLM context
        chat_context = []
        try:
            from Backend.Chatbot import chatlog_path
            from json import load as json_load
            with open(chatlog_path, 'r') as f:
                history = json_load(f)
                chat_context = history[-6:] if len(history) > 6 else history  # Last 6 messages
        except Exception as ctx_err:
            pass  # Silent fail for context loading
        
        # === PRE-CHECK: DIRECT APP/FILE COMMANDS ===
        # These often get misclassified as Chrome commands
        # Use original_query_lower (without attachment context) to avoid false matches
        query_lower = original_query_lower
        
        # Known app names that should NOT go to Chrome
        app_names = [
            "notepad", "calculator", "calc", "chrome", "google chrome", "firefox", "edge", "brave",
            "code", "vscode", "vs code", "visual studio", "word", "excel", "powerpoint",
            "outlook", "discord", "slack", "spotify", "vlc", "paint", "photoshop",
            "teams", "zoom", "skype", "telegram", "whatsapp", "obs", "gimp",
            "terminal", "cmd", "powershell", "explorer", "file explorer", "file manager", "files",
            "recycle bin", "downloads", "documents", "pictures", "videos", "music",
            "settings", "control panel", "task manager", "snipping tool", "screen snip",
            "steam", "epic games", "valorant", "fortnite", "minecraft", "blender",
            "unity", "android studio", "pycharm", "intellij", "webstorm", "postman", 
            "figma", "notion", "obsidian", "onenote", "magnifier"
        ]
        
        
        # Direct app command detection
        trigger_type = None
        command = None
        
        # === @MENTION PRIORITY DETECTION ===
        # Highest priority - explicit tool invocation via @mention
        mention_map = {
            "@figma": "figma", "@notion": "notion", "@slack": "slack", 
            "@trello": "trello", "@calendar": "calendar", "@weather": "weather",
            "@news": "news", "@crypto": "crypto", "@github": "github",
            "@system": "system_stats", "@nasa": "nasa_apod", "@pdf": "document",
            "@image": "image", "@spotify": "spotify", "@search": "chrome"
        }
        for mention, ttype in mention_map.items():
            if mention in query_lower:
                trigger_type = ttype
                command = query.replace(mention, "").strip()
                print(f"[PRE-CHECK] @Mention detected: {mention} → {ttype}")
                break
        
        # Check for explicit app commands (including common typos)
        if any(query_lower.startswith(p) for p in ["open ", "opn ", "opne ", "oepn ", "launch ", "lanch ", "laucnh ", "start ", "strt ", "close ", "quit ", "exit ", "run ", "fire up "]):
            try:
                from Backend.LocalAgentIntentDetector import detect_intent
                intent_result = detect_intent(query, use_ai=True)
                
                if intent_result.get("intent") == "open_app" and intent_result.get("target"):
                    trigger_type = "app"
                    command = intent_result["target"]
                    print(f"[PRE-CHECK] AI detected app command: {command} (confidence: {intent_result.get('confidence')}, method: {intent_result.get('method')})")
            except Exception as e:
                print(f"[PRE-CHECK] AI intent detection failed: {e}")
                # Fallback to basic matching
                for app in app_names:
                    if app in query_lower:
                        trigger_type = "app"
                        command = app
                        print(f"[PRE-CHECK] Fallback app detection: {app}")
                        break
        
        # Check for explicit file commands (EXPANDED)
        file_keywords = [
            "create file", "delete file", "list files", "open folder", "search file", "read file",
            "remove everything", "delete everything", "delete all", "remove all", "clear all",
            "delete files", "remove files", "copy file", "move file", "rename file",
            "select all", "copy", "cut", "paste", "undo", "redo",
            "open downloads", "open documents", "open desktop", "open pictures",
            "wipe", "cleanup", "clean up", "empty folder", "trash"
        ]
        if not trigger_type and any(k in query_lower for k in file_keywords):
            trigger_type = "file"
            command = query
            print(f"[PRE-CHECK] Detected file command: {query}")
        
        # Check for code commands (MOVED UP PRIORITY)
        code_keywords = ["generate code", "write code", "create code", "code for", "python code", 
                         "javascript code", "write a script", "create a script", "execute code",
                         "run code", "run python", "explain code", "create project", "create flask",
                         "generate python", "generate javascript", "generate html"]
        if not trigger_type and any(k in query_lower for k in code_keywords):
            trigger_type = "code"
            command = query
            print(f"[PRE-CHECK] Detected code command")


        # === FLEXIBLE GENERATION TRIGGERS ===
        # Supports: generate/create/make/build/write + pdf/image/document/picture
        generation_verbs = ["generate", "create", "make", "build", "write", "produce", "design"]
        pdf_nouns = ["pdf", "document", "report", "paper", "doc"]
        image_nouns = ["image", "picture", "photo", "illustration", "art", "drawing", "graphic", 
                       "background", "wallpaper", "icon", "logo", "thumbnail", "poster", "cover"]
        
        has_gen_verb = any(v in query_lower for v in generation_verbs)
        has_pdf_noun = any(n in query_lower for n in pdf_nouns)
        has_image_noun = any(n in query_lower for n in image_nouns)
        
        # PDF/Document generation takes priority when pdf keywords are detected
        if not trigger_type and has_gen_verb and has_pdf_noun:
            trigger_type = "document"
            command = query
            print(f"[PRE-CHECK] Flexible detect: DOCUMENT generation (priority)")
        # Image generation only if no pdf keywords
        elif not trigger_type and has_gen_verb and has_image_noun:
            trigger_type = "image"
            command = query
            print(f"[PRE-CHECK] Flexible detect: IMAGE generation")
        
        # Check for reminder/schedule commands
        reminder_keywords = ["remind me", "set reminder", "set alarm", "schedule", "in 30 minutes", 
                            "in an hour", "every hour", "every 2 hours", "at 9 am", "at noon"]
        if not trigger_type and any(k in query_lower for k in reminder_keywords):
            trigger_type = "reminder"
            command = query
            print(f"[PRE-CHECK] Detected reminder command")
        
        # Check for action chain commands (form filling, typing, etc.)
        action_keywords = ["fill form", "fill this", "fill out", "type this", "type for me", 
                          "click here", "select all", "copy this", "paste"]
        if not trigger_type and any(k in query_lower for k in action_keywords):
            trigger_type = "action"
            command = query
            print(f"[PRE-CHECK] Detected action chain command")
        
        # === SMART CONTEXT-AWARE SEARCH DETECTION ===
        # "search python files" → file
        # "search python" → file (default for ambiguous)  
        # "search google for python" or "search online" → chrome
        if not trigger_type and "search" in query_lower:
            print(f"[PRE-CHECK] Search keyword detected in query: '{query_lower}'")
            # File search indicators
            file_indicators = ["files", "file", "documents", "downloads", "desktop", "folder", 
                               "in c:", "in d:", "on drive", "on my computer", "locally"]
            # Web search indicators  
            web_indicators = ["google", "online", "web", "internet", "on google", 
                              "youtube", "bing", "duckduckgo", "wikipedia", "reddit"]
            
            is_file_search = any(i in query_lower for i in file_indicators)
            is_web_search = any(i in query_lower for i in web_indicators)
            
            if is_file_search and not is_web_search:
                trigger_type = "file"
                command = query
                print(f"[PRE-CHECK] Smart detect: FILE search")
            elif is_web_search and not is_file_search:
                trigger_type = "chrome"
                command = query
                print(f"[PRE-CHECK] Smart detect: WEB search")
            # For ambiguous "search X" without context, default to WEB search for better results
            elif not is_web_search and not is_file_search:
                trigger_type = "chrome"  # Now routes to RealtimeSearchEngine
                command = query
                print(f"[PRE-CHECK] Ambiguous search → defaulting to WEB search")
        
        # === SMART MUSIC vs VIDEO vs SPOTIFY vs ANIME DETECTION ===
        if not trigger_type and ("play" in query_lower or "watch" in query_lower or "stream" in query_lower or "listen" in query_lower):
            
            # 0. ANIME Priority - Check for anime-specific keywords FIRST
            anime_keywords = ["anime", "episode", "ep ", "episodes", "manga", "demon slayer", "naruto", 
                              "attack on titan", "one piece", "jujutsu", "my hero", "dragon ball",
                              "bleach", "death note", "fullmetal", "spy x family", "chainsaw man",
                              "trending anime", "popular anime", "top anime", "anime info"]
            is_anime = any(kw in query_lower for kw in anime_keywords)
            
            if is_anime:
                trigger_type = "anime"
                command = query
                print(f"[PRE-CHECK] Smart detect: ANIME")
            # 1. Spotify Priority - Check for explicit Spotify request
            elif any(sp in query_lower for sp in ["spotify", "on spotify", "using spotify", "from spotify", "in spotify"]):
                trigger_type = "spotify"
                command = query
                print(f"[PRE-CHECK] Smart detect: SPOTIFY")
            
            # 1a. NEW INTEGRATIONS DETECTION
            elif "weather" in query_lower or "forecast" in query_lower or "temperature" in query_lower:
                trigger_type = "weather"
                command = query
            elif "news" in query_lower or "headline" in query_lower:
                trigger_type = "news" if "hacker" not in query_lower else "hacker_news"
                command = query
            elif "system" in query_lower and ("stat" in query_lower or "info" in query_lower or "usage" in query_lower):
                trigger_type = "system_stats"
            elif ("cpu" in query_lower or "ram" in query_lower or "battery" in query_lower) and ("usage" in query_lower or "level" in query_lower):
                 trigger_type = "system_stats"
            elif "crypto" in query_lower or "bitcoin" in query_lower or "btc" in query_lower or "eth" in query_lower:
                trigger_type = "crypto"
                command = query
            elif "stock" in query_lower or "share price" in query_lower:
                trigger_type = "stock"
                command = query
            elif "github" in query_lower and ("repo" in query_lower or "code" in query_lower):
                trigger_type = "github"
                command = query
            elif "apod" in query_lower or "astronomy picture" in query_lower or "space image" in query_lower:
                trigger_type = "nasa_apod"
            
            # 1b. SAAS INTEGRATIONS DETECTION
            elif "figma" in query_lower:
                trigger_type = "figma"
                command = query
            elif "notion" in query_lower:
                trigger_type = "notion"
                command = query
            elif "slack" in query_lower:
                trigger_type = "slack"
                command = query
            elif "trello" in query_lower:
                trigger_type = "trello"
                command = query
            elif "calendar" in query_lower or "schedule" in query_lower or "event" in query_lower:
                trigger_type = "calendar"
                command = query


            else:
                music_words = ["music", "song", "audio", "track", "playlist", "album"]
                video_words = ["video", "movie", "youtube video", "clip", "show me"]  # Removed "watch" to avoid false positives
                stream_words = ["radio", "stream", "live", "news", "tv", "channel", "broadcast"]
                
                is_music = any(w in query_lower for w in music_words)
                is_video = any(w in query_lower for w in video_words)
                is_stream = any(w in query_lower for w in stream_words)
                
                if is_stream:
                    trigger_type = "stream"
                    command = query
                    print(f"[PRE-CHECK] Smart detect: STREAM")
                elif is_music and not is_video:
                    trigger_type = "music"
                    command = query
                    print(f"[PRE-CHECK] Smart detect: MUSIC")
                elif is_video and not is_music:
                    trigger_type = "video"
                    command = query
                    print(f"[PRE-CHECK] Smart detect: VIDEO")
                # NOTE: Removed "play defaults to music" - too many false positives
                # "play game", "play chess", etc. would wrongly trigger music
                # Only trigger music when explicit music words are present
                elif "watch" in query_lower:
                    # "watch" without video keywords could be anime
                    trigger_type = "anime"
                    command = query
                    print(f"[PRE-CHECK] 'watch' without specific context → ANIME")

        # === COGNITIVE ORCHESTRATOR (NEW ARCHITECTURE) ===
        # Uses Goal Inference → Hypothesis Generation → Confidence Gating
        # Falls back to SmartTrigger if goal inference fails or is disabled
        
        # Use CognitiveOrchestrator only if pre-check didn't match
        if not trigger_type:
            try:
                from Backend.CognitiveOrchestrator import cognitive_orchestrator
                
                # Process through goal-based pipeline
                cognitive_result = cognitive_orchestrator.process(original_query, chat_context)
                
                # Check if clarification is needed (low confidence)
                if cognitive_orchestrator.needs_clarification(cognitive_result):
                    clarification = cognitive_result.get("clarification", "Could you please provide more details?")
                    print(f"[COGNITIVE] 🤔 Clarification needed: {clarification[:50]}...")
                    return jsonify({
                        "response": clarification,
                        "type": "clarification",
                        "metadata": {
                            "needs_clarification": True,
                            "detected_intent": cognitive_result.get("intent"),
                            "confidence": cognitive_result.get("confidence", 0)
                        }
                    }), 200
                
                # Extract trigger info for existing handler logic
                trigger_type = cognitive_result.get("trigger_type")
                command = cognitive_result.get("command") or original_query
                
                # Log the result
                print(f"[COGNITIVE] ✅ {cognitive_result.get('intent')} (conf: {cognitive_result.get('confidence', 0):.2f}) → trigger: {trigger_type}")
                
            except Exception as cog_err:
                print(f"[COGNITIVE] ⚠️ Orchestrator error: {cog_err}, using legacy SmartTrigger")
                # Fallback to direct SmartTrigger call
                from Backend.SmartTrigger import smart_trigger
                trigger_type, command, _ = smart_trigger.detect(original_query)

        # === VISION ANALYSIS GUARD ===
        # If user uploaded image attachments and wants analysis (not generation), skip image generation trigger
        # This prevents "analyze image" from generating new images when user uploaded an image
        if trigger_type == "image" and attachments:
            has_image_attachments = any(
                att.get('type') == 'image' or 
                att.get('name', '').lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'))
                for att in attachments
            )
            analysis_keywords = ['analyze', 'describe', 'what is', "what's", 'explain', 'look at', 'tell me about', 
                                'identify', 'recognize', 'read', 'extract', 'ocr', 'transcribe', 'caption']
            wants_analysis = any(kw in original_query_lower for kw in analysis_keywords)
            
            if has_image_attachments and (wants_analysis or not any(v in original_query_lower for v in ['generate', 'create', 'make', 'draw'])):
                print(f"[GUARD] 🛡️ Skipping image generation - user has image attachment and wants analysis, not generation")
                trigger_type = None  # Let it fall through to ChatBot with vision context


        response_text = ""
        
        
        # 1. MUSIC/MEDIA COMMANDS
        # 1. MUSIC COMMANDS - YOUTUBE (Spotify Removed)
        if trigger_type == "music":
             print(f"[SMART-TRIGGER] Music command detected: {command} -> Using YouTube")
             try:
                 from Backend.MultiMusicPlayer import multi_music_player
                 
                 search_query = command if command and command.lower() not in ['music', 'song', 'track', 'audio'] else "lofi beats"
                 
                 # Play using MultiMusicPlayer (forced to YouTube)
                 result = multi_music_player.play(search_query, source="youtube")
                 
                 if result.get("status") == "success":
                     return jsonify({
                         "response": result["message"],
                         "music": result.get("music"),
                         "type": "music" 
                     }), 200
                 else:
                     response_text = result.get("message", "Could not play music.")
                     
             except Exception as e:
                 print(f"[ERROR] Music player error: {e}")
                 import traceback
                 traceback.print_exc()
                 response_text = f"Music error: {str(e)}"
                 
        # 1c. STREAM/RADIO COMMANDS (YouTube Live)
        elif trigger_type == "stream":
             print(f"[SMART-TRIGGER] Stream command detected: {command}")
             try:
                 from Backend.MultiMusicPlayer import multi_music_player
                 
                 search_query = command if command else "lofi hip hop radio"
                 
                 # Force YouTube for streams
                 result = multi_music_player.play(search_query, source="youtube")
                 
                 if result.get("status") == "success":
                     # Override type to 'stream' for different UI
                     return jsonify({
                         "response": result["message"].replace("Now playing", "Streaming"),
                         "music": result["music"],
                         "type": "stream"
                     }), 200
                 else:
                     response_text = result.get("error", "Could not find stream.")
                     
             except Exception as e:
                 print(f"[ERROR] Stream player error: {e}")
                 response_text = f"Stream player error: {str(e)}"

        # 1e. ANIME STREAMING
        elif trigger_type == "anime":
             print(f"[SMART-TRIGGER] Anime command detected: {command}")
             try:
                 from Backend.AnimeStreaming import anime_system
                 import re
                 
                 # Extract anime name and episode from query
                 anime_query = query.lower()
                 for prefix in ["watch anime ", "play anime ", "stream anime ", "anime ", "watch ", "play ", "stream "]:
                     if anime_query.startswith(prefix):
                         anime_query = anime_query[len(prefix):]
                         break
                 
                 # Check for episode number
                 ep_match = re.search(r'\bepisode\s+(\d+)\b', anime_query)
                 episode = int(ep_match.group(1)) if ep_match else 1
                 anime_name = re.sub(r'\bepisode\s+\d+\b', '', anime_query).strip()
                 
                 print(f"[ANIME] Searching: {anime_name}, Episode: {episode}")
                 
                 # Get stream data
                 result = anime_system.watch_anime(anime_name, episode)
                 
                 if result.get("status") == "success":
                     return jsonify({
                         "response": result.get("message", f"🎬 Now playing: {anime_name} Episode {episode}"),
                         "anime": result,  # Pass all the stream data
                         "type": "anime"
                     }), 200
                 else:
                     response_text = f"Could not stream '{anime_name}': {result.get('message', 'Unknown error')}"
                     
             except Exception as e:
                 print(f"[ERROR] Anime streaming error: {e}")
                 import traceback
                 traceback.print_exc()
                 response_text = f"Anime streaming error: {str(e)}"


        # 1f. ADVANCED INTEGRATIONS HANDLERS
        elif trigger_type in ["weather", "news", "hacker_news", "crypto", "stock", "github", "system_stats", "nasa_apod", "figma", "notion", "slack", "trello", "calendar"]:

             print(f"[SMART-TRIGGER] Integration command detected: {trigger_type}")
             try:
                 from Backend.AdvancedIntegrations import integrations
                 
                 data = {}
                 ui_type = trigger_type
                 response_msg = "Here is the information you requested."
                 
                 if trigger_type == "weather":
                     # Extract city from command - improved parsing
                     city = "London"  # Default
                     
                     if command:
                         words = command.split()
                         if "in" in words:
                             # Handle "weather in mumbai" format
                             try:
                                 idx = words.index("in")
                                 city_parts = words[idx + 1:]
                                 city = " ".join(city_parts) if city_parts else "London"
                             except: pass
                         else:
                             # Handle "@weather mumbai" format - take remaining words as city
                             # Filter out common non-city words
                             skip_words = ["weather", "forecast", "temperature", "temp", "for", "the", "what", "is", "check", "show", "me", "get"]
                             city_words = [w for w in words if w.lower() not in skip_words]
                             if city_words:
                                 city = " ".join(city_words)
                     
                     print(f"[WEATHER] Extracted city: {city}")
                     data = integrations.get_weather(city)
                     if "error" not in data:
                         response_msg = f"Current weather in {data['city']}: {data['temperature']}, {data['condition']}."
                     else:
                         response_msg = "Could not fetch weather data."
                         
                 elif trigger_type == "news":
                     topic = "technology"
                     if "about" in command:
                         try: topic = command.split("about")[1].strip()
                         except: pass
                     data = {"articles": integrations.get_news(topic)}
                     response_msg = f"Here are the latest headlines about {topic}."
                     
                 elif trigger_type == "hacker_news":
                     data = {"articles": integrations.get_hacker_news()}
                     response_msg = "Here are the top stories from Hacker News."
                     ui_type = "news" # Use same UI as news
                     
                 elif trigger_type == "crypto":
                     symbol = "bitcoin"
                     for coin in ["bitcoin", "ethereum", "dogecoin", "solana"]:
                         if coin in command.lower():
                             symbol = coin
                             break
                     data = integrations.get_crypto_price(symbol)
                     if "error" not in data:
                         response_msg = f"The price of {data['symbol']} is {data['price']} ({data['change_24h']})."
                     
                 elif trigger_type == "stock":
                     symbol = "AAPL"
                     # Very basic symbol extraction (assumes uppercase word)
                     for word in command.split():
                         if word.isupper() and len(word) <= 5 and word not in ["STOCK", "PRICE", "SHOW", "ME", "THE", "IS", "WHAT"]:
                             symbol = word
                             break
                     data = integrations.get_stock_price(symbol)
                     if "error" not in data:
                         response_msg = f"{data['symbol']} stock is at {data['price']}."
                         
                 elif trigger_type == "github":
                     username = "torvalds" # Default demo
                     if "user" in command or "for" in command:
                         # Try to grab last word
                         username = command.split()[-1]
                     data = {"repos": integrations.get_github_repos(username)}
                     response_msg = f"Found public repositories for {username}."
                     
                 elif trigger_type == "system_stats":
                     data = integrations.get_system_stats()
                     response_msg = f"System Status: CPU {data.get('cpu')}, RAM {data.get('ram')}."
                     
                 elif trigger_type == "nasa_apod":
                     data = integrations.get_nasa_apod()
                     response_msg = f"NASA Astronomy Picture of the Day: {data.get('title')}."
                 
                 # --- SAAS SUITE ---
                 elif trigger_type == "figma":
                     data = {"files": integrations.get_figma_files()}
                     response_msg = "Here are your recent Figma design files."
                 
                 elif trigger_type == "notion":
                     q = command.replace("notion", "").replace("search", "").strip()
                     data = {"pages": integrations.search_notion(q)}
                     response_msg = f"Found these Notion pages matching '{q}'." if q else "Here are your recent Notion pages."
                 
                 elif trigger_type == "slack":
                     if "send" in command or "message" in command:
                         # Very basic extraction: "send hello to general"
                         parts = command.split(" to ")
                         msg = parts[0].replace("send", "").replace("message", "").strip()
                         chn = parts[1].strip() if len(parts) > 1 else "general"
                         res = integrations.send_slack_message(chn, msg)
                         data = {"status": res, "message": msg, "channel": chn}
                         response_msg = f"Message sent to #{chn}."
                     else:
                         data = {"channels": integrations.get_slack_channels()}
                         response_msg = "Here are your public Slack channels."
                         
                 elif trigger_type == "trello":
                     data = {"boards": integrations.get_trello_boards()}
                     response_msg = "Here are your Trello boards."
                     
                 elif trigger_type == "calendar":
                     data = {"events": integrations.get_calendar_events()}
                     response_msg = "Here are your upcoming calendar events."
                 
                 return jsonify({
                     "response": response_msg,
                     "data": data,
                     "type": ui_type
                 }), 200

                 
             except Exception as e:
                 print(f"[ERROR] Integration error: {e}")
                 import traceback
                 traceback.print_exc()
                 response_text = f"Integration unavailable: {str(e)}"

        # 1d. WEB SCRAPING
        elif trigger_type == "device_status":
             print(f"[SMART-TRIGGER] Device status command detected")
             try:
                 from Backend.LocalAgentAPI import _registered_devices, _pending_tasks, _task_results, get_first_online_device, log_command
                 import uuid
                 import time as time_module
                 
                 # SECURITY: Get user's devices only
                 current_user_id = user_id if user_id != 'anonymous' else None
                 device_id, device_info = get_first_online_device(current_user_id)
                 
                 if not device_id:
                     return jsonify({
                         "response": "🔌 No PC is connected to your account. Please pair a device first.",
                         "type": "device_status",
                         "data": {"connected": False}
                     }), 200
                 
                 from datetime import datetime, timedelta
                 last_seen = datetime.fromisoformat(device_info.get('last_seen', '2000-01-01'))
                 is_online = (datetime.now() - last_seen).total_seconds() < 60
                 
                 if not is_online:
                     return jsonify({
                         "response": f"🔴 Your PC '{device_info.get('name', 'Unknown')}' is currently offline. Start the Local Agent to connect.",
                         "type": "device_status",
                         "data": {"connected": False, "device_name": device_info.get('name')}
                     }), 200
                 
                 task_id = str(uuid.uuid4())
                 task = {"task_id": task_id, "command": "system_status", "params": {}, "user_id": current_user_id or "anonymous", "created_at": datetime.now().isoformat()}
                 if device_id not in _pending_tasks:
                     _pending_tasks[device_id] = []
                 _pending_tasks[device_id].append(task)

                 # Push task to WebSocket
                 try:
                     from Backend.AgentWebSocket import send_task_sync
                     send_task_sync(device_id, task_id, task['command'], task['params'])
                 except Exception: pass
                 
                 # Audit log
                 log_command(current_user_id or "anonymous", device_id, "system_status", {}, "queued")
                 
                 max_wait, start_time, result_data = 10, time_module.time(), None
                 while time_module.time() - start_time < max_wait:
                     if task_id in _task_results:
                         result_data = _task_results[task_id]
                         break
                     time_module.sleep(0.5)
                 
                 if result_data and result_data.get("status") == "success":
                     agent_result = result_data.get("result", {})
                     data = agent_result.get("data", {})
                     cpu, memory, uptime, system = data.get("cpu", {}), data.get("memory", {}), data.get("uptime", {}), data.get("system", {})
                     
                     response_msg = f"🖥️ **{device_info.get('name', 'Your PC')}** is online!\n\n📊 **System Status:**\n• CPU: {cpu.get('percent', 'N/A')}% ({cpu.get('cores_logical', 'N/A')} cores)\n• RAM: {memory.get('percent', 'N/A')}% ({memory.get('used_gb', 'N/A')}GB / {memory.get('total_gb', 'N/A')}GB)\n• Uptime: {uptime.get('formatted', 'N/A')}\n• OS: {system.get('os', 'N/A')} {system.get('os_release', '')}"
                     
                     return jsonify({"response": response_msg, "type": "device_status", "data": {"connected": True, "device_name": device_info.get('name'), "cpu_percent": cpu.get('percent'), "ram_percent": memory.get('percent'), "uptime": uptime.get('formatted'), "os": system.get('os')}}), 200
                 else:
                     return jsonify({"response": f"🟡 Your PC '{device_info.get('name')}' is connected but didn't respond in time.", "type": "device_status", "data": {"connected": True, "timeout": True}}), 200
                     
             except Exception as e:
                 print(f"[ERROR] Device status error: {e}")
                 response_text = f"Device status unavailable: {str(e)}"

        # OPEN APP: Open application via LocalAgent
        elif trigger_type == "open_app":
             print(f"[SMART-TRIGGER] 🚀 Open app command detected: {command}")
             try:
                 import uuid
                 import time as time_module
                 from datetime import datetime
                 from Backend.LocalAgentAPI import get_first_online_device, _pending_tasks, _task_results, log_command
                 
                 current_user_id = user_id if user_id != 'anonymous' else None
                 device_id, device_info = get_first_online_device(current_user_id)
                 
                 if not device_id:
                     return jsonify({
                         "response": f"❌ No PC connected. Pair a device first to open {command}.",
                         "type": "chat"
                     }), 200
                 
                 task_id = str(uuid.uuid4())
                 task = {
                     "task_id": task_id,
                     "command": "open_app",
                     "params": {"app": command},
                     "user_id": current_user_id or "anonymous",
                     "created_at": datetime.now().isoformat()
                 }
                 if device_id not in _pending_tasks:
                     _pending_tasks[device_id] = []
                 _pending_tasks[device_id].append(task)
                 
                 # Push task to WebSocket
                 try:
                     from Backend.AgentWebSocket import send_task_sync
                     send_task_sync(device_id, task_id, task['command'], task['params'])
                 except Exception: pass

                 log_command(current_user_id or "anonymous", device_id, "open_app", {"app": command}, "queued")
                 
                 max_wait, start_time, result_data = 10, time_module.time(), None
                 while time_module.time() - start_time < max_wait:
                     if task_id in _task_results:
                         result_data = _task_results[task_id]
                         break
                     time_module.sleep(0.3)
                 
                 if result_data and result_data.get("status") == "success":
                     return jsonify({"response": f"🚀 Opened {command}", "type": "open_app", "data": {"success": True}}), 200
                 elif result_data and result_data.get("status") == "error":
                     return jsonify({"response": f"❌ Couldn't open {command}: {result_data.get('result', {}).get('message', 'Unknown error')}", "type": "open_app"}), 200
                 else:
                     return jsonify({"response": f"🚀 Opening {command}...", "type": "open_app", "data": {"async": True}}), 200
                 
             except Exception as e:
                 print(f"[ERROR] Open app error: {e}")
                 response_text = f"Couldn't open {command}: {str(e)}"

        # CLOSE APP: Close application via LocalAgent
        elif trigger_type == "close_app":
             print(f"[SMART-TRIGGER] 🛑 Close app command detected: {command}")
             try:
                 import uuid
                 import time as time_module
                 from datetime import datetime
                 from Backend.LocalAgentAPI import get_first_online_device, _pending_tasks, _task_results, log_command
                 
                 current_user_id = user_id if user_id != 'anonymous' else None
                 device_id, device_info = get_first_online_device(current_user_id)
                 
                 if not device_id:
                     return jsonify({"response": f"❌ No PC connected. Pair a device first to close {command}.", "type": "chat"}), 200
                 
                 task_id = str(uuid.uuid4())
                 task = {
                     "task_id": task_id,
                     "command": "close_app",
                     "params": {"app": command},
                     "user_id": current_user_id or "anonymous",
                     "created_at": datetime.now().isoformat()
                 }
                 if device_id not in _pending_tasks:
                     _pending_tasks[device_id] = []
                 _pending_tasks[device_id].append(task)
                 
                 # Push task to WebSocket
                 try:
                     from Backend.AgentWebSocket import send_task_sync
                     send_task_sync(device_id, task_id, task['command'], task['params'])
                 except Exception: pass

                 log_command(current_user_id or "anonymous", device_id, "close_app", {"app": command}, "queued")
                 
                 max_wait, start_time, result_data = 10, time_module.time(), None
                 while time_module.time() - start_time < max_wait:
                     if task_id in _task_results:
                         result_data = _task_results[task_id]
                         break
                     time_module.sleep(0.3)
                 
                 if result_data and result_data.get("status") == "success":
                     return jsonify({"response": f"🛑 Closed {command}", "type": "close_app", "data": {"success": True}}), 200
                 elif result_data and result_data.get("status") == "error":
                     return jsonify({"response": f"❌ Couldn't close {command}: {result_data.get('result', {}).get('message', 'Unknown error')}", "type": "close_app"}), 200
                 else:
                     return jsonify({"response": f"🛑 Closing {command}...", "type": "close_app", "data": {"async": True}}), 200
                 
             except Exception as e:
                 print(f"[ERROR] Close app error: {e}")
                 response_text = f"Couldn't close {command}: {str(e)}"

        # SYSTEM CONTROL: Volume, Brightness, Mute, Lock via LocalAgent
        elif trigger_type == "system_control":
             # command is a dict with action and optional level
             action_data = command if isinstance(command, dict) else {"action": command}
             action = action_data.get("action", "")
             level = action_data.get("level")
             
             print(f"[SMART-TRIGGER] 🎛️ System control detected: {action} (level: {level})")
             try:
                 import uuid
                 import time as time_module
                 from datetime import datetime
                 from Backend.LocalAgentAPI import get_first_online_device, _pending_tasks, _task_results, log_command
                 
                 current_user_id = user_id if user_id != 'anonymous' else None
                 device_id, device_info = get_first_online_device(current_user_id)
                 
                 if not device_id:
                     # Provide helpful response for system controls
                     action_name = action.replace("_", " ").title()
                     return jsonify({
                         "response": f"❌ No PC connected. I can't control {action_name} without a paired device.",
                         "type": "chat"
                     }), 200
                 
                 # Build params for executor
                 params = {"action": action}
                 if level is not None:
                     params["level"] = level
                 
                 task_id = str(uuid.uuid4())
                 task = {
                     "task_id": task_id,
                     "command": "system_control",
                     "params": params,
                     "user_id": current_user_id or "anonymous",
                     "created_at": datetime.now().isoformat()
                 }
                 if device_id not in _pending_tasks:
                     _pending_tasks[device_id] = []
                 _pending_tasks[device_id].append(task)
                 
                 # Push task to WebSocket
                 try:
                     from Backend.AgentWebSocket import send_task_sync
                     send_task_sync(device_id, task_id, task['command'], task['params'])
                 except Exception: pass

                 log_command(current_user_id or "anonymous", device_id, "system_control", params, "queued")
                 
                 # Wait for result
                 max_wait, start_time, result_data = 10, time_module.time(), None
                 while time_module.time() - start_time < max_wait:
                     if task_id in _task_results:
                         result_data = _task_results[task_id]
                         break
                     time_module.sleep(0.3)
                 
                 if result_data and result_data.get("status") == "success":
                     msg = result_data.get("result", {}).get("message", f"{action} completed")
                     data = result_data.get("result", {}).get("data", {})
                     return jsonify({
                         "response": msg,
                         "type": "system_control",
                         "data": {"success": True, **data}
                     }), 200
                 elif result_data and result_data.get("status") == "error":
                     error_msg = result_data.get("result", {}).get("message", "Unknown error")
                     return jsonify({
                         "response": f"❌ {error_msg}",
                         "type": "system_control",
                         "data": {"success": False}
                     }), 200
                 else:
                     # Async response
                     action_name = action.replace("_", " ")
                     return jsonify({
                         "response": f"🎛️ {action_name.title()}...",
                         "type": "system_control",
                         "data": {"async": True}
                     }), 200
                 
             except Exception as e:
                 print(f"[ERROR] System control error: {e}")
                 response_text = f"System control failed: {str(e)}"

        # FILE MANAGER: Sandboxed file operations via LocalAgent
        elif trigger_type == "file_manager":
             action_data = command if isinstance(command, dict) else {"action": "list_files"}
             action = action_data.get("action", "list_files")
             
             print(f"[SMART-TRIGGER] 📁 File manager detected: {action}")
             try:
                 import uuid
                 import time as time_module
                 from datetime import datetime
                 from Backend.LocalAgentAPI import get_first_online_device, _pending_tasks, _task_results, log_command
                 from Backend.WritingContext import get_last_writing
                 
                 current_user_id = user_id if user_id != 'anonymous' else None
                 device_id, device_info = get_first_online_device(current_user_id)
                 
                 if not device_id:
                     return jsonify({
                         "response": f"❌ No PC connected. I need a paired device for file operations.",
                         "type": "chat"
                     }), 200
                 
                 # Build params for executor
                 params = {"action": action}
                 
                 # Copy relevant params from action_data
                 for key in ["name", "content", "folder", "parent", "old_name", "new_name", "destination"]:
                     if key in action_data and action_data[key]:
                         params[key] = action_data[key]
                 
                 # For save_file, get content from WritingContext if not provided
                 if action == "save_file" and "content" not in params:
                     last_writing = get_last_writing(current_user_id or "anonymous")
                     if last_writing:
                         params["content"] = last_writing.get("content", "")
                         # Generate filename from content type if not provided
                         if "name" not in params or not params["name"]:
                             content_type = last_writing.get("content_type", "note")
                             timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
                             params["name"] = f"kai_{content_type}_{timestamp}.txt"
                     else:
                         return jsonify({
                             "response": "📝 No recent content to save. Write something first!",
                             "type": "chat"
                         }), 200
                 
                 # For create_folder without name, ask for clarification
                 if action == "create_folder" and "name" not in params:
                     return jsonify({
                         "response": "📁 What would you like to name the folder?",
                         "type": "chat"
                     }), 200
                 
                 task_id = str(uuid.uuid4())
                 task = {
                     "task_id": task_id,
                     "command": "file_manager",
                     "params": params,
                     "user_id": current_user_id or "anonymous",
                     "created_at": datetime.now().isoformat()
                 }
                 if device_id not in _pending_tasks:
                     _pending_tasks[device_id] = []
                 _pending_tasks[device_id].append(task)
                 
                 # Push task to WebSocket
                 try:
                     from Backend.AgentWebSocket import send_task_sync
                     send_task_sync(device_id, task_id, task['command'], task['params'])
                 except Exception: pass

                 log_command(current_user_id or "anonymous", device_id, "file_manager", params, "queued")
                 
                 # Wait for result
                 max_wait, start_time, result_data = 10, time_module.time(), None
                 while time_module.time() - start_time < max_wait:
                     if task_id in _task_results:
                         result_data = _task_results[task_id]
                         break
                     time_module.sleep(0.3)
                 
                 if result_data and result_data.get("status") == "success":
                     msg = result_data.get("result", {}).get("message", f"File operation completed")
                     data = result_data.get("result", {}).get("data", {})
                     
                     # Format list_files response nicely
                     if action == "list_files" and "items" in data:
                         items = data["items"]
                         if items:
                             item_list = "\n".join([f"{'📁' if i['type']=='folder' else '📄'} {i['name']}" for i in items[:10]])
                             msg = f"📂 Your Kai folder:\n{item_list}"
                             if len(items) > 10:
                                 msg += f"\n...and {len(items)-10} more"
                         else:
                             msg = "📂 Your Kai folder is empty"
                     
                     return jsonify({
                         "response": msg,
                         "type": "file_manager",
                         "data": {"success": True, **data}
                     }), 200
                 elif result_data and result_data.get("status") == "error":
                     error_msg = result_data.get("result", {}).get("message", "Unknown error")
                     return jsonify({
                         "response": f"❌ {error_msg}",
                         "type": "file_manager",
                         "data": {"success": False}
                     }), 200
                 else:
                     return jsonify({
                         "response": f"📁 {action.replace('_', ' ').title()}...",
                         "type": "file_manager",
                         "data": {"async": True}
                     }), 200
                 
             except Exception as e:
                 print(f"[ERROR] File manager error: {e}")
                 import traceback
                 traceback.print_exc()
                 response_text = f"File operation failed: {str(e)}"

        # CONTINUE WRITING: Continue/extend previous writing via WritingContext
        elif trigger_type == "continue_writing":
             print(f"[SMART-TRIGGER] ✍️ Continue writing detected: {command}")
             try:
                 import uuid
                 import time as time_module
                 from datetime import datetime
                 from Backend.LocalAgentAPI import get_first_online_device, _pending_tasks, _task_results, log_command
                 from Backend.WritingContext import get_last_writing, save_writing
                 from Backend.LLM.ChatCompletion import ChatCompletion
                 
                 current_user_id = user_id if user_id != 'anonymous' else None
                 
                 # Get last written content
                 last_writing = get_last_writing(current_user_id or "anonymous")
                 if not last_writing:
                     return jsonify({
                         "response": "📝 I don't have any recent writing to continue. Ask me to write something first!",
                         "type": "chat"
                     }), 200
                 
                 original_content = last_writing.get("content", "")
                 content_type = last_writing.get("content_type", "text")
                 
                 # Build continuation prompt
                 system_prompt = f"""You are a creative writing assistant. The user previously wrote this {content_type}:

---
{original_content}
---

Now continue or extend this {content_type} based on the user's request. 
Maintain the same style, tone, and format. 
Output ONLY the continuation (not the original), ready to be appended."""

                 user_request = command if command else "continue this"
                 
                 # Generate continuation
                 chat = ChatCompletion()
                 continuation = chat.chat(user_request, system_prompt=system_prompt)
                 
                 if not continuation:
                     return jsonify({
                         "response": "❌ Couldn't generate continuation. Please try again.",
                         "type": "chat"
                     }), 200
                 
                 # Combine original + continuation
                 combined_content = original_content + "\n\n" + continuation
                 
                 # Save to WritingContext
                 save_writing(current_user_id or "anonymous", combined_content, content_type)
                 
                 # Check if device is available to write to Notepad
                 device_id, device_info = get_first_online_device(current_user_id)
                 
                 if device_id:
                     # Write continuation to Notepad
                     task_id = str(uuid.uuid4())
                     task = {
                         "task_id": task_id,
                         "command": "write_notepad",
                         "params": {"text": "\n\n" + continuation},  # Append with spacing
                         "user_id": current_user_id or "anonymous",
                         "created_at": datetime.now().isoformat()
                     }
                     if device_id not in _pending_tasks:
                         _pending_tasks[device_id] = []
                     _pending_tasks[device_id].append(task)
                     
                     return jsonify({
                         "response": f"✍️ Continuing your {content_type}...\n\n{continuation[:200]}{'...' if len(continuation) > 200 else ''}",
                         "type": "continue_writing",
                         "data": {"content": continuation, "combined": combined_content}
                     }), 200
                 else:
                     # No device, return in chat
                     return jsonify({
                         "response": f"✍️ Here's the continuation:\n\n{continuation}",
                         "type": "continue_writing",
                         "data": {"content": continuation}
                     }), 200
                 
             except Exception as e:
                 print(f"[ERROR] Continue writing error: {e}")
                 import traceback
                 traceback.print_exc()
                 response_text = f"Continue writing failed: {str(e)}"

        # NOTEPAD: Write text to Notepad via LocalAgent (includes CREATIVE WRITING)
        elif trigger_type == "notepad":
             print(f"[SMART-TRIGGER] 📝 Notepad command detected: {command}")
             try:
                 import uuid
                 import time as time_module
                 from Backend.LocalAgentAPI import get_first_online_device, _pending_tasks, _task_results, log_command
                 from Backend.WritingContext import save_writing, get_last_writing
                 
                 query_lower = query.lower()
                 
                 # Define user_id early so it's available for save_writing
                 current_user_id = user_id if user_id != 'anonymous' else None
                 
                 # === CREATIVE WRITING DETECTION ===
                 # Note: 'note' is NOT here to avoid conflict with 'take a note' direct commands
                 creative_types = {
                     "poem": ["poem", "haiku", "verse", "poetry"],
                     "letter": ["letter to", "letter for"],
                     "story": ["story about", "tale about", "short story"],
                     "reflection": ["reflection on", "reflection about", "thought about"],
                     "paragraph": ["paragraph about"]
                 }
                 
                 detected_type = None
                 for ctype, keywords in creative_types.items():
                     if any(kw in query_lower for kw in keywords):
                         detected_type = ctype
                         break
                 
                 # Creative if we detected a type (about/on/for is already in the keywords)
                 is_creative = detected_type is not None
                 
                 # Check for continuation
                 is_continuation = any(word in query_lower for word in [
                     "add another", "continue", "extend", "another stanza", "another verse"
                 ])
                 
                 print(f"[NOTEPAD] Detection: creative={is_creative}, type={detected_type}, continuation={is_continuation}")
                 
                 if is_creative or is_continuation:
                     # === GENERATE CONTENT VIA LLM ===
                     print(f"[NOTEPAD] ✨ Creative writing mode: generating {detected_type}")
                     
                     try:
                         from Backend.LLM import ChatCompletion
                         
                         # Build the generation prompt
                         if is_continuation:
                             system_prompt = """You are a creative writer. Continue the previous piece.
Add another stanza, verse, or paragraph that flows naturally.
Output ONLY the new content, no explanations.
Use plain text with line breaks for structure."""
                             content_prompt = query
                         else:
                             structure_hints = {
                                 "poem": "Include a title at the top, then blank lines between stanzas. Write 3-4 stanzas of 3-4 lines each.",
                                 "letter": "Start with 'Dear...', include 2-3 heartfelt paragraphs, end with a warm signature.",
                                 "story": "Include a creative title, then 2-3 short narrative paragraphs.",
                                 "reflection": "Include a thoughtful title, then flowing contemplative paragraphs.",
                                 "paragraph": "Write a well-structured, meaningful paragraph."
                             }
                             
                             system_prompt = f"""You are a creative writer generating beautiful content for Notepad.
Output ONLY the content - no markdown, no code blocks, no backticks, just plain text.
{structure_hints.get(detected_type, '')}
Use line breaks (press Enter) and blank lines for visual structure.
Make it beautiful, meaningful, and intentional."""
                             
                             # Use FULL query for proper context, not just extracted command
                             content_prompt = query
                         
                         # Generate the content using ChatCompletion
                         generated_content = ChatCompletion(
                             messages=[
                                 {"role": "user", "content": content_prompt}
                             ],
                             system_prompt=system_prompt,
                             model="llama-3.3-70b-versatile",
                             text_only=True,
                             inject_memory=False
                         )
                         
                         text_to_write = generated_content.strip()
                         print(f"[NOTEPAD] ✨ Generated {len(text_to_write)} chars of {detected_type}")
                         
                         # Save writing context for continuity
                         save_writing(
                             user_id=current_user_id or "anonymous",
                             content=text_to_write,
                             content_type=detected_type or "creative",
                             destination="notepad",
                             metadata={"topic": command, "query": query}
                         )
                         
                     except Exception as gen_error:
                         print(f"[NOTEPAD] Generation error: {gen_error}")
                         text_to_write = command  # Fall back to direct text
                 else:
                     # === DIRECT TEXT MODE ===
                     text_to_write = command if command else ""
                     
                     # Clean up the text - remove common prefixes
                     for prefix in ["to notepad", "in notepad", "notepad:", "note:", "take a note", "note down", "jot down"]:
                         if text_to_write.lower().startswith(prefix):
                             text_to_write = text_to_write[len(prefix):].strip()
                             break
                     text_to_write = text_to_write.lstrip(":").strip()
                     
                     if not text_to_write:
                         text_to_write = query.replace("write to notepad", "").replace("notepad", "").replace("take a note", "").strip()
                         text_to_write = text_to_write.lstrip(":").strip()
                 
                 if not text_to_write:
                     return jsonify({
                         "response": "📝 What would you like me to write? Try 'Write a poem about silence in notepad' or 'Put my shopping list on my PC'",
                         "type": "notepad"
                     }), 200
                 
                 # Get user's online device
                 current_user_id = user_id if user_id != 'anonymous' else None
                 device_id, device_info = get_first_online_device(current_user_id)
                 
                 # GRACEFUL FALLBACK: If no device, generate content and show in chat
                 if not device_id:
                      # Generate content if creative, then show in chat
                      if is_creative or is_continuation:
                          # Save for continuity (destination=chat since no device)
                          save_writing(
                              user_id=current_user_id or "anonymous",
                              content=text_to_write,
                              content_type=detected_type or "direct",
                              destination="chat",
                              metadata={"topic": command, "fallback": "no_device"}
                          )
                          return jsonify({
                              "response": f"I can't access your PC right now (no device paired). Here's your {detected_type} instead:\n\n{text_to_write}",
                              "type": "chat"
                          }), 200
                      else:
                          return jsonify({
                              "response": f"I can't access your PC right now (no device paired). Here's what I would write:\n\n{text_to_write}",
                              "type": "chat"
                          }), 200
                 
                 from datetime import datetime, timedelta
                 last_seen = datetime.fromisoformat(device_info.get('last_seen', '2000-01-01'))
                 is_online = (datetime.now() - last_seen).total_seconds() < 60
                 
                 # GRACEFUL FALLBACK: If device offline, show content in chat
                 if not is_online:
                     if is_creative or is_continuation:
                          # Save for continuity (destination=chat since device offline)
                          save_writing(
                              user_id=current_user_id or "anonymous",
                              content=text_to_write,
                              content_type=detected_type or "direct",
                              destination="chat",
                              metadata={"topic": command, "fallback": "device_offline"}
                          )
                          return jsonify({
                              "response": f"Your PC '{device_info.get('name')}' is offline. Here's your {detected_type} instead:\n\n{text_to_write}",
                              "type": "chat"
                          }), 200
                     else:
                         return jsonify({
                             "response": f"Your PC '{device_info.get('name')}' is offline. Here's what I would write:\n\n{text_to_write}",
                             "type": "chat"
                         }), 200
                 
                 # Queue the write_notepad command
                 task_id = str(uuid.uuid4())
                 task = {
                     "task_id": task_id,
                     "command": "write_notepad",
                     "params": {"text": text_to_write},
                     "user_id": current_user_id or "anonymous",
                     "created_at": datetime.now().isoformat()
                 }
                 if device_id not in _pending_tasks:
                     _pending_tasks[device_id] = []
                 _pending_tasks[device_id].append(task)
                 
                 # Audit log
                 log_command(current_user_id or "anonymous", device_id, "write_notepad", {"text_length": len(text_to_write)}, "queued")
                 
                 print(f"[NOTEPAD] Queued write_notepad for device {device_id[:8]}...: {len(text_to_write)} chars")
                 
                 # Wait for result (max 15 seconds for Notepad to open and type)
                 max_wait, start_time, result_data = 15, time_module.time(), None
                 while time_module.time() - start_time < max_wait:
                     if task_id in _task_results:
                         result_data = _task_results[task_id]
                         break
                     time_module.sleep(0.5)
                 
                 if result_data and result_data.get("status") == "success":
                     agent_result = result_data.get("result", {})
                     chars_written = agent_result.get("data", {}).get("chars_written", len(text_to_write))
                     
                     # Custom message based on content type
                     if is_creative and detected_type:
                         type_messages = {
                             "poem": f"✨ I've written a poem for you ({chars_written} characters). Check Notepad!",
                             "letter": f"✨ I've composed a letter for you ({chars_written} characters). It's in Notepad!",
                             "story": f"✨ I've crafted a short story ({chars_written} characters). Open Notepad to read it!",
                             "reflection": f"✨ I've written a reflection ({chars_written} characters). See Notepad!",
                             "note": f"📝 Done! Your note is in Notepad ({chars_written} characters).",
                             "paragraph": f"📝 Done! Written to Notepad ({chars_written} characters)."
                         }
                         response_msg = type_messages.get(detected_type, f"✨ Done! I've written your {detected_type} to Notepad.")
                     elif is_continuation:
                         response_msg = f"✨ Added new content to Notepad ({chars_written} characters)!"
                     else:
                         response_msg = f"📝 Done! Written to Notepad ({chars_written} characters)."
                     
                     return jsonify({
                         "response": response_msg,
                         "type": "notepad",
                         "data": {"success": True, "chars_written": chars_written, "content_type": detected_type or "direct"}
                     }), 200
                 elif result_data and result_data.get("status") == "error":
                     error_msg = result_data.get("result", {}).get("message", "Unknown error")
                     return jsonify({
                         "response": f"📝 Couldn't write to Notepad: {error_msg}",
                         "type": "notepad",
                         "data": {"success": False, "error": error_msg}
                     }), 200
                 else:
                     return jsonify({
                         "response": f"📝 I've sent the note to your PC '{device_info.get('name')}'. It should appear in Notepad shortly!",
                         "type": "notepad",
                         "data": {"success": True, "async": True}
                     }), 200
                     
             except Exception as e:
                 print(f"[ERROR] Notepad error: {e}")
                 import traceback
                 traceback.print_exc()
                 response_text = f"Notepad error: {str(e)}"

        # WRITING CONTINUITY: Continue, extend, or refine previous writing
        elif trigger_type == "continue_writing":
             print(f"[SMART-TRIGGER] 📝 Writing continuation request: {query}")
             try:
                 current_user_id = user_id if user_id != 'anonymous' else None
                 
                 # Get user's last writing context
                 last_writing = get_last_writing(current_user_id or "anonymous")
                 
                 if not last_writing:
                     return jsonify({
                         "response": "📝 I don't have anything to continue. Write something first, like 'Write a poem about the moon'.",
                         "type": "chat"
                     }), 200
                 
                 query_lower = query.lower()
                 original_content = last_writing["content"]
                 content_type = last_writing["content_type"]
                 
                 # Parse continuation intent
                 action = "continue"  # default
                 mood_change = None
                 quantity = None
                 
                 # Detect action type
                 if any(w in query_lower for w in ["rewrite", "redo", "fix"]):
                     action = "rewrite"
                 elif any(w in query_lower for w in ["add", "another", "more"]):
                     action = "add"
                 elif any(w in query_lower for w in ["shorter", "longer", "darker", "lighter", "happier", "sadder", "better", "stronger"]):
                     action = "modify"
                     for mod in ["shorter", "longer", "darker", "lighter", "happier", "sadder", "better", "stronger", "more dramatic", "more emotional"]:
                         if mod in query_lower:
                             mood_change = mod
                             break
                 
                 # Detect quantity
                 import re
                 quantity_match = re.search(r"(\d+|another|one more|a)\s+(stanza|stanzas|verse|verses|paragraph|paragraphs|line|lines)", query_lower)
                 if quantity_match:
                     quantity = quantity_match.group(0)
                 
                 print(f"[CONTINUE_WRITING] Action: {action}, Mood: {mood_change}, Quantity: {quantity}, Original: {len(original_content)} chars")
                 
                 # Build LLM prompt based on action
                 from Backend.LLM import ChatCompletion
                 
                 if action == "continue":
                     system_prompt = f"""You are continuing a {content_type}.
The user's previous content is provided. Generate the next part that flows naturally.
Output ONLY the new content, no explanations or commentary.
Keep the same tone, style, and voice as the original."""
                     user_prompt = f"Continue this {content_type}:\n\n{original_content}"
                     
                 elif action == "add":
                     system_prompt = f"""You are adding to a {content_type}.
Add {quantity or 'another section'} that follows naturally from the original.
Output ONLY the new content, no explanations.
Maintain the same style and voice."""
                     user_prompt = f"Add {quantity or 'more'} to this {content_type}:\n\n{original_content}"
                     
                 elif action == "rewrite":
                     system_prompt = f"""You are improving the ending of a {content_type}.
Rewrite the last part to make it stronger and more impactful.
Output the COMPLETE piece with the improved ending."""
                     user_prompt = f"Improve the ending of this {content_type}:\n\n{original_content}"
                     
                 elif action == "modify":
                     system_prompt = f"""You are modifying a {content_type} to make it {mood_change or 'better'}.
Adjust the tone and mood while keeping the core meaning intact.
Output the COMPLETE modified piece."""
                     user_prompt = f"Make this {content_type} {mood_change or 'better'}:\n\n{original_content}"
                 else:
                     system_prompt = f"Continue this {content_type} naturally."
                     user_prompt = f"Continue:\n\n{original_content}"
                 
                 # Generate continuation
                 continued_content = ChatCompletion(
                     messages=[{"role": "user", "content": user_prompt}],
                     system_prompt=system_prompt,
                     model="llama-3.3-70b-versatile",
                     text_only=True,
                     inject_memory=False
                 ).strip()
                 
                 print(f"[CONTINUE_WRITING] Generated {len(continued_content)} chars")
                 
                 # Save the new content for future continuations
                 save_writing(
                     user_id=current_user_id or "anonymous",
                     content=continued_content,
                     content_type=content_type,
                     destination=last_writing["destination"],
                     metadata={"action": action, "original_length": len(original_content)}
                 )
                 
                 # Route output based on where original was sent
                 original_destination = last_writing.get("destination", "chat")
                 
                 if original_destination == "notepad":
                     # Try to send to notepad if device is online
                     from Backend.LocalAgentAPI import get_first_online_device, _pending_tasks, log_command
                     device_id, device_info = get_first_online_device(current_user_id)
                     
                     if device_id:
                         from datetime import datetime
                         last_seen = datetime.fromisoformat(device_info.get('last_seen', '2000-01-01'))
                         is_online = (datetime.now() - last_seen).total_seconds() < 60
                         
                         if is_online:
                             # Queue continuation for notepad
                             import uuid
                             task_id = str(uuid.uuid4())
                             
                             # Add newlines to separate from existing content
                             text_with_separator = "\n\n" + continued_content
                             
                             task = {
                                 "task_id": task_id,
                                 "command": "write_notepad",
                                 "params": {"text": text_with_separator},
                                 "user_id": current_user_id or "anonymous",
                                 "created_at": datetime.now().isoformat()
                             }
                             if device_id not in _pending_tasks:
                                 _pending_tasks[device_id] = []
                             _pending_tasks[device_id].append(task)
                             
                             log_command(current_user_id or "anonymous", device_id, "write_notepad", {"text_length": len(text_with_separator), "action": "continuation"}, "queued")
                             
                             # Build response message
                             action_msgs = {
                                 "continue": f"✨ I've continued your {content_type} in Notepad!",
                                 "add": f"✨ Added {quantity or 'more content'} to Notepad!",
                                 "rewrite": f"✨ I've rewritten the ending in Notepad!",
                                 "modify": f"✨ I've made it {mood_change or 'better'} in Notepad!"
                             }
                             
                             return jsonify({
                                 "response": action_msgs.get(action, "✨ Updated your writing in Notepad!"),
                                 "type": "notepad",
                                 "data": {"success": True, "action": action, "chars_added": len(continued_content)}
                             }), 200
                 
                 # Fallback to chat (device offline, not paired, or original was in chat)
                 action_msgs = {
                     "continue": f"Here's the continuation of your {content_type}:",
                     "add": f"Here's what I added to your {content_type}:",
                     "rewrite": f"Here's the improved version:",
                     "modify": f"Here's your {content_type}, now {mood_change or 'improved'}:"
                 }
                 
                 response_intro = action_msgs.get(action, "Here's the updated version:")
                 
                 return jsonify({
                     "response": f"{response_intro}\n\n{continued_content}",
                     "type": "writing_continuation",
                     "data": {"action": action, "content_type": content_type, "chars": len(continued_content)}
                 }), 200
                 
             except Exception as e:
                 print(f"[ERROR] Writing continuation error: {e}")
                 import traceback
                 traceback.print_exc()
                 response_text = f"I couldn't continue the writing: {str(e)}"

        elif trigger_type == "scrape":
             print(f"[SMART-TRIGGER] Scrape command detected: {command}")
             try:
                 import asyncio
                 from Backend.JarvisWebScraper import JarvisWebScraper
                 
                 url = command.strip()
                 # Basic URL cleanup
                 if not url.startswith('http'):
                     url = f"https://{url}" if '.' in url else f"https://google.com/search?q={url}"
                 
                 scraper = JarvisWebScraper()
                 
                 # Detect Deep Scrape
                 is_deep = any(k in query_lower for k in ['deep', 'analyze', 'full', 'comprehensive', 'extensively'])
                 
                 # Use new event loop for this sync request
                 content = asyncio.run(scraper.deep_scrape(url) if is_deep else scraper.scrape_to_markdown(url))
                 asyncio.run(scraper.close())
                 
                 # Parse metadata from content
                 lines = content.split('\n')
                 title = lines[0].replace("# ", "").strip() if len(lines) > 0 and lines[0].startswith("# ") else "Scraped Content"
                 
                 return jsonify({
                     "response": f"I've {'deeply analyzed' if is_deep else 'scraped'} the content from {title}.",
                     "scrape_result": {
                         "title": title,
                         "url": url,
                         "content": content,
                         "is_deep": is_deep
                     },
                     "type": "scrape"
                 }), 200
                     
             except Exception as e:
                 print(f"[ERROR] Scraper error: {e}")
                 response_text = f"Scraper error: {str(e)}"

        # RAG (Chat with Documents) - Handles PDF URLs and document chat
        elif trigger_type == "rag":
             print(f"[SMART-TRIGGER] RAG command detected: {command}")
             try:
                 from Backend.DocumentRAG import document_rag
                 
                 # Extract URL from command
                 import re
                 url_match = re.search(r'https?://[^\s]+', command or query)
                 
                 if url_match:
                     url = url_match.group(0)
                     # Upload and process the URL
                     result = document_rag.upload_url(url)
                     
                     if result.get("status") == "success":
                         # Now chat with it to summarize
                         chat_result = document_rag.chat_with_document("Please provide a comprehensive summary of this document.")
                         
                         summary = chat_result.get("response", "Document uploaded successfully!")
                         
                         return jsonify({
                             "response": f"📄 **{result.get('title', 'Document')}**\n\n{summary}",
                             "type": "rag",
                             "rag_result": {
                                 "doc_id": result.get("doc_id"),
                                 "title": result.get("title"),
                                 "char_count": result.get("char_count"),
                                 "summary": result.get("summary"),
                                 "suggested_questions": result.get("suggested_questions", [])
                             }
                         }), 200
                     else:
                         response_text = result.get("message", "Failed to process document")
                 else:
                     # No URL found - might be a follow-up question
                     chat_result = document_rag.chat_with_document(command or query)
                     if chat_result.get("status") == "success":
                         return jsonify({
                             "response": chat_result.get("response"),
                             "type": "rag_chat",
                             "documents_used": chat_result.get("documents_used", [])
                         }), 200
                     else:
                         response_text = chat_result.get("message", "No document loaded for chat")
                         
             except Exception as e:
                 print(f"[ERROR] RAG error: {e}")
                 import traceback
                 traceback.print_exc()
                 response_text = f"Document processing error: {str(e)}"


        # 2. IMAGE GENERATION (FIX)
        elif trigger_type == "image":
             print(f"[SMART-TRIGGER] Image generation command: {command}")
             try:
                 from Backend.EnhancedImageGen import enhanced_image_gen
                 
                 # Extract style from query
                 query_lower = query.lower()
                 detected_style = "realistic"  # Default
                 
                 # All available styles
                 style_keywords = {
                     "anime": "anime", "manga": "anime",
                     "oil_painting": "oil_painting", "oil painting": "oil_painting",
                     "watercolor": "watercolor", "water color": "watercolor",
                     "sketch": "sketch", "pencil": "sketch", "drawing": "sketch",
                     "3d_render": "3d_render", "3d": "3d_render", "unreal": "3d_render",
                     "cyberpunk": "cyberpunk", "neon": "neon", "futuristic": "cyberpunk",
                     "fantasy": "fantasy", "magical": "fantasy",
                     "minimalist": "minimalist", "minimal": "minimalist", "simple": "minimalist",
                     "vintage": "vintage", "retro": "vintage", "old": "vintage",
                     "comic": "comic", "cartoon": "comic",
                     "pixel_art": "pixel_art", "pixel": "pixel_art", "8-bit": "pixel_art",
                     "vaporwave": "vaporwave", "80s": "vaporwave",
                     "steampunk": "steampunk", "victorian": "steampunk",
                     "art_nouveau": "art_nouveau",
                     "pop_art": "pop_art", "warhol": "pop_art",
                     "impressionist": "impressionist", "monet": "impressionist",
                     "surrealist": "surrealist", "dali": "surrealist", "surreal": "surrealist",
                     "gothic": "gothic", "dark": "gothic",
                     "pastel": "pastel", "soft": "pastel", "kawaii": "pastel",
                     "low_poly": "low_poly", "geometric": "low_poly",
                     "isometric": "isometric",
                     "film_noir": "film_noir", "noir": "film_noir", "black and white": "film_noir",
                     "ukiyo_e": "ukiyo_e", "japanese": "ukiyo_e", "woodblock": "ukiyo_e",
                     "art_deco": "art_deco", "deco": "art_deco",
                     "realistic": "realistic", "photorealistic": "realistic", "photo": "realistic"
                 }
                 
                 # Find style in query
                 for keyword, style in style_keywords.items():
                     if keyword in query_lower:
                         detected_style = style
                         break
                 
                 print(f"[IMAGE] Detected style: {detected_style}")
                 
                 # Clean command to get just the subject
                 clean_prompt = command
                 for remove_word in ["generate", "create", "make", "draw", "image", "picture", "of", "the", "in", detected_style, "style"]:
                     clean_prompt = clean_prompt.lower().replace(remove_word, "").strip()
                 clean_prompt = " ".join(clean_prompt.split())  # Remove extra spaces
                 if not clean_prompt:
                     clean_prompt = command
                 
                 print(f"[IMAGE] Clean prompt: {clean_prompt}, Style: {detected_style}")
                 
                 user_id = request.current_user.get('user_id') if hasattr(request, 'current_user') else None
                 images = enhanced_image_gen.generate_with_style(clean_prompt, style=detected_style, num_images=1, user_id=user_id)
                 if images:
                     # Use direct URL from Pollinations (no local file system needed)
                     img_url = images[0]  # Already a full URL from generate_pollinations
                     print(f"[IMAGE] Generated image URL: {img_url[:80]}...")
                     
                     # LOG ACTION FOR CONTEXT/RETRY
                     try:
                         from Backend.ActionHistory import action_history
                         action_history.log_action(
                            "image_gen", 
                            {"prompt": clean_prompt, "style": detected_style, "num_images": 1, "model": "flux", "url": img_url}, 
                            f"Generated {detected_style} image of {clean_prompt}"
                         )
                     except ImportError:
                         print("[WARN] ActionHistory not found, context saving skipped")

                     response_text = f"Here is your **{detected_style}** image of {clean_prompt}:\n![Generated Image]({img_url})"
                 else:
                     response_text = "I tried to generate the image, but something went wrong."
             except Exception as e:
                 print(f"[ERROR] Image generation failed: {e}")
                 import traceback
                 traceback.print_exc()
                 response_text = f"Image generation failed: {str(e)}"

        # 2b. IMAGE MODIFICATION (Upscale, Variations, Background)
        elif any(k in query_lower for k in ["upscale", "enhance", "variation", "remove background", "no background"]):
             print(f"[SMART-TRIGGER] Image modification: {command}")
             try:
                 import os  # Explicit import to avoid UnboundLocalError
                 from Backend.ActionHistory import action_history
                 from Backend.EnhancedImageGen import enhanced_image_gen
                 
                 last_action = action_history.get_last_action()
                 
                 # Check if we have a previous image context
                 if last_action and last_action.action_type == "image_gen" and last_action.params.get("url"):
                     image_url = last_action.params.get("url")
                     
                     if "upscale" in query_lower or "enhance" in query_lower:
                         # CONVERT WEB PATH TO LOCAL ABSOLUTE PATH - ROBUST
                         if "/Data/" in image_url:
                             # Extract part after /Data/ e.g. "Images/foo.png"
                             rel_path = image_url.split("/Data/")[-1]
                             # Build local path: C:\...\Data\Images\foo.png
                             # Assuming Data folder is in os.getcwd()
                             local_path = os.path.join(os.getcwd(), "Data", rel_path.replace("/", os.sep))
                             image_url = local_path
                             print(f"[DEBUG] Converted web path to local: {image_url}")
                         elif image_url.startswith("http"):
                              # It's a remote URL from Pollinations, use as is (download logic inside upscale_image handles it)
                              pass
                         else:
                              # Assume relative path if not http
                              if not os.path.isabs(image_url):
                                  local_path = os.path.join(os.getcwd(), image_url.lstrip("/").replace("/", os.sep))
                                  image_url = local_path
                         
                         scale = 4 if "4x" in query_lower else 2
                         upscaled_path = enhanced_image_gen.upscale_image(image_url, scale=scale)
                         
                         # upscale_image already returns a web-servable path like /data/Images/filename.png
                         # Just need to capitalize "data" to "Data" for consistency
                         web_path = upscaled_path.replace("/data/", "/Data/")
                         
                         # LOG THE UPSCALED IMAGE FOR FUTURE REFERENCE
                         action_history.log_action(
                             "image_gen",
                             {"prompt": f"upscaled {scale}x", "style": "upscaled", "url": web_path},
                             f"Upscaled image {scale}x"
                         )
                             
                         response_text = f"Here is the **upscaled ({scale}x)** image:\n![Upscaled Image]({web_path})"
                         
                     elif "variation" in query_lower:
                         variations = enhanced_image_gen.generate_variations(image_url, num_variations=3)
                         if variations:
                             # Variations usually return /Data/... paths already, but let's be safe
                             imgs_md = ""
                             first_variation = None
                             for i, v in enumerate(variations):
                                 v_name = os.path.basename(v)
                                 v_path = f"/Data/{v_name}"
                                 if i == 0:
                                     first_variation = v_path  # Remember first one
                                 imgs_md += f"![Variation]({v_path})\n"
                             
                             # LOG THE FIRST VARIATION FOR FUTURE REFERENCE
                             if first_variation:
                                 action_history.log_action(
                                     "image_gen",
                                     {"prompt": "variation", "style": "variation", "url": first_variation},
                                     "Generated image variation"
                                 )
                             
                             response_text = f"Here are **3 variations** of your image:\n\n{imgs_md}"
                         else:
                             response_text = "Failed to generate variations."
                             
                     elif "background" in query_lower:
                         nobg_path = enhanced_image_gen.remove_background(image_url)
                         
                         # remove_background already returns a web-servable path, just capitalize "data"
                         web_path = nobg_path.replace("/data/", "/Data/")
                         
                         # LOG THE NO-BG IMAGE FOR FUTURE REFERENCE
                         action_history.log_action(
                             "image_gen",
                             {"prompt": "no background", "style": "transparent", "url": web_path},
                             "Removed background from image"
                         )
                         
                         response_text = f"Here is the image with **background removed**:\n![No BG Image]({web_path})"
                     
                     else:
                         response_text = "I'm not sure which modification you want. Try 'upscale', 'variations', or 'remove background'."
                 else:
                     response_text = "I don't remember the last image we generated. Please generate a new one first!"
                     
             except Exception as e:
                 print(f"[ERROR] Image modification failed: {e}")
                 import traceback
                 traceback.print_exc()
                 response_text = f"Image modification error: {str(e)}"

        # 4. MATH/CALCULATOR
        elif trigger_type == "math":
             try:
                 from Backend.MathSolver import MathSolver
                 solver = MathSolver()
                 result = solver.solve(command)
                 response_text = f"The answer is: {result}"
             except Exception as e:
                 response_text = f"Could not solve math problem: {str(e)}"

        # 5. TRANSLATOR
        elif trigger_type == "translate":
             try:
                 from Backend.Translator import Translator
                 target_lang_code = "fr"  # Default to French
                 text_to_translate = command
                 
                 # Parse "translate X to Y"
                 if " to " in command.lower():
                     parts = command.lower().split(" to ")
                     text_to_translate = parts[0].replace("translate", "").strip()
                     target_lang_name = parts[1].strip().lower()
                     
                     # Map language names to codes
                     lang_map = {'french': 'fr', 'spanish': 'es', 'german': 'de', 'italian': 'it', 
                                 'portuguese': 'pt', 'russian': 'ru', 'japanese': 'ja', 'korean': 'ko', 
                                 'chinese': 'zh', 'arabic': 'ar', 'hindi': 'hi', 'english': 'en'}
                     target_lang_code = lang_map.get(target_lang_name, target_lang_name[:2])
                 
                 translator = Translator()
                 result = translator.translate(text_to_translate, target_lang=target_lang_code)
                 
                 if result.get('status') == 'success':
                     response_text = f"Translation to {result.get('target_lang_name', target_lang_code)}: **{result['translation']}**"
                 else:
                     response_text = f"Translation: {result.get('message', 'Unavailable')}"
             except Exception as e:
                 print(f"[ERROR] Translation failed: {e}")
                 response_text = f"Translation failed: {str(e)}"

        # 6a. LIVE STREAMS (Radio & TV) - NEW
        elif trigger_type == "stream":
             print(f"[SMART-TRIGGER] Stream command: {command}")
             try:
                 from Backend.LiveStreamPlayer import live_stream_player
                 
                 q = query.lower()
                 
                 # Determine if searching for specific stream or listing
                 if any(w in q for w in ["list", "show", "available", "what"]):
                     if "tv" in q or "news" in q:
                         channels = live_stream_player.get_tv_channels()
                         channel_list = "\n".join([f"• **{c['name']}** ({c['genre']})" for c in channels[:5]])
                         response_text = f"📺 **Available TV Channels:**\n{channel_list}"
                     elif "radio" in q or "music" in q:
                         stations = live_stream_player.get_radio_stations()
                         station_list = "\n".join([f"• **{s['name']}** ({s['genre']})" for s in stations[:5]])
                         response_text = f"📻 **Available Radio Stations:**\n{station_list}"
                     else:
                         genres = live_stream_player.get_genres()
                         response_text = f"🎵 **Genres:** Music: {', '.join(genres['music'])} | TV: {', '.join(genres['tv'])}"
                 else:
                     # Play stream by query
                     result = live_stream_player.play_by_query(query)
                     
                     if result.get("status") == "success":
                         return jsonify({
                             "response": result.get("message"),
                             "music": result.get("music"),
                             "type": "stream",
                             "stream_type": result.get("stream_type")
                         }), 200
                     else:
                         response_text = f"❌ {result.get('error', 'Could not find stream')}"
             except Exception as e:
                 print(f"[ERROR] Stream error: {e}")
                 response_text = f"Stream error: {str(e)}"

        # 6b. WEBSITE CAPTURE (PDF) - NEW
        elif trigger_type == "capture":
             print(f"[SMART-TRIGGER] Capture command: {command}")
             try:
                 from Backend.WebsiteCapture import website_capture
                 import re
                 
                 # Extract URL from command
                 url_match = re.search(r'(https?://[^\s]+)', command)
                 if not url_match:
                     # Try to extract domain-like patterns
                     domain_match = re.search(r'([a-zA-Z0-9][-a-zA-Z0-9]*\.(?:com|org|net|io|co|edu|gov)[^\s]*)', command)
                     if domain_match:
                         url = "https://" + domain_match.group(1)
                     else:
                         response_text = "📄 Please provide a URL to capture. Example: 'capture https://example.com as pdf'"
                         url = None
                 else:
                     url = url_match.group(1)
                 
                 if url:
                     result = website_capture.url_to_pdf(url)
                     
                     if result.get("status") == "success":
                         return jsonify({
                             "response": f"📄 **PDF Captured:** {result.get('title', 'Page')}",
                             "type": "pdf_capture",
                             "title": result.get("title"),
                             "pdf_url": result.get("pdf_url"),
                             "thumbnail_url": result.get("thumbnail_url"),
                             "page_count": result.get("page_count", 1)
                         }), 200
                     else:
                         response_text = f"❌ Capture failed: {result.get('message', 'Unknown error')}"
             except ImportError:
                 response_text = "📄 Website capture module not available. Install playwright: pip install playwright"
             except Exception as e:
                 print(f"[ERROR] Capture error: {e}")
                 response_text = f"Capture error: {str(e)}"

        # 6c. WEB SCRAPING - ENHANCED
        elif trigger_type == "scrape":
             print(f"[SMART-TRIGGER] Scrape command: {command}")
             try:
                 import re
                 
                 # Extract URL from command
                 url_match = re.search(r'(https?://[^\s]+)', command)
                 if not url_match:
                     # Try to extract domain-like patterns
                     domain_match = re.search(r'([a-zA-Z0-9][-a-zA-Z0-9]*\.(?:com|org|net|io|co|edu|gov)[^\s]*)', command)
                     if domain_match:
                         url = "https://" + domain_match.group(1)
                     else:
                         response_text = "🌐 Please provide a URL to scrape. Example: 'scrape https://example.com'"
                         url = None
                 else:
                     url = url_match.group(1)
                 
                 if url:
                     # Try enhanced scraper first
                     try:
                         from Backend.EnhancedWebScraper import JarvisWebScraper
                         scraper = JarvisWebScraper()
                         result = scraper.scrape(url)
                         
                         if result:
                             title = result.get('title', 'Unknown')
                             description = result.get('meta_description', '')[:200]
                             text_preview = result.get('text', '')[:500]
                             links_count = len(result.get('links', []))
                             images_count = len(result.get('images', []))
                             
                             response_text = f"""🌐 **Scraped: {title}**

**Description:** {description}

**Content Preview:**
{text_preview}...

📊 Found {links_count} links, {images_count} images"""
                         else:
                             response_text = f"❌ Could not scrape {url}"
                     except ImportError:
                         # Fallback to basic requests
                         import requests
                         from bs4 import BeautifulSoup
                         
                         resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                         soup = BeautifulSoup(resp.text, 'html.parser')
                         
                         title = soup.title.string if soup.title else "No title"
                         text = soup.get_text()[:500].strip()
                         
                         response_text = f"🌐 **{title}**\n\n{text}..."
             except Exception as e:
                 print(f"[ERROR] Scrape error: {e}")
                 response_text = f"Scrape error: {str(e)}"
        # 6a. ANIME STREAMING (Watch, Search, Trending, Info)
        elif trigger_type in ["anime", "video"]:
             print(f"[SMART-TRIGGER] Anime/Video command detected: {command}")
             try:
                 from Backend.AnimeStreaming import anime_system
                 import re
                 
                 q = query.lower()
                 
                 # === TRENDING ANIME ===
                 if any(w in q for w in ["trending", "popular", "top anime", "best anime", "what anime"]):
                     result = anime_system.get_trending()
                     
                     if result.get("status") == "success":
                         trending_list = result.get("trending", [])[:8]
                         
                         # Format for display
                         anime_items = []
                         for anime in trending_list:
                             title = anime.get("title", "Unknown")
                             score = anime.get("score", "N/A")
                             episodes = anime.get("episodes", "?")
                             genres = ", ".join(anime.get("genres", [])[:3])
                             anime_items.append(f"• **{title}** ⭐{score} | {episodes} eps | {genres}")
                         
                         return jsonify({
                             "response": f"🔥 **Trending Anime:**\n\n" + "\n".join(anime_items),
                             "type": "anime_list",
                             "anime_list": trending_list
                         }), 200
                     else:
                         response_text = f"❌ Could not fetch trending: {result.get('error', 'Unknown error')}"
                 
                 # === SEARCH ANIME ===
                 elif any(w in q for w in ["search anime", "find anime", "anime search", "look for anime"]):
                     # Extract search query
                     search_query = command
                     for remove in ["search", "find", "anime", "for", "look"]:
                         search_query = search_query.lower().replace(remove, "").strip()
                     search_query = " ".join(search_query.split())
                     
                     if not search_query:
                         search_query = "naruto"  # Default
                     
                     result = anime_system.search_anime(search_query)
                     
                     if result.get("status") == "success":
                         results_list = result.get("results", [])[:6]
                         
                         anime_items = []
                         for anime in results_list:
                             title = anime.get("title", "Unknown")
                             anime_id = anime.get("id", "")
                             anime_items.append(f"• **{title}** (ID: {anime_id})")
                         
                         return jsonify({
                             "response": f"🔍 **Search Results for '{search_query}':**\n\n" + "\n".join(anime_items) + "\n\nSay 'Watch [anime name]' to start streaming!",
                             "type": "anime_search",
                             "search_results": results_list,
                             "search_query": search_query
                         }), 200
                     else:
                         response_text = f"❌ Search failed: {result.get('error', 'Unknown error')}"
                 
                 # === ANIME INFO ===
                 elif any(w in q for w in ["anime info", "info about", "details about", "about anime"]):
                     # Extract anime name
                     anime_name = command
                     for remove in ["anime", "info", "about", "details", "tell me"]:
                         anime_name = anime_name.lower().replace(remove, "").strip()
                     anime_name = " ".join(anime_name.split())
                     
                     if anime_name:
                         result = anime_system.get_anime_info(anime_name)
                         
                         if result.get("status") == "success":
                             info = result.get("info", {})
                             title = info.get("title", anime_name)
                             synopsis = info.get("synopsis", "No synopsis available")[:400]
                             score = info.get("score", "N/A")
                             episodes = info.get("episodes", "?")
                             status = info.get("status", "Unknown")
                             genres = ", ".join(info.get("genres", [])[:4])
                             image = info.get("image", "")
                             
                             response_md = f"""🎬 **{title}**
⭐ Score: {score} | 📺 {episodes} episodes | 📡 {status}
🏷️ Genres: {genres}

📝 **Synopsis:**
{synopsis}...

Say 'Watch {title}' to start streaming!"""
                             
                             return jsonify({
                                 "response": response_md,
                                 "type": "anime_info",
                                 "anime_info": info,
                                 "image_url": image
                             }), 200
                         else:
                             response_text = f"❌ Could not find info: {result.get('error', 'Unknown')}"
                     else:
                         response_text = "Please specify an anime name. Example: 'Anime info Demon Slayer'"
                 
                 # === WATCH ANIME (Default - Most common action) ===
                 else:
                     # Extract anime name and episode
                     anime_name = command if command else query
                     episode = 1
                     
                     # Remove trigger words
                     for remove in ["watch", "play", "stream", "anime", "video", "show", "episode"]:
                         anime_name = anime_name.lower().replace(remove, "").strip()
                     
                     # Extract episode number if present
                     ep_match = re.search(r'(?:ep|episode|eps?)\s*(\d+)', query.lower())
                     if ep_match:
                         episode = int(ep_match.group(1))
                         # Remove episode part from name
                         anime_name = re.sub(r'(?:ep|episode|eps?)\s*\d+', '', anime_name).strip()
                     
                     # Also check for just a number at the end
                     trailing_num = re.search(r'\s+(\d+)\s*$', anime_name)
                     if trailing_num and not ep_match:
                         episode = int(trailing_num.group(1))
                         anime_name = anime_name[:trailing_num.start()].strip()
                     
                     anime_name = " ".join(anime_name.split())  # Clean up spaces
                     
                     if not anime_name:
                         anime_name = "demon slayer"  # Default
                     
                     print(f"[ANIME] Watching: {anime_name}, Episode: {episode}")
                     
                     result = anime_system.watch_anime(anime_name, episode)
                     
                     if result.get("status") == "success":
                         stream_data = result.get("stream", {})
                         anime_title = result.get("anime_title", anime_name)
                         episode_title = result.get("episode_title", f"Episode {episode}")
                         streaming_url = stream_data.get("url", "")
                         quality = stream_data.get("quality", "default")
                         thumbnail = result.get("thumbnail", "")
                         total_episodes = result.get("total_episodes", "?")
                         
                         return jsonify({
                             "response": f"🎬 **Now Streaming:** {anime_title}\n📺 {episode_title}\n⚙️ Quality: {quality}",
                             "type": "anime",
                             "anime": {
                                 "title": anime_title,
                                 "episode": episode,
                                 "episode_title": episode_title,
                                 "streaming_url": streaming_url,
                                 "quality": quality,
                                 "thumbnail": thumbnail,
                                 "total_episodes": total_episodes,
                                 "sources": stream_data.get("sources", [])
                             }
                         }), 200
                     else:
                         error_msg = result.get("error", "Could not find streaming source")
                         
                         # Provide helpful suggestions
                         response_text = f"""❌ **Could not stream '{anime_name}'**

{error_msg}

💡 **Try these instead:**
• "Watch [anime name]" - Stream anime
• "Trending anime" - Popular shows
• "Search anime [name]" - Find anime
• "Anime info [name]" - Get details"""
             
             except ImportError as ie:
                 print(f"[ERROR] AnimeStreaming import failed: {ie}")
                 response_text = "❌ Anime streaming module not available. Please check installation."
             except Exception as e:
                 print(f"[ERROR] Anime streaming error: {e}")
                 import traceback
                 traceback.print_exc()
                 response_text = f"Anime streaming error: {str(e)}"

        # 6a. APP COMMANDS via LOCAL AGENT (routes to user's PC)
        elif trigger_type == "app":
             print(f"[SMART-TRIGGER] App command routed to Local Agent: {command}")
             query_lower = query.lower()
             is_close = "close" in query_lower or "quit" in query_lower or "exit" in query_lower
             
             # Use AI Intent Detector to get canonical app name
             app_name = command.strip()
             try:
                 from Backend.LocalAgentIntentDetector import fuzzy_match_app
                 matched = fuzzy_match_app(app_name)
                 if matched:
                     app_name = matched
             except:
                 pass
             
             if not app_name:
                 response_text = "Please specify an app name."
             elif is_close:
                 response_text = f"❌ Close commands aren't supported yet for {app_name}."
             else:
                 # Route through Local Agent
                 try:
                     from Backend.LocalAgentAPI import _registered_devices, _pending_tasks, _task_results, get_first_online_device, log_command
                     import uuid
                     import time as time_module
                     
                     # SECURITY: Get user's devices only
                     current_user_id = user_id if user_id != 'anonymous' else None
                     device_id, device_info = get_first_online_device(current_user_id)
                     
                     # ALSO CHECK WEBSOCKET CONNECTED DEVICES (prefer these)
                     try:
                         from Backend.AgentWebSocket import get_connected_agents, send_task_sync
                         connected_devices = get_connected_agents()
                         if connected_devices:
                             # Use the first connected device (real-time)
                             device_id = list(connected_devices.keys())[0]
                             device_info = _registered_devices.get(device_id, {'name': 'Connected Device', 'last_seen': datetime.now().isoformat()})
                             print(f"[APP->AGENT] Using WebSocket-connected device: {device_id[:8]}...")
                     except Exception as ws_check_err:
                         print(f"[APP->AGENT] WebSocket check error: {ws_check_err}")
                     
                     if not device_id:
                         response_text = "🔌 No PC is connected to your account. Pair a device first."
                     else:
                         # Check if online via WebSocket OR polling (heartbeat)
                         from datetime import datetime
                         last_seen = datetime.fromisoformat(device_info.get('last_seen', '2000-01-01'))
                         is_online = (datetime.now() - last_seen).total_seconds() < 60
                         
                         # Also check WebSocket connection
                         try:
                             from Backend.AgentWebSocket import is_agent_connected
                             ws_connected = is_agent_connected(device_id)
                             is_online = is_online or ws_connected
                         except:
                             ws_connected = False
                         
                         if not is_online:
                             response_text = f"🔴 Your PC '{device_info.get('name')}' is offline. Start the Local Agent to connect."
                         else:
                             # Queue open_app task
                             task_id = str(uuid.uuid4())
                             task = {"task_id": task_id, "command": "open_app", "params": {"app": app_name}, "user_id": current_user_id or "anonymous", "created_at": datetime.now().isoformat()}
                             
                             # TRY WEBSOCKET PUSH FIRST (instant delivery)
                             ws_sent = False
                             try:
                                 from Backend.AgentWebSocket import is_agent_connected, send_task_sync
                                 if is_agent_connected(device_id):
                                     ws_sent = send_task_sync(device_id, task_id, "open_app", {"app": app_name})
                                     if ws_sent:
                                         print(f"[APP->AGENT] ⚡ Task sent via WebSocket: open_app({app_name})")
                             except Exception as ws_err:
                                 print(f"[APP->AGENT] WebSocket send error: {ws_err}")
                             
                             # FALLBACK to polling queue if WS failed
                             if not ws_sent:
                                 if device_id not in _pending_tasks:
                                     _pending_tasks[device_id] = []
                                 _pending_tasks[device_id].append(task)
                                 print(f"[APP->AGENT] Task queued for polling: open_app({app_name})")
                             
                             # Audit log
                             log_command(current_user_id or "anonymous", device_id, "open_app", {"app": app_name}, "sent_ws" if ws_sent else "queued")
                             
                             print(f"[APP->AGENT] Task {'sent' if ws_sent else 'queued'}: open_app({app_name}) - {task_id[:8]}... (user: {current_user_id[:8] if current_user_id else 'anon'})")
                             
                             # Wait for result (up to 15 seconds)
                             max_wait, start_time, result_data = 15, time_module.time(), None
                             while time_module.time() - start_time < max_wait:
                                 if task_id in _task_results:
                                     result_data = _task_results[task_id]
                                     break
                                 time_module.sleep(0.5)
                             
                             if result_data and result_data.get("status") == "success":
                                 response_text = f"🚀 Opened {app_name}"
                             elif result_data and result_data.get("status") == "error":
                                 error_msg = result_data.get("result", {}).get("message", "Unknown error")
                                 response_text = f"⚠️ Failed to open {app_name}: {error_msg}"
                             else:
                                 response_text = f"⏳ Command sent to open {app_name}, but no response yet."
                 except Exception as agent_err:
                     print(f"[APP->AGENT] Error: {agent_err}")
                     import traceback
                     traceback.print_exc()
                     response_text = f"⚠️ Could not connect to Local Agent: {agent_err}"

        # 6b. GENERIC AUTOMATION (Fallback for others) - NOTE: "app" handled above via Local Agent
        elif trigger_type in ["chrome", "system", "workflow", "whatsapp", "switch"]:


             print(f"[SMART-TRIGGER] Detected {trigger_type} command: {command}")
             
             try:
                 # Handle SYSTEM commands directly using psutil (no UltimatePCControl needed)
                 if trigger_type == "system":
                     import psutil
                     # Use global 'os' module (imported at top of file)
                     cmd_lower = command.lower() if command else ""
                     
                     if "battery" in cmd_lower or "power" in cmd_lower:
                         battery = psutil.sensors_battery()
                         if battery:
                             percent = battery.percent
                             plugged = battery.power_plugged
                             mem = psutil.virtual_memory()
                             response_text = f"🔋 Battery: {percent}% [{'⚡ Plugged' if plugged else '🔌 On Battery'}] | RAM Use: {mem.percent}%"
                         else:
                             mem = psutil.virtual_memory()
                             response_text = f"🖥️ Desktop PC (no battery) | RAM Use: {mem.percent}%"
                     elif "shutdown" in cmd_lower:
                         os.system("shutdown /s /t 60")
                         response_text = "⚠️ System will shutdown in 60 seconds."
                     elif "restart" in cmd_lower:
                         os.system("shutdown /r /t 60")
                         response_text = "🔄 System will restart in 60 seconds."
                     elif "sleep" in cmd_lower:
                         os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                         response_text = "😴 System Sleeping."
                     elif "optimize" in cmd_lower or "cleanup" in cmd_lower:
                         response_text = "🧹 System optimization initiated. Use Windows Disk Cleanup for best results."
                     elif "stats" in cmd_lower or "health" in cmd_lower or "pc" in cmd_lower:
                         cpu_percent = psutil.cpu_percent(interval=0.1)
                         mem = psutil.virtual_memory()
                         # Get top processes
                         procs = sorted(psutil.process_iter(['name', 'cpu_percent']), key=lambda p: p.info['cpu_percent'] or 0, reverse=True)[:3]
                         top_hogs = ", ".join([p.info['name'] for p in procs if p.info['name']])
                         boot_time = psutil.boot_time()
                         import datetime
                         uptime = str(datetime.datetime.now() - datetime.datetime.fromtimestamp(boot_time)).split('.')[0]
                         response_text = f"🖥️ **System Health**\\n- CPU: {cpu_percent}% | RAM: {mem.percent}%\\n- Top Processes: {top_hogs}\\n- Uptime: {uptime}"
                     elif "screenshot" in cmd_lower:
                         try:
                             from Backend.ChromeAutomation import chrome_bot
                             # Use advanced screenshot if chrome is active
                             result = chrome_bot.screenshot()
                             if result:
                                 response_text = f"📸 Screenshot saved: {result}"
                             else:
                                 # Fallback to basic screenshot
                                 import pyautogui
                                 import datetime
                                 timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                 filename = f"screenshot_{timestamp}.png"
                                 pyautogui.screenshot(filename)
                                 response_text = f"📸 Screenshot saved: {filename}"
                         except Exception as ss_err:
                             # Ultimate fallback
                             import pyautogui
                             import datetime
                             timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") 
                             filename = f"screenshot_{timestamp}.png"
                             pyautogui.screenshot(filename)
                             response_text = f"📸 Screenshot saved: {filename}"
                     elif "grid" in cmd_lower or "arrange" in cmd_lower:
                         from Backend.WindowManager import grid_layout
                         response_text = f"🪟 {grid_layout()}"
                     elif "split" in cmd_lower:
                         from Backend.WindowManager import window_manager
                         response_text = f"🌓 {window_manager.split_screen()}"
                     elif "volume" in cmd_lower:
                         import keyboard
                         if "up" in cmd_lower: keyboard.press_and_release("volume up")
                         else: keyboard.press_and_release("volume down")
                         response_text = "🔊 Volume adjusted."
                     elif "lock" in cmd_lower:
                         import keyboard
                         keyboard.press_and_release("win+l")
                         response_text = "🔒 Screen locked"
                     else:
                         # Run through multi-tier automation
                         from Backend.Automation import System as sys_auto
                         res = sys_auto(command)
                         response_text = str(res) if res else f"✅ Executed: {command}"
                 
                 # Handle WEB SEARCH commands (renamed from chrome - now uses RealtimeSearchEngine)
                 elif trigger_type == "chrome" or trigger_type == "web_search":
                     try:
                         from Backend.RealtimeSearchEngine import RealtimeSearchEngine
                         search_query = command if command else query
                         print(f"[WEB-SEARCH] Executing realtime search: {search_query}")
                         result = RealtimeSearchEngine(search_query)
                         
                         # Handle new structured response format
                         if isinstance(result, dict):
                             response_text = result.get("text", "No results found.")
                             sources = result.get("sources", [])
                             engine = result.get("engine", "unknown")
                             print(f"[WEB-SEARCH] Engine: {engine}, Sources: {len(sources)}")
                             
                             # Return with sources for UI cards
                             return jsonify({
                                 "response": response_text,
                                 "sources": sources,
                                 "search_engine": engine,
                                 "type": "web_search"
                             }), 200
                         else:
                             # Fallback for string response
                             response_text = result if result else "No results found."
                     except Exception as se:
                         print(f"[WEB-SEARCH] Error: {se}")
                         response_text = f"Search error: {str(se)}"
                 
                 # Handle WORKFLOW commands with SmartWorkflows
                 elif trigger_type == "workflow":
                     try:
                         from Backend.SmartWorkflows import smart_workflows
                         
                         # Try to find matching workflow
                         workflow_key = smart_workflows.find_workflow(query)
                         
                         if workflow_key:
                             # Execute the workflow
                             result = asyncio.run(smart_workflows.execute_workflow(workflow_key))
                             
                             if result.get('status') == 'completed':
                                 steps_done = result.get('steps_completed', 0)
                                 total = result.get('total_steps', 0)
                                 workflow_name = result.get('workflow', workflow_key)
                                 response_text = f"✅ **{workflow_name}** activated! ({steps_done}/{total} steps completed)"
                             else:
                                 response_text = f"⚠️ Workflow error: {result.get('message', 'Unknown error')}"
                         else:
                             # List available workflows
                             wf_list = smart_workflows.list_workflows()
                             wf_names = ", ".join([wf['command'] for wf in wf_list[:5]])
                             response_text = f"🔧 Available workflows: {wf_names}. Try 'morning routine' or 'work mode'!"
                     except Exception as wf_err:
                         print(f"[ERROR] Workflow failed: {wf_err}")
                         import traceback
                         traceback.print_exc()
                         response_text = f"Workflow error: {str(wf_err)}"
                
                 # Handle CONFIRM commands (Yes/Proceed for pending actions)
                 elif trigger_type == "confirm":
                     from Backend.AutomationChain import automation_chain
                     from Backend.EmailAutomation import email_automation
                     
                     if automation_chain.has_pending():
                         success, msg = automation_chain.confirm_typing()
                         response_text = f"{'✅' if success else '❌'} {msg}"
                     elif email_automation.has_pending():
                         result = email_automation.send_pending()
                         response_text = result["message"]
                     else:
                         # No pending action, treat as general affirmation
                         response_text = "👍 Understood! What would you like me to do?"
                
                 # Handle INTERACTION commands (Write/Save)
                 elif trigger_type == "interaction":
                     from Backend.AutomationChain import automation_chain
                     
                     if any(k in query.lower() for k in ["save", "save as"]):
                         # SAVE operation
                         filename = command.strip()
                         if not filename:
                             filename = "Untitled"
                         
                         success, msg = automation_chain.save_file(filename)
                         response_text = f"{'✅' if success else '❌'} {msg}"
                         
                     else:
                         # WRITE/TYPE operation - utilize LLM for content
                         prompt = f"Write {command}" # Reconstruct prompt
                         try:
                             # Use Simple ChatBot to generate content (Function based)
                             from Backend.Chatbot import ChatBot as SimpleChatBot
                             gen_content = SimpleChatBot(prompt) 
                             
                             # Use prepare_typing for confirmation flow
                             success, msg, window = automation_chain.prepare_typing(gen_content)
                             if success:
                                 response_text = f"📝 I've drafted the content. {msg}"
                             else:
                                 response_text = f"❌ {msg}"
                         except Exception as ce:
                             response_text = f"❌ Interaction failed: {ce}"

                 # Handle EMAIL commands
                 elif trigger_type == "email":
                     from Backend.EmailAutomation import email_automation
                     from Backend.Chatbot import ChatBot as SimpleChatBot
                     
                     # Parse recipient and subject from command
                     query_lower = query.lower()
                     recipient = command.strip()
                     subject = "Message from KAI"
                     
                     # Extract "about X" if present
                     if " about " in query_lower:
                         parts = query.split(" about ", 1)
                         if len(parts) > 1:
                             subject = parts[1].strip().title()
                     
                     # Generate email body using LLM
                     prompt = f"Write a brief, professional email about: {subject}"
                     try:
                         body = SimpleChatBot(prompt)
                         
                         # Draft the email
                         result = email_automation.draft_email(recipient, subject, body)
                         response_text = result["message"]
                     except Exception as e:
                         response_text = f"❌ Email draft failed: {e}"
                
                 # Handle FORM FILL commands
                 elif trigger_type == "form_fill":
                     from Backend.UserProfile import user_profile
                     from Backend.WebsiteAutomation import website_automation
                     
                     try:
                         # Get user's auto-fill data
                         fill_data = user_profile.auto_fill_data()
                         
                         if not fill_data:
                             response_text = "❌ No profile data set. Tell me your details first!"
                         else:
                             # Try to fill form on current page
                             result = website_automation.fill_form(fill_data)
                             if result.get("success"):
                                 response_text = f"✅ Form filled with {len(fill_data)} fields!"
                             else:
                                 response_text = f"⚠️ Could not auto-fill: {result.get('message', 'Unknown error')}"
                     except Exception as e:
                         response_text = f"❌ Form fill failed: {e}"

                 # Handle ANIME commands - NEW
                 elif trigger_type == "anime":
                     try:
                         from Backend.AnimeStreaming import anime_system
                         import re
                         
                         query_lower = query.lower()
                         
                         # Watch anime
                         if "watch" in query_lower or "play" in query_lower or "stream" in query_lower:
                             # Extract anime name and episode
                             ep_match = re.search(r'episode\s*(\d+)', query_lower)
                             episode = int(ep_match.group(1)) if ep_match else 1
                             
                             # Clean anime name
                             anime_name = re.sub(r'(watch|play|stream|anime|episode\s*\d+)', '', query_lower).strip()
                             anime_name = anime_name.replace('jarvis', '').strip().strip('"\'')
                             
                             if anime_name:
                                 result = anime_system.watch_anime(anime_name, episode)
                                 if result.get("status") == "success":
                                     anime_info = result.get("anime", {})
                                     streams = result.get("streams", [])
                                     stream_url = streams[0].get("url") if streams else "No stream"
                                     response_text = f"""🎬 **{anime_info.get('title', anime_name)}** - Episode {episode}

📺 **Found {len(streams)} streaming sources!**
▶️ Quality: {streams[0].get('quality', 'HD') if streams else 'HD'}

🔗 Stream ready! Use the anime player to watch."""
                                 else:
                                     response_text = f"❌ {result.get('message', 'Anime not found')}"
                             else:
                                 response_text = "❓ What anime do you want to watch? Try: 'Watch Demon Slayer episode 5'"
                         
                         # Trending anime
                         elif "trending" in query_lower or "popular" in query_lower:
                             result = anime_system.get_trending()
                             if result.get("status") == "success":
                                 trending = result.get("trending", [])[:5]
                                 anime_list = "\n".join([f"• **{a.get('title')}** ⭐{a.get('score', 'N/A')}" for a in trending])
                                 response_text = f"🔥 **Trending Anime:**\n\n{anime_list}\n\nSay 'watch [name]' to start streaming!"
                             else:
                                 response_text = "❌ Could not fetch trending anime"
                         
                         # Search anime
                         elif "search" in query_lower or "find" in query_lower:
                             search_query = re.sub(r'(search|find|anime|jarvis)', '', query_lower).strip()
                             if search_query:
                                 result = anime_system.search_anime(search_query, 5)
                                 results = result.get("results", [])
                                 if results:
                                     anime_list = "\n".join([f"• **{a.get('title')}**" for a in results[:5]])
                                     response_text = f"🔍 **Found {len(results)} anime:**\n\n{anime_list}\n\nSay 'watch [name]' to stream!"
                                 else:
                                     response_text = f"❌ No anime found for '{search_query}'"
                             else:
                                 response_text = "❓ What anime are you looking for?"
                         
                         # Info
                         elif "info" in query_lower or "about" in query_lower:
                             info_query = re.sub(r'(info|about|anime|jarvis|details)', '', query_lower).strip()
                             if info_query:
                                 result = anime_system.get_anime_info(info_query)
                                 if result.get("status") == "success":
                                     anime = result.get("anime", {})
                                     response_text = f"""📺 **{anime.get('title')}**

⭐ Score: {anime.get('score', 'N/A')}/10
📺 Episodes: {anime.get('episodes', 'Unknown')}
🎭 Genres: {', '.join(anime.get('genres', [])[:3])}

📝 {anime.get('synopsis', 'No synopsis')[:300]}..."""
                                 else:
                                     response_text = f"❌ No info found for '{info_query}'"
                             else:
                                 response_text = "❓ Which anime do you want info about?"
                         
                         else:
                             response_text = """🎬 **Anime Commands:**
• "Watch [anime] episode [num]" - Stream anime
• "Trending anime" - See what's popular
• "Search anime [name]" - Find anime
• "Anime info [name]" - Get details"""
                     
                     except Exception as e:
                         print(f"[ANIME] Error: {e}")
                         import traceback
                         traceback.print_exc()
                         response_text = f"❌ Anime error: {e}"

                 # Handle SPOTIFY & MUSIC commands
                 elif trigger_type in ["spotify", "music"]:
                     try:
                          from Backend.SpotifyPlayer import spotify_player
                          
                          # Determine what to play
                          search_query = command
                          
                          # Execute play
                          result = spotify_player.play(search_query)
                          
                          if result.get("status") == "success":
                              return jsonify({
                                  "response": result.get("message"),
                                  "type": "spotify",
                                  "spotify": result.get("spotify")
                              }), 200
                          else:
                              response_text = result.get("message", "Could not play music")
                              
                     except Exception as me:
                         print(f"[ERROR] Music error: {me}")
                         response_text = f"Music module error: {me}"

                 # Handle AGENTS commands - NEW  
                 elif trigger_type == "agents":
                     try:
                         from Backend.Agents.AgentOrchestrator import run_multi_agent_task
                         result = run_multi_agent_task(command, "auto")
                         if result.get("status") == "success":
                             output = result.get("final_output", "")[:1000]
                             steps = ", ".join(result.get("steps_executed", []))
                             response_text = f"""🤖 **Multi-Agent Task Complete!**

📋 Steps: {steps}
⏱️ Time: {result.get('execution_time_seconds', 0)}s

{output}"""
                         else:
                             response_text = f"❌ Agent error: {result.get('message', 'Unknown')}"
                     except Exception as e:
                         response_text = f"❌ Agent system error: {e}"

                 # Handle CODE commands - NEW
                 elif trigger_type == "code":
                     try:
                         from Backend.Agents.CoderAgent import coder_agent
                         result = coder_agent.execute(command)
                         if result.get("status") == "success":
                             output = result.get("output", "")[:1500]
                             response_text = f"""💻 **Code Result:**

{output}"""
                             if result.get("execution_time"):
                                 response_text += f"\n\n⏱️ Executed in {result.get('execution_time')}s"
                         else:
                             response_text = f"❌ Code error: {result.get('error', 'Unknown')}"
                     except Exception as e:
                         response_text = f"❌ Coder error: {e}"

                 # Handle unknown trigger types - Show helpful response
                 else:
                     response_text = f"""🤔 I didn't recognize that command type: '{trigger_type}'

💡 **Try these instead:**
• "Watch [anime name]" - Stream anime
• "Trending anime" - Popular shows
• "Generate image of..." - Create images
• "Translate [text] to [language]" - Translate
• "Search [query]" - Web search
• "Write code to..." - Code generation
• "Research and write about..." - Multi-agent task

What would you like me to do?"""
                          
             except Exception as e:
                 print(f"[ERROR] Command processing error: {e}")
                 import traceback
                 traceback.print_exc()
                 response_text = f"Command processing error: {str(e)}"
        
        # 7. FILE OPERATIONS
        elif trigger_type == "file":
             print(f"[SMART-TRIGGER] File operation: {command}")
             try:
                 query_lower = query.lower()
                 
                 # Try the new AdvancedFileOps first for enhanced commands
                 try:
                     from Backend.BasicFileOps import file_ops
                     
                     # Keyboard shortcuts
                     if "select all" in query_lower:
                         result = file_ops.select_all()
                         response_text = "✅ Selected all (Ctrl+A)"
                     elif query_lower.strip() in ["copy", "ctrl c", "ctrl+c"]:
                         result = file_ops.copy()
                         response_text = "✅ Copied (Ctrl+C)"
                     elif query_lower.strip() in ["cut", "ctrl x", "ctrl+x"]:
                         result = file_ops.cut()
                         response_text = "✅ Cut (Ctrl+X)"
                     elif query_lower.strip() in ["paste", "ctrl v", "ctrl+v"]:
                         result = file_ops.paste()
                         response_text = "✅ Pasted (Ctrl+V)"
                     elif "undo" in query_lower:
                         result = file_ops.undo()
                         response_text = "✅ Undone (Ctrl+Z)"
                     elif "redo" in query_lower:
                         result = file_ops.redo()
                         response_text = "✅ Redone (Ctrl+Y)"
                     
                     # Copy file to destination
                     elif "copy" in query_lower and " to " in query_lower:
                         result = file_ops.execute_command(query)
                         response_text = f"📁 {result.get('message', 'Copy operation complete')}"
                     
                     # Move file to destination
                     elif "move" in query_lower and " to " in query_lower:
                         result = file_ops.execute_command(query)
                         response_text = f"📁 {result.get('message', 'Move operation complete')}"
                     
                     # Rename file
                     elif "rename" in query_lower and " to " in query_lower:
                         result = file_ops.execute_command(query)
                         response_text = f"📁 {result.get('message', 'Rename complete')}"
                     
                     # Open folder in explorer
                     elif "open" in query_lower and ("folder" in query_lower or "explorer" in query_lower):
                         if "explorer" in query_lower and "folder" not in query_lower:
                             result = file_ops.open_folder(".")
                         else:
                             result = file_ops.execute_command(query)
                         response_text = f"📂 {result.get('message', 'Opened folder')}"
                     
                     # Delete all / Clean up / Wipe operations
                     elif any(x in query_lower for x in ["delete all", "remove all", "clear all", "wipe", "empty", "clean up", "cleanup", "purge", "remove everything", "delete everything"]):
                         folder = None
                         for f in ["downloads", "documents", "desktop", "pictures", "videos", "music", "temp"]:
                             if f in query_lower:
                                 folder = f
                                 break
                         if folder:
                             folder_path = file_ops.FOLDER_ALIASES.get(folder, folder)
                             result = file_ops.list_files(folder_path)
                             count = result.get("file_count", 0) + result.get("folder_count", 0)
                             response_text = f"⚠️ Found {count} items in {folder.title()}. Say 'confirm delete {folder}' to delete."
                         else:
                             response_text = "⚠️ Specify folder: delete all files in downloads/documents/desktop/pictures"
                     
                     # Organize/Sort files
                     elif any(x in query_lower for x in ["organize", "sort", "arrange"]):
                         response_text = "📊 Organize files: Say 'move *.jpg to Pictures' or 'move *.pdf to Documents'"
                     
                     # Backup
                     elif "backup" in query_lower:
                         response_text = "💾 Backup: Say 'copy Documents to Backup' or 'copy folder to destination'"
                     
                     # Zip/Compress
                     elif any(x in query_lower for x in ["zip", "compress"]):
                         response_text = "🗜️ Zip: Right-click files in Explorer > Send to > Compressed folder"
                     
                     # Unzip/Extract
                     elif any(x in query_lower for x in ["unzip", "extract"]):
                         response_text = "📦 Extract: Right-click .zip file > Extract All"
                     
                     else:
                        # Default file operation message
                        response_text = "📁 File commands: copy, move, rename, create, delete, list, search, select all, cut, past, undo, redo, open folder"

                 except ImportError:
                     # Fall through to legacy FileIOAutomation
                    # Fall through to RealtimeSearchEngine for web searches
                    pass
                         
             except Exception as e:
                 print(f"[ERROR] File operation failed: {e}")
                 response_text = f"File operation error: {str(e)}"
        
        # 8. WEB SCRAPING (Enhanced with ProWebScraper)
        elif trigger_type == "scrape":
             print(f"[SMART-TRIGGER] Web scraping: {command}")
             try:
                 import re
                 # Extract URL from command
                 url_match = re.search(r'https?://[^\s]+', query)
                 
                 if url_match:
                     url = url_match.group(0)
                     
                     # Use enhanced ProWebScraper
                     try:
                         from Backend.ProWebScraper import pro_scraper
                         result = pro_scraper.scrape_smart(url)
                     except ImportError:
                         from Backend.EnhancedWebScraper import EnhancedWebScraper
                         scraper = EnhancedWebScraper()
                         result = scraper.scrape_url(url)
                     
                     if result.get("status") == "success":
                         content_type = result.get("type", "general")
                         title = result.get("title", "Unknown")
                         
                         if content_type == "product":
                             # Product info
                             price = result.get("price", "N/A")
                             rating = result.get("rating", "N/A")
                             desc = result.get("description", "")[:200]
                             response_text = f"🛒 **{title}**\n\n💰 Price: **{price}**\n⭐ Rating: {rating}\n\n{desc}"
                         
                         elif content_type == "article":
                             # Article info
                             author = result.get("author", "")
                             summary = result.get("summary", result.get("content", "")[:400])
                             words = result.get("word_count", 0)
                             response_text = f"📰 **{title}**\n\n{summary}\n\n📝 {words} words"
                             if author:
                                 response_text += f" | By {author}"
                         
                         elif content_type == "wikipedia":
                             # Wikipedia info
                             summary = result.get("summary", "")[:500]
                             infobox = result.get("infobox", {})
                             response_text = f"📚 **{title}**\n\n{summary}"
                             if infobox:
                                 info_str = " | ".join([f"{k}: {v}" for k, v in list(infobox.items())[:3]])
                                 response_text += f"\n\n📋 {info_str}"
                         
                         else:
                             # General
                             content = result.get("content", "")[:600]
                             response_text = f"🌐 **{title}**\n\n{content}"
                     else:
                         response_text = f"Scraping failed: {result.get('message', 'Unknown error')}"
                 else:
                     # No URL - maybe search?
                     if "search" in query.lower():
                         search_term = query.lower().replace("search", "").replace("scrape", "").strip()
                         try:
                             from Backend.ProWebScraper import pro_scraper
                             result = pro_scraper.search_google(search_term)
                             if result.get("status") == "success":
                                 results = result.get("results", [])[:3]
                                 res_text = "\n".join([f"• [{r['title']}]({r['url']})" for r in results])
                                 response_text = f"🔍 Search results for '{search_term}':\n\n{res_text}"
                             else:
                                 response_text = "Search failed"
                         except:
                             response_text = "Please provide a URL to scrape."
                     else:
                         response_text = "Please provide a URL to scrape. Example: 'scrape https://example.com'"
             except Exception as e:
                 print(f"[ERROR] Web scraping failed: {e}")
                 import traceback
                 traceback.print_exc()
                 response_text = f"Scraping error: {str(e)}"

        # 9. CODE GENERATION & EXECUTION
        elif trigger_type == "code":
             print(f"[SMART-TRIGGER] Code command: {command}")
             try:
                 from Backend.CodeEngine import code_engine
                 query_lower = query.lower()
                 
                 # Determine code language
                 language = "python"  # default
                 if "javascript" in query_lower or " js " in query_lower:
                     language = "javascript"
                 elif "html" in query_lower or "webpage" in query_lower:
                     language = "html"
                 
                 # Execute code
                 if any(k in query_lower for k in ["execute", "run code", "run python", "run this"]):
                     # Extract code from query or use last generated
                     if "```" in query:
                         code_blocks = query.split("```")
                         code = code_blocks[1] if len(code_blocks) > 1 else ""
                         # Remove language identifier
                         lines = code.split('\n')
                         if lines[0].strip() in ['python', 'py', 'javascript', 'js']:
                             code = '\n'.join(lines[1:])
                     else:
                         code = query.replace("execute", "").replace("run code", "").replace("run python", "").strip()
                     
                     result = code_engine.execute_python(code=code)
                     if result.get("status") == "success":
                         output = result.get("output", "No output")
                         response_text = f"✅ **Code executed successfully!**\n\n```\n{output[:500]}\n```"
                     else:
                         error = result.get("error") or result.get("message")
                         response_text = f"❌ **Execution error:**\n```\n{error[:300]}\n```"
                 
                 # Explain code
                 elif "explain" in query_lower:
                     code = query.replace("explain code", "").replace("explain", "").strip()
                     if "```" in code:
                         code_blocks = code.split("```")
                         code = code_blocks[1] if len(code_blocks) > 1 else code
                     
                     result = code_engine.explain_code(code=code)
                     if result.get("status") == "success":
                         response_text = f"📖 **Code Explanation:**\n\n{result['explanation']}"
                     else:
                         response_text = result.get("message", "Could not explain code")
                 
                 # Create project
                 elif any(k in query_lower for k in ["create project", "create flask", "new project"]):
                     if "flask" in query_lower:
                         project_type = "flask"
                     elif "html" in query_lower:
                         project_type = "html"
                     else:
                         project_type = "python"
                     
                     # Extract project name
                     name = "my_project"
                     words = query.split()
                     for i, w in enumerate(words):
                         if w in ["project", "called", "named"] and i + 1 < len(words):
                             name = words[i + 1].strip('"\' ')
                             break
                     
                     result = code_engine.create_project(project_type, name)
                     if result.get("status") == "success":
                         files = ", ".join(result.get("files", []))
                         response_text = f"✅ **Created {project_type} project: {name}**\n\n📁 Path: `{result['path']}`\n📄 Files: {files}"
                     else:
                         response_text = result.get("message")
                 
                 # Generate code (default)
                 else:
                     # Extract the actual request
                     prompt = query
                     for remove in ["generate", "write", "create", "code", "python", "javascript", "for", "a", "that"]:
                         prompt = prompt.replace(remove, " ")
                     prompt = " ".join(prompt.split()).strip()
                     
                     if len(prompt) < 5:
                         prompt = query  # Use original if too short
                     
                     result = code_engine.generate_code(prompt, language)
                     if result.get("status") == "success":
                         code_preview = result.get("code", "")[:400]
                         response_text = f"✅ **Generated {language} code!**\n\n```{language}\n{code_preview}\n```\n\n💾 Saved to: `{result.get('filename')}`"
                     else:
                         response_text = result.get("message", "Code generation failed")
                         
             except Exception as e:
                 print(f"[ERROR] Code operation failed: {e}")
                 import traceback
                 traceback.print_exc()
                 response_text = f"Code error: {str(e)}"


        # 10. VISION COMMANDS
        elif trigger_type == "vision":
             # Check if this is a PDF/document query with attachment context - use ChatBot instead
             if attachment_context and ('[PDF' in attachment_context or '[ATTACHED' in attachment_context):
                 print(f"[VISION] Redirecting to ChatBot - has attachment context, not an image path")
                 trigger_type = None  # Will fall through to ChatBot
             else:
                 try:
                     from Backend.VisionService import get_vision_service
                     vision = get_vision_service()
                     print(f"[SMART-TRIGGER] Vision command detected.")
                     # Use VisionService for vision analysis - command should be an image path
                     if hasattr(vision, 'analyze') and command and _os.path.exists(command):
                         result = vision.analyze(command, "Describe this image in detail.")
                         response_text = result.get('description', 'Vision analysis completed.')
                     else:
                         # Not a valid image path, redirect to ChatBot
                         print(f"[VISION] Not a valid image path, using ChatBot")
                         trigger_type = None
                 except Exception as ve:
                     print(f"[VISION] Error: {ve}")
                     response_text = "Vision module is not available."
                 
        # 11. DOCUMENT/PDF GENERATION

        elif trigger_type == "document":
             print(f"[SMART-TRIGGER] Document generation: {command}")
             try:
                 from Backend.DocumentGenerator import document_generator
                 from datetime import datetime
                 import re
                 
                 # ===================== SMART TOPIC & TYPE EXTRACTION =====================
                 cmd_lower = command.lower()
                 
                 # Detect document type from command
                 # Priority: expo/submission > pitch > technical/guide > report (default)
                 document_type = "professional_report"  # Default
                 
                 if any(kw in cmd_lower for kw in ["expo", "submission", "conference", "hackathon"]):
                     document_type = "expo_submission"
                 elif any(kw in cmd_lower for kw in ["pitch", "investor", "funding", "startup"]):
                     document_type = "pitch_document"
                 elif any(kw in cmd_lower for kw in ["technical", "guide", "whitepaper", "documentation", "tutorial"]):
                     document_type = "technical_guide"
                 
                 print(f"[PDF] Detected document type: {document_type}")
                 
                 # Smart topic extraction using regex
                 # Pattern: "create/generate [a] [pdf/document/report/etc] [about/on/for] <TOPIC>"
                 topic_patterns = [
                     r"(?:create|generate|make|write)\s+(?:a\s+)?(?:pdf|document|report|submission|pitch|guide)\s+(?:about|on|for|regarding)\s+(.+?)$",
                     r"(?:pdf|document|report|submission)\s+(?:about|on|for|regarding)\s+(.+?)$",
                     r"(?:about|on|for|regarding)\s+(.+?)$",
                     r"expo\s+submission\s+(?:for|about)?\s*(.+?)$",
                     r"pitch\s+(?:document|deck)\s+(?:for|about)?\s*(.+?)$",
                 ]
                 
                 topic = None
                 for pattern in topic_patterns:
                     match = re.search(pattern, cmd_lower, re.IGNORECASE)
                     if match:
                         topic = match.group(1).strip()
                         # Clean up common trailing words
                         topic = re.sub(r'\s+(?:please|now|thanks|asap)$', '', topic, flags=re.IGNORECASE)
                         break
                 
                 # Fallback: Remove known keywords and use remainder
                 if not topic:
                     topic = re.sub(r'\b(create|generate|make|write|a|an|the|pdf|document|report|guide|about|on|for|submission|expo|pitch|technical)\b', '', cmd_lower, flags=re.IGNORECASE)
                     topic = re.sub(r'\s+', ' ', topic).strip()
                 
                 if not topic or len(topic) < 3:
                     topic = "General Overview"
                 
                 print(f"[PDF] Extracted topic: '{topic}'")
                 print(f"[PDF] ========== STARTING {document_type.upper()} GENERATION =========")
                 
                 # ===================== NEW TEMPLATE SYSTEM (FAST PATH) =====================
                 # Use the new template-based system directly - skip old web research + Gemini
                 # The content_generator will use LLM to generate structured content
                 
                 pdf_result = document_generator.generate(
                     topic=topic.title(),
                     document_type=document_type,
                     # Don't pass content - let the generator create it from topic
                     additional_context=f"Create a professional {document_type.replace('_', ' ')} about {topic}."
                 )
                 
                 if pdf_result.get("success"):
                     pdf_filename = pdf_result.get("filename", "document.pdf")
                     pdf_url = pdf_result.get("url", f"/data/Documents/{pdf_filename}")
                     pdf_title = pdf_result.get("title", f"Report on {topic.title()}")
                     
                     print(f"[PDF] ✅ Generated: {pdf_title} ({pdf_result.get('format', 'unknown')})")
                     
                     return jsonify({
                         "response": f"📄 Generated PDF: **{pdf_title}**",
                         "type": "pdf",
                         "title": pdf_title,
                         "url": pdf_url,
                         "format": pdf_result.get("format", "pdf")
                     }), 200
                 else:
                     # Fallback to expanded content generation if new system failed
                     print(f"[PDF] ⚠️ New system failed: {pdf_result.get('error')}, using legacy...")
                     ai_content = ""
                     web_research = ""
                 
                 # ===================== LEGACY FALLBACK (only if new system fails) =====================
                 # Step 1: Web scraping for research content
                 print(f"[PDF] Step 1: Web research for '{topic}'")
                 try:
                     from Backend.RealtimeSearchEngine import RealtimeSearchEngine
                     print(f"[PDF] 🔍 Researching '{topic}' from the web...")
                     search_results = RealtimeSearchEngine(f"comprehensive guide about {topic}")
                     if search_results and isinstance(search_results, str) and len(search_results) > 100:
                         web_research = search_results
                         print(f"[PDF] ✅ Got {len(web_research)} chars from web research")
                     else:
                         print(f"[PDF] ⚠️ Limited search results")
                 except Exception as search_err:
                     print(f"[PDF] ⚠️ Web research failed: {search_err}")
                 
                 # Step 2: Use Gemini directly (NOT ChatBot)
                 print(f"[PDF] Step 2: Gemini content generation")
                 try:
                     import google.generativeai as genai
                     import os
                     
                     # Get Gemini API key  
                     gemini_keys = [
                         os.getenv("GEMINI_API_KEY"),
                         os.getenv("GOOGLE_API_KEY"),
                         os.getenv("GEMINI_API_KEY_1"),
                     ]
                     gemini_key = next((k for k in gemini_keys if k and len(k) > 10), None)
                     print(f"[PDF] Gemini key found: {'YES' if gemini_key else 'NO'}")
                     
                     if gemini_key:
                         genai.configure(api_key=gemini_key)
                         # Use models/gemini-pro - widely available
                         model = genai.GenerativeModel('models/gemini-pro')
                         
                         research_context = f"\n\nUse this research:\n{web_research[:2000]}" if web_research else ""
                         
                         ai_prompt = f"""Create a comprehensive 2500+ word report about "{topic}".{research_context}

Write detailed sections with these exact headers on separate lines:

Introduction
[3 detailed paragraphs about what {topic} is and why it matters]

Background and History
[3 paragraphs about the origins and evolution of {topic}]

Key Concepts
[Explain 8 core concepts about {topic}, each as a bullet point with explanation]

Applications and Use Cases  
[3 paragraphs with specific real-world examples]

Benefits and Advantages
[List 8 benefits, each starting with a bullet point]

Challenges and Considerations
[List 6 challenges as bullet points with explanations]

Future Trends
[3 paragraphs about where {topic} is heading]

Best Practices
[List 6 actionable recommendations as bullet points]

Conclusion
[2 paragraphs summarizing key points]

RULES: Write AT LEAST 2500 words. Be detailed and informative. Use plain text only."""

                         response = model.generate_content(ai_prompt)
                         ai_content = response.text
                         print(f"[PDF] ✅ Gemini generated {len(ai_content)} characters")
                         
                 except Exception as gemini_err:
                     print(f"[PDF] ⚠️ Gemini content generation failed: {gemini_err}")
                 
                 # Step 3: Comprehensive LOCAL FALLBACK when all APIs fail
                 if not ai_content or len(ai_content) < 500:
                     print("[PDF] 📝 Using comprehensive local content generation...")
                     
                     # Create topic-specific title for sections
                     topic_title = topic.title()
                     
                     # Generate substantial content locally with TOPIC-SPECIFIC headings
                     ai_content = f"""===TITLE===
The Complete Guide to {topic_title}

===SUBTITLE===
Everything You Need to Know About {topic_title}

===EXECUTIVE_SUMMARY===
This comprehensive document provides a thorough exploration of {topic_title}, covering its fundamental concepts, practical applications, benefits, challenges, and future outlook. Whether you are new to {topic} or seeking to deepen your understanding, this guide offers valuable insights and actionable information that you can apply immediately.

===SECTION: Introduction to {topic_title}===
{topic_title} represents one of the most significant and fascinating subjects in its field. Understanding {topic} is essential for anyone looking to stay current with developments in this area. This subject has evolved considerably over time and continues to shape how we think about related concepts and applications.

The importance of {topic} cannot be overstated. It touches virtually every aspect of modern life, from personal applications to professional implementations. As we explore this topic in depth, we will uncover the core principles that make it so impactful and relevant.

In this comprehensive guide, we will examine {topic} from multiple perspectives, providing you with a well-rounded understanding that you can apply in various contexts. We will cover the historical background, key concepts, practical applications, benefits, challenges, and future trends associated with {topic_title}.

===SECTION: The History and Evolution of {topic_title}===
The history of {topic} is rich and multifaceted, spanning decades of development and innovation. The origins can be traced back to early pioneering work that laid the foundation for what we see today. Over time, dedicated researchers, practitioners, and enthusiasts have contributed to its evolution.

In the early stages, {topic} was primarily understood through theoretical frameworks. As technology advanced and more practical applications emerged, the field began to mature and gain mainstream recognition. This transformation was marked by significant milestones that changed how people perceived and utilized {topic}.

Today, {topic} has become an integral part of numerous industries and daily activities. The journey from its inception to its current state reflects the remarkable progress made through continuous innovation, collaboration, and a commitment to advancing knowledge about {topic_title}.

===SECTION: Understanding {topic_title} - Core Concepts===
Understanding {topic} requires familiarity with several core concepts that form its foundation:

• Fundamental Principles of {topic_title}: The basic rules and theories that govern how {topic} works and why it behaves in certain ways. These principles provide the framework for deeper understanding.

• Essential Components of {topic_title}: The key elements that make up {topic}, including the structural and functional aspects that define its characteristics and capabilities.

• {topic_title} Terminology: The specialized vocabulary used when discussing {topic}, which helps ensure clear communication among practitioners and researchers.

• {topic_title} Methodologies: The various methods and strategies employed when working with {topic}, each suited to different contexts and objectives.

• Tools for Working with {topic_title}: The instruments, software, and technological solutions that enable effective engagement with {topic} in practical settings.

• {topic_title} Standards: The established guidelines and proven approaches that ensure quality and consistency when implementing {topic}-related initiatives.

• Measuring {topic_title} Success: The metrics and criteria used to assess performance, progress, and outcomes related to {topic}.

• Integrating {topic_title}: How {topic} connects with and complements other related areas, creating synergies and enhanced capabilities.

===SECTION: Real-World Applications of {topic_title}===
The practical applications of {topic} span numerous domains and industries, demonstrating its versatility and value:

In the technology sector, {topic} plays a crucial role in driving innovation and solving complex problems. Companies leverage {topic_title} to improve their products, streamline operations, and create better experiences for their customers and users.

The business world has embraced {topic} as a means of gaining competitive advantage. Organizations use {topic_title} to make informed decisions, optimize processes, and identify new opportunities for growth and development.

In everyday life, {topic} impacts how individuals work, learn, and interact. From personal productivity to entertainment, the influence of {topic_title} is evident in countless daily activities and experiences.

===SECTION: Benefits of {topic_title}===
Engaging with {topic} offers numerous benefits that make it worthwhile:

• Enhanced Efficiency with {topic_title}: Working with {topic} often leads to significant improvements in how quickly and effectively tasks can be completed.

• Better Decision Making through {topic_title}: Understanding {topic} provides valuable insights that support more informed and effective choices.

• Cost Savings from {topic_title}: Proper implementation of {topic} can result in reduced expenses and more efficient resource utilization.

• Improved Quality via {topic_title}: Applying {topic} principles often leads to higher-quality outcomes and better results overall.

• Competitive Advantage through {topic_title}: Organizations that master {topic} frequently outperform those that do not in relevant metrics.

• Innovation through {topic_title}: {topic} opens doors to new possibilities and creative solutions that might not otherwise be apparent.

• Personal Growth with {topic_title}: Individuals who study {topic} often experience significant professional and personal development.

• Future Readiness via {topic_title}: Familiarity with {topic} helps prepare for upcoming changes and developments in the field.

===SECTION: Challenges When Working with {topic_title}===
While {topic} offers many benefits, there are also challenges to consider:

• Learning {topic_title}: Mastering {topic} requires time and effort, and the initial learning phase can be demanding for newcomers.

• Resources for {topic_title}: Effective implementation of {topic} may require significant investment in tools, training, or infrastructure.

• {topic_title} Complexity: The intricate nature of {topic} can make it difficult to fully understand or implement without proper guidance.

• Keeping Up with {topic_title}: The fast pace of change in {topic} means that continuous learning is necessary to stay current.

• Integrating {topic_title}: Incorporating {topic} into existing systems or workflows may present technical or organizational difficulties.

• Quality Control with {topic_title}: Ensuring consistent quality when working with {topic} requires careful attention and proper processes.

===SECTION: The Future of {topic_title}===
The future of {topic} looks promising, with several exciting developments on the horizon:

Emerging technologies and methodologies are expected to enhance how we work with {topic}, making {topic_title} more accessible and powerful than ever before. These advancements will likely open new applications and use cases that we cannot yet fully anticipate.

The growing recognition of {topic}'s importance suggests that investment and interest in {topic_title} will continue to increase. This will drive further research, development, and innovation, benefiting practitioners and end-users alike.

As {topic} becomes more mainstream, we can expect to see greater integration of {topic_title} with other fields and disciplines. This convergence will create new opportunities for collaboration and cross-pollination of ideas.

===SECTION: Best Practices for {topic_title}===
To make the most of {topic}, consider the following recommendations:

• Start with {topic_title} Basics: Build a strong foundation by understanding the fundamental concepts before moving to advanced topics.

• Practice {topic_title} Regularly: Consistent practice helps reinforce learning and develop practical skills that are essential for success.

• Stay Current with {topic_title}: Keep up with the latest developments and trends to ensure your knowledge remains relevant and useful.

• Seek {topic_title} Guidance: Learn from experienced practitioners and experts who can provide valuable insights and mentorship.

• Apply Your {topic_title} Knowledge: Put your knowledge into practice through real-world projects and applications.

• Collaborate on {topic_title}: Work with peers and colleagues to share knowledge, exchange ideas, and learn from different perspectives.

===CONCLUSION===
{topic_title} represents a significant and valuable area of study that offers numerous benefits for those who take the time to understand it. From its historical roots to its future potential, {topic} continues to evolve and shape the world around us.

By developing a solid understanding of {topic} and staying current with developments in {topic_title}, you position yourself to take advantage of the opportunities it presents. Whether your interest is personal, professional, or academic, engaging with {topic_title} is a worthwhile investment that can yield substantial returns over time.
"""
                     print(f"[PDF] ✅ Generated {len(ai_content)} chars of local content")
                 
                 # Parse AI content with smart structured parser
                 date_str = datetime.now().strftime("%B %d, %Y")
                 content = []
                 doc_title = f"Report on {topic.title()}"
                 doc_subtitle = "Generated by KAI AI"
                 
                 if ai_content and len(ai_content) > 200:
                     # Parse structured format with ===SECTION=== markers
                     import re
                     
                     # Extract title and subtitle
                     title_match = re.search(r'===TITLE===\s*\n(.+?)(?=\n===|\Z)', ai_content, re.DOTALL)
                     if title_match:
                         doc_title = title_match.group(1).strip()
                     
                     subtitle_match = re.search(r'===SUBTITLE===\s*\n(.+?)(?=\n===|\Z)', ai_content, re.DOTALL)
                     if subtitle_match:
                         doc_subtitle = subtitle_match.group(1).strip()
                     
                     # Find all sections
                     section_pattern = r'===(?:SECTION:\s*)?([^=]+)===\s*\n(.*?)(?=\n===|\Z)'
                     sections_found = re.findall(section_pattern, ai_content, re.DOTALL)
                     
                     for section_name, section_content in sections_found:
                         section_name = section_name.strip()
                         section_content = section_content.strip()
                         
                         if not section_content or section_name in ['TITLE', 'SUBTITLE']:
                             continue
                         
                         # Add section heading
                         content.append({"type": "heading", "text": section_name.replace('_', ' ').title()})
                         
                         # Parse content - detect bullets and paragraphs
                         lines = section_content.split('\n')
                         current_para = []
                         
                         for line in lines:
                             line = line.strip()
                             if not line:
                                 if current_para:
                                     content.append({"type": "paragraph", "text": ' '.join(current_para)})
                                     current_para = []
                                 continue
                             
                             # Detect bullet points
                             if line.startswith(('• ', '- ', '* ', '· ')):
                                 if current_para:
                                     content.append({"type": "paragraph", "text": ' '.join(current_para)})
                                     current_para = []
                                 content.append({"type": "bullet", "text": line.lstrip('•-*· ').strip()})
                             elif re.match(r'^\d+[\.\)]\s', line):
                                 if current_para:
                                     content.append({"type": "paragraph", "text": ' '.join(current_para)})
                                     current_para = []
                                 content.append({"type": "bullet", "text": re.sub(r'^\d+[\.\)]\s*', '', line)})
                             else:
                                 current_para.append(line)
                         
                         if current_para:
                             content.append({"type": "paragraph", "text": ' '.join(current_para)})
                         
                         content.append({"type": "spacer"})
                     
                     print(f"[PDF] Parsed {len(sections_found)} sections from AI content")
                 
                 # Fallback if no structured content
                 if not content:
                     content = [
                         {"type": "heading", "text": "Introduction"},
                         {"type": "paragraph", "text": f"This comprehensive document explores {topic} in detail, covering key concepts, practical applications, and important insights."},
                         {"type": "spacer"},
                         {"type": "heading", "text": f"Understanding {topic.title()}"},
                         {"type": "paragraph", "text": f"{topic.title()} is a significant topic with wide-ranging implications. Understanding it requires examining core principles, historical context, and modern applications."},
                         {"type": "spacer"},
                         {"type": "heading", "text": "Key Concepts"},
                         {"type": "bullet", "text": f"Fundamental principles of {topic}"},
                         {"type": "bullet", "text": "Historical development and evolution"},
                         {"type": "bullet", "text": "Current trends and modern interpretations"},
                         {"type": "bullet", "text": "Practical applications across industries"},
                         {"type": "bullet", "text": "Future prospects and emerging developments"},
                         {"type": "spacer"},
                         {"type": "heading", "text": "Applications"},
                         {"type": "paragraph", "text": f"The applications of {topic} span multiple industries. From everyday use cases to specialized implementations, understanding these applications provides valuable context."},
                         {"type": "spacer"},
                         {"type": "heading", "text": "Conclusion"},
                         {"type": "paragraph", "text": f"In summary, {topic} represents an important area with significant implications. The key concepts covered here provide a comprehensive foundation for further exploration."},
                     ]
                 
                 # Convert content list to expected format for generate_pdf
                 sections = []
                 current_section = {"heading": "", "content": "", "type": "paragraph", "data": []}
                 
                 for item in content:
                     item_type = item.get("type", "paragraph")
                     item_text = item.get("text", "")
                     
                     if item_type == "heading":
                         # Save current section if it has content
                         if current_section["content"] or current_section["data"]:
                             sections.append(current_section)
                         # Start new section
                         current_section = {"heading": item_text, "content": "", "type": "paragraph", "data": []}
                     elif item_type == "paragraph":
                         if current_section["content"]:
                             current_section["content"] += "\n\n" + item_text
                         else:
                             current_section["content"] = item_text
                     elif item_type == "bullet":
                         current_section["type"] = "bullet"
                         current_section["data"].append(item_text)
                     # spacer is ignored
                 
                 # Add final section
                 if current_section["content"] or current_section["data"]:
                     sections.append(current_section)
                 
                 # Build the proper content dict with AI-generated title/subtitle
                 pdf_content = {
                     "title": doc_title,
                     "subtitle": doc_subtitle,
                     "sections": sections,
                     "document_type": "professional_report"
                 }
                 
                 # Use new template-based generation system
                 pdf_result = document_generator.generate(
                     topic=topic.title(), 
                     document_type="professional_report",
                     content=pdf_content
                 )
                 
                 # generate() returns: success, filepath, url, format, title
                 pdf_filename = pdf_result.get("filename", "document.pdf")
                 pdf_url = pdf_result.get("url", f"/data/Documents/{pdf_filename}")
                 pdf_title = pdf_result.get("title", f"Report on {topic.title()}")
                 
                 # Return structured response for PDF preview card
                 return jsonify({
                     "response": f"📄 Generated PDF: **{pdf_title}**",
                     "type": "pdf",
                     "title": pdf_title,
                     "url": pdf_url,
                     "format": pdf_result.get("format", "pdf")
                 }), 200
             except Exception as e:
                 print(f"[ERROR] Document generation failed: {e}")
                 import traceback
                 traceback.print_exc()
                 response_text = f"Document generation failed: {str(e)}"


        # 4. REMINDERS (TaskScheduler)
        elif trigger_type == "reminder":
             print(f"[SMART-TRIGGER] Reminder command: {command}")
             try:
                 from Backend.TaskScheduler import task_scheduler
                 
                 # Start scheduler if not running
                 if not task_scheduler.is_running:
                     task_scheduler.start()
                 
                 # Parse natural language reminder
                 result = task_scheduler.parse_natural_language(query)
                 
                 if result.get("status") == "success":
                     response_text = result.get("message")
                 else:
                     response_text = result.get("message", "Failed to set reminder")
             except Exception as e:
                 print(f"[ERROR] Reminder failed: {e}")
                 response_text = f"Reminder error: {str(e)}"
        
        # 4b. ACTION CHAINS (Form filling, typing, etc.)
        elif trigger_type == "action":
             print(f"[SMART-TRIGGER] Action chain: {command}")
             try:
                 from Backend.ActionChain import action_chain
                 
                 result = action_chain.parse_and_execute(query)
                 
                 if result.get("status") == "success":
                     response_text = result.get("message")
                 else:
                     response_text = result.get("message", "Action failed")
             except Exception as e:
                 print(f"[ERROR] Action chain failed: {e}")
                 response_text = f"Action error: {str(e)}"
              
        # 4c. GESTURE CONTROL (Vision Engine)
        elif trigger_type == "gesture":
             print(f"[SMART-TRIGGER] Gesture command: {command}")
             try:
                 from Backend.JarvisGesture import gesture_control
                 query_lower = query.lower()
                 
                 if any(x in query_lower for x in ["stop", "disable", "turn off", "quit", "exit"]):
                     gesture_control.stop()
                     response_text = "👁️ Gesture Control Engine stopped."
                 else:
                     # Run in background to not block the server
                     import threading
                     threading.Thread(target=gesture_control.start, daemon=True).start()
                     response_text = "👁️ Vision Engine Activated! You can now use your nose to move the cursor and wink/smile for clicks."
             except Exception as e:
                 print(f"[ERROR] Gesture engine failed: {e}")
                 response_text = f"Gesture error: {str(e)}"

        # 5. GENERAL / CONVERSATIONAL (Fallback to ChatBot)
        if not response_text:
             # FIRST: Try AI Intent Detection for PC control that SmartTrigger may have missed
             try:
                 from Backend.LocalAgentIntentDetector import detect_intent
                 ai_intent = detect_intent(query, use_ai=False)  # Quick pattern match only (fast)
                 
                 if ai_intent.get("intent") == "system_status" and ai_intent.get("confidence", 0) >= 0.7:
                     print(f"[AI-FALLBACK] Detected system_status intent, routing to Local Agent")
                     # Route to device_status handler  
                     from Backend.LocalAgentAPI import _registered_devices, _pending_tasks, _task_results, get_first_online_device, log_command
                     import uuid
                     import time as time_module
                     
                     # SECURITY: Get user's devices only
                     current_user_id = user_id if user_id != 'anonymous' else None
                     device_id, device_info = get_first_online_device(current_user_id)
                     
                     if device_id:
                         from datetime import datetime
                         last_seen = datetime.fromisoformat(device_info.get('last_seen', '2000-01-01'))
                         is_online = (datetime.now() - last_seen).total_seconds() < 60
                         
                         if is_online:
                             task_id = str(uuid.uuid4())
                             task = {"task_id": task_id, "command": "system_status", "params": {}, "user_id": current_user_id or "anonymous", "created_at": datetime.now().isoformat()}
                             if device_id not in _pending_tasks:
                                 _pending_tasks[device_id] = []
                             _pending_tasks[device_id].append(task)
                             
                             # Audit log
                             log_command(current_user_id or "anonymous", device_id, "system_status", {}, "queued")
                             
                             max_wait, start_time, result_data = 10, time_module.time(), None
                             while time_module.time() - start_time < max_wait:
                                 if task_id in _task_results:
                                     result_data = _task_results[task_id]
                                     break
                                 time_module.sleep(0.5)
                             
                             if result_data and result_data.get("status") == "success":
                                 data = result_data.get("result", {}).get("data", {})
                                 cpu, memory, uptime, system = data.get("cpu", {}), data.get("memory", {}), data.get("uptime", {}), data.get("system", {})
                                 response_text = f"🖥️ **{device_info.get('name', 'Your PC')}** is online!\n\n📊 **System Status:**\n• CPU: {cpu.get('percent', 'N/A')}% ({cpu.get('cores_logical', 'N/A')} cores)\n• RAM: {memory.get('percent', 'N/A')}% ({memory.get('used_gb', 'N/A')}GB / {memory.get('total_gb', 'N/A')}GB)\n• Uptime: {uptime.get('formatted', 'N/A')}\n• OS: {system.get('os', 'N/A')} {system.get('os_release', '')}"
                             else:
                                 response_text = f"🟡 Your PC is connected but didn't respond. Try 'system status' in a moment."
                         else:
                             response_text = f"🔴 Your PC '{device_info.get('name')}' is offline."
                     else:
                         response_text = "🔌 No PC is connected to your account. Pair a device first."
             except Exception as ai_err:
                 print(f"[AI-FALLBACK] Error: {ai_err}")
             
             # If no response from AI Intent fallback, use ChatBot
             if not response_text:
                 print(f"[SMART-TRIGGER] No specific automation triggers. Using ChatBot for conversation.")
                 
                 # Prepend user context and memory context if available
                 combined_context = (memory_context or "") + (user_context or "")
                 personalized_query = combined_context + query if combined_context else query
             
                 if ChatBot:
                     print("[DEBUG] Using ChatBot for general query")
                     cb_response = ChatBot(personalized_query)
                     
                     # Handle dictionary response from Enhanced Chatbot
                     if isinstance(cb_response, dict):
                         response_text = cb_response.get("response", "")
                         chat_metadata = cb_response.get("metadata", {})
                     else:
                         response_text = str(cb_response)
                 else:
                     # Lazy load ChatBot
                     print("[DEBUG] Loading ChatBot module")
                     from Backend.Chatbot_Enhanced import ChatBot as CB
                     cb_response = CB(personalized_query)
                     if isinstance(cb_response, dict):
                         response_text = cb_response.get("response", "")
                         chat_metadata = cb_response.get("metadata", {})
                     else:
                         response_text = str(cb_response)
             
             if response_text:
                 print(f"[DEBUG] ChatBot Response: {response_text[:100] if response_text else 'None'}...")
        else:
            # === SAVE COMMAND RESPONSES TO CHAT HISTORY ===
            # This enables continuous conversation flow
            try:
                import os
                from json import load as json_load, dump as json_dump
                chatlog_path = os.path.join(os.path.dirname(__file__), "Data", "ChatLog.json")

                
                # Load existing history
                try:
                    with open(chatlog_path, 'r') as f:
                        chat_history = json_load(f)
                except:
                    chat_history = []
                
                # Add this exchange
                chat_history.append({"role": "user", "content": query})
                chat_history.append({"role": "assistant", "content": response_text[:500]})  # Limit for speed
                
                # Keep only recent messages (last 20)
                if len(chat_history) > 20:
                    chat_history = chat_history[-20:]
                
                # Save back
                with open(chatlog_path, 'w') as f:
                    json_dump(chat_history, f, indent=2)
                    
                print(f"[MEMORY] Saved command to chat history: {query[:50]}...")
            except Exception as mem_err:
                print(f"[MEMORY] Failed to save: {mem_err}")

        # === SAVE TO PER-USER MEMORY (Beast Mode) ===
        if PER_USER_MEMORY_ENABLED and user_id != 'anonymous':
            try:
                # Extract important information from the conversation
                # Check for memory-worthy patterns in user's query
                query_lower = query.lower()
                memory_triggers = {
                    'preference': ['i prefer', 'i like', 'i love', 'i hate', 'i enjoy', 'my favorite'],
                    'personal': ['my name is', 'i am', "i'm", 'i work', 'i live', 'my job'],
                    'context': ['working on', 'my project', 'the app', 'the code'],
                }
                
                saved_category = None
                for category, triggers in memory_triggers.items():
                    if any(trigger in query_lower for trigger in triggers):
                        remember(user_id, query, category, 0.6, session_id)
                        saved_category = category
                        memory_saved = True
                        break
                
                # Save explicit memory requests
                if any(phrase in query_lower for phrase in ['remember that', 'remember this', "don't forget"]):
                    remember(user_id, query, 'explicit', 0.9, session_id)
                    memory_saved = True
                    
                if memory_saved:
                    print(f"[MEMORY] Saved to per-user memory: {query[:50]}... (cat: {saved_category})")
            except Exception as mem_save_err:
                print(f"[MEMORY] Per-user save failed: {mem_save_err}")

        # Include memory metadata in response
        if 'metadata' not in chat_metadata or chat_metadata.get('metadata') is None:
            chat_metadata['metadata'] = {}
        chat_metadata['memory_accessed'] = memory_accessed
        chat_metadata['memory_saved'] = memory_saved

        return jsonify({
            "response": response_text,
            "command_executed": True,
            "metadata": chat_metadata,
            "memory_accessed": memory_accessed,
            "memory_saved": memory_saved
        })


        
    except Exception as e:
        print(f"[ERROR] ========== CHAT ENDPOINT EXCEPTION ==========")
        print(f"[ERROR] Query: {query[:200] if query else 'None'}...")
        print(f"[ERROR] Exception: {e}")
        print(f"[ERROR] Exception Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print(f"[ERROR] ================================================")
        
        # Return a user-friendly error with details for debugging
        return jsonify({
            "error": "Chat processing failed",
            "details": str(e),
            "type": type(e).__name__
        }), 500


# ==================== PER-USER MEMORY API ====================
@app.route('/api/v1/memory/stats', methods=['POST'])
@require_api_key
def memory_stats():
    """Get memory statistics for a user"""
    try:
        data = request.json
        user_id = data.get('uid', '')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        if not PER_USER_MEMORY_ENABLED:
            return jsonify({"error": "Memory system not available"}), 503
        
        stats = _per_user_memory.get_memory_stats(user_id)
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/memory/search', methods=['POST'])
@require_api_key
def memory_search():
    """Search user's memories semantically"""
    try:
        data = request.json
        user_id = data.get('uid', '')
        query = data.get('query', '')
        limit = data.get('limit', 5)
        
        if not user_id or not query:
            return jsonify({"error": "User ID and query required"}), 400
        
        if not PER_USER_MEMORY_ENABLED:
            return jsonify({"error": "Memory system not available"}), 503
        
        results = recall(user_id, query, limit)
        # Clean up results (remove embeddings)
        clean_results = []
        for r in results:
            clean_results.append({
                "content": r.get('content', ''),
                "category": r.get('category', 'general'),
                "importance": r.get('importance', 0.5),
                "similarity": r.get('similarity', 0),
                "created_at": r.get('created_at', '')
            })
        
        return jsonify({"results": clean_results, "count": len(clean_results)})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/memory/add', methods=['POST'])
@require_api_key
def memory_add():
    """Manually add a memory for a user"""
    try:
        data = request.json
        user_id = data.get('uid', '')
        content = data.get('content', '')
        category = data.get('category', 'general')
        importance = data.get('importance', 0.5)
        
        if not user_id or not content:
            return jsonify({"error": "User ID and content required"}), 400
        
        if not PER_USER_MEMORY_ENABLED:
            return jsonify({"error": "Memory system not available"}), 503
        
        success = remember(user_id, content, category, importance)
        return jsonify({"success": success})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/memory/clear', methods=['POST'])
@require_api_key
def memory_clear():
    """Clear memories for a user (GDPR compliance)"""
    try:
        data = request.json
        user_id = data.get('uid', '')
        category = data.get('category')  # Optional: clear only specific category
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        if not PER_USER_MEMORY_ENABLED:
            return jsonify({"error": "Memory system not available"}), 503
        
        success = _per_user_memory.delete_user_memories(user_id, category)
        return jsonify({"success": success, "message": "Memories cleared" if success else "Failed to clear"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/memory/compress', methods=['POST'])
@require_api_key
def memory_compress():
    """Compress old memories to save space"""
    try:
        data = request.json
        user_id = data.get('uid', '')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        if not PER_USER_MEMORY_ENABLED:
            return jsonify({"error": "Memory system not available"}), 503
        
        compressed_count = _per_user_memory.compress_old_memories(user_id)
        return jsonify({"compressed": compressed_count})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- SPEECH ---
@app.route('/api/v1/speech/recognize', methods=['POST'])
@require_api_key
def speech_recognize():
    """Trigger microphone to listen and return text"""
    try:
        if enhanced_speech:
            # Calibrate first if needed? Maybe skip for speed
            text = enhanced_speech.listen_once()
            if text:
                return jsonify({"status": "success", "text": text})
            else:
                return jsonify({"status": "failed", "error": "No speech detected"}), 400
        else:
            return jsonify({"error": "Speech module not loaded"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/speech/synthesize', methods=['POST'])
@require_api_key
def speech_synthesize():
    """Convert text to speech (play locally or return file)"""
    data = request.json
    text = data.get('text', '')
    mode = data.get('mode', 'play') # 'play' or 'file'
    
    if not text: return jsonify({"error": "Text required"}), 400
    
    try:
        if mode == 'play':
            try:
                TTS(text)
            except Exception:
                # Silently ignore TTS errors (async loop issues)
                pass
            return jsonify({"status": "success", "message": "Playing audio"})
        else:
            # Generate file
            filename = "speech_output.mp3"
            try:
                asyncio.run(TextToAudioFile(text)) # Saves to Data/speech.mp3 usually
            except Exception:
                pass
            # We assume it saves to Data/speech.mp3 based on TextToSpeech.py
            return jsonify({
                "status": "success", 
                "url": f"/data/speech.mp3",
                "timestamp": time.time()
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- VISION & IMAGES ---
# Note: /api/v1/vision/analyze endpoint is defined in the VISION API section below (line ~5431)
# This section now only handles screen-based analysis via a different endpoint

@app.route('/api/v1/vision/screen', methods=['POST'])
@require_api_key
def vision_screen_analyze():
    """Analyze the current screen (screenshot-based) - for desktop automation"""
    data = request.json
    query = data.get('query', 'Describe this screen')
    
    try:
        if VisionAnalysis:
            result = VisionAnalysis(query)
            
            # Save to history for context awareness
            try:
                from Backend.Chatbot_Enhanced import add_interaction_to_history
                add_interaction_to_history(query, result)
            except Exception as h_err:
                print(f"[WARN] Failed to save vision to history: {h_err}")
                
            return jsonify({"status": "success", "result": result})
        else:
            return jsonify({"error": "Vision module not loaded"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/image/generate', methods=['POST'])
@require_api_key
def image_generate():
    data = request.json
    prompt = data.get('prompt', '')
    if not prompt: return jsonify({"error": "Prompt required"}), 400
    
    try:
        # Try enhanced image gen first
        if enhanced_image_gen:
            style = data.get('style', 'realistic')
            images = enhanced_image_gen.generate_with_style(prompt, style, num_images=1)
            if images:
                image_urls = []
                for img_path in images:
                    img_filename = os.path.basename(img_path)
                    image_urls.append(f"/data/{img_filename}")
                # Save to history for context
                try:
                    from Backend.Chatbot_Enhanced import add_interaction_to_history
                    cmd = f"Generate {style} image of {prompt}"
                    # Add image markdown to response for history
                    response_md = f"Generated {style} image of {prompt}:\n\n![Generated Image]({image_urls[0]})"
                    add_interaction_to_history(cmd, response_md)
                except Exception:
                    pass
                return jsonify({"status": "success", "images": image_urls})
        
        # Fallback to standard image generation
        if GenerateImages:
            GenerateImages(prompt)
            
            # Find generated images
            safe_prompt = prompt.replace(" ", "_")[:30]
            images = []
            for i in range(1, 5):
                filename = f"{safe_prompt}{i}.jpg"
                if os.path.exists(os.path.join(DATA_DIR, filename)):
                    images.append(f"/data/{filename}")
            
            return jsonify({"status": "success", "images": images})
        else:
            return jsonify({"error": "ImageGen module not loaded"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- VISUAL QUESTION ANSWERING (VQA) ---
@app.route('/vqa', methods=['POST'])
def vqa_endpoint():
    """
    Visual Question Answering endpoint
    Accepts image + question and returns caption, OCR text, and AI answer
    """
    try:
        # Validate request
        if 'image' not in request.files:
            return jsonify({"success": False, "error": "No image file provided"}), 400
        
        if 'question' not in request.form:
            return jsonify({"success": False, "error": "No question provided"}), 400
        
        image_file = request.files['image']
        question = request.form['question']
        
        # Validate image file
        if image_file.filename == '':
            return jsonify({"success": False, "error": "Empty filename"}), 400
        
        # Validate file extension
        allowed_extensions = {'jpg', 'jpeg', 'png', 'bmp', 'webp', 'gif'}
        file_ext = image_file.filename.rsplit('.', 1)[1].lower() if '.' in image_file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({
                "success": False, 
                "error": f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            }), 400
        
        # Validate file size (max 10MB)
        image_file.seek(0, 2)  # Seek to end
        file_size = image_file.tell()
        image_file.seek(0)  # Reset to beginning
        
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            return jsonify({
                "success": False,
                "error": f"File too large. Maximum size: 10MB"
            }), 400
        
        # Validate question length
        if len(question) > 500:
            return jsonify({
                "success": False,
                "error": "Question too long. Maximum 500 characters"
            }), 400
        
        # Save image temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as temp_file:
            image_file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Process with VQA service
            if vqa_service:
                result = vqa_service.analyze_image_vqa(temp_path, question)
                
                # Save to history so the chatbot can "see" the image context in subsequent turns
                try:
                    from Backend.Chatbot_Enhanced import add_interaction_to_history
                    # Format a context entry
                    user_msg = f"[Image Upload] {question}"
                    # result contains 'answer' which is the AI response
                    ai_msg = result.get('answer', '')
                    caption = result.get('caption', '')
                    
                    # If answer is just the caption or different, we want to store enough info
                    # best to store the full AI answer.
                    # We can also inject the caption into the user message context if needed, but 
                    # saving the Q&A pair is usually enough for "continuity" 
                    # as long as the LLM sees previous turn.
                    
                    # However, if the result is just a JSON object to the frontend, the frontend displays it.
                    # Does the frontend display 'answer'? Yes.
                    
                    full_response = ai_msg
                    if caption and caption not in ai_msg:
                        full_response += f"\n(Caption: {caption})"
                        
                    add_interaction_to_history(user_msg, full_response)
                except Exception as h_err:
                    print(f"[WARN] Failed to save VQA to history: {h_err}")
                
                return jsonify(result)
            else:
                return jsonify({
                    "success": False,
                    "error": "VQA service not available"
                }), 503
        finally:
            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"VQA processing error: {str(e)}"
        }), 500


# --- FILE UPLOAD & ANALYSIS ---
# @app.route('/api/v1/files/upload', methods=['POST'])
def files_upload():
    """Upload file with automatic VQA analysis for images"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "Empty filename"}), 400
        
        question = request.form.get('question', 'Describe this image in detail')
        auto_analyze = request.form.get('auto_analyze', 'true').lower() == 'true'
        
        if file_analyzer:
            file_data = file.read()
            file_size_mb = len(file_data) / (1024 * 1024)
            
            # Validate file size (max 150MB)
            if file_size_mb > 150:
                return jsonify({
                    "success": False, 
                    "error": f"File too large ({file_size_mb:.1f}MB). Maximum size is 150MB."
                }), 400
            
            filepath = file_analyzer.save_upload(file_data, file.filename)
            file_type = file_analyzer.get_file_type(file.filename)
            
            response_data = {
                "success": True,
                "file": {
                    "filename": os.path.basename(filepath),
                    "filepath": filepath,
                    "type": file_type,
                    "size_mb": round(file_size_mb, 2)
                }
            }
            
            # Analyze images with VQA
            if file_type == 'image' and auto_analyze and vqa_service:
                try:
                    analysis = file_analyzer.analyze_with_vqa(filepath, question)
                    response_data["analysis"] = analysis
                except Exception as e:
                    print(f"[VQA ERROR] {e}")
                    response_data["analysis_error"] = str(e)
            
            # For videos, add metadata (duration, resolution, etc.)
            elif file_type == 'video':
                try:
                    # Basic video info for now
                    response_data["video_info"] = {
                        "message": "Video uploaded successfully. Playback available in chat."
                    }
                except Exception as e:
                    print(f"[VIDEO ERROR] {e}")
            
            return jsonify(response_data)
        else:
            return jsonify({"success": False, "error": "File analyzer not available"}), 503
    except Exception as e:
        print(f"[UPLOAD ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/v1/files/analyze', methods=['POST'])
def files_analyze():
    """Analyze uploaded file with VQA"""
    try:
        data = request.json
        filepath = data.get('filepath')
        question = data.get('question', 'Describe this image in detail')
        
        if not filepath or not os.path.exists(filepath):
            return jsonify({"success": False, "error": "File not found"}), 404
        
        if file_analyzer and vqa_service:
            return jsonify(file_analyzer.analyze_with_vqa(filepath, question))
        return jsonify({"success": False, "error": "Service unavailable"}), 503
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/v1/files/list', methods=['GET'])
def files_list():
    """List uploaded files with analysis summaries"""
    try:
        if file_analyzer:
            files = file_analyzer.list_uploads(limit=request.args.get('limit', 20, type=int))
            for f in files:
                cached = file_analyzer.load_analysis(f['path'])
                f['has_analysis'] = bool(cached)
                f['caption'] = cached.get('caption', '') if cached else ''
            return jsonify({"success": True, "files": files})
        return jsonify({"success": False, "error": "Service unavailable"}), 503
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/v1/whatsapp/send-image', methods=['POST'])
@require_api_key
def whatsapp_send_image():
    """Send image via WhatsApp with VQA-generated caption"""
    try:
        data = request.json
        if not data.get('phone') or not data.get('image_path'):
            return jsonify({"success": False, "error": "phone and image_path required"}), 400
        
        if whatsapp:
            return jsonify(whatsapp.send_image(
                data['phone'], 
                data['image_path'], 
                data.get('caption'), 
                data.get('auto_caption', True)
            ))
        return jsonify({"success": False, "error": "WhatsApp unavailable"}), 503
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# --- UNIVERSAL SEARCH ---
@app.route('/api/v1/search/universal', methods=['POST'])
@require_api_key
def universal_search():
    """Universal search across all sources"""
    try:
        data = request.json
        query = data.get('query', '').strip()
        sources = data.get('sources')
        limit = data.get('limit', 50)
        
        if not query or len(query) < 2:
            return jsonify({"success": False, "error": "Query must be at least 2 characters"}), 400
        
        if search_engine:
            results = search_engine.universal_search(query, sources, limit)
            return jsonify(results)
        else:
            return jsonify({"success": False, "error": "Search engine not available"}), 503
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/v1/search/suggestions', methods=['GET'])
@require_api_key
def search_suggestions():
    """Get autocomplete suggestions"""
    try:
        partial_query = request.args.get('q', '').strip()
        
        if search_engine:
            suggestions = search_engine.get_suggestions(partial_query)
            return jsonify({"success": True, "suggestions": suggestions})
        else:
            return jsonify({"success": False, "error": "Search engine not available"}), 503
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/v1/search/recent', methods=['GET'])
@require_api_key
def recent_searches():
    """Get recent search queries"""
    try:
        if search_engine:
            recent = search_engine.get_recent_searches()
            return jsonify({"success": True, "recent": recent})
        else:
            return jsonify({"success": False, "error": "Search engine not available"}), 503
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# --- AUTOMATION & CONTROL ---
@app.route('/api/v1/automation/execute', methods=['POST'])
@require_api_key
def automation_execute():
    data = request.json
    commands = data.get('commands', [])
    if not commands: return jsonify({"error": "Commands required"}), 400
    
    try:
        if Automation:
            asyncio.run(Automation(commands))
            
            # Save to history
            try:
                from Backend.Chatbot_Enhanced import add_interaction_to_history
                cmd_str = ", ".join(commands)
                add_interaction_to_history(f"Execute automation: {cmd_str}", f"✅ Executed automation commands: {cmd_str}")
            except Exception:
                pass
                
            return jsonify({"status": "success", "executed": len(commands)})
        else:
            return jsonify({"error": "Automation module not loaded"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/workflow/run', methods=['POST'])
@require_api_key
def workflow_run():
    data = request.json
    workflow = data.get('workflow', '')
    if not workflow: return jsonify({"error": "Workflow required"}), 400
    
    try:
        if workflow_engine:
            result = asyncio.run(workflow_engine.execute_workflow(workflow))
            
            # Save to history
            try:
                from Backend.Chatbot_Enhanced import add_interaction_to_history
                add_interaction_to_history(f"Run workflow: {workflow}", f"✅ Workflow executed: {result}")
            except Exception:
                pass

            return jsonify({"status": "success", "result": result})
        else:
            return jsonify({"error": "Workflow module not loaded"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- WEB & SEARCH ---
@app.route('/api/v1/search/realtime', methods=['POST'])
@require_api_key
def search_realtime():
    data = request.json
    query = data.get('query', '')
    if not query: return jsonify({"error": "Query required"}), 400
    
    try:
        if RealtimeSearchEngine:
            # RealtimeSearchEngine is a function that returns a string response
            result = RealtimeSearchEngine(query)
            return jsonify({"status": "success", "result": result, "message": "Search completed"})
        else:
            return jsonify({"error": "Search module not loaded"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- REALTIME DATA ---
@app.route('/api/v1/data/live', methods=['GET'])
@require_api_key
def data_live():
    """Get live data for dashboard (Crypto, Weather, etc.)"""
    try:
        from Backend.RealtimeSearchEngine import fetch_crypto_price
        
        # Bitcoin
        btc_price = fetch_crypto_price("bitcoin")
        if not btc_price:
            btc_price = "$98,000 (est)"
        else:
            # Extract just the price part if possible, but the function returns "Bitcoin price: $90,000..."
            pass
            
        return jsonify({
            "status": "success",
            "bitcoin": btc_price,
            "weather": "22°C ☀️ (Local)" # Placeholder until we have weather
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- REMINDERS ---
@app.route('/api/v1/reminders', methods=['GET', 'POST'])
@require_api_key
def reminders():
    try:
        if request.method == 'GET':
            if load_reminders:
                return jsonify({"status": "success", "reminders": load_reminders()})
        elif request.method == 'POST':
            if set_reminder:
                data = request.json
                text = data.get('text', '')
                time_str = data.get('time', '') # Format: YYYY-MM-DD HH:MM:SS
                
                if not text or not time_str:
                    return jsonify({"error": "Text and time required"}), 400
                
                # Parse time
                try:
                    reminder_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    return jsonify({"error": "Invalid time format. Use YYYY-MM-DD HH:MM:SS"}), 400
                
                msg = set_reminder(text, reminder_time)
                
                # Save to history
                try:
                    from Backend.Chatbot_Enhanced import add_interaction_to_history
                    add_interaction_to_history(f"Set reminder: {text} at {time_str}", f"✅ {msg}")
                except Exception:
                    pass

                return jsonify({"status": "success", "message": msg})
        
        return jsonify({"error": "Reminder module not loaded"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- SYSTEM & UTILS ---
@app.route('/api/v1/system/stats', methods=['GET'])
@require_api_key
def system_stats_api():
    import psutil
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return jsonify({"status": "success", "stats": {
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "memory_used_gb": round(mem.used / (1024**3), 2),
            "disk_percent": disk.percent
        }})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== USER SETTINGS API ====================

@app.route('/api/v1/settings/<user_id>', methods=['GET'])
def get_user_settings(user_id):
    """Get all user settings"""
    try:
        from Backend.SupabaseDB import supabase_db
        if not supabase_db:
            return jsonify({"error": "Database not available"}), 503
        
        settings = supabase_db.get_user_settings(user_id)
        return jsonify({
            "status": "success",
            "settings": settings
        })
    except Exception as e:
        print(f"[SETTINGS API] Get error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/settings/<user_id>', methods=['PUT'])
def save_user_settings(user_id):
    """Save all user settings"""
    try:
        from Backend.SupabaseDB import supabase_db
        if not supabase_db:
            return jsonify({"error": "Database not available"}), 503
        
        data = request.json
        if not data:
            return jsonify({"error": "No settings data provided"}), 400
        
        success = supabase_db.save_user_settings(user_id, data)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Settings saved successfully"
            })
        else:
            return jsonify({"error": "Failed to save settings"}), 500
            
    except Exception as e:
        print(f"[SETTINGS API] Save error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/profile/<user_id>', methods=['GET'])
def get_settings_profile(user_id):
    """Get user profile with stats, rank, and achievements"""
    try:
        from Backend.SupabaseDB import supabase_db
        if not supabase_db:
            return jsonify({"error": "Database not available"}), 503
        
        profile = supabase_db.get_user_profile(user_id)
        return jsonify({
            "status": "success",
            "profile": profile
        })
    except Exception as e:
        print(f"[PROFILE API] Get error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/profile/<user_id>', methods=['PUT'])
def update_settings_profile(user_id):
    """Update user profile"""
    try:
        from Backend.SupabaseDB import supabase_db
        if not supabase_db:
            return jsonify({"error": "Database not available"}), 503
        
        data = request.json
        if not data:
            return jsonify({"error": "No profile data provided"}), 400
        
        success = supabase_db.update_user_profile(user_id, data)
        
        if success:
            # Return updated profile with stats
            profile = supabase_db.get_user_profile(user_id)
            return jsonify({
                "status": "success",
                "message": "Profile updated successfully",
                "profile": profile
            })
        else:
            return jsonify({"error": "Failed to update profile"}), 500
            
    except Exception as e:
        print(f"[PROFILE API] Update error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/predictions', methods=['GET'])
@require_api_key
def predictions_api():
    if ai_predictor:
        return jsonify({
            "status": "success", 
            "predictions": ai_predictor.predict_tasks(limit=5),
            "suggestions": ai_predictor.get_smart_suggestions()
        })
    return jsonify({"error": "AI Predictor not loaded"}), 503

@app.route('/api/v1/windows/list', methods=['GET'])
@require_api_key
def windows_list_api():
    if window_manager:
        return jsonify({"status": "success", "windows": window_manager.list_open_apps()})
    return jsonify({"error": "Window Manager not loaded"}), 503

@app.route('/api/v1/windows/switch', methods=['POST'])
@require_api_key
def windows_switch_api():
    data = request.json
    app_name = data.get('app', '')
    if window_manager:
        return jsonify({"status": "success", "result": window_manager.switch_to_app(app_name)})
    return jsonify({"error": "Window Manager not loaded"}), 503

# --- GESTURES & VOICE ---
@app.route('/api/v1/gestures/control', methods=['POST'])
@require_api_key
def gestures_control():
    data = request.json
    action = data.get('action', 'stop') # start/stop
    
    if not ultra_smooth_gesture:
        return jsonify({"error": "Gesture module not loaded"}), 503
        
    try:
        if action == 'start':
            # Run in thread
            if not ultra_smooth_gesture.is_running:
                threading.Thread(target=ultra_smooth_gesture.run, daemon=True).start()
                msg = "Gesture control started"
            else:
                msg = "Gesture control already running"
        else:
            ultra_smooth_gesture.stop()
            msg = "Gesture control stopped"
            
        return jsonify({"status": "success", "message": msg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/voice/level', methods=['GET'])
@require_api_key
def voice_level():
    if not visualizer:
        return jsonify({"error": "Visualizer not loaded"}), 503
    
    # Auto-start if not running
    if not visualizer.is_running:
        visualizer.start()
        
    return jsonify({"status": "success", "level": visualizer.get_volume()})

# --- WAKE WORD & STATUS ---

def wake_word_listener():
    """Background thread for wake word detection"""
    if not PORCUPINE_AVAILABLE:
        print("[WARN] Wake Word loop skipped (Module missing)")
        return
        
    try:
        # Use a hardcoded key if env not set for demo purposes or use the one from main.py logic
        ACCESS_KEY = os.getenv("PORCUPINE_KEY", "pKTkEFJzE5noAcbw7gYkMAVszshY/LcZV2jxAKwnBXdChmiouehw4g==")
        
        porcupine = pvporcupine.create(access_key=ACCESS_KEY, keywords=["jarvis", "computer"]) # or standard keywords
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )
        
        print("[INFO] Wake Word Listener Active (Keywords: jarvis, computer)")
        
        while True:
            try:
                pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
                keyword_index = porcupine.process(pcm)
                
                if keyword_index >= 0:
                    print(f"[ACTION] Wake Word Detected!")
                    system_status.wake_word_detected = True
                    system_status.status = "Listening..."
                    # Check repeatedly or use callback? 
                    # Simpler to just set flag and let frontend poll or we push if we had sockets
                    # sleep briefly to avoid multiple triggers
                    time.sleep(1)
            except Exception as e:
                # print(f"Wake loop error: {e}")
                pass
                
    except Exception as e:
        print(f"[ERROR] Wake Word Init Failed: {e}")

@app.route('/api/v1/status', methods=['GET'])
@require_api_key
def get_status():
    """Get current system status (wake word, etc)"""
    return jsonify({
        "status": system_status.status,
        "wake_word_detected": system_status.wake_word_detected
    })

@app.route('/api/v1/status/reset', methods=['POST'])
@require_api_key
def reset_status():
    """Reset wake word flag"""
    system_status.wake_word_detected = False
    system_status.status = "Available..."
    return jsonify({"status": "success"})

@app.route('/api/v1/predictions', methods=['GET'])
@require_api_key
def get_predictions():
    if not ai_predictor:
        return jsonify({"error": "Predictor not loaded"}), 503
    return jsonify({"suggestions": ai_predictor.get_smart_suggestions()})

@app.route('/api/v1/system/detailed_stats', methods=['GET'])
@require_api_key
def get_system_stats():
    import psutil
    try:
        cpu = psutil.cpu_percent(interval=0.1, percpu=True)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot = psutil.boot_time()
        import datetime
        uptime = str(datetime.datetime.now() - datetime.datetime.fromtimestamp(boot)).split('.')[0]
        battery = psutil.sensors_battery()
        return jsonify({"stats": {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "cpu_per_core": cpu,
            "memory_percent": mem.percent,
            "memory_available_gb": round(mem.available / (1024**3), 2),
            "disk_percent": disk.percent,
            "uptime": uptime,
            "battery": {"percent": battery.percent, "plugged": battery.power_plugged} if battery else None
        }})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/system/control', methods=['POST'])
@require_api_key
def system_control():
    data = request.json
    action = data.get('action', '')
    
    try:
        if action == 'shutdown':
            os.system("shutdown /s /t 60")
            return jsonify({"message": "Shutting down in 60s"})
        elif action == 'restart':
            os.system("shutdown /r /t 60")
            return jsonify({"message": "Restarting in 60s"})
        elif action == 'lock':
            os.system("rundll32.exe user32.dll,LockWorkStation")
            return jsonify({"message": "System Locked"})
        elif action == 'screenshot':
            import pyautogui
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            pyautogui.screenshot(filename)
            return jsonify({"message": "Screenshot taken", "file": filename})
        else:
            return jsonify({"error": "Unknown action"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- FILE UPLOAD & ANALYSIS ---
# --- VISION & FILE UPLOAD ROUTES ---
if VISION_AVAILABLE:
    app.add_url_rule('/api/v1/files/upload', view_func=upload_endpoint, methods=['POST'])
    app.add_url_rule('/api/v1/files', view_func=list_endpoint, methods=['GET'])
    app.add_url_rule('/api/v1/files/<path:file_id>/download', view_func=download_endpoint, methods=['GET'])
    app.add_url_rule('/api/v1/files/<path:file_id>', view_func=delete_endpoint, methods=['DELETE'])
    app.add_url_rule('/api/v1/files/<path:file_id>/analyze', view_func=analyze_endpoint, methods=['GET'])
    app.add_url_rule('/api/v1/analyze-image', view_func=analyze_image_endpoint, methods=['POST'])
    print("[OK] Vision & File Upload routes registered")
else:
    print("[INFO] Vision routes disabled (cloud deployment)")



# --- CONTEXTUAL MEMORY ---
@app.route('/api/v1/memory/facts', methods=['GET', 'POST'])
@require_api_key
def memory_facts():
    """Get or add facts to memory"""
    if not contextual_memory:
        return jsonify({"error": "Memory module not loaded"}), 503
    
    try:
        if request.method == 'GET':
            # Search facts
            query = request.args.get('query', '')
            if query:
                results = contextual_memory.search_memory(query)
                return jsonify({"status": "success", "results": results})
            else:
                return jsonify({"status": "success", "facts": contextual_memory.memory.get("facts", [])})
        
        elif request.method == 'POST':
            data = request.json
            fact = data.get('fact', '')
            category = data.get('category', 'general')
            
            if not fact:
                return jsonify({"error": "Fact required"}), 400
            
            success = contextual_memory.remember_fact(fact, category)
            return jsonify({"status": "success", "added": success})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/memory/preferences', methods=['GET', 'POST'])
@require_api_key
def memory_preferences():
    """Get or set user preferences"""
    if not contextual_memory:
        return jsonify({"error": "Memory module not loaded"}), 503
    
    try:
        if request.method == 'GET':
            return jsonify({"status": "success", "preferences": contextual_memory.memory.get("preferences", {})})
        
        elif request.method == 'POST':
            data = request.json
            key = data.get('key', '')
            value = data.get('value', '')
            
            if not key or not value:
                return jsonify({"error": "Key and value required"}), 400
            
            contextual_memory.remember_preference(key, value)
            return jsonify({"status": "success", "message": f"Preference '{key}' saved"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/memory/projects', methods=['GET', 'POST'])
@require_api_key
def memory_projects():
    """Get or add projects to memory"""
    if not contextual_memory:
        return jsonify({"error": "Memory module not loaded"}), 503
    
    try:
        if request.method == 'GET':
            return jsonify({"status": "success", "projects": contextual_memory.memory.get("projects", [])})
        
        elif request.method == 'POST':
            data = request.json
            name = data.get('name', '')
            description = data.get('description', '')
            
            if not name:
                return jsonify({"error": "Project name required"}), 400
            
            success = contextual_memory.remember_project(name, description)
            return jsonify({"status": "success", "added": success})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/memory/context', methods=['POST'])
@require_api_key
def memory_context():
    """Get contextual information for a query"""
    if not contextual_memory:
        return jsonify({"error": "Memory module not loaded"}), 503
    
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "Query required"}), 400
        
        context = contextual_memory.get_context(query)
        return jsonify({"status": "success", "context": context})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/memory/summary', methods=['GET'])
@require_api_key
def memory_summary():
    """Get memory system summary"""
    if not contextual_memory:
        return jsonify({"error": "Memory module not loaded"}), 503
    
    try:
        summary = contextual_memory.get_summary()
        return jsonify({"status": "success", "summary": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- RESPONSE CACHE ---
@app.route('/api/v1/cache/stats', methods=['GET'])
@require_api_key
def cache_stats():
    """Get cache statistics"""
    if not get_cache:
        return jsonify({"error": "Cache module not loaded"}), 503
    
    try:
        cache = get_cache()
        stats = cache.get_stats()
        return jsonify({"status": "success", "stats": stats})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/cache/clear', methods=['POST'])
@require_api_key
def cache_clear():
    """Clear response cache"""
    if not get_cache:
        return jsonify({"error": "Cache module not loaded"}), 503
    
    try:
        cache = get_cache()
        cache.clear()
        return jsonify({"status": "success", "message": "Cache cleared"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ADVANCED INTEGRATIONS ---
@app.route('/api/v1/integrations/weather', methods=['GET'])
@require_api_key
def integration_weather():
    """Get current weather"""
    if not integrations:
        return jsonify({"error": "Integrations module not loaded"}), 503
    
    try:
        city = request.args.get('city', 'London')
        weather = integrations.get_weather(city)
        return jsonify({"status": "success", "weather": weather})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/integrations/forecast', methods=['GET'])
@require_api_key
def integration_forecast():
    """Get weather forecast"""
    if not integrations:
        return jsonify({"error": "Integrations module not loaded"}), 503
    
    try:
        city = request.args.get('city', 'London')
        days = int(request.args.get('days', 3))
        forecast = integrations.get_forecast(city, days)
        return jsonify({"status": "success", "forecast": forecast})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/integrations/news', methods=['GET'])
@require_api_key
def integration_news():
    """Get latest news"""
    if not integrations:
        return jsonify({"error": "Integrations module not loaded"}), 503
    
    try:
        topic = request.args.get('topic', 'technology')
        limit = int(request.args.get('limit', 5))
        news = integrations.get_news(topic, limit)
        return jsonify({"status": "success", "news": news})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/integrations/crypto', methods=['GET'])
@require_api_key
def integration_crypto():
    """Get cryptocurrency price"""
    if not integrations:
        return jsonify({"error": "Integrations module not loaded"}), 503
    
    try:
        symbol = request.args.get('symbol', 'bitcoin')
        price = integrations.get_crypto_price(symbol)
        return jsonify({"status": "success", "crypto": price})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/integrations/stock', methods=['GET'])
@require_api_key
def integration_stock():
    """Get stock price"""
    if not integrations:
        return jsonify({"error": "Integrations module not loaded"}), 503
    
    try:
        symbol = request.args.get('symbol', 'AAPL')
        price = integrations.get_stock_price(symbol)
        return jsonify({"status": "success", "stock": price})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/integrations/quote', methods=['GET'])
@require_api_key
def integration_quote():
    """Get inspirational quote"""
    if not integrations:
        return jsonify({"error": "Integrations module not loaded"}), 503
    
    try:
        quote = integrations.get_quote()
        return jsonify({"status": "success", "quote": quote})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/integrations/joke', methods=['GET'])
@require_api_key
def integration_joke():
    """Get a random joke"""
    if not integrations:
        return jsonify({"error": "Integrations module not loaded"}), 503
    
    try:
        joke = integrations.get_joke()
        return jsonify({"status": "success", "joke": joke})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/integrations/fact', methods=['GET'])
@require_api_key
def integration_fact():
    """Get random fact"""
    if not integrations:
        return jsonify({"error": "Integrations module not loaded"}), 503
    
    try:
        fact = integrations.get_fact()
        return jsonify({"status": "success", "fact": fact})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/integrations/define', methods=['GET'])
@require_api_key
def integration_define():
    """Get word definition"""
    if not integrations:
        return jsonify({"error": "Integrations module not loaded"}), 503
    
    try:
        word = request.args.get('word', '')
        if not word:
            return jsonify({"error": "Word parameter required"}), 400
        
        definition = integrations.define_word(word)
        return jsonify({"status": "success", "definition": definition})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/integrations/ip', methods=['GET'])
@require_api_key
def integration_ip():
    """Get IP information"""
    if not integrations:
        return jsonify({"error": "Integrations module not loaded"}), 503
    
    try:
        ip_info = integrations.get_ip_info()
        return jsonify({"status": "success", "ip_info": ip_info})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- YOUTUBE AUTOMATION ---
@app.route('/api/v1/youtube/control', methods=['POST'])
@require_api_key
def youtube_control():
    """Control YouTube playback"""
    if not YoutubeAutomation:
        return jsonify({"error": "YouTube Automation not loaded"}), 503
    
    try:
        data = request.json
        action = data.get('action', '')  # play, pause, search, next, previous
        query = data.get('query', '')
        
        yt = YoutubeAutomation()
        
        if action == 'search' and query:
            yt.search_and_play(query)
            return jsonify({"status": "success", "message": f"Playing: {query}"})
        elif action == 'pause':
            yt.pause()
            return jsonify({"status": "success", "message": "Paused"})
        elif action == 'play':
            yt.play()
            return jsonify({"status": "success", "message": "Playing"})
        elif action == 'next':
            yt.next_video()
            return jsonify({"status": "success", "message": "Next video"})
        elif action == 'previous':
            yt.previous_video()
            return jsonify({"status": "success", "message": "Previous video"})
        else:
            return jsonify({"error": "Invalid action or missing query"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- WEB SCRAPING ---
@app.route('/api/v1/scrape', methods=['POST'])
@require_api_key
def web_scrape():
    """Scrape a website"""
    if not JarvisWebScraper:
        return jsonify({"error": "Web Scraper not loaded"}), 503
    
    try:
        data = request.json
        url = data.get('url', '')
        
        if not url:
            return jsonify({"error": "URL required"}), 400
        
        scraper = JarvisWebScraper()
        result = scraper.scrape(url)
        
        return jsonify({
            "status": "success",
            "url": url,
            "data": result
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- CHROME AUTOMATION ---
@app.route('/api/v1/chrome/control', methods=['POST'])
@require_api_key
def chrome_control():
    """Control Chrome browser"""
    try:
        from Backend.ChromeAutomation import chrome_bot, chrome_search, chrome_open, chrome_command
    except ImportError as e:
        return jsonify({"error": f"Chrome Automation not available: {str(e)}"}), 503
    
    try:
        data = request.json
        action = data.get('action', '')  # start, search, open, command
        target = data.get('target', '')
        
        if action == 'start':
            chrome_bot.start_chrome()
            return jsonify({"status": "success", "message": "Chrome started"})
        elif action == 'search' and target:
            chrome_search(target)
            return jsonify({"status": "success", "message": f"Searching: {target}"})
        elif action == 'open' and target:
            chrome_open(target)
            return jsonify({"status": "success", "message": f"Opening: {target}"})
        elif action == 'command' and target:
            result = chrome_command(target)
            return jsonify({"status": "success", "message": str(result)})
        else:
            return jsonify({"error": "Invalid action or missing target"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- DOCUMENT GENERATION ---
@app.route('/api/v1/documents/pdf', methods=['POST'])
@require_api_key
def create_pdf():
    """Generate a PDF document"""
    if not document_generator:
        return jsonify({"error": "Document Generator not loaded"}), 503
    
    try:
        data = request.json
        title = data.get('title', 'Document')
        content = data.get('content', [])
        
        if not content:
            # Generate default content
            content = [
                {"type": "heading", "text": f"About {title}"},
                {"type": "paragraph", "text": f"This document provides information about {title}."}
            ]
        
        # Convert list content to expected dict format
        sections = []
        current_section = {"heading": "", "content": "", "type": "paragraph", "data": []}
        
        for item in content:
            item_type = item.get("type", "paragraph")
            item_text = item.get("text", "")
            
            if item_type == "heading":
                if current_section["content"] or current_section["data"]:
                    sections.append(current_section)
                current_section = {"heading": item_text, "content": "", "type": "paragraph", "data": []}
            elif item_type == "paragraph":
                if current_section["content"]:
                    current_section["content"] += "\n\n" + item_text
                else:
                    current_section["content"] = item_text
            elif item_type == "bullet":
                current_section["type"] = "bullet"
                current_section["data"].append(item_text)
        
        if current_section["content"] or current_section["data"]:
            sections.append(current_section)
        
        # Use new template-based document generation
        user_id = request.current_user.get('user_id') if hasattr(request, 'current_user') else None
        document_type = data.get('document_type', 'professional_report')  # Can be: expo_submission, pitch_document, technical_guide, professional_report
        
        pdf_content = {
            "title": title,
            "subtitle": "Generated by Kai AI",
            "sections": sections,
            "document_type": document_type
        }
        
        pdf_result = document_generator.generate(
            topic=title,
            document_type=document_type,
            content=pdf_content,
            user_id=user_id
        )
        
        return jsonify({
            "status": "success",
            "message": "PDF created successfully",
            "filepath": pdf_result.get("filepath"),
            "filename": pdf_result.get("filename"),
            "url": pdf_result.get("url"),
            "format": pdf_result.get("format", "pdf")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/documents/powerpoint', methods=['POST'])
@require_api_key
def create_powerpoint():
    """Generate a PowerPoint presentation"""
    if not document_generator:
        return jsonify({"error": "Document Generator not loaded"}), 503
    
    try:
        data = request.json
        title = data.get('title', 'Presentation')
        slides = data.get('slides', [])
        
        if not slides:
            # Generate default slides
            slides = [
                {"title": "Introduction", "content": [f"Overview of {title}"], "layout": "bullet"},
                {"title": "Conclusion", "content": ["Summary", "Next steps"], "layout": "bullet"}
            ]
        
        # Build content dict for generate_presentation
        ppt_content = {
            "title": title,
            "slides": slides
        }
        
        # generate_presentation returns a filepath string
        user_id = request.current_user.get('user_id') if hasattr(request, 'current_user') else None
        filepath = document_generator.generate_presentation(title, ppt_content, user_id=user_id)
        
        filename = os.path.basename(filepath)
        return jsonify({
            "status": "success",
            "message": "PowerPoint created successfully",
            "filepath": filepath,
            "url": f"/data/Documents/{filename}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/documents/report', methods=['POST'])
@require_api_key
def create_report():
    """Generate a comprehensive report"""
    if not document_generator:
        return jsonify({"error": "Document Generator not loaded"}), 503
    
    try:
        data = request.json
        topic = data.get('topic', 'Report')
        sections = data.get('sections', [])
        
        # Use new template-based document generation
        document_type = data.get('document_type', 'professional_report')
        
        user_id = request.current_user.get('user_id') if hasattr(request, 'current_user') else None
        
        # Use the new generate() method - it can generate content from topic if sections is empty
        pdf_result = document_generator.generate(
            topic=topic,
            document_type=document_type,
            content={
                "title": f"Report on {topic}",
                "subtitle": "Generated by Kai AI",
                "sections": sections if sections else None
            } if sections else None,  # Let LLM generate if no sections provided
            user_id=user_id
        )
        
        return jsonify({
            "status": "success",
            "message": "Report created successfully",
            "filepath": pdf_result.get("filepath"),
            "filename": pdf_result.get("filename"),
            "url": pdf_result.get("url"),
            "format": pdf_result.get("format", "pdf")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ENHANCED IMAGE GENERATION ---
@app.route('/api/v1/images/generate', methods=['POST'])
@require_api_key
def generate_enhanced_image():
    """Generate images with enhanced AI"""
    if not enhanced_image_gen:
        return jsonify({"error": "Enhanced Image Generator not loaded"}), 503
    
    try:
        data = request.json
        prompt = data.get('prompt', '')
        style = data.get('style', 'realistic')
        num_images = data.get('num_images', 1)
        
        if not prompt:
            return jsonify({"error": "Prompt required"}), 400
        
        user_id = request.current_user.get('user_id') if hasattr(request, 'current_user') else None
        images = enhanced_image_gen.generate_with_style(prompt, style, num_images, user_id=user_id)
        
        # Convert to relative URLs
        image_urls = [f"/data/Images/{os.path.basename(img)}" for img in images]
        
        return jsonify({
            "status": "success",
            "message": f"Generated {len(images)} images",
            "images": image_urls,
            "filepaths": images
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/images/generate/hd', methods=['POST'])
@require_api_key
def generate_hd_image():
    """Generate HD images"""
    if not enhanced_image_gen:
        return jsonify({"error": "Enhanced Image Generator not loaded"}), 503
    
    try:
        data = request.json
        prompt = data.get('prompt', '')
        num_images = data.get('num_images', 1)
        
        if not prompt:
            return jsonify({"error": "Prompt required"}), 400
        
        user_id = request.current_user.get('user_id') if hasattr(request, 'current_user') else None
        images = enhanced_image_gen.generate_hd(prompt, num_images, user_id=user_id)
        image_urls = [f"/data/Images/{os.path.basename(img)}" for img in images]
        
        return jsonify({
            "status": "success",
            "message": f"Generated {len(images)} HD images",
            "images": image_urls,
            "filepaths": images
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/images/generate/variations', methods=['POST'])
@require_api_key
def generate_image_variations():
    """Generate image variations"""
    if not enhanced_image_gen:
        return jsonify({"error": "Enhanced Image Generator not loaded"}), 503
    
    try:
        data = request.json
        prompt = data.get('prompt', '')
        variations = data.get('variations', ['realistic', 'artistic', 'vibrant'])
        
        if not prompt:
            return jsonify({"error": "Prompt required"}), 400
        
        user_id = request.current_user.get('user_id') if hasattr(request, 'current_user') else None
        result = enhanced_image_gen.generate_variations(prompt, variations, num_per_variation=1, user_id=user_id)
        
        # Format response
        formatted_result = {}
        for variation, images in result.items():
            formatted_result[variation] = [f"/data/Images/{os.path.basename(img)}" for img in images]
        
        total_count = sum(len(imgs) for imgs in result.values())
        
        return jsonify({
            "status": "success",
            "message": f"Generated {total_count} image variations",
            "variations": formatted_result
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/images/styles', methods=['GET'])
@require_api_key
def list_image_styles():
    """List available image styles"""
    styles = [
        "realistic", "anime", "oil_painting", "watercolor", "sketch",
        "3d_render", "cyberpunk", "fantasy", "minimalist", "vintage",
        "comic", "pixel_art"
    ]
    
    return jsonify({
        "status": "success",
        "styles": styles
    })

@app.route('/api/v1/images/list', methods=['GET'])
@require_api_key
def list_generated_images():
    """List recently generated images"""
    if not enhanced_image_gen:
        return jsonify({"error": "Enhanced Image Generator not loaded"}), 503
    
    try:
        limit = int(request.args.get('limit', 20))
        images = enhanced_image_gen.list_generated_images(limit)
        
        return jsonify({
            "status": "success",
            "count": len(images),
            "images": images
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== RAG - CHAT WITH DOCUMENTS ====================

# Global RAG instance (lazy loaded)
document_rag = None

def get_document_rag():
    """Lazy load DocumentRAG module."""
    global document_rag
    if document_rag is None:
        try:
            from Backend.DocumentRAG import document_rag as rag
            document_rag = rag
        except Exception as e:
            print(f"[WARN] DocumentRAG not available: {e}")
            return None
    return document_rag

@app.route('/api/v1/rag/upload-url', methods=['POST'])
@require_api_key
def rag_upload_url():
    """Upload a URL for RAG (Chat with Documents)"""
    rag = get_document_rag()
    if not rag:
        return jsonify({"error": "RAG module not available"}), 503
    
    try:
        data = request.json
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({"error": "URL required"}), 400
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        result = rag.upload_url(url)
        
        if result.get("status") == "success":
            return jsonify({
                "status": "success",
                "type": "rag_upload",
                "doc_id": result.get("doc_id"),
                "title": result.get("title"),
                "char_count": result.get("char_count"),
                "message": result.get("message")
            })
        else:
            return jsonify({"error": result.get("message", "Upload failed")}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/rag/chat', methods=['POST'])
@require_api_key
def rag_chat():
    """Chat with an uploaded document"""
    rag = get_document_rag()
    if not rag:
        return jsonify({"error": "RAG module not available"}), 503
    
    try:
        data = request.json
        query = data.get('query', '').strip()
        doc_id = data.get('doc_id')  # Optional - uses active document if not provided
        
        if not query:
            return jsonify({"error": "Query required"}), 400
        
        result = rag.chat_with_document(query, doc_id)
        
        if result.get("status") == "success":
            return jsonify({
                "status": "success",
                "type": "rag_response",
                "response": result.get("response"),
                "document_title": result.get("document_title"),
                "doc_id": result.get("doc_id")
            })
        else:
            return jsonify({"error": result.get("message", "Chat failed")}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/rag/documents', methods=['GET'])
@require_api_key
def rag_list_documents():
    """List uploaded RAG documents"""
    rag = get_document_rag()
    if not rag:
        return jsonify({"error": "RAG module not available"}), 503
    
    try:
        documents = rag.list_documents()
        return jsonify({
            "status": "success",
            "count": len(documents),
            "documents": documents
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/rag/document/<doc_id>', methods=['DELETE'])
@require_api_key
def rag_delete_document(doc_id):
    """Delete a RAG document"""
    rag = get_document_rag()
    if not rag:
        return jsonify({"error": "RAG module not available"}), 503
    
    try:
        result = rag.delete_document(doc_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/rag/compare', methods=['POST'])
@require_api_key
def rag_compare_documents():
    """Compare two RAG documents"""
    rag = get_document_rag()
    if not rag:
        return jsonify({"error": "RAG module not available"}), 503
    
    try:
        data = request.json
        doc_id1 = data.get('doc_id1')
        doc_id2 = data.get('doc_id2')
        aspect = data.get('aspect')  # Optional focus area
        
        if not doc_id1 or not doc_id2:
            return jsonify({"error": "Two document IDs required"}), 400
        
        result = rag.compare_documents(doc_id1, doc_id2, aspect)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/rag/set-active', methods=['POST'])
@require_api_key
def rag_set_active_documents():
    """Set multiple documents as active for multi-document chat"""
    rag = get_document_rag()
    if not rag:
        return jsonify({"error": "RAG module not available"}), 503
    
    try:
        data = request.json
        doc_ids = data.get('doc_ids', [])
        
        if not doc_ids:
            return jsonify({"error": "At least one document ID required"}), 400
        
        result = rag.set_active_documents(doc_ids)
        return jsonify({
            "status": "success",
            "message": f"Set {len(doc_ids)} document(s) as active",
            "active_documents": doc_ids
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/rag/clear-history', methods=['POST'])
@require_api_key
def rag_clear_conversation():
    """Clear RAG conversation history for fresh start"""
    rag = get_document_rag()
    if not rag:
        return jsonify({"error": "RAG module not available"}), 503
    
    try:
        result = rag.clear_conversation()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== BEAST-LEVEL FEATURES ====================

# --- MULTI-SOURCE MUSIC PLAYER ---
@app.route('/api/v1/music/play', methods=['POST'])
@require_api_key
def play_music():
    """Play music from YouTube, Spotify, or SoundCloud"""
    try:
        from Backend.MultiMusicPlayer import multi_music_player
        
        data = request.json
        query = data.get('query', '')
        source = data.get('source', 'auto')  # auto, youtube, spotify, soundcloud
        
        if not query:
            return jsonify({"error": "Query required"}), 400
        
        result = multi_music_player.play(query, source)
        
        if result.get("status") == "success":
            return jsonify({
                "status": "success",
                "type": "music",
                "response": result.get("message"),
                "music": result.get("music"),
                "platform": result.get("platform")
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/music/sources', methods=['GET'])
@require_api_key
def list_music_sources():
    """List available music sources"""
    try:
        from Backend.MultiMusicPlayer import multi_music_player
        sources = multi_music_player.get_available_sources()
        return jsonify({"status": "success", "sources": sources})
    except Exception as e:
        return jsonify({"sources": [
            {"id": "youtube", "name": "YouTube", "icon": "🎬"},
            {"id": "spotify", "name": "Spotify", "icon": "🎵"},
            {"id": "soundcloud", "name": "SoundCloud", "icon": "🔊"}
        ]})


# --- LIVE TV & RADIO STREAMS ---
@app.route('/api/v1/streams/radio', methods=['GET'])
@require_api_key
def list_radio_stations():
    """List available radio stations"""
    try:
        from Backend.LiveStreamPlayer import live_stream_player
        genre = request.args.get('genre')
        stations = live_stream_player.get_radio_stations(genre)
        return jsonify({"status": "success", "stations": stations})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/streams/tv', methods=['GET'])
@require_api_key
def list_tv_channels():
    """List available TV channels"""
    try:
        from Backend.LiveStreamPlayer import live_stream_player
        genre = request.args.get('genre')
        channels = live_stream_player.get_tv_channels(genre)
        return jsonify({"status": "success", "channels": channels})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/streams/play', methods=['POST'])
@require_api_key
def play_stream():
    """Play a radio station or TV channel"""
    try:
        from Backend.LiveStreamPlayer import live_stream_player
        
        data = request.json
        station_id = data.get('station_id')
        query = data.get('query')
        
        if station_id:
            result = live_stream_player.play_station(station_id)
        elif query:
            result = live_stream_player.play_by_query(query)
        else:
            return jsonify({"error": "station_id or query required"}), 400
        
        if result.get("status") == "success":
            return jsonify({
                "status": "success",
                "type": "stream",
                "response": result.get("message"),
                "music": result.get("music"),
                "stream_type": result.get("stream_type")
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/streams/genres', methods=['GET'])
@require_api_key
def list_stream_genres():
    """List available stream genres"""
    try:
        from Backend.LiveStreamPlayer import live_stream_player
        genres = live_stream_player.get_genres()
        return jsonify({"status": "success", "genres": genres})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- AI CODE GENERATOR ---
@app.route('/api/v1/code/generate', methods=['POST'])
@require_api_key
def generate_code():
    """Generate code from natural language prompt"""
    try:
        from Backend.CodeExecutor import code_executor
        
        data = request.json
        prompt = data.get('prompt', '')
        language = data.get('language', 'python')
        
        if not prompt:
            return jsonify({"error": "Prompt required"}), 400
        
        result = code_executor.generate_code(prompt, language)
        
        return jsonify({
            "status": result.get("status"),
            "type": "code_generation",
            "code": result.get("code"),
            "language": language,
            "explanation": result.get("explanation"),
            "error": result.get("error")
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/code/execute', methods=['POST'])
@require_api_key
def execute_code():
    """Execute Python code safely"""
    try:
        from Backend.CodeExecutor import code_executor
        
        data = request.json
        code = data.get('code', '')
        language = data.get('language', 'python')
        
        if not code:
            return jsonify({"error": "Code required"}), 400
        
        result = code_executor.execute(code, language)
        
        return jsonify({
            "status": result.get("status"),
            "type": "code_execution",
            "output": result.get("output"),
            "error": result.get("error"),
            "execution_time": result.get("execution_time"),
            "variables": result.get("variables", {})
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/code/generate-and-run', methods=['POST'])
@require_api_key
def generate_and_execute_code():
    """Generate code from prompt AND execute it"""
    try:
        from Backend.CodeExecutor import code_executor
        
        data = request.json
        prompt = data.get('prompt', '')
        language = data.get('language', 'python')
        
        if not prompt:
            return jsonify({"error": "Prompt required"}), 400
        
        result = code_executor.generate_and_execute(prompt, language)
        
        return jsonify({
            "status": result.get("status"),
            "type": "code_execution",
            "response": result.get("message"),
            "code": result.get("code"),
            "output": result.get("output"),
            "error": result.get("error"),
            "execution_time": result.get("execution_time"),
            "explanation": result.get("explanation")
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- YOUTUBE VIDEO SUMMARIZER ---
@app.route('/api/v1/video/summarize', methods=['POST'])
@require_api_key
def summarize_video():
    """Summarize a YouTube video"""
    try:
        from Backend.VideoSummarizer import video_summarizer
        
        data = request.json
        url = data.get('url', '')
        
        if not url:
            return jsonify({"error": "YouTube URL required"}), 400
        
        result = video_summarizer.summarize(url)
        
        if result.get("status") == "success":
            return jsonify({
                "status": "success",
                "type": "video_summary",
                "response": result.get("message"),
                "title": result.get("title"),
                "thumbnail": result.get("thumbnail"),
                "summary": result.get("summary"),
                "key_points": result.get("key_points"),
                "target_audience": result.get("target_audience"),
                "duration": result.get("duration"),
                "url": result.get("url"),
                "embed_url": result.get("embed_url")
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/video/transcript', methods=['POST'])
@require_api_key
def get_video_transcript():
    """Get transcript of a YouTube video"""
    try:
        from Backend.VideoSummarizer import video_summarizer
        
        data = request.json
        url = data.get('url', '')
        
        if not url:
            return jsonify({"error": "YouTube URL required"}), 400
        
        result = video_summarizer.get_transcript_only(url)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- WEBSITE CAPTURE (PDF & SCREENSHOT) ---
@app.route('/api/v1/capture/pdf', methods=['POST'])
@require_api_key
def capture_url_as_pdf():
    """Capture a website as a PDF with preview thumbnail"""
    try:
        from Backend.WebsiteCapture import website_capture
        
        data = request.json
        url = data.get('url', '')
        
        if not url:
            return jsonify({"error": "URL required"}), 400
        
        result = website_capture.url_to_pdf(url)
        
        if result.get("status") == "success":
            return jsonify({
                "status": "success",
                "type": "pdf_capture",
                "response": result.get("message"),
                "title": result.get("title"),
                "pdf_url": result.get("pdf_url"),
                "thumbnail_url": result.get("thumbnail_url"),
                "url": result.get("url"),
                "page_count": result.get("page_count", 1)
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/capture/screenshot', methods=['POST'])
@require_api_key
def capture_url_as_screenshot():
    """Take a screenshot of a website"""
    try:
        from Backend.WebsiteCapture import website_capture
        
        data = request.json
        url = data.get('url', '')
        full_page = data.get('full_page', True)
        
        if not url:
            return jsonify({"error": "URL required"}), 400
        
        result = website_capture.url_to_screenshot(url, full_page)
        
        if result.get("status") == "success":
            return jsonify({
                "status": "success",
                "type": "screenshot",
                "response": result.get("message"),
                "screenshot_url": result.get("screenshot_url"),
                "url": result.get("url")
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== END BEAST-LEVEL FEATURES ====================

# --- FILE UPLOAD & ANALYSIS ---
@app.route('/api/v1/files/upload', methods=['POST'])
@require_api_key
def upload_file():
    """Upload and analyze a file"""
    if not file_analyzer:
        return jsonify({"error": "File Analyzer not loaded"}), 503
    
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Save file
        file_data = file.read()
        filepath = file_analyzer.save_upload(file_data, file.filename)
        
        # Analyze file
        analysis = file_analyzer.analyze_file(filepath)
        
        # Get AI analysis text
        ai_analysis = analysis.get("ai_analysis") or analysis.get("analysis", "File analyzed successfully")
        
        return jsonify({
            "status": "success",
            "message": "File uploaded and analyzed",
            "filename": os.path.basename(filepath),
            "filepath": filepath,
            "url": f"/data/Uploads/{os.path.basename(filepath)}",
            "analysis": analysis,
            "ai_summary": ai_analysis
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- VISION API (Groq Llama 3.2 Vision) ---
@app.route('/api/v1/vision/analyze', methods=['POST'])
@require_api_key
def vision_analyze():
    """Analyze an image with AI vision - describe, OCR, or answer questions"""
    try:
        from Backend.VisionService import get_vision_service
        vision = get_vision_service()
        
        data = request.json
        image_url = data.get('image_url', '')
        prompt = data.get('prompt', 'Describe this image in detail.')
        
        if not image_url:
            return jsonify({"error": "image_url required"}), 400
        
        result = vision.analyze(image_url, prompt)
        
        if result.get("success"):
            return jsonify({
                "status": "success",
                "type": "vision_analysis",
                "description": result.get("description"),
                "model": result.get("model"),
                "tokens_used": result.get("tokens_used", 0)
            })
        else:
            return jsonify({"error": result.get("error", "Analysis failed")}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/vision/describe', methods=['POST'])
@require_api_key  
def vision_describe():
    """Get a detailed description of an image"""
    try:
        from Backend.VisionService import get_vision_service
        vision = get_vision_service()
        
        data = request.json
        image_url = data.get('image_url', '')
        
        if not image_url:
            return jsonify({"error": "image_url required"}), 400
        
        description = vision.describe(image_url)
        
        return jsonify({
            "status": "success",
            "type": "vision_description",
            "description": description
        })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/vision/ocr', methods=['POST'])
@require_api_key
def vision_ocr():
    """Extract text from an image (OCR)"""
    try:
        from Backend.VisionService import get_vision_service
        vision = get_vision_service()
        
        data = request.json
        image_url = data.get('image_url', '')
        
        if not image_url:
            return jsonify({"error": "image_url required"}), 400
        
        text = vision.extract_text(image_url)
        
        return jsonify({
            "status": "success",
            "type": "ocr",
            "extracted_text": text
        })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/vision/ask', methods=['POST'])
@require_api_key
def vision_ask():
    """Answer a question about an image"""
    try:
        from Backend.VisionService import get_vision_service
        vision = get_vision_service()
        
        data = request.json
        image_url = data.get('image_url', '')
        question = data.get('question', '')
        
        if not image_url:
            return jsonify({"error": "image_url required"}), 400
        if not question:
            return jsonify({"error": "question required"}), 400
        
        answer = vision.answer_question(image_url, question)
        
        return jsonify({
            "status": "success",
            "type": "visual_qa",
            "question": question,
            "answer": answer
        })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/files/analyze', methods=['POST'])
@require_api_key
def analyze_uploaded_file():
    """Analyze a previously uploaded file"""
    if not file_analyzer:
        return jsonify({"error": "File Analyzer not loaded"}), 503
    
    try:
        data = request.json
        filename = data.get('filename', '')
        
        if not filename:
            return jsonify({"error": "Filename required"}), 400
        
        filepath = os.path.join(file_analyzer.upload_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404
        
        analysis = file_analyzer.analyze_file(filepath)
        
        # Show full AI analysis
        if analysis.get("status") == "success":
            ai_analysis = analysis.get("ai_analysis", "No analysis available")
        else:
            ai_analysis = "Analysis failed"
        
        return jsonify({
            "status": "success",
            "analysis": analysis
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/files/list', methods=['GET'])
@require_api_key
def list_uploaded_files():
    """List uploaded files"""
    if not file_analyzer:
        return jsonify({"error": "File Analyzer not loaded"}), 503
    
    try:
        limit = int(request.args.get('limit', 20))
        files = file_analyzer.list_uploads(limit)
        
        return jsonify({
            "status": "success",
            "count": len(files),
            "files": files
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/files/delete', methods=['DELETE'])
@require_api_key
def delete_uploaded_file():
    """Delete an uploaded file"""
    if not file_analyzer:
        return jsonify({"error": "File Analyzer not loaded"}), 503
    
    try:
        data = request.json
        filename = data.get('filename', '')
        
        if not filename:
            return jsonify({"error": "Filename required"}), 400
        
        success = file_analyzer.delete_upload(filename)
        
        if success:
            return jsonify({
                "status": "success",
                "message": f"File {filename} deleted"
            })
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ENHANCED AUTOMATION ---
@app.route('/api/v1/automation/execute', methods=['POST'])
@require_api_key
def execute_automation():
    """Execute system automation command"""
    if not enhanced_automation:
        return jsonify({"error": "Enhanced Automation not loaded"}), 503
    
    try:
        data = request.json
        command = data.get('command', '')
        
        if not command:
            return jsonify({"error": "Command required"}), 400
        
        result = enhanced_automation.execute_command(command)
        
        return jsonify({
            "status": "success",
            "result": result
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/automation/screenshot', methods=['POST'])
@require_api_key
def take_screenshot():
    """Take a screenshot"""
    if not enhanced_automation:
        return jsonify({"error": "Enhanced Automation not loaded"}), 503
    
    try:
        filepath = enhanced_automation.take_screenshot()
        filename = os.path.basename(filepath)
        
        return jsonify({
            "status": "success",
            "message": "Screenshot captured",
            "filepath": filepath,
            "url": f"/data/Screenshots/{filename}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/automation/battery', methods=['GET'])
@require_api_key
def get_battery_status():
    """Get battery status"""
    if not enhanced_automation:
        return jsonify({"error": "Enhanced Automation not loaded"}), 503
    
    try:
        status = enhanced_automation.get_battery_status()
        
        return jsonify({
            "status": "success",
            "battery": status
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== DATABASE & CONVERSATION HISTORY ====================

@app.route('/api/v1/conversations', methods=['GET', 'POST', 'DELETE'])
@require_api_key
def conversations():
    """Get all conversations, create new one, or bulk delete"""
    if not chat_history:
        return jsonify({"error": "Chat history not available"}), 503
    
    try:
        user_id = get_user_id(request)
        
        if request.method == 'GET':
            limit = int(request.args.get('limit', 50))
            convs = chat_history.get_conversations(user_id, limit)
            return jsonify({"status": "success", "conversations": convs})
        
        elif request.method == 'POST':
            data = request.json
            title = data.get('title', 'New Conversation')
            conv_id = chat_history.create_conversation(user_id, title)
            return jsonify({"status": "success", "conversation_id": conv_id})

        elif request.method == 'DELETE':
            # Bulk Delete
            success = chat_history.delete_all_conversations(user_id)
            if success:
                 return jsonify({"status": "success", "message": "All conversations deleted"})
            else:
                 return jsonify({"error": "Bulk delete failed"}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/conversations/<conversation_id>', methods=['GET', 'PUT', 'DELETE'])
@require_api_key
def conversation_detail(conversation_id):
    """Get, update, or delete a specific conversation"""
    if not chat_history:
        return jsonify({"error": "Chat history not available"}), 503
    
    try:
        user_id = get_user_id(request)
        
        if request.method == 'GET':
            conv = chat_history.get_conversation(user_id, conversation_id)
            if not conv:
                return jsonify({"error": "Conversation not found"}), 404
            return jsonify({"status": "success", "conversation": conv})
        
        elif request.method == 'PUT':
            data = request.json
            title = data.get('title')
            chat_history.update_conversation_title(user_id, conversation_id, title)
            return jsonify({"status": "success", "message": "Conversation updated"})
        
        elif request.method == 'DELETE':
            success = chat_history.delete_conversation(user_id, conversation_id)
            if success:
                return jsonify({"status": "success", "message": "Conversation deleted"})
            else:
                return jsonify({"error": "Delete failed"}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/conversations/<conversation_id>/messages', methods=['POST'])
@require_api_key
def add_message_legacy(conversation_id):
    """Add a message to a conversation"""
    if not chat_history:
        return jsonify({"error": "Chat history not available"}), 503
    
    try:
        user_id = get_user_id(request)
        data = request.json
        role = data.get('role', 'user')
        content = data.get('content', '')
        metadata = data.get('metadata')
        
        success = chat_history.add_message(user_id, conversation_id, role, content, metadata)
        if success:
             return jsonify({"status": "success", "message_id": "firebase_id"})
        else:
             return jsonify({"error": "Failed to add message"}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/conversations/search', methods=['GET'])
@require_api_key
def search_conversations():
    """Search messages"""
    if not db:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        query = request.args.get('q', '')
        workspace = request.args.get('workspace', 'default')
        limit = int(request.args.get('limit', 20))
        
        results = db.search_messages(query, workspace, limit)
        return jsonify({"status": "success", "results": results})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/preferences', methods=['GET', 'POST'])
@require_api_key
def preferences():
    """Get or set user preferences"""
    if not db:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        if request.method == 'GET':
            key = request.args.get('key')
            
            if key:
                value = db.get_preference(key)
                return jsonify({"status": "success", "key": key, "value": value})
            else:
                all_prefs = db.get_all_preferences()
                return jsonify({"status": "success", "preferences": all_prefs})
        
        elif request.method == 'POST':
            data = request.json
            key = data.get('key')
            value = data.get('value')
            
            if not key:
                return jsonify({"error": "Key required"}), 400
            
            db.set_preference(key, value)
            return jsonify({"status": "success", "message": "Preference saved"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/files/history', methods=['GET'])
@require_api_key
def file_history():
    """Get file upload history"""
    if not db:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        limit = int(request.args.get('limit', 50))
        files = db.get_file_uploads(limit)
        
        return jsonify({"status": "success", "files": files})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/analytics', methods=['GET'])
@require_api_key
def analytics():
    """Get analytics data"""
    if not db:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        days = int(request.args.get('days', 7))
        event_type = request.args.get('type')
        
        if event_type:
            events = db.get_analytics(event_type, days)
            return jsonify({"status": "success", "events": events})
        else:
            voices = voice_service.list_voices()
        return jsonify({"status": "success", "voices": voices}), 200
    except Exception as e:
        return jsonify({" error": str(e)}), 500


# ==================== ADVANCED AGENT ENDPOINTS ====================

@app.route('/api/v1/agents/tool-use', methods=['POST'])
@require_auth
@rate_limit("default")
def agent_tool_use():
    """Execute Tool-Using Agent for API calling and function execution."""
    try:
        data = request.json
        task = data.get('task')
        
        if not task:
            return jsonify({"error": "Task is required"}), 400
        
        from Backend.Agents.ToolUsingAgent import tool_using_agent
        result = tool_using_agent.execute(task, data.get('context'))
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/agents/browse', methods=['POST'])
@require_auth
@rate_limit("heavy")
def agent_web_browse():
    """Execute Web Browsing Agent for browser automation."""
    try:
        data = request.json
        task = data.get('task')
        
        if not task:
            return jsonify({"error": "Task is required"}), 400
        
        from Backend.Agents.WebBrowsingAgent import web_browsing_agent
        result = web_browsing_agent.execute(task, data.get('context'))
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/agents/analyze-doc', methods=['POST'])
@require_auth
@rate_limit("default")
def agent_analyze_document():
    """Execute Document Analysis Agent for PDF/DOCX analysis."""
    try:
        data = request.json
        task = data.get('task')
        file_path = data.get('file_path')
        analysis_type = data.get('analysis_type', 'full')
        
        if not task and not file_path:
            return jsonify({"error": "Task or file_path is required"}), 400
        
        from Backend.Agents.DocumentAnalysisAgent import document_analysis_agent
        
        context = {
            "file_path": file_path,
            "analysis_type": analysis_type
        }
        if data.get('question'):
            context['question'] = data['question']
        if data.get('file_path2'):
            context['file_path2'] = data['file_path2']
        
        result = document_analysis_agent.execute(task or f"Analyze {file_path}", context)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/agents/multimodal', methods=['POST'])
@require_auth
@rate_limit("default")
def agent_multimodal():
    """Execute Multi-modal Agent for image + text reasoning."""
    try:
        data = request.json
        task = data.get('task')
        images = data.get('images', [])
        
        if not task:
            return jsonify({"error": "Task is required"}), 400
        if not images:
            return jsonify({"error": "At least one image is required"}), 400
        
        from Backend.Agents.MultiModalAgent import multimodal_agent
        
        context = {"images": images}
        result = multimodal_agent.execute(task, context)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== ENHANCED DEBATE ARENA ENDPOINTS ====================

@app.route('/api/v1/debate/start', methods=['POST'])
@require_auth
@rate_limit("default")
def debate_start():
    """Start a new AI debate."""
    try:
        data = request.json
        topic = data.get('topic')
        rounds = data.get('rounds', 3)
        debate_format = data.get('format', 'standard')
        participants = data.get('participants')
        
        if not topic:
            return jsonify({"error": "Topic is required"}), 400
        
        from Backend.DebateArena import debate_arena
        
        # Set format if specified
        if debate_format:
            debate_arena.set_debate_format(debate_format)
        
        # Multi-participant or standard debate
        if participants and len(participants) >= 3:
            result = debate_arena.multi_participant_debate(topic, participants, rounds)
        else:
            result = debate_arena.start_debate(topic, rounds, participants)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/debate/formats', methods=['GET'])
def debate_formats():
    """Get available debate formats."""
    try:
        from Backend.DebateArena import AIDebateArena
        formats = list(AIDebateArena.DEBATE_FORMATS.keys())
        
        return jsonify({
            "status": "success",
            "formats": formats,
            "details": AIDebateArena.DEBATE_FORMATS
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/debate/templates', methods=['GET'])
def debate_templates():
    """Get debate topic templates."""
    try:
        from Backend.DebateArena import debate_arena
        templates = debate_arena.get_debate_templates()
        
        return jsonify({
            "status": "success",
            "templates": templates
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== ENHANCED PERSONALITY CLONE ENDPOINTS ====================

@app.route('/api/v1/personality-clone/create', methods=['POST'])
@require_auth
@rate_limit("default")
def personality_clone_create():
    """Create a personality clone from messages."""
    try:
        user = get_current_user()
        data = request.json
        messages = data.get('messages', [])
        user_id = data.get('clone_user_id', user['user_id'])
        
        if not messages:
            return jsonify({"error": "Messages array is required"}), 400
        
        from Backend.PersonalityClone import personality_clone
        result = personality_clone.analyze_messages(messages, user_id)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/personality-clone/upload-file', methods=['POST'])
@require_auth
@rate_limit("default")
def personality_clone_upload():
    """Create a personality clone from uploaded file."""
    try:
        user = get_current_user()
        
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if not file.filename:
            return jsonify({"error": "Empty filename"}), 400
        
        # Save temporarily
        temp_dir = os.path.join(current_dir, 'temp_uploads')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{int(time.time())}_{file.filename}")
        file.save(temp_path)
        
        # Analyze file
        from Backend.PersonalityClone import personality_clone
        user_id = request.form.get('clone_user_id', user['user_id'])
        format_type = request.form.get('format_type', 'auto')
        
        result = personality_clone.analyze_file(temp_path, format_type, user_id)
        
        # Cleanup
        try:
            os.remove(temp_path)
        except:
            pass
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/personality-clone/chat', methods=['POST'])
@require_auth
@rate_limit("chat")
def personality_clone_chat():
    """Chat with a personality clone."""
    try:
        data = request.json
        user_id = data.get('clone_user_id')
        message = data.get('message')
        
        if not user_id or not message:
            return jsonify({"error": "clone_user_id and message are required"}), 400
        
        from Backend.PersonalityClone import personality_clone
        response = personality_clone.chat_as_clone(user_id, message)
        
        return jsonify({
            "status": "success",
            "response": response
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/personality-clone/style-transfer', methods=['POST'])
@require_auth
@rate_limit("default")
def personality_clone_style_transfer():
    """Rewrite text in a user's style."""
    try:
        data = request.json
        user_id = data.get('clone_user_id')
        text = data.get('text')
        
        if not user_id or not text:
            return jsonify({"error": "clone_user_id and text are required"}), 400
        
        from Backend.PersonalityClone import personality_clone
        result = personality_clone.style_transfer(text, user_id)
        
        return jsonify({
            "status": "success",
            "original": text,
            "styled": result
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/personality-clone/insights', methods=['GET'])
@require_auth
@rate_limit("default")
def personality_clone_insights():
    """Get writing insights for a clone."""
    try:
        user_id = request.args.get('clone_user_id')
        
        if not user_id:
            return jsonify({"error": "clone_user_id parameter is required"}), 400
        
        from Backend.PersonalityClone import personality_clone
        result = personality_clone.get_writing_insights(user_id)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== ENHANCED JOB INTERVIEWER ENDPOINTS ====================

@app.route('/api/v1/interview/start', methods=['POST'])
@require_auth
@rate_limit("default")
def interview_start():
    """Start a job interview session."""
    try:
        user = get_current_user()
        data = request.json
        job_role = data.get('job_role')
        company = data.get('company', 'a top company')
        experience_level = data.get('experience_level', 'mid')
        difficulty = data.get('difficulty', 'medium')
        industry = data.get('industry')
        
        if not job_role:
            return jsonify({"error": "job_role is required"}), 400
        
        from Backend.JobInterviewer import job_interviewer
        result = job_interviewer.start_interview(
            job_role, company, experience_level, difficulty, industry, user['user_id']
        )
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/interview/answer', methods=['POST'])
@require_auth
@rate_limit("default")
def interview_answer():
    """Submit an answer to the current interview question."""
    try:
        user = get_current_user()
        data = request.json
        answer = data.get('answer')
        
        if not answer:
            return jsonify({"error": "answer is required"}), 400
        
        from Backend.JobInterviewer import job_interviewer
        result = job_interviewer.answer_question(answer, user['user_id'])
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/interview/hint', methods=['GET'])
@require_auth
@rate_limit("default")
def interview_hint():
    """Get a hint for the current question."""
    try:
        user = get_current_user()
        
        from Backend.JobInterviewer import job_interviewer
        result = job_interviewer.get_hint(user['user_id'])
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/interview/templates', methods=['GET'])
def interview_templates():
    """Get industry-specific interview templates."""
    try:
        from Backend.JobInterviewer import job_interviewer
        templates = job_interviewer.get_industry_templates()
        
        return jsonify({
            "status": "success",
            "templates": templates
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/interview/analytics', methods=['GET'])
@require_auth
@rate_limit("default")
def interview_analytics():
    """Get performance analytics for a user."""
    try:
        user = get_current_user()
        
        from Backend.JobInterviewer import job_interviewer
        result = job_interviewer.get_analytics(user['user_id'])
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== UNIFIED AGENT CHAT ENDPOINT ====================
# Smart routing to advanced agents based on message content

@app.route('/api/v1/agent-chat', methods=['POST'])
@require_auth
@rate_limit("chat")
def agent_chat():
    """
    Unified chat endpoint that intelligently routes to advanced agents.
    NOW INCLUDES: @command detection for quick actions (@news, @weather, @crypto, @github)!
    """
    try:
        data = request.json
        message = data.get('message', '').lower()
        original_message = data.get('message', '')
        
        if not original_message:
            return jsonify({"error": "Message is required"}), 400
        
        user = get_current_user()
        
        # ===== FIRST: Check for quick action commands =====
        # This prevents LLM from handling @news, @weather, @crypto, @github
        try:
            from Backend.QuickActionsHandler import quick_actions_handler
            quick_result = quick_actions_handler.process_message(original_message)
            
            if quick_result:
                # Quick action was successfully handled!
                return jsonify(quick_result), 200
        except Exception as e:
            logger.error(f"[AGENT-CHAT] Quick actions handler error: {e}")
            import traceback
            traceback.print_exc()
        # =================================================
        
        # If no quick action detected, proceed with regular agent detection
        
        # Detection keywords
        calc_keywords = ['calculate', 'compute', '×', '*', '+', '-', '/', 'math', 'multiply']
        browse_keywords = ['browse', 'navigate', 'go to', 'visit', 'screenshot', 'extract from']
        doc_keywords = ['analyze document', 'analyze this pdf', 'analyze this docx', 'read document', 'summarize pdf']
        image_keywords = ['analyze image', "what's in this image", 'describe image', 'compare images']
        debate_keywords = ['start a debate', 'debate:', 'create debate', 'debate about', 'debate on']
        interview_keywords = ['start interview', 'mock interview', 'job interview', 'interview for']
        clone_keywords = ['personality clone', 'create clone', 'chat as clone', 'my writing style']
        
        # Route to appropriate agent
        
        # 1. Calculator/Tool Use
        if any(kw in message for kw in calc_keywords):
            from Backend.Agents.ToolUsingAgent import tool_using_agent
            result = tool_using_agent.execute(original_message, {})
            
            # Format calculator output nicely
            if isinstance(result, dict):
                if 'result' in result and 'formatted' in result:
                    response = f"**🔢 Calculation Result**\n\n```\n{result['formatted']}\n```\n\n**Answer:** `{result['result']}`"
                elif result.get('status') == 'success':
                    response = f"**✅ Result:** {result.get('output', result.get('result', str(result)))}"
                else:
                    response = result.get('output', result.get('result', str(result)))
            else:
                response = str(result)
            
            return jsonify({
                "status": "success",
                "agent": "tool_using",
                "response": response
            }), 200
        
        # 2. Web Browsing
        elif any(kw in message for kw in browse_keywords):
            from Backend.Agents.WebBrowsingAgent import web_browsing_agent
            result = web_browsing_agent.execute(original_message, {})
            return jsonify({
                "status": "success",
                "agent": "web_browsing",
                "response": result.get('output', result.get('result', str(result)))
            }), 200
        
        # 3. Document Analysis
        elif any(kw in message for kw in doc_keywords) or '.pdf' in message or '.docx' in message:
            from Backend.Agents.DocumentAnalysisAgent import document_analysis_agent
            
            # Try to extract file path
            import re
            file_match = re.search(r'[C-Z]:[\\\/][^\s]+\.(?:pdf|docx)', original_message, re.IGNORECASE)
            file_path = file_match.group(0) if file_match else None
            
            if not file_path:
                return jsonify({
                    "status": "error",
                    "message": "Please provide a file path (e.g., C:/path/to/document.pdf)"
                }), 400
            
            context = {"file_path": file_path, "analysis_type": "full"}
            result = document_analysis_agent.execute(original_message, context)
            return jsonify({
                "status": "success",
                "agent": "doc_analysis",
                "response": result.get('output', result.get('result', str(result)))
            }), 200
        
        # 4. Multi-modal (Image Analysis)
        elif any(kw in message for kw in image_keywords) or '.png' in message or '.jpg' in message:
            from Backend.Agents.MultiModalAgent import multimodal_agent
            
            # Extract image paths
            import re
            image_matches = re.findall(r'[C-Z]:[\\\/][^\s]+\.(?:png|jpg|jpeg|gif|bmp)', original_message, re.IGNORECASE)
            
            if not image_matches:
                return jsonify({
                    "status": "error",
                    "message": "Please provide image path(s) (e.g., C:/path/to/image.png)"
                }), 400
            
            context = {"images": image_matches}
            result = multimodal_agent.execute(original_message, context)
            return jsonify({
                "status": "success",
                "agent": "multimodal",
                "response": result.get('output', result.get('result', str(result)))
            }), 200
        
        # 5. Debate Arena
        elif any(kw in message for kw in debate_keywords):
            from Backend.DebateArena import debate_arena
            
            # Extract topic
            topic = original_message
            for kw in debate_keywords:
                topic = topic.replace(kw, '').strip()
            topic = topic.lstrip(':').strip()
            
            result = debate_arena.start_debate(topic, rounds=2)
            
            if result.get('status') == 'success':
                # Format debate output (removed emoji to fix Windows error)
                output = f"**DEBATE: {topic}**\n\n"
                for exchange in result.get('debate_log', []):
                    side_emoji = "🔵" if exchange['side'] == "PRO" else "🔴"
                    output += f"**Round {exchange['round']} - {side_emoji} {exchange['side']}:**\n{exchange['argument']}\n\n"
                
                verdict = result.get('verdict', {})
                output += f"\n**VERDICT:** {verdict.get('winner', 'TIE')}\n{verdict.get('analysis', '')}"
                
                return jsonify({
                    "status": "success",
                    "agent": "debate",
                    "response": output
                }), 200
            else:
                return jsonify(result), 200
        
        # 6. Job Interview
        elif any(kw in message for kw in interview_keywords):
            from Backend.JobInterviewer import job_interviewer
            
            # Extract job role
            import re
            role_match = re.search(r'(?:for|as)\s+([A-Z][a-z\s]+(?:Engineer|Developer|Manager|Scientist|Analyst))', original_message)
            job_role = role_match.group(1) if role_match else "Software Engineer"
            
            result = job_interviewer.start_interview(job_role, user_id=user['user_id'])
            
            if result.get('status') == 'success':
                output = f"**INTERVIEW STARTED: {job_role}**\n\n"
                output += f"**Question 1:**\n{result['question']}\n\n"
                output += "_Type your answer to continue the interview._"
                
                return jsonify({
                    "status": "success",
                    "agent": "interview",
                    "response": output
                }), 200
            else:
                return jsonify(result), 200
        
        # 7. Personality Clone
        elif any(kw in message for kw in clone_keywords):
            return jsonify({
                "status": "info",
                "agent": "personality_clone",
                "response": "To create a personality clone, use:\n• `Create clone from: [your messages]`\n• Or upload a file via the file upload endpoint"
            }), 200
        
        # Default: No specialized agent needed
        else:
            return jsonify({
                "status": "info",
                "message": "No specialized agent detected. Use specific keywords like 'calculate', 'browse', 'debate', 'interview', etc."
            }), 200
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ==================== REAL WEATHER & CRYPTO APIS ====================

@app.route('/api/v1/weather', methods=['GET'])
def get_weather_api():
    """Get real-time weather data from OpenWeatherMap."""
    try:
        from Backend.WeatherService import weather_service
        
        city = request.args.get('city', 'London')
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        result = weather_service.get_weather(city=city, lat=lat, lon=lon)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/v1/weather/forecast', methods=['GET'])
def get_forecast_api():
    """Get weather forecast for upcoming days."""
    try:
        from Backend.WeatherService import weather_service
        
        city = request.args.get('city', 'London')
        days = request.args.get('days', 5, type=int)
        
        result = weather_service.get_forecast(city=city, days=min(days, 5))
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/v1/crypto/prices', methods=['GET'])
def get_crypto_prices_api():
    """Get real-time cryptocurrency prices from CoinGecko."""
    try:
        from Backend.CryptoService import crypto_service
        
        # Get comma-separated coin IDs or default to top 10
        coins_param = request.args.get('coins')
        coins = coins_param.split(',') if coins_param else None
        vs_currency = request.args.get('currency', 'usd')
        
        result = crypto_service.get_prices(coins=coins, vs_currency=vs_currency)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/v1/crypto/details/<coin_id>', methods=['GET'])
def get_crypto_details_api(coin_id):
    """Get detailed information about a specific cryptocurrency."""
    try:
        from Backend.CryptoService import crypto_service
        
        result = crypto_service.get_coin_details(coin_id)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/v1/crypto/search', methods=['GET'])
def search_crypto_api():
    """Search for cryptocurrencies."""
    try:
        from Backend.CryptoService import crypto_service
        
        query = request.args.get('q', '')
        if not query:
            return jsonify({"status": "error", "message": "Query parameter 'q' required"}), 400
        
        result = crypto_service.search_coins(query)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/v1/news', methods=['GET'])
def get_news_api():
    """Get real-time news headlines from NewsAPI."""
    try:
        from Backend.NewsService import news_service
        
        category = request.args.get('category')  # tech, business, sports, etc.
        country = request.args.get('country', 'us')
        page_size = request.args.get('page_size', 10, type=int)
        
        result = news_service.get_top_headlines(
            category=category,
            country=country,
            page_size=page_size
        )
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/v1/news/search', methods=['GET'])
def search_news_api():
    """Search news articles."""
    try:
        from Backend.NewsService import news_service
        
        query = request.args.get('q', '')
        if not query:
            return jsonify({"status": "error", "message": "Query parameter 'q' required"}), 400
        
        page_size = request.args.get('page_size', 10, type=int)
        
        result = news_service.search_news(query, page_size=page_size)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/v1/github/repos/<username>', methods=['GET'])
def get_github_repos_api(username):
    """Get GitHub user's repositories."""
    try:
        from Backend.GitHubService import github_service
        
        sort = request.args.get('sort', 'updated')
        per_page = request.args.get('per_page', 10, type=int)
        
        result = github_service.get_user_repos(
            username=username,
            sort=sort,
            per_page=per_page
        )
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/v1/github/trending', methods=['GET'])
def get_github_trending_api():
    """Get trending GitHub repositories."""
    try:
        from Backend.GitHubService import github_service
        
        language = request.args.get('language', '')
        
        result = github_service.get_trending_repos(language=language)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/v1/github/search', methods=['GET'])
def search_github_api():
    """Search GitHub repositories."""
    try:
        from Backend.GitHubService import github_service
        
        query = request.args.get('q', '')
        if not query:
            return jsonify({"status": "error", "message": "Query parameter 'q' required"}), 400
        
        per_page = request.args.get('per_page', 10, type=int)
        
        result = github_service.search_repos(query, per_page=per_page)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==================== LEGACY CODE LOADING ====================



@app.route('/api/v1/whatsapp/send', methods=['POST'])
@require_api_key
def whatsapp_send_message():
    """Send WhatsApp message"""
    if not whatsapp:
        return jsonify({"error": "WhatsApp Automation not loaded"}), 503
    
    try:
        data = request.json
        phone = data.get('phone')
        message = data.get('message')
        instant = data.get('instant', True)
        
        if not phone or not message:
            return jsonify({"error": "Phone and message required"}), 400
        
        result = whatsapp.send_message(phone, message, instant)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/whatsapp/send-group', methods=['POST'])
@require_api_key
def whatsapp_send_group():
    """Send message to WhatsApp group"""
    if not whatsapp:
        return jsonify({"error": "WhatsApp Automation not loaded"}), 503
    
    try:
        data = request.json
        group_name = data.get('group')
        message = data.get('message')
        
        if not group_name or not message:
            return jsonify({"error": "Group name and message required"}), 400
        
        result = whatsapp.send_message_to_group(group_name, message)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/whatsapp/call', methods=['POST'])
@require_api_key
def whatsapp_call():
    """Make WhatsApp call"""
    if not whatsapp:
        return jsonify({"error": "WhatsApp Automation not loaded"}), 503
    
    try:
        data = request.json
        phone = data.get('phone')
        
        if not phone:
            return jsonify({"error": "Phone required"}), 400
        
        result = whatsapp.make_call(phone)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/whatsapp/bulk-send', methods=['POST'])
@require_api_key
def whatsapp_bulk_send():
    """Send bulk messages"""
    if not whatsapp:
        return jsonify({"error": "WhatsApp Automation not loaded"}), 503
    
    try:
        data = request.json
        contacts = data.get('contacts', [])
        message = data.get('message')
        
        if not contacts or not message:
            return jsonify({"error": "Contacts list and message required"}), 400
        
        result = whatsapp.send_bulk_messages(contacts, message)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/whatsapp/status', methods=['GET'])
@require_api_key
def whatsapp_status():
    """Get WhatsApp automation status"""
    if not whatsapp:
        return jsonify({"error": "WhatsApp Automation not loaded"}), 503
    
    try:
        status = whatsapp.get_status()
        return jsonify(status)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== INSTAGRAM AUTOMATION ====================

@app.route('/api/v1/instagram/login', methods=['POST'])
@require_api_key
def instagram_login():
    """Login to Instagram"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        result = instagram.login(username, password)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/logout', methods=['POST'])
@require_api_key
def instagram_logout():
    """Logout from Instagram"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        result = instagram.logout()
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/messages', methods=['GET'])
@require_api_key
def instagram_get_messages():
    """Get Instagram direct messages"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        limit = request.args.get('limit', 20, type=int)
        result = instagram.get_direct_messages(limit)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/send-message', methods=['POST'])
@require_api_key
def instagram_send_message():
    """Send Instagram direct message"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        data = request.json
        username = data.get('username')
        message = data.get('message')
        
        if not username or not message:
            return jsonify({"error": "Username and message required"}), 400
        
        result = instagram.send_direct_message(username, message)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/notifications', methods=['GET'])
@require_api_key
def instagram_get_notifications():
    """Get Instagram notifications"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        result = instagram.get_notifications()
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/post-photo', methods=['POST'])
@require_api_key
def instagram_post_photo():
    """Post photo to Instagram feed"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        data = request.json
        image_path = data.get('image_path')
        caption = data.get('caption', '')
        
        if not image_path:
            return jsonify({"error": "Image path required"}), 400
        
        result = instagram.post_photo(image_path, caption)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/post-story', methods=['POST'])
@require_api_key
def instagram_post_story():
    """Post story to Instagram"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        data = request.json
        image_path = data.get('image_path')
        
        if not image_path:
            return jsonify({"error": "Image path required"}), 400
        
        result = instagram.post_story(image_path)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/user-info', methods=['GET'])
@require_api_key
def instagram_get_user_info():
    """Get Instagram user information"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        username = request.args.get('username')
        
        if not username:
            return jsonify({"error": "Username required"}), 400
        
        result = instagram.get_user_info(username)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/start-monitoring', methods=['POST'])
@require_api_key
def instagram_start_monitoring():
    """Start monitoring Instagram messages"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        data = request.json
        interval = data.get('interval', 30)
        
        result = instagram.start_monitoring(interval)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/stop-monitoring', methods=['POST'])
@require_api_key
def instagram_stop_monitoring():
    """Stop monitoring Instagram messages"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        result = instagram.stop_monitoring()
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/status', methods=['GET'])
@require_api_key
def instagram_status():
    """Get Instagram automation status"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        status = instagram.get_status()
        return jsonify(status)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/like-post', methods=['POST'])
@require_api_key
def instagram_like_post():
    """Like an Instagram post"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        data = request.json
        media_id = data.get('media_id')
        
        if not media_id:
            return jsonify({"error": "Media ID required"}), 400
        
        result = instagram.like_post(media_id)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/comment-post', methods=['POST'])
@require_api_key
def instagram_comment_post():
    """Comment on an Instagram post"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        data = request.json
        media_id = data.get('media_id')
        comment = data.get('comment')
        
        if not media_id or not comment:
            return jsonify({"error": "Media ID and comment required"}), 400
        
        result = instagram.comment_on_post(media_id, comment)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/follow', methods=['POST'])
@require_api_key
def instagram_follow():
    """Follow an Instagram user"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        data = request.json
        username = data.get('username')
        
        if not username:
            return jsonify({"error": "Username required"}), 400
        
        result = instagram.follow_user(username)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/unfollow', methods=['POST'])
@require_api_key
def instagram_unfollow():
    """Unfollow an Instagram user"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        data = request.json
        username = data.get('username')
        
        if not username:
            return jsonify({"error": "Username required"}), 400
        
        result = instagram.unfollow_user(username)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/followers', methods=['GET'])
@require_api_key
def instagram_get_followers():
    """Get Instagram followers list"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        username = request.args.get('username')
        limit = request.args.get('limit', 50, type=int)
        
        result = instagram.get_followers(username, limit)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/following', methods=['GET'])
@require_api_key
def instagram_get_following():
    """Get Instagram following list"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        username = request.args.get('username')
        limit = request.args.get('limit', 50, type=int)
        
        result = instagram.get_following(username, limit)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/search-users', methods=['POST'])
@require_api_key
def instagram_search_users():
    """Search Instagram users"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        data = request.json
        query = data.get('query')
        limit = data.get('limit', 20)
        
        if not query:
            return jsonify({"error": "Search query required"}), 400
        
        result = instagram.search_users(query, limit)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/user-posts', methods=['POST'])
@require_api_key
def instagram_get_user_posts():
    """Get user's Instagram posts"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        data = request.json
        username = data.get('username')
        limit = data.get('limit', 12)
        
        if not username:
            return jsonify({"error": "Username required"}), 400
        
        result = instagram.get_user_posts(username, limit)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/instagram/auto-reply', methods=['POST'])
@require_api_key
def instagram_auto_reply():
    """Set up Instagram auto-reply"""
    if not instagram:
        return jsonify({"error": "Instagram Automation not loaded"}), 503
    
    try:
        data = request.json
        keywords = data.get('keywords', {})
        enable = data.get('enable', True)
        
        result = instagram.auto_reply(keywords, enable)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== FILE SERVING ====================

@app.route('/data/<path:filename>')
def serve_data_file(filename):
    """Serve files from Data directory (images, videos, etc.)"""
    try:
        return send_from_directory(DATA_DIR, filename)
    except Exception as e:
        return jsonify({"error": f"File not found: {filename}"}), 404

@app.route('/data/Uploads/<path:filename>')
def serve_uploaded_file(filename):
    """Serve uploaded files (images, videos, documents)"""
    try:
        uploads_dir = os.path.join(DATA_DIR, "Uploads")
        return send_from_directory(uploads_dir, filename)
    except Exception as e:
        return jsonify({"error": f"File not found: {filename}"}), 404

# ==================== MULTI-AGENT SYSTEM ====================
# KAI's team of specialist AI agents working together

# Lazy load agent orchestrator
_agent_orchestrator = None

def get_orchestrator():
    """Lazy load the agent orchestrator."""
    global _agent_orchestrator
    if _agent_orchestrator is None:
        try:
            from Backend.Agents.AgentOrchestrator import agent_orchestrator
            _agent_orchestrator = agent_orchestrator
            print("[AGENTS] Multi-Agent System loaded")
        except Exception as e:
            print(f"[AGENTS] Failed to load: {e}")
    return _agent_orchestrator

@app.route('/api/v1/agents/execute', methods=['POST'])
def execute_multi_agent_task():
    """
    Execute a task using the multi-agent system.
    
    Body: {
        "task": "Research AI trends and write a summary",
        "mode": "auto" | "research" | "write" | "analyze" | "research_write" | "full"
    }
    """
    orchestrator = get_orchestrator()
    if not orchestrator:
        return jsonify({"error": "Multi-agent system not available"}), 500
    
    try:
        data = request.json
        task = data.get('task', '')
        mode = data.get('mode', 'auto')
        
        if not task:
            return jsonify({"error": "Task is required"}), 400
        
        print(f"[AGENTS] Executing: {task[:50]}... (mode: {mode})")
        
        # Execute the task
        from Backend.Agents.AgentOrchestrator import run_multi_agent_task
        result = run_multi_agent_task(task, mode)
        
        return jsonify({
            "status": result.get("status"),
            "task": result.get("task"),
            "mode": result.get("task_type"),
            "steps": result.get("steps_executed"),
            "result": result.get("final_output"),
            "agent_details": result.get("agent_results"),
            "execution_time": result.get("execution_time_seconds"),
            "timestamp": result.get("timestamp")
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/status', methods=['GET'])
def get_agents_status():
    """Get status of all agents and recent executions."""
    orchestrator = get_orchestrator()
    if not orchestrator:
        return jsonify({"error": "Multi-agent system not available"}), 500
    
    try:
        status = orchestrator.get_status()
        return jsonify({
            "status": "active",
            "agents": status.get("agents"),
            "total_executions": status.get("total_executions"),
            "recent": status.get("recent_executions")
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/research', methods=['POST'])
def agent_research():
    """Quick access to research agent."""
    orchestrator = get_orchestrator()
    if not orchestrator:
        return jsonify({"error": "Multi-agent system not available"}), 500
    
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        result = orchestrator.research(query)
        return jsonify({
            "status": result.get("status"),
            "result": result.get("final_output"),
            "sources": result.get("agent_results", [{}])[0].get("sources", [])
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/write', methods=['POST'])
def agent_write():
    """Quick access to writer agent."""
    orchestrator = get_orchestrator()
    if not orchestrator:
        return jsonify({"error": "Multi-agent system not available"}), 500
    
    try:
        data = request.json
        content_request = data.get('content', '') or data.get('request', '')
        
        if not content_request:
            return jsonify({"error": "Content request is required"}), 400
        
        result = orchestrator.write(content_request)
        return jsonify({
            "status": result.get("status"),
            "result": result.get("final_output"),
            "word_count": len(result.get("final_output", "").split())
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/analyze', methods=['POST'])
def agent_analyze():
    """Quick access to analyst agent."""
    orchestrator = get_orchestrator()
    if not orchestrator:
        return jsonify({"error": "Multi-agent system not available"}), 500
    
    try:
        data = request.json
        content = data.get('content', '')
        
        if not content:
            return jsonify({"error": "Content to analyze is required"}), 400
        
        result = orchestrator.analyze(content)
        return jsonify({
            "status": result.get("status"),
            "analysis": result.get("final_output")
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/agents/code', methods=['POST'])
def agent_code():
    """
    Access to coder agent for code writing, debugging, and execution.
    
    Body: {
        "task": "write python code to sort a list",
        "code": "optional code to run/debug",
        "action": "write" | "debug" | "explain" | "run"
    }
    """
    try:
        from Backend.Agents.CoderAgent import coder_agent
        
        data = request.json
        task = data.get('task', '')
        code = data.get('code', '')
        action = data.get('action', 'auto')
        
        if not task and not code:
            return jsonify({"error": "Task or code is required"}), 400
        
        print(f"[CODER] Action: {action}, Task: {(task or code)[:50]}...")
        
        context = {"code": code} if code else None
        
        if action == "run" and code:
            # Direct code execution
            result = coder_agent.run(code)
        elif action == "debug":
            result = coder_agent._debug_code(task, context)
        elif action == "explain":
            result = coder_agent._explain_code(task, context)
        else:
            # Auto or write
            result = coder_agent.execute(task or f"Debug this code: {code}", context)
        
        return jsonify({
            "status": result.get("status"),
            "task_type": result.get("task_type"),
            "result": result.get("output"),
            "code": result.get("code"),
            "execution_time": result.get("execution_time"),
            "error": result.get("error")
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ==================== MIND-BLOWING FEATURES ====================

# --- AI DEBATE ARENA ---
@app.route('/api/v1/debate', methods=['POST'])
def start_debate():
    """
    Start an AI debate on any topic.
    
    Body: {
        "topic": "Should AI be regulated?",
        "rounds": 3  // optional, default 3
    }
    """
    try:
        from Backend.DebateArena import debate_arena
        
        data = request.json
        topic = data.get('topic', '')
        rounds = data.get('rounds', 3)
        
        if not topic:
            return jsonify({"error": "Topic is required"}), 400
        
        print(f"[DEBATE] Starting: {topic}")
        result = debate_arena.start_debate(topic, rounds)
        
        return jsonify(result), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/debate/quick', methods=['POST'])
def quick_debate():
    """Quick 1-round debate summary."""
    try:
        from Backend.DebateArena import debate_arena
        
        data = request.json
        topic = data.get('topic', '')
        
        if not topic:
            return jsonify({"error": "Topic is required"}), 400
        
        result = debate_arena.quick_debate(topic)
        return jsonify({"status": "success", "debate": result}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- PERSONALITY CLONE ---
@app.route('/api/v1/clone/create', methods=['POST'])
def create_personality_clone():
    """
    Create a personality clone from messages.
    
    Body: {
        "messages": ["msg1", "msg2", ...],  // OR
        "text": "block of text to analyze",
        "user_id": "optional_id"
    }
    """
    try:
        from Backend.PersonalityClone import personality_clone
        
        data = request.json
        messages = data.get('messages', [])
        text = data.get('text', '')
        user_id = data.get('user_id', 'default')
        
        if text and not messages:
            result = personality_clone.create_clone_from_text(text, user_id)
        elif messages:
            result = personality_clone.analyze_messages(messages, user_id)
        else:
            return jsonify({"error": "Provide 'messages' array or 'text' block"}), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/clone/chat', methods=['POST'])
def chat_with_clone():
    """
    Chat with a personality clone.
    
    Body: {
        "message": "What do you think about...?",
        "user_id": "the_clone_id"
    }
    """
    try:
        from Backend.PersonalityClone import personality_clone
        
        data = request.json
        message = data.get('message', '')
        user_id = data.get('user_id', 'default')
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        response = personality_clone.chat_as_clone(user_id, message)
        return jsonify({"status": "success", "response": response}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/clone/profile/<user_id>', methods=['GET'])
def get_clone_profile(user_id):
    """Get a personality clone's profile."""
    try:
        from Backend.PersonalityClone import personality_clone
        
        profile = personality_clone.get_profile(user_id)
        if profile:
            return jsonify({"status": "success", "profile": profile}), 200
        else:
            return jsonify({"error": "Clone not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- AI JOB INTERVIEWER ---
@app.route('/api/v1/interview/start', methods=['POST'])
def start_interview_session():
    """
    Start a job interview session.
    
    Body: {
        "job_role": "Software Engineer",
        "company": "Google",  // optional
        "experience": "mid",  // junior/mid/senior
        "user_id": "optional"
    }
    """
    try:
        from Backend.JobInterviewer import job_interviewer
        
        data = request.json
        job_role = data.get('job_role', '')
        company = data.get('company', 'a top company')
        experience = data.get('experience', 'mid')
        user_id = data.get('user_id', 'default')
        
        if not job_role:
            return jsonify({"error": "job_role is required"}), 400
        
        result = job_interviewer.start_interview(job_role, company, experience, user_id)
        return jsonify(result), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/interview/answer', methods=['POST'])
def submit_interview_answer():
    """
    Submit an answer to the current interview question.
    
    Body: {
        "answer": "Your answer here...",
        "user_id": "optional"
    }
    """
    try:
        from Backend.JobInterviewer import job_interviewer
        
        data = request.json
        answer = data.get('answer', '')
        user_id = data.get('user_id', 'default')
        
        if not answer:
            return jsonify({"error": "Answer is required"}), 400
        
        result = job_interviewer.answer_question(answer, user_id)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/interview/question', methods=['POST'])
def get_practice_question():
    """Get a random practice interview question."""
    try:
        from Backend.JobInterviewer import job_interviewer
        
        data = request.json
        job_role = data.get('job_role', 'Software Engineer')
        
        result = job_interviewer.quick_question(job_role)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== ANIME STREAMING ====================
# 🎬 Watch anime directly with KAI

@app.route('/api/v1/anime/search', methods=['GET', 'POST'])
def search_anime_endpoint():
    """
    Search for anime.
    
    GET: /api/v1/anime/search?q=naruto
    POST: {"query": "naruto", "limit": 10}
    """
    try:
        from Backend.AnimeStreaming import anime_system
        
        if request.method == 'GET':
            query = request.args.get('q', '')
            limit = int(request.args.get('limit', 10))
        else:
            data = request.json
            query = data.get('query', '')
            limit = data.get('limit', 10)
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        result = anime_system.search_anime(query, limit)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/anime/watch', methods=['POST'])
def watch_anime_endpoint():
    """
    Get streaming links for an anime episode.
    
    Body: {
        "anime": "Demon Slayer",
        "episode": 1
    }
    """
    try:
        from Backend.AnimeStreaming import anime_system
        
        data = request.json
        anime_name = data.get('anime', '')
        episode = data.get('episode', 1)
        
        if not anime_name:
            return jsonify({"error": "Anime name is required"}), 400
        
        result = anime_system.watch_anime(anime_name, episode)
        return jsonify(result), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/anime/episodes/<anime_id>', methods=['GET'])
def get_anime_episodes(anime_id):
    """Get all episodes for an anime."""
    try:
        from Backend.AnimeStreaming import anime_system
        
        result = anime_system.get_episodes(anime_id)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/anime/stream/<episode_id>', methods=['GET'])
def get_stream_links(episode_id):
    """Get streaming links for a specific episode."""
    try:
        from Backend.AnimeStreaming import anime_system
        
        result = anime_system.get_streaming_links(episode_id)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/anime/info', methods=['GET', 'POST'])
def anime_info_endpoint():
    """
    Get detailed anime information.
    
    GET: /api/v1/anime/info?name=naruto
    POST: {"name": "naruto"}
    """
    try:
        from Backend.AnimeStreaming import anime_system
        
        if request.method == 'GET':
            name = request.args.get('name', '')
        else:
            data = request.json
            name = data.get('name', '')
        
        if not name:
            return jsonify({"error": "Anime name is required"}), 400
        
        result = anime_system.get_anime_info(name)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/anime/trending', methods=['GET'])
def anime_trending_endpoint():
    """Get trending anime."""
    try:
        from Backend.AnimeStreaming import anime_system
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('limit', 10))
        
        result = anime_system.get_trending(page, per_page)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/anime/seasonal', methods=['GET'])
def anime_seasonal_endpoint():
    """Get popular anime this season."""
    try:
        from Backend.AnimeStreaming import anime_system
        
        result = anime_system.get_popular_this_season()
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/anime/watchlist', methods=['GET', 'POST', 'DELETE'])
def anime_watchlist_endpoint():
    """
    Manage anime watchlist.
    
    GET: Get watchlist
    POST: Add to watchlist {"anime": "Naruto"}
    DELETE: Remove from watchlist {"anime": "Naruto"}
    """
    try:
        from Backend.AnimeStreaming import anime_system
        
        user_id = request.args.get('user_id', 'default')
        
        if request.method == 'GET':
            result = anime_system.get_watchlist(user_id)
        elif request.method == 'POST':
            data = request.json
            anime_name = data.get('anime', '')
            anime_id = data.get('id')
            if not anime_name:
                return jsonify({"error": "Anime name required"}), 400
            result = anime_system.add_to_watchlist(user_id, anime_name, anime_id)
        else:  # DELETE
            data = request.json
            anime_name = data.get('anime', '')
            if not anime_name:
                return jsonify({"error": "Anime name required"}), 400
            result = anime_system.remove_from_watchlist(user_id, anime_name)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== ULTIMATE VOICE API ====================

@app.route('/api/v1/voice/speak', methods=['POST'])
def voice_speak():
    """
    Text-to-Speech endpoint.
    
    Body: {
        "text": "Text to speak",
        "language": "english|hindi|hinglish" (optional, auto-detect),
        "voice": "specific voice name" (optional),
        "speed": "+10%" (optional)
    }
    
    Returns: { "status": "success", "audio_url": "/Data/tts_xxx.mp3" }
    """
    try:
        from Backend.UltimateVoice import get_ultimate_voice
        import asyncio
        
        data = request.json or {}
        text = data.get('text', '')
        language = data.get('language')  # english, hindi, hinglish
        voice = data.get('voice')
        speed = data.get('speed', '+0%')
        
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        voice_service = get_ultimate_voice()
        
        # Run async TTS in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            audio_path = loop.run_until_complete(
                voice_service.speak_async(text, voice=voice, language=language, speed=speed)
            )
        finally:
            loop.close()
        
        if audio_path and os.path.exists(audio_path):
            # Return relative URL for frontend
            relative_path = audio_path.replace(os.path.dirname(os.path.abspath(__file__)), '').replace('\\', '/').lstrip('/')
            return jsonify({
                "status": "success",
                "audio_url": f"/{relative_path}",
                "language": language or voice_service.detect_language(text)
            }), 200
        else:
            return jsonify({"error": "TTS generation failed"}), 500
            
    except Exception as e:
        print(f"[Voice/Speak] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/voice/transcribe', methods=['POST'])
def voice_transcribe():
    """
    Speech-to-Text endpoint using Groq Whisper.
    
    Accepts audio file upload or base64 audio.
    
    Returns: { "status": "success", "text": "transcribed text" }
    """
    try:
        from Backend.UltimateVoice import get_ultimate_voice
        import asyncio
        
        voice_service = get_ultimate_voice()
        audio_data = None
        temp_path = None
        
        # Check for file upload
        if 'audio' in request.files:
            audio_file = request.files['audio']
            temp_path = os.path.join(DATA_DIR, f"stt_temp_{int(time.time()*1000)}.wav")
            audio_file.save(temp_path)
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
        
        # Check for base64 audio
        elif request.json and 'audio_base64' in request.json:
            import base64
            audio_data = base64.b64decode(request.json['audio_base64'])
        
        else:
            return jsonify({"error": "No audio provided. Send 'audio' file or 'audio_base64'"}), 400
        
        # Transcribe
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            text = loop.run_until_complete(
                voice_service.transcribe_async(audio_data=audio_data)
            )
        finally:
            loop.close()
        
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        
        if text:
            return jsonify({
                "status": "success",
                "text": text
            }), 200
        else:
            return jsonify({"error": "Transcription failed or no speech detected"}), 400
            
    except Exception as e:
        print(f"[Voice/Transcribe] Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/voice/interrupt', methods=['POST'])
def voice_interrupt():
    """Stop any ongoing TTS playback (barge-in)."""
    try:
        from Backend.UltimateVoice import get_ultimate_voice
        
        voice_service = get_ultimate_voice()
        voice_service.interrupt()
        
        return jsonify({"status": "success", "message": "TTS interrupted"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/voice/voices', methods=['GET'])
def voice_list_voices():
    """Get list of available TTS voices."""
    try:
        from Backend.UltimateVoice import get_ultimate_voice
        
        voice_service = get_ultimate_voice()
        voices = voice_service.get_available_voices()
        
        return jsonify({
            "status": "success",
            "voices": voices
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== OPERATOR MODE ENDPOINTS ====================
# 🎯 HACKATHON FEATURE: AI-Powered DOM Control
# Enables KAI to understand and control any web page intelligently

@app.route('/api/v1/operator/analyze', methods=['POST'])
@rate_limit("default")
def operator_analyze_page():
    """
    Analyze page DOM and generate smart fill/click actions.
    
    Receives DOM structure from Chrome extension, uses AI to understand
    the page context, and returns actionable commands.
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        dom_structure = data.get('dom', {})
        user_profile = data.get('profile', {})
        user_query = data.get('query', 'Fill this form')
        user_id = data.get('user_id', 'default')
        
        # Get user profile from backend if not provided
        if not user_profile and user_id != 'default':
            try:
                if firebase_dal:
                    stored_profile = firebase_dal.get_document('users', user_id)
                    if stored_profile:
                        user_profile = stored_profile.get('profile', {})
            except Exception as profile_err:
                print(f"[OPERATOR] Could not fetch profile: {profile_err}")
        
        # Import and use DOMController
        try:
            from Backend.DOMController import dom_controller
            import asyncio
            
            # Run async analysis
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    dom_controller.analyze_page(dom_structure, user_profile, user_query)
                )
            finally:
                loop.close()
            
            return jsonify({
                "success": True,
                "type": "operator_analysis",
                **result
            }), 200
            
        except ImportError as ie:
            print(f"[OPERATOR] DOMController not available: {ie}")
            return jsonify({
                "error": "Operator mode not available",
                "details": str(ie)
            }), 503
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/operator/quick-fill', methods=['POST'])
@rate_limit("default")
def operator_quick_fill():
    """
    Quick synchronous form fill using rule-based matching.
    Faster but less intelligent than /analyze.
    """
    try:
        data = request.json
        
        dom_structure = data.get('dom', {})
        user_profile = data.get('profile', {})
        
        from Backend.DOMController import dom_controller
        
        actions = dom_controller.get_quick_fill_actions(dom_structure, user_profile)
        
        return jsonify({
            "success": True,
            "type": "quick_fill",
            "actions": actions,
            "count": len(actions)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/operator/status', methods=['GET'])
def operator_status():
    """Get operator mode status and capabilities."""
    try:
        from Backend.DOMController import dom_controller
        status = dom_controller.get_status()
        
        return jsonify({
            "success": True,
            "operator_mode": True,
            "capabilities": [
                "form_fill",
                "button_click", 
                "dropdown_select",
                "checkbox_toggle",
                "ai_analysis"
            ],
            **status
        }), 200
        
    except ImportError:
        return jsonify({
            "success": False,
            "operator_mode": False,
            "error": "DOMController not available"
        }), 200


@app.route('/api/v1/operator/execute', methods=['POST'])
@rate_limit("default")
def operator_execute_actions():
    """
    Log action execution results from the extension.
    The extension executes actions locally, this tracks results.
    """
    try:
        data = request.json
        
        actions_executed = data.get('actions', [])
        results = data.get('results', [])
        page_url = data.get('url', '')
        
        # Log for analytics
        success_count = sum(1 for r in results if r.get('success', False))
        total_count = len(results)
        
        print(f"[OPERATOR] Executed {success_count}/{total_count} actions on {page_url}")
        
        return jsonify({
            "success": True,
            "executed": total_count,
            "successful": success_count,
            "failed": total_count - success_count
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== EXTENSION MEMORY & AUTOMATION API ====================

@app.route('/api/v1/extension/memory', methods=['GET'])
def get_extension_memory():
    """Get user's extension memory (preferences, frequent actions, site data)"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        if firebase_storage and firebase_storage.db:
            doc_ref = firebase_storage.db.collection('extension_memory').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return jsonify({"success": True, "memory": doc.to_dict()})
            
            # Return default memory structure
            default_memory = {
                "user_id": user_id,
                "site_actions": {},
                "favorite_sites": [],
                "frequent_commands": [],
                "preferences": {
                    "voice_enabled": True,
                    "auto_speak": False,
                    "default_fill_delay": 100
                },
                "created_at": datetime.utcnow().isoformat()
            }
            doc_ref.set(default_memory)
            return jsonify({"success": True, "memory": default_memory})
        
        return jsonify({"error": "Database not available"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/extension/memory', methods=['POST'])
def update_extension_memory():
    """Update user's extension memory"""
    try:
        data = request.json
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        if firebase_storage and firebase_storage.db:
            doc_ref = firebase_storage.db.collection('extension_memory').document(user_id)
            
            # Merge update data
            update_data = {k: v for k, v in data.items() if k != 'user_id'}
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            doc_ref.set(update_data, merge=True)
            return jsonify({"success": True, "message": "Memory updated"})
        
        return jsonify({"error": "Database not available"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/extension/macros', methods=['GET'])
def get_extension_macros():
    """Get user's saved macros"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        if firebase_storage and firebase_storage.db:
            doc_ref = firebase_storage.db.collection('extension_macros').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return jsonify({"success": True, "macros": doc.to_dict().get('macros', [])})
            
            return jsonify({"success": True, "macros": []})
        
        return jsonify({"error": "Database not available"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/extension/macros', methods=['POST'])
def save_extension_macro():
    """Save a new macro or update existing"""
    try:
        data = request.json
        user_id = data.get('user_id')
        macro = data.get('macro')
        
        if not user_id or not macro:
            return jsonify({"error": "user_id and macro required"}), 400
        
        if firebase_storage and firebase_storage.db:
            import uuid
            doc_ref = firebase_storage.db.collection('extension_macros').document(user_id)
            doc = doc_ref.get()
            
            macros = doc.to_dict().get('macros', []) if doc.exists else []
            
            # Add ID and timestamp
            if 'id' not in macro:
                macro['id'] = f"macro_{uuid.uuid4().hex[:8]}"
            macro['created_at'] = datetime.utcnow().isoformat()
            macro['run_count'] = 0
            
            # Check for existing macro with same name
            existing_idx = next((i for i, m in enumerate(macros) if m.get('name') == macro.get('name')), None)
            if existing_idx is not None:
                macros[existing_idx] = macro
            else:
                macros.append(macro)
            
            doc_ref.set({'user_id': user_id, 'macros': macros}, merge=True)
            return jsonify({"success": True, "macro_id": macro['id'], "message": "Macro saved"})
        
        return jsonify({"error": "Database not available"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/extension/macros/<macro_id>', methods=['DELETE'])
def delete_extension_macro(macro_id):
    """Delete a macro"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        if firebase_storage and firebase_storage.db:
            doc_ref = firebase_storage.db.collection('extension_macros').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                macros = doc.to_dict().get('macros', [])
                macros = [m for m in macros if m.get('id') != macro_id]
                doc_ref.set({'macros': macros}, merge=True)
                return jsonify({"success": True, "message": "Macro deleted"})
            
            return jsonify({"error": "Macro not found"}), 404
        
        return jsonify({"error": "Database not available"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/extension/templates', methods=['GET'])
def get_extension_templates():
    """Get user's form templates"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        if firebase_storage and firebase_storage.db:
            doc_ref = firebase_storage.db.collection('extension_templates').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return jsonify({"success": True, "templates": doc.to_dict().get('templates', [])})
            
            return jsonify({"success": True, "templates": []})
        
        return jsonify({"error": "Database not available"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/extension/templates', methods=['POST'])
def save_extension_template():
    """Save a new form template"""
    try:
        data = request.json
        user_id = data.get('user_id')
        template = data.get('template')
        
        if not user_id or not template:
            return jsonify({"error": "user_id and template required"}), 400
        
        if firebase_storage and firebase_storage.db:
            import uuid
            doc_ref = firebase_storage.db.collection('extension_templates').document(user_id)
            doc = doc_ref.get()
            
            templates = doc.to_dict().get('templates', []) if doc.exists else []
            
            # Add ID and timestamp
            if 'id' not in template:
                template['id'] = f"tpl_{uuid.uuid4().hex[:8]}"
            template['created_at'] = datetime.utcnow().isoformat()
            
            # Check for existing template with same name
            existing_idx = next((i for i, t in enumerate(templates) if t.get('name') == template.get('name')), None)
            if existing_idx is not None:
                templates[existing_idx] = template
            else:
                templates.append(template)
            
            doc_ref.set({'user_id': user_id, 'templates': templates}, merge=True)
            return jsonify({"success": True, "template_id": template['id'], "message": "Template saved"})
        
        return jsonify({"error": "Database not available"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/extension/templates/<template_id>', methods=['DELETE'])
def delete_extension_template(template_id):
    """Delete a template"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        if firebase_storage and firebase_storage.db:
            doc_ref = firebase_storage.db.collection('extension_templates').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                templates = doc.to_dict().get('templates', [])
                templates = [t for t in templates if t.get('id') != template_id]
                doc_ref.set({'templates': templates}, merge=True)
                return jsonify({"success": True, "message": "Template deleted"})
            
            return jsonify({"error": "Template not found"}), 404
        
        return jsonify({"error": "Database not available"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/extension/track-action', methods=['POST'])
def track_extension_action():
    """Track user action for learning patterns"""
    try:
        data = request.json
        user_id = data.get('user_id')
        action = data.get('action')  # e.g., "fill", "click", "open"
        site = data.get('site')
        details = data.get('details', {})
        
        if not user_id or not action:
            return jsonify({"error": "user_id and action required"}), 400
        
        if firebase_storage and firebase_storage.db:
            doc_ref = firebase_storage.db.collection('extension_memory').document(user_id)
            doc = doc_ref.get()
            
            memory = doc.to_dict() if doc.exists else {"user_id": user_id, "site_actions": {}, "frequent_commands": []}
            
            # Update site-specific actions
            if site:
                if 'site_actions' not in memory:
                    memory['site_actions'] = {}
                if site not in memory['site_actions']:
                    memory['site_actions'][site] = {"visits": 0, "actions": []}
                
                memory['site_actions'][site]['visits'] += 1
                memory['site_actions'][site]['last_visit'] = datetime.utcnow().isoformat()
                if details:
                    memory['site_actions'][site]['last_data'] = details
            
            # Update command frequency
            if 'frequent_commands' not in memory:
                memory['frequent_commands'] = []
            
            cmd_found = False
            for cmd in memory['frequent_commands']:
                if cmd.get('cmd') == action:
                    cmd['count'] = cmd.get('count', 0) + 1
                    cmd_found = True
                    break
            
            if not cmd_found:
                memory['frequent_commands'].append({"cmd": action, "count": 1})
            
            # Sort by frequency
            memory['frequent_commands'].sort(key=lambda x: x.get('count', 0), reverse=True)
            memory['frequent_commands'] = memory['frequent_commands'][:20]  # Keep top 20
            
            memory['updated_at'] = datetime.utcnow().isoformat()
            doc_ref.set(memory, merge=True)
            
            return jsonify({"success": True, "message": "Action tracked"})
        
        return jsonify({"error": "Database not available"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== STARTUP ====================

def load_all_integrations():
    """Load and initialize all backend modules to ensure full functionality"""
    print("[INIT] Loading ALL system integrations...")
    gl = globals()
    
    # List of (Module Path, Attribute Name, Global Variable Name)
    modules_to_load = [
        ("Backend.Chatbot_Enhanced", "ChatBot", "ChatBot"),
        ("Backend.EnhancedIntelligence", "enhanced_intelligence", "enhanced_intelligence"),
        ("Backend.EnhancedAutomation", "enhanced_automation", "enhanced_automation"),
        ("Backend.Automation", "Automation", "Automation"), 
        ("Backend.MusicPlayerV2", "music_player_v2", "music_player_v2"),
        ("Backend.DocumentGenerator", "document_generator", "document_generator"),
        ("Backend.EnhancedImageGen", "enhanced_image_gen", "enhanced_image_gen"),
        ("Backend.AdvancedIntegrations", "integrations", "integrations"),
        ("Backend.EnhancedSpeech", "enhanced_speech", "enhanced_speech"), 
        ("Backend.TextToSpeech_Enhanced", "TextToSpeech", "TTS"),
        ("Backend.RealtimeSearchEngine", "RealtimeSearchEngine", "RealtimeSearchEngine"),
        ("Backend.EnhancedWebScraper", "EnhancedWebScraper", "enhanced_scraper"),
        ("Backend.CodeExecutor", "CodeExecutor", "code_executor"),
    ]

    for mod_path, attr_name, global_name in modules_to_load:
        try:
            mod = __import__(mod_path, fromlist=[attr_name])
            if hasattr(mod, attr_name):
                val = getattr(mod, attr_name)
                gl[global_name] = val
                print(f"[OK] Loaded {global_name}")
            else:
                print(f"[WARN] {attr_name} not found in {mod_path}")
        except Exception as e:
            print(f"[FAIL] {global_name}: {e}")

    # Special instantiations
    try:
        from Backend.FileManager import FileManager
        gl['file_manager'] = FileManager()
        print("[OK] Loaded file_manager")
    except Exception as e: print(f"[FAIL] file_manager: {e}")

    try:
        from Backend.VideoPlayer import get_video_player
        gl['video_player'] = get_video_player()
        print("[OK] Loaded video_player")
    except Exception as e: print(f"[FAIL] video_player: {e}")

    # UltimatePCControl removed - using psutil directly for system commands
    
    print("[INIT] All integrations loaded.")




def start_api_server(port=5000, debug=False):
    print(f"\n[START] JARVIS API Server (Ultimate Edition) running on port {port}")
    
    # Load all modules
    load_all_integrations()
    
    # Start Background Services
    if 'start_reminder_checker' in globals() and callable(start_reminder_checker):
        threading.Thread(target=start_reminder_checker, daemon=True).start()
        print("[INFO] Reminder Checker started")
        
    # ==================== WAKE WORD ISOLATED ====================
    def start_wake_word_safely():
        try:
            if PORCUPINE_AVAILABLE and wake_word_listener:
                 wake_word_listener()
        except Exception as e:
             print("Wake word disabled due to error:", e)

    threading.Thread(
        target=start_wake_word_safely,
        daemon=True
    ).start()
        
    print(f"[INFO] Data directory: {DATA_DIR}")
    print(f"[INFO] API Endpoint: http://localhost:{port}/api/v1")
    
    # ==================== WEBSOCKET SERVER ====================
    def start_websocket_server_safely():
        try:
            print(f"[WS] Starting WebSocket server on port 8765...")
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Initialize RealtimeSync with database
            from Backend.RealtimeSync import initialize_realtime_sync
            if firebase_storage and firebase_storage.db:
                rs = initialize_realtime_sync(firebase_storage.db, 8765)
                # Run the server
                loop.run_until_complete(rs.start_websocket_server())
                print("[WS] WebSocket server started on port 8765")
            else:
                print("[WARN] Firebase DB not available, skipping WebSocket server")
                
        except Exception as e:
            # Check for common websockets error if module missing
            if "No module named 'websockets'" in str(e):
                 print("[WARN] 'websockets' module not found. Realtime features disabled.")
                 print("       Run: pip install websockets")
            else:
                 print(f"[ERROR] WebSocket server failed to start: {e}")

    threading.Thread(target=start_websocket_server_safely, daemon=True).start()

    # ==================== AGENT WEBSOCKET SERVER ====================
    def start_agent_websocket_safely():
        try:
            from Backend.AgentWebSocket import start_agent_websocket_server
            start_agent_websocket_server(host="0.0.0.0", port=8766)
            print("[WS-AGENT] ✅ Agent WebSocket server started on port 8766")
        except ImportError:
            print("[WS-AGENT] ⚠️ AgentWebSocket module not found")
        except Exception as e:
            print(f"[WS-AGENT] ⚠️ Failed to start: {e}")
    
    threading.Thread(target=start_agent_websocket_safely, daemon=True).start()


    # Force Network Binding
    # DEBUG: Print registered after_request functions to detect duplicates
    print("\n[DEBUG] Registered after_request middleware:")
    for fn in app.after_request_funcs.get(None, []):
        print(f" - {fn.__module__}.{fn.__name__}")
    
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)

if __name__ == "__main__":
    # Disable debug reloader to prevent double-init
    start_api_server(debug=False)
