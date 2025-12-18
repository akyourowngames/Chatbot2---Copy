"""
JARVIS API Server - The Brain of the Desktop Assistant
======================================================
Serving all AI capabilities via REST API

PRODUCTION-READY with secure CORS, rate limiting, and security headers.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
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

app = Flask(__name__)

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

# Configure CORS with security settings
CORS(app, resources={
    r"/api/*": {
        "origins": CORS_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-API-Key", "X-Requested-With"],
        "supports_credentials": True,
        "max_age": 600,  # Cache preflight for 10 minutes
    },
    r"/health": {"origins": "*"},  # Health checks can be public
    r"/data/*": {"origins": CORS_ORIGINS},
})

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
# from Backend.Dispatcher import dispatcher # KAI Intelligence Engine (Bypassed)

# ==================== HEALTH CHECK (CRITICAL) ====================
@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200 

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
ultimate_pc = None
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
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "API key required"}), 401
        if api_key not in API_KEYS:
            return jsonify({"error": "Invalid API key"}), 403
        request.user = API_KEYS[api_key]
        # Set default user for backward compatibility
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

# --- DATA SERVING ---
@app.route('/data/<path:filename>')
def serve_data(filename):
    """Serve files from Data directory (images, audio)"""
    return send_from_directory(DATA_DIR, filename)

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
        if enhanced_image_gen:
            images = enhanced_image_gen.generate_with_style(prompt, style, num_images=1)
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
@app.route('/api/v1/chat', methods=['POST'])
@require_api_key
@rate_limit("chat")
def chat():
    global ChatBot
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
    image_path = data.get('image_path') # Support for uploaded images
    
    # === VISION AWARENESS UPGRADE ===
    # If an image is provided, analyze it immediately and inject context
    if image_path:
        print(f"[VISION] Received image: {image_path}")
        try:
            from Backend.vision.florence_inference import analyze_image_comprehensive
            vision_result = analyze_image_comprehensive(image_path)
            
            if vision_result.get('error'):
                print(f"[VISION] Error: {vision_result['error']}")
                # Don't fail, just let chat continue
            else:
                description = vision_result.get('friendly_response', '')
                query += f"\n\n[SYSTEM: I have analyzed the uploaded image. Here is what I see:]\n{description}"
                print(f"[VISION] Context injected into query.")
        except Exception as ve:
            print(f"[VISION] Failed to process image: {ve}")

    if not query: return jsonify({"error": "Query required"}), 400
    
    try:
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
        query_lower = query.lower().strip()
        
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
        
        # Check for explicit app commands
        if any(query_lower.startswith(p) for p in ["open ", "launch ", "start ", "close ", "quit ", "exit "]):
            for app in app_names:
                if app in query_lower:
                    trigger_type = "app"
                    command = app
                    print(f"[PRE-CHECK] Detected app command: {app}")
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
        
        # Check for code commands
        code_keywords = ["generate code", "write code", "create code", "code for", "python code", 
                         "javascript code", "write a script", "create a script", "execute code",
                         "run code", "run python", "explain code", "create project", "create flask",
                         "generate python", "generate javascript", "generate html"]
        if not trigger_type and any(k in query_lower for k in code_keywords):
            trigger_type = "code"
            command = query
            print(f"[PRE-CHECK] Detected code command")
        
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
            # For ambiguous "search X" without context, use file (more useful locally)
            elif not is_web_search and not is_file_search:
                trigger_type = "file"
                command = query
                print(f"[PRE-CHECK] Ambiguous search → defaulting to FILE search")
        
        # === SMART MUSIC vs VIDEO DETECTION ===
        # "play music/song" → music
        # "play video" or "watch" → video
        if not trigger_type and ("play" in query_lower or "watch" in query_lower):
            music_words = ["music", "song", "audio", "track", "playlist", "album"]
            video_words = ["video", "watch", "movie", "youtube video", "clip", "show me"]
            
            is_music = any(w in query_lower for w in music_words)
            is_video = any(w in query_lower for w in video_words)
            
            if is_music and not is_video:
                trigger_type = "music"
                command = query
                print(f"[PRE-CHECK] Smart detect: MUSIC")
            elif is_video and not is_music:
                trigger_type = "video"
                command = query
                print(f"[PRE-CHECK] Smart detect: VIDEO")
            elif "play" in query_lower and not is_video:
                # Default "play X" to music
                trigger_type = "music"
                command = query
                print(f"[PRE-CHECK] 'play' without context → MUSIC")

        # === LEGACY RESTORATION (FASTER) ===
        # Using SmartTrigger for instant, low-latency command detection.
        # This replaces the heavy "Agent" dispatcher.
        
        # Use SmartTrigger only if pre-check didn't match
        if not trigger_type:
            from Backend.SmartTrigger import smart_trigger
            trigger_type, command, _ = smart_trigger.detect(query)

        

        response_text = ""
        
        # 1. MUSIC/MEDIA COMMANDS
        if trigger_type == "music":
             print(f"[SMART-TRIGGER] Music command detected: {command}")
             try:
                 from Backend.MusicPlayer import music_player
                 
                 if "play" in query.lower():
                     search_query = command if command and command.lower() not in ['music', 'song', 'track', 'audio'] else "lofi music"
                     result_msg = music_player.play(search_query)
                     response_text = f"🎵 {result_msg}"
                 elif "pause" in query.lower():
                     response_text = f"⏸️ {music_player.pause()}"
                 elif "resume" in query.lower():
                     response_text = f"▶️ {music_player.resume()}"
                 elif "stop" in query.lower():
                     response_text = f"⏹️ {music_player.stop()}"
                 elif "next" in query.lower() or "skip" in query.lower():
                     response_text = f"⏭️ {music_player.next_song()}"
                 elif "lyrics" in query.lower():
                     song_name = command or (music_player.current_song['title'] if music_player.current_song else None)
                     if song_name:
                         response_text = f"📖 {music_player.get_lyrics(song_name)}"
                     else:
                         response_text = "Which song's lyrics do you want?"
                 elif "volume" in query.lower():
                     import re as re_vol
                     vol_match = re_vol.search(r'(\d+)', query)
                     if vol_match:
                         volume = int(vol_match.group(1))
                         response_text = f"🔊 {music_player.set_volume(volume)}"
                     else:
                         response_text = "Specify volume (0-100)"
                 else:
                     # Default: try to play whatever was requested
                     result_msg = music_player.play(command if command else "relaxing music")
                     response_text = f"🎵 {result_msg}"
             except Exception as e:
                 print(f"[ERROR] Music player error: {e}")
                 response_text = f"Music player error: {str(e)}"

        
        # 2. IMAGE GENERATION (FIX)
        elif trigger_type == "image":
             print(f"[SMART-TRIGGER] Image generation command: {command}")
             try:
                 import os
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
                 
                 images = enhanced_image_gen.generate_with_style(clean_prompt, style=detected_style, num_images=1)
                 if images:
                     # Helper to convert to URL path relative to server root
                     img_url = f"/data/Images/{os.path.basename(images[0])}"
                     response_text = f"Here is your **{detected_style}** image of {clean_prompt}:\n![Generated Image]({img_url})"
                 else:
                     response_text = "I tried to generate the image, but something went wrong."
             except Exception as e:
                 print(f"[ERROR] Image generation failed: {e}")
                 import traceback
                 traceback.print_exc()
                 response_text = f"Image generation failed: {str(e)}"


        # 3. INSTAGRAM AUTOMATION (Beast Mode)
        elif trigger_type == "instagram":
             print(f"[SMART-TRIGGER] Instagram command: {command}")
             try:
                 from Backend.InstagramAutomation import instagram
                 q = query.lower()
                 
                 if "dm" in q or "message" in q:
                     # Extract username and message: "dm @user saying hello"
                     import re
                     match = re.search(r'(?:dm|message)\s+@?(\w+)\s+(?:saying|:)\s+(.+)', q)
                     if match:
                         user, msg = match.groups()
                         result = instagram.send_direct_message(user, msg)
                         response_text = f"📩 {result.get('message', 'DM sent!')}"
                     else:
                         result = instagram.get_direct_messages(limit=5)
                         if result.get('status') == 'success':
                             msgs = result.get('messages', [])[:3]
                             dm_list = "\n".join([f"• @{m['users'][0]}: {m['last_message']['text'][:50]}..." for m in msgs if m.get('last_message')])
                             response_text = f"📬 **Recent DMs:**\n{dm_list}" if dm_list else "📭 No recent DMs"
                         else:
                             response_text = "❌ " + result.get('message', 'Could not fetch DMs')
                 
                 elif "post" in q or "upload" in q:
                     response_text = "📸 To post: provide image path. Use 'instagram post [path] caption [text]'"
                 
                 elif "story" in q:
                     response_text = "📖 To post story: provide image path. Use 'instagram story [path]'"
                 
                 elif "like" in q:
                     response_text = "❤️ To like: provide media ID. Use 'instagram like [media_id]'"
                 
                 elif "follow" in q and "unfollow" not in q:
                     match = re.search(r'follow\s+@?(\w+)', q)
                     if match:
                         result = instagram.follow_user(match.group(1))
                         response_text = f"👤 {result.get('message', 'Followed!')}"
                     else:
                         response_text = "👤 Specify username: 'instagram follow @username'"
                 
                 elif "unfollow" in q:
                     match = re.search(r'unfollow\s+@?(\w+)', q)
                     if match:
                         result = instagram.unfollow_user(match.group(1))
                         response_text = f"👤 {result.get('message', 'Unfollowed!')}"
                     else:
                         response_text = "👤 Specify username: 'instagram unfollow @username'"
                 
                 elif "info" in q or "profile" in q:
                     match = re.search(r'(?:info|profile)\s+@?(\w+)', q)
                     if match:
                         result = instagram.get_user_info(match.group(1))
                         if result.get('status') == 'success':
                             u = result['user']
                             response_text = f"👤 **@{u['username']}** ({u['full_name']})\n📊 {u['followers']} followers | {u['following']} following | {u['posts']} posts\n📝 {u['biography'][:100]}"
                         else:
                             response_text = "❌ " + result.get('message', 'User not found')
                     else:
                         response_text = "👤 Specify username: 'instagram info @username'"
                 
                 elif "search" in q:
                     match = re.search(r'search\s+(.+)', q)
                     if match:
                         result = instagram.search_users(match.group(1), limit=5)
                         if result.get('status') == 'success':
                             users = result.get('users', [])[:5]
                             user_list = "\n".join([f"• @{u['username']} ({u['full_name']}) - {u['follower_count']} followers" for u in users])
                             response_text = f"🔍 **Search Results:**\n{user_list}"
                         else:
                             response_text = "❌ " + result.get('message', 'Search failed')
                     else:
                         response_text = "🔍 Specify search term: 'instagram search [query]'"
                 
                 elif "status" in q:
                     status = instagram.get_status()
                     response_text = f"📱 **Instagram Status:** {'🟢 Logged in as @' + status.get('username') if status.get('logged_in') else '🔴 Not logged in'}"
                 
                 else:
                     response_text = "📱 **Instagram Commands:** dm, post, story, follow, unfollow, info, search, status"
             except Exception as e:
                  response_text = f"Instagram error: {str(e)}"

        # 3b. WHATSAPP AUTOMATION (Beast Mode)
        elif trigger_type == "whatsapp":
             print(f"[SMART-TRIGGER] WhatsApp command: {command}")
             try:
                 from Backend.WhatsAppAutomation import whatsapp
                 import re
                 q = query.lower()
                 
                 if "send" in q or "message" in q:
                     # Parse: "send whatsapp to +1234567890 saying Hello there"
                     match = re.search(r'(?:send|message)\s+(?:whatsapp\s+)?(?:to\s+)?(\+?\d[\d\s-]+)\s+(?:saying|:)\s+(.+)', q, re.I)
                     if match:
                         phone = '+' + re.sub(r'[^\d]', '', match.group(1))
                         msg = match.group(2).strip()
                         result = whatsapp.send_message(phone, msg)
                         response_text = f"📱 {result.get('message', 'Message sent!')}"
                     else:
                         response_text = "📱 Format: 'whatsapp +1234567890 saying Hello!'"
                 
                 elif "group" in q:
                     match = re.search(r'group\s+(.+?)\s+(?:saying|:)\s+(.+)', q)
                     if match:
                         group, msg = match.groups()
                         result = whatsapp.send_message_to_group(group.strip(), msg.strip())
                         response_text = f"👥 {result.get('message', 'Group message sent!')}"
                     else:
                         response_text = "👥 Format: 'whatsapp group [name] saying [message]'"
                 
                 elif "call" in q:
                     match = re.search(r'call\s+(\+?\d[\d\s-]+)', q)
                     if match:
                         phone = '+' + re.sub(r'[^\d]', '', match.group(1))
                         result = whatsapp.make_call(phone)
                         response_text = f"📞 {result.get('message', 'Call initiated!')}"
                     else:
                         response_text = "📞 Format: 'whatsapp call +1234567890'"
                 
                 elif "image" in q or "photo" in q:
                     response_text = "🖼️ To send image: 'whatsapp image +1234567890 path/to/image.jpg'"
                 
                 elif "status" in q:
                     status = whatsapp.get_status()
                     features = ", ".join(status.get('features', [])[:3])
                     response_text = f"📱 **WhatsApp Status:** Ready\n🔧 Features: {features}"
                 
                 else:
                     response_text = "📱 **WhatsApp Commands:** send, group, call, image, status"
             except Exception as e:
                  response_text = f"WhatsApp error: {str(e)}"

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

        # 6. GENERIC AUTOMATION (Fallback for others)
        elif trigger_type in ["chrome", "system", "app", "workflow", "whatsapp", "video", "switch"]:
             print(f"[SMART-TRIGGER] Detected {trigger_type} command: {command}")
             
             try:
                 # Handle SYSTEM commands directly for immediate feedback
                 if trigger_type == "system":
                     from Backend.UltimatePCControl import ultimate_pc
                     cmd_lower = command.lower() if command else ""
                     
                     if "battery" in cmd_lower or "power" in cmd_lower:
                         stats = ultimate_pc.get_beast_stats()
                         batt = stats.get('battery', {})
                         percent = batt.get('percent', 'Unknown')
                         plugged = batt.get('plugged', False)
                         response_text = f"🔋 Battery: {percent}% [{'⚡ Plugged' if plugged else '🔌 On Battery'}] | RAM Use: {stats['memory']['percent']}%"
                     elif "shutdown" in cmd_lower:
                         ultimate_pc.shutdown(60)
                         response_text = "⚠️ System will shutdown in 60 seconds."
                     elif "restart" in cmd_lower:
                         ultimate_pc.restart(60)
                         response_text = "🔄 System will restart in 60 seconds."
                     elif "sleep" in cmd_lower:
                         ultimate_pc.sleep()
                         response_text = "😴 System Sleeping."
                     elif "optimize" in cmd_lower or "cleanup" in cmd_lower:
                         response_text = f"🧹 {ultimate_pc.optimize_system()}"
                     elif "stats" in cmd_lower or "health" in cmd_lower or "pc" in cmd_lower:
                         stats = ultimate_pc.get_beast_stats()
                         top_hogs = ", ".join([h['name'] for h in stats['hogs'][:3]])
                         response_text = f"🖥️ **System Health**\n- CPU: {stats['cpu']['total']}% | RAM: {stats['memory']['percent']}%\n- Hogs: {top_hogs}\n- Uptime: {stats['uptime']}"
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
                 
                 # Handle APP commands with robust fallback chain
                 elif trigger_type == "app":
                     query_lower = query.lower()
                     is_close = "close" in query_lower or "quit" in query_lower or "exit" in query_lower
                     
                     # Extract app name from command
                     app_name = command.strip()
                     for remove in ["open", "close", "launch", "start", "quit", "exit", "the", "app", "application"]:
                         app_name = app_name.lower().replace(remove, "").strip()
                     app_name = " ".join(app_name.split())  # Clean extra spaces
                     
                     if not app_name:
                         response_text = "Please specify an app name."
                     elif is_close:
                         # Close app
                         try:
                             import subprocess
                             subprocess.run(f'taskkill /f /im {app_name}.exe', shell=True, capture_output=True)
                             response_text = f"❌ Closed {app_name}"
                         except Exception as e:
                             response_text = f"Failed to close {app_name}: {e}"
                     else:
                         # Open app with fallback chain
                         opened = False
                         
                         # Method 1: Direct paths (MOST RELIABLE)
                         common_apps = {
                             "notepad": "notepad.exe",
                             "calculator": "calc.exe",
                             "calc": "calc.exe",
                             "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                             "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                             "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
                             "edge": "msedge",
                             "brave": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                             "code": "code",
                             "vscode": "code",
                             "vs code": "code",
                             "visual studio code": "code",
                             "explorer": "explorer.exe",
                             "file explorer": "explorer.exe",
                             "file manager": "explorer.exe",
                             "files": "explorer.exe",
                             "recycle bin": "explorer.exe shell:RecycleBinFolder",
                             "downloads": "explorer.exe shell:Downloads",
                             "documents": "explorer.exe shell:Personal",
                             "pictures": "explorer.exe shell:My Pictures",
                             "videos": "explorer.exe shell:My Video",
                             "music": "explorer.exe shell:My Music",
                             "cmd": "cmd.exe",
                             "terminal": "wt.exe",
                             "command prompt": "cmd.exe",
                             "powershell": "powershell.exe",
                             "word": "winword",
                             "excel": "excel",
                             "powerpoint": "powerpnt",
                             "outlook": "outlook",
                             "discord": r"C:\Users\%USERNAME%\AppData\Local\Discord\Update.exe --processStart Discord.exe",
                             "slack": "slack",
                             "spotify": r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
                             "vlc": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                             "paint": "mspaint.exe",
                             "settings": "ms-settings:",
                             "control panel": "control",
                             "task manager": "taskmgr.exe",
                             "snipping tool": "snippingtool.exe",
                             "screen snip": "ms-screenclip:",
                             "magnifier": "magnify.exe",
                             "onenote": "onenote",
                             "teams": "msteams",
                             "zoom": "zoom",
                             "obs": r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
                             "steam": r"C:\Program Files (x86)\Steam\Steam.exe",
                         }
                         
                         exe_cmd = common_apps.get(app_name.lower())
                         if exe_cmd:
                             try:
                                 import subprocess
                                 import os
                                 # Use AutomationChain for robust opening and verification
                                 from Backend.AutomationChain import automation_chain
                                 
                                 success, msg = automation_chain.open_and_verify(app_name, app_name)
                                 if success:
                                     response_text = f"🚀 {msg}"
                                     opened = True # Added to maintain original logic flow
                                 else:
                                     # Fallback to simple generic open if verify fails (it might be a background app)
                                     response_text = f"⚠️ Attempted to open '{app_name}', but could not verify window visibility. {msg}"
                             except Exception as e1:
                                 print(f"[APP] Direct path failed: {e1}")
                         
                         # Method 2: Windows start command
                         if not opened:
                             try:
                                 import subprocess
                                 result = subprocess.Popen(f'start "" "{app_name}"', shell=True)
                                 opened = True
                                 response_text = f"🚀 Opened {app_name}"
                             except Exception as e2:
                                 print(f"[APP] Start command failed: {e2}")
                         
                         # Method 3: AppOpener (fallback)
                         if not opened:
                             try:
                                 from AppOpener import open as appopen
                                 appopen(app_name, match_closest=True, output=False)
                                 opened = True
                                 response_text = f"🚀 Opened {app_name}"
                             except Exception as e3:
                                 print(f"[APP] AppOpener failed: {e3}")
                         
                         # Method 4: PowerShell search
                         if not opened:
                             try:
                                 import subprocess
                                 ps_cmd = f'powershell -Command "Start-Process \'{app_name}\'"'
                                 subprocess.Popen(ps_cmd, shell=True)
                                 opened = True
                                 response_text = f"🚀 Opened {app_name}"
                             except Exception as e4:
                                 print(f"[APP] PowerShell failed: {e4}")

                         
                         if not opened:
                             response_text = f"⚠️ Could not find or open '{app_name}'. Make sure it's installed."

                 
                 # Handle CHROME commands
                 elif trigger_type == "chrome":
                     if Automation:
                         asyncio.run(Automation([f"chrome {command}"]))
                         response_text = f"🌐 Chrome: {command}"
                     else:
                         response_text = "Automation module is not loaded."
                 
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

                 # Handle other types with Automation
                 else:
                     if Automation:
                         asyncio.run(Automation([command]))
                         response_text = f"✅ Executed {trigger_type} command: {command}"
                     else:
                         response_text = "Automation module is not loaded."
                         
             except Exception as e:
                 print(f"[ERROR] Automation error: {e}")
                 import traceback
                 traceback.print_exc()
                 response_text = f"Automation error: {str(e)}"
        
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
                         # Fall through to legacy FileIOAutomation
                         raise ImportError("Use legacy module for this command")
                         
                 except ImportError:
                     # Fall back to FileIOAutomation for other commands
                     from Backend.FileIOAutomation import file_io
                 
                     if "create" in query_lower or "make" in query_lower:
                         # Extract filename: "create file test.txt"
                         filename = command.replace("create", "").replace("file", "").replace("make", "").strip()
                         if not filename:
                             filename = "new_file.txt"
                         result = file_io.create_file(filename)
                         response_text = result.get("message", f"Created {filename}")
                     
                     elif "delete" in query_lower or "remove" in query_lower:
                         filename = command.replace("delete", "").replace("remove", "").replace("file", "").strip()
                         result = file_io.delete_file(filename)
                         response_text = result.get("message", f"Deleted {filename}")
                     
                     elif "read" in query_lower or "show" in query_lower:
                         filename = command.replace("read", "").replace("show", "").replace("open", "").replace("file", "").strip()
                         result = file_io.read_file(filename)
                         if result.get("status") == "success":
                             content = result.get("content", "")[:500]
                             response_text = f"📄 **{filename}** ({result.get('size')} bytes):\n```\n{content}\n```"
                         else:
                             response_text = result.get("message", "File not found")
                     
                     elif "list" in query_lower:
                         # Check for system folder listing
                         folder_name = None
                         for f in ["downloads", "documents", "desktop", "pictures", "videos", "music"]:
                             if f in query_lower:
                                 folder_name = f
                                 break
                         
                         if folder_name:
                             result = file_io.list_system_folder(folder_name)
                             if result.get("status") == "success":
                                 items = result.get("items", [])[:10]
                                 item_list = "\n".join([f"• {i['name']} ({i['type']})" for i in items])
                                 response_text = f"📁 **{folder_name.title()}** ({result.get('count')} items):\n{item_list}"
                             else:
                                 response_text = result.get("message")
                         else:
                             result = file_io.list_files()
                             if result.get("status") == "success":
                                 files = result.get("files", [])[:10]
                                 file_list = "\n".join([f"• {f['name']} ({f['size']} bytes)" for f in files])
                                 response_text = f"📁 Files in workspace ({result.get('count')} total):\n{file_list}"
                             else:
                                 response_text = result.get("message")
                     
                     elif "search" in query_lower or "find" in query_lower:
                         search_query = command.replace("search", "").replace("find", "").replace("file", "").replace("files", "").strip()
                         
                         # Check if searching specific drive
                         if " in d:" in query_lower or " on d:" in query_lower:
                             result = file_io.search_drive(search_query, "D:")
                         elif " in c:" in query_lower or " on c:" in query_lower:
                             result = file_io.search_drive(search_query, "C:")
                         else:
                             # System-wide search (Downloads, Documents, Desktop, etc.)
                             result = file_io.search_system(search_query)
                         
                         if result.get("status") == "success":
                             results = result.get("results", [])[:5]
                             if results:
                                 res_list = "\n".join([f"• {r['name']} - {r.get('size', '')} ({r.get('path', '')[:50]}...)" for r in results])
                                 response_text = f"🔍 Found {result.get('count')} files for '{search_query}':\n{res_list}"
                             else:
                                 response_text = f"No files found matching '{search_query}'"
                         else:
                             response_text = result.get("message")
                     
                     else:
                         response_text = "📁 File commands: copy, move, rename, create, delete, list, search, select all, cut, paste, undo, redo, open folder"

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
             if VisionAnalysis:
                 print(f"[SMART-TRIGGER] Vision command detected.")
                 response_text = VisionAnalysis(command)
             else:
                 response_text = "Vision module is not loaded."
                 
        # 11. DOCUMENT/PDF GENERATION

        elif trigger_type == "document":
             print(f"[SMART-TRIGGER] Document generation: {command}")
             try:
                 from Backend.DocumentGenerator import document_generator
                 from datetime import datetime
                 
                 # Extract topic
                 topic = command.replace("generate", "").replace("create", "").replace("pdf", "").replace("document", "").replace("about", "").replace("report", "").replace("on", "").strip()
                 if not topic:
                     topic = "General Topic"
                 
                 # Generate AI content using ChatBot
                 ai_content = ""
                 try:
                     if ChatBot:
                         ai_prompt = f"""Write a comprehensive 500-word article about {topic}. Structure it with:
1. An engaging introduction (2-3 sentences)
2. Overview section explaining what {topic} is
3. Five key points about {topic} (one paragraph each)
4. Practical applications and real-world examples
5. A conclusion summarizing the main takeaways

Be informative, professional, and engaging. Do not use markdown formatting."""
                         ai_content = ChatBot(ai_prompt)
                 except Exception as ai_err:
                     print(f"[WARN] AI content generation failed: {ai_err}")
                 
                 # Parse AI content or use enhanced defaults
                 date_str = datetime.now().strftime("%B %d, %Y")
                 
                 content = [
                     {"type": "paragraph", "text": f"Generated on {date_str} by KAI AI"},
                     {"type": "spacer"},
                     {"type": "heading", "text": "Introduction"},
                 ]
                 
                 if ai_content and len(ai_content) > 100:
                     # Split AI content into paragraphs
                     paragraphs = [p.strip() for p in ai_content.split('\n\n') if p.strip()]
                     for para in paragraphs[:8]:  # Limit to 8 paragraphs
                         if para.startswith(('1.', '2.', '3.', '4.', '5.', '•', '-', '*')):
                             content.append({"type": "bullet", "text": para.lstrip('0123456789.-•* ')})
                         elif len(para) < 60 and not para.endswith('.'):
                             content.append({"type": "heading", "text": para})
                         else:
                             content.append({"type": "paragraph", "text": para})
                         content.append({"type": "spacer"})
                 else:
                     # Fallback: Enhanced default content
                     content.extend([
                         {"type": "paragraph", "text": f"This comprehensive document explores {topic} in detail, covering key concepts, practical applications, and important insights that will help you understand this subject thoroughly."},
                         {"type": "spacer"},
                         {"type": "heading", "text": f"What is {topic.title()}?"},
                         {"type": "paragraph", "text": f"{topic.title()} is a significant topic that encompasses various aspects and has wide-ranging implications across multiple domains. Understanding {topic} requires examining its core principles, historical context, and modern applications."},
                         {"type": "spacer"},
                         {"type": "heading", "text": "Key Points"},
                         {"type": "bullet", "text": f"Fundamental concepts and principles of {topic}"},
                         {"type": "bullet", "text": "Historical development and evolution over time"},
                         {"type": "bullet", "text": "Current trends and modern interpretations"},
                         {"type": "bullet", "text": "Practical applications in various fields"},
                         {"type": "bullet", "text": "Future prospects and emerging developments"},
                         {"type": "spacer"},
                         {"type": "heading", "text": "Practical Applications"},
                         {"type": "paragraph", "text": f"The practical applications of {topic} span across multiple industries and sectors. From everyday use cases to specialized implementations, understanding these applications provides valuable context for appreciating its importance."},
                         {"type": "spacer"},
                         {"type": "heading", "text": "Conclusion"},
                         {"type": "paragraph", "text": f"In summary, {topic} represents an important area of study with significant implications. By understanding the key concepts and applications discussed in this document, readers can develop a comprehensive understanding of this subject."},
                     ])
                 
                 pdf_path = document_generator.generate_pdf(f"Report on {topic.title()}", content)
                 response_text = f"I've generated a PDF about **{topic.title()}**. Saved at: `{pdf_path}`"
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
             print(f"[SMART-TRIGGER] No specific automation triggers. Using ChatBot for conversation.")
             
             # Use ChatBot for general conversational queries
             if ChatBot:
                 print("[DEBUG] Using ChatBot for general query")
                 response_text = ChatBot(query)
             else:
                 # Lazy load ChatBot
                 print("[DEBUG] Loading ChatBot module")
                 from Backend.Chatbot_Enhanced import ChatBot as CB
                 response_text = CB(query)
             
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

        return jsonify({
            "response": response_text,
            "command_executed": True
        })


        
    except Exception as e:
        print(f"[ERROR] Chat Processing Failed: {e}")
        import traceback
        traceback.print_exc()
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
@app.route('/api/v1/vision/analyze', methods=['POST'])
@require_api_key
def vision_analyze():
    data = request.json
    query = data.get('query', 'Describe this screen')
    
    # Check if image file uploaded
    # For now, Vision.py captures screenshot. 
    # To support upload, we need to modify Vision.py or handle it here.
    # The user "Vision Analysis" feature usually implies looking at the screen (JARVIS eyes).
    # But if there is a file upload...
    
    try:
        if VisionAnalysis:
            result = VisionAnalysis(query)
            
            # Save to history for context awareness
            try:
                from Backend.Chatbot_Enhanced import add_interaction_to_history
                # context_query = f"[User uploaded an image/screenshot] {query}"
                # actually, usually query is "Describe this screen". 
                # We'll tag it clearly.
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
    if ultimate_pc:
        return jsonify({"status": "success", "stats": ultimate_pc.get_system_stats()})
    return jsonify({"error": "PC Control not loaded"}), 503

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
    if not ultimate_pc:
        return jsonify({"error": "PC Control not loaded"}), 503
    return jsonify({"stats": ultimate_pc.get_system_stats()})

@app.route('/api/v1/system/control', methods=['POST'])
@require_api_key
def system_control():
    if not ultimate_pc:
        return jsonify({"error": "PC Control not loaded"}), 503
    data = request.json
    action = data.get('action', '')
    
    if action == 'shutdown':
        ultimate_pc.shutdown(60)
        return jsonify({"message": "Shutting down in 60s"})
    elif action == 'restart':
        ultimate_pc.restart(60)
        return jsonify({"message": "Restarting in 60s"})
    elif action == 'lock':
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return jsonify({"message": "System Locked"})
    elif action == 'screenshot':
        file = ultimate_pc.take_screenshot()
        return jsonify({"message": "Screenshot taken", "file": file})
        
    return jsonify({"error": "Unknown action"}), 400

# --- FILE UPLOAD & ANALYSIS ---
# --- VISION & FILE UPLOAD ROUTES ---
app.add_url_rule('/api/v1/files/upload', view_func=upload_endpoint, methods=['POST'])
app.add_url_rule('/api/v1/files', view_func=list_endpoint, methods=['GET'])
app.add_url_rule('/api/v1/files/<path:file_id>/download', view_func=download_endpoint, methods=['GET'])
app.add_url_rule('/api/v1/files/<path:file_id>', view_func=delete_endpoint, methods=['DELETE'])
app.add_url_rule('/api/v1/files/<path:file_id>/analyze', view_func=analyze_endpoint, methods=['GET'])
app.add_url_rule('/api/v1/analyze-image', view_func=analyze_image_endpoint, methods=['POST'])



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
        
        filepath = document_generator.generate_pdf(title, content)
        
        # Return relative path for serving
        filename = os.path.basename(filepath)
        return jsonify({
            "status": "success",
            "message": "PDF created successfully",
            "filepath": filepath,
            "url": f"/data/Documents/{filename}"
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
                {"title": "Introduction", "content": [f"Overview of {title}"]},
                {"title": "Conclusion", "content": ["Summary", "Next steps"]}
            ]
        
        filepath = document_generator.generate_powerpoint(title, slides)
        
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
        
        filepath = document_generator.generate_report(topic, sections)
        
        filename = os.path.basename(filepath)
        return jsonify({
            "status": "success",
            "message": "Report created successfully",
            "filepath": filepath,
            "url": f"/data/Documents/{filename}"
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
        
        images = enhanced_image_gen.generate_with_style(prompt, style, num_images)
        
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
        
        images = enhanced_image_gen.generate_hd(prompt, num_images)
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
        
        result = enhanced_image_gen.generate_variations(prompt, variations, num_per_variation=1)
        
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

# --- FILE UPLOAD & ANALYSIS ---
# @app.route('/api/v1/files/upload', methods=['POST'])
# @require_api_key
# def upload_file():
#     """Upload and analyze a file"""
#     if not file_analyzer:
#         return jsonify({"error": "File Analyzer not loaded"}), 503
#     
#     try:
#         if 'file' not in request.files:
#             return jsonify({"error": "No file provided"}), 400
#         
#         file = request.files['file']
#         
#         if file.filename == '':
#             return jsonify({"error": "No file selected"}), 400
#         
#         # Save file
#         file_data = file.read()
#         filepath = file_analyzer.save_upload(file_data, file.filename)
#         
#         # Analyze file
#         analysis = file_analyzer.analyze_file(filepath)
#         
#         # Show full AI analysis
#         if analysis.get("status") == "success":
#             ai_analysis = analysis.get("ai_analysis", "No analysis available")
#         else:
#             ai_analysis = "Analysis failed"
#         
#         return jsonify({
#             "status": "success",
#             "message": "File uploaded and analyzed",
#             "analysis": analysis
#         })
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

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
            summary = db.get_analytics_summary(days)
            return jsonify({"status": "success", "summary": summary})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== WHATSAPP AUTOMATION ====================

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
        ("Backend.InstagramAutomation", "instagram", "instagram"),
        ("Backend.WhatsAppAutomation", "whatsapp", "whatsapp"),
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

    try:
        from Backend.UltimatePCControl import UltimatePCControl
        gl['ultimate_pc'] = UltimatePCControl()
        print("[OK] Loaded ultimate_pc")
    except: pass
    
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

    # Force Network Binding
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)

if __name__ == "__main__":
    # Disable debug reloader to prevent double-init
    start_api_server(debug=False)
