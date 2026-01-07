"""
Kai Local Agent API - Cloud Endpoints for Device Management
============================================================
Provides REST endpoints for local agents to register, poll tasks,
report results, and maintain heartbeat with the Kai cloud.

Security Model (Multi-User):
- Every device is bound to exactly one user_id
- Device pairing requires authenticated user session
- All commands are verified against user→device ownership
- Agent trusts Kai cloud only (never browsers/users directly)
"""

import os
import json
import uuid
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, g, session

# ==================== CONFIGURATION ====================

# Firebase Firestore for persistent device storage
_firestore_db = None
_firestore_init_attempted = False

def _get_firestore():
    """Get Firestore client (lazy initialization)."""
    global _firestore_db, _firestore_init_attempted
    
    # If we already have a valid db, return it
    if _firestore_db is not None:
        return _firestore_db
    
    # Try to get Firestore client directly from firebase_admin
    try:
        import firebase_admin
        from firebase_admin import firestore, credentials
        import os
        import json
        
        # Check if Firebase app is already initialized (by auth or other modules)
        if firebase_admin._apps:
            _firestore_db = firestore.client()
            print("[LOCAL_AGENT] ✅ Firebase Firestore connected for device storage")
            return _firestore_db
        
        # Try to initialize Firebase from FIREBASE_CREDENTIALS env var (JSON string)
        firebase_creds_json = os.getenv('FIREBASE_CREDENTIALS')
        if firebase_creds_json and not _firestore_init_attempted:
            _firestore_init_attempted = True
            try:
                # Parse JSON string from environment variable
                cred_dict = json.loads(firebase_creds_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                _firestore_db = firestore.client()
                print("[LOCAL_AGENT] ✅ Firebase Firestore initialized from FIREBASE_CREDENTIALS env var")
                return _firestore_db
            except Exception as e:
                print(f"[LOCAL_AGENT] ⚠️ Failed to init Firebase from env var: {e}")
        
        # Fallback: try via FirebaseStorage module
        if not _firestore_init_attempted:
            _firestore_init_attempted = True
            from Backend.FirebaseStorage import get_firebase_storage
            storage = get_firebase_storage()
            if storage and storage.db:
                _firestore_db = storage.db
                print("[LOCAL_AGENT] ✅ Firebase Firestore connected via FirebaseStorage")
                return _firestore_db
            else:
                print("[LOCAL_AGENT] ⚠️ Firebase storage returned but db is None")
        
        # Fallback 2: Try loading credentials from file directly
        if _firestore_db is None and not firebase_admin._apps:
            cred_file_paths = [
                'kai-g-80f9c-firebase-adminsdk-fbsvc-d577c79d28.json',
                os.path.join(os.path.dirname(__file__), '..', 'kai-g-80f9c-firebase-adminsdk-fbsvc-d577c79d28.json'),
                'firebase-credentials.json',
                os.path.join(os.path.dirname(__file__), '..', 'firebase-credentials.json'),
            ]
            
            for cred_path in cred_file_paths:
                if os.path.exists(cred_path):
                    try:
                        cred = credentials.Certificate(cred_path)
                        firebase_admin.initialize_app(cred)
                        _firestore_db = firestore.client()
                        print(f"[LOCAL_AGENT] ✅ Firebase initialized from file: {cred_path}")
                        return _firestore_db
                    except Exception as e:
                        print(f"[LOCAL_AGENT] ⚠️ Failed to init from {cred_path}: {e}")
                
    except Exception as e:
        print(f"[LOCAL_AGENT] ⚠️ Firebase not available: {e}")

    
    return _firestore_db

def _load_devices_from_firestore():
    """Load all registered devices from Firestore."""
    devices = {}
    try:
        db = _get_firestore()
        if db:
            # PRIORITY 1: Query top-level devices collection (fast path)
            # This is where devices are saved with full data including user_id
            try:
                devices_ref = db.collection('devices')
                for device_doc in devices_ref.stream():
                    device_data = device_doc.to_dict()
                    if device_data:
                        devices[device_doc.id] = device_data
                print(f"[LOCAL_AGENT] ✅ Loaded {len(devices)} devices from top-level Firestore collection")
            except Exception as e:
                print(f"[LOCAL_AGENT] ⚠️ Top-level devices query failed: {e}")
            
            # PRIORITY 2: Also check user-nested collections (backup)
            if len(devices) == 0:
                try:
                    users_ref = db.collection('users')
                    for user_doc in users_ref.stream():
                        user_devices_ref = db.collection('users').document(user_doc.id).collection('devices')
                        for device_doc in user_devices_ref.stream():
                            if device_doc.id not in devices:  # Don't overwrite
                                device_data = device_doc.to_dict()
                                device_data['user_id'] = user_doc.id
                                devices[device_doc.id] = device_data
                    print(f"[LOCAL_AGENT] Loaded {len(devices)} devices from user subcollections")
                except Exception as e:
                    print(f"[LOCAL_AGENT] ⚠️ User subcollection query failed: {e}")
        else:
            print("[LOCAL_AGENT] ⚠️ Firestore not available - devices will only persist in memory")
    except Exception as e:
        print(f"[LOCAL_AGENT] Error loading devices from Firestore: {e}")
    return devices


def _save_device_to_firestore(device_id: str, device_data: dict):
    """Save a single device to Firestore."""
    try:
        db = _get_firestore()
        if db:
            user_id = device_data.get('user_id')
            if user_id:
                # Save under users/{user_id}/devices/{device_id}
                db.collection('users').document(user_id).collection('devices').document(device_id).set({
                    'name': device_data.get('name'),
                    'auth_token': device_data.get('auth_token'),
                    'registered_at': device_data.get('registered_at'),
                    'last_seen': device_data.get('last_seen'),
                }, merge=True)
                
                # ALSO save to top-level devices collection for fast lookup
                db.collection('devices').document(device_id).set({
                    'user_id': user_id,
                    'name': device_data.get('name'),
                    'auth_token': device_data.get('auth_token'),
                    'registered_at': device_data.get('registered_at'),
                    'last_seen': device_data.get('last_seen'),
                }, merge=True)
                
                print(f"[LOCAL_AGENT] ✅ Device {device_id[:8]}... saved to Firestore (user: {user_id[:8]}...)")
                return True
            else:
                print(f"[LOCAL_AGENT] ⚠️ Cannot save device - no user_id in device_data")
        else:
            print(f"[LOCAL_AGENT] ⚠️ Cannot save device - Firestore not available")
    except Exception as e:
        print(f"[LOCAL_AGENT] ❌ Error saving device to Firestore: {e}")
    return False

def _update_device_heartbeat(device_id: str, user_id: str):
    """Update device last_seen timestamp in Firestore."""
    try:
        db = _get_firestore()
        if db and user_id:
            db.collection('users').document(user_id).collection('devices').document(device_id).update({
                'last_seen': datetime.now().isoformat()
            })
            return True
    except Exception as e:
        print(f"[LOCAL_AGENT] Error updating heartbeat in Firestore: {e}")
    return False

def _delete_device_from_firestore(device_id: str, user_id: str):
    """Delete a device from Firestore."""
    try:
        db = _get_firestore()
        if db and user_id:
            db.collection('users').document(user_id).collection('devices').document(device_id).delete()
            return True
    except Exception as e:
        print(f"[LOCAL_AGENT] Error deleting device from Firestore: {e}")
    return False

def _get_user_devices_from_firestore(user_id: str):
    """Get all devices for a specific user from Firestore."""
    devices = {}
    try:
        db = _get_firestore()
        if db and user_id:
            user_devices_ref = db.collection('users').document(user_id).collection('devices')
            for device_doc in user_devices_ref.stream():
                device_data = device_doc.to_dict()
                device_data['user_id'] = user_id
                devices[device_doc.id] = device_data
    except Exception as e:
        print(f"[LOCAL_AGENT] Error getting user devices from Firestore: {e}")
    return devices

# In-memory cache (synced with Firestore)
# SECURITY: Every device is bound to a user_id
_registered_devices = _load_devices_from_firestore()  # {device_id: {user_id, name, auth_token, registered_at, last_seen}}
_pending_tasks = {}       # {device_id: [{task_id, command, params, created_at, user_id}]}
_task_results = {}        # {task_id: {device_id, status, result, reported_at}}

# Pairing codes (one-time use, 10-minute expiry)
_pending_pairing_codes = {}  # {code: {user_id, expires_at, used}}

def _save_pairing_code_to_firestore(code: str, pairing_data: dict):
    """Save a pairing code to Firestore for persistence across server restarts."""
    try:
        db = _get_firestore()
        if db:
            db.collection('pairing_codes').document(code).set({
                'user_id': pairing_data.get('user_id'),
                'expires_at': pairing_data.get('expires_at'),
                'used': pairing_data.get('used', False),
            })
            print(f"[LOCAL_AGENT] ✅ Pairing code saved to Firestore")
            return True
    except Exception as e:
        print(f"[LOCAL_AGENT] ⚠️ Error saving pairing code to Firestore: {e}")
    return False

def _get_pairing_code_from_firestore(code: str):
    """Retrieve a pairing code from Firestore."""
    try:
        db = _get_firestore()
        if db:
            doc = db.collection('pairing_codes').document(code).get()
            if doc.exists:
                data = doc.to_dict()
                print(f"[LOCAL_AGENT] ✅ Pairing code found in Firestore")
                return data
    except Exception as e:
        print(f"[LOCAL_AGENT] ⚠️ Error retrieving pairing code from Firestore: {e}")
    return None

def _mark_pairing_code_used_in_firestore(code: str):
    """Mark a pairing code as used in Firestore."""
    try:
        db = _get_firestore()
        if db:
            db.collection('pairing_codes').document(code).update({'used': True})
            return True
    except Exception as e:
        print(f"[LOCAL_AGENT] ⚠️ Error marking pairing code as used: {e}")
    return False

# Audit log for command tracking
_command_audit_log = []  # [{id, user_id, device_id, command, params, timestamp, status, ip}]

# Token expiry (30 days for MVP)
TOKEN_EXPIRY_DAYS = 30

print(f"[LOCAL_AGENT] Loaded {len(_registered_devices)} registered devices (Firebase + cache)")

# ==================== BLUEPRINT ====================

local_agent_bp = Blueprint('local_agent', __name__, url_prefix='/agent')


# Blueprint-level CORS handler for ALL /agent/* endpoints
@local_agent_bp.after_request
def add_cors_headers(response):
    """Add CORS headers to all agent API responses."""
    origin = request.headers.get('Origin', 'http://localhost:3000')
    allowed_origins = ['http://localhost:3000', 'https://kai2010.netlify.app', 'https://kai-frontend.onrender.com']
    
    if origin in allowed_origins or origin.startswith('http://localhost:') or origin.endswith('.netlify.app') or origin.endswith('.onrender.com'):
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-User-ID'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


# Blueprint-level OPTIONS handler for preflight requests
@local_agent_bp.before_request
def handle_preflight():
    """Handle CORS preflight OPTIONS requests."""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return response, 200

def generate_auth_token():
    """Generate a secure auth token for device authentication."""
    return secrets.token_urlsafe(32)


def generate_device_id():
    """Generate a unique device ID."""
    return str(uuid.uuid4())


def require_device_auth(f):
    """
    Decorator to require valid device authentication.
    Expects Authorization header: Bearer <auth_token>
    And query param: device_id=xxx
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get device_id from query params or JSON body
        device_id = request.args.get('device_id')
        if not device_id and request.is_json:
            device_id = request.json.get('device_id')
        
        if not device_id:
            return jsonify({"error": "device_id required"}), 400
        
        # Get auth token from header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authorization header required"}), 401
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Validate device and token - check memory cache first, then Firestore
        device = _registered_devices.get(device_id)
        if not device:
            # Try to load from Firestore (device might have been registered on different instance)
            try:
                db = _get_firestore()
                if db:
                    # Fast O(1) lookup from top-level devices collection
                    device_doc = db.collection('devices').document(device_id).get()
                    if device_doc.exists:
                        device = device_doc.to_dict()
                        # Cache it for future requests
                        _registered_devices[device_id] = device
                        print(f"[LOCAL_AGENT] ✅ Device {device_id[:8]}... loaded from Firestore")
            except Exception as e:
                print(f"[LOCAL_AGENT] ⚠️ Firestore lookup error: {e}")
        
        if not device:
            return jsonify({"error": "Device not registered"}), 401
        
        if device['auth_token'] != token:
            return jsonify({"error": "Invalid auth token"}), 401
        
        # Check token expiry
        registered_at = datetime.fromisoformat(device['registered_at'])
        if datetime.now() - registered_at > timedelta(days=TOKEN_EXPIRY_DAYS):
            return jsonify({"error": "Token expired, re-register required"}), 401
        
        # Store device info in request context
        g.device_id = device_id
        g.device = device
        
        return f(*args, **kwargs)
    return decorated_function


def get_authenticated_user_id(req=None) -> str:
    """
    Get authenticated user ID from request context.
    
    Priority:
    1. Firebase token in Authorization header (for web requests)
    2. Session-based user_id (for authenticated web sessions)
    3. X-User-ID header (for internal/trusted requests only)
    
    Returns:
        user_id string or None if not authenticated
    """
    req = req or request
    
    # Method 1: Check session (Flask session with Firebase)
    user_id = session.get('user_id')
    if user_id:
        return user_id
    
    # Method 2: Check Authorization header for Firebase token
    auth_header = req.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        # Try to verify Firebase token
        try:
            # Firebase verification would go here
            # For MVP, we'll accept the token and extract user_id from it
            # In production, verify with firebase_admin.auth.verify_id_token(token)
            import base64
            import json
            # Decode payload (middle part of JWT)
            parts = token.split('.')
            if len(parts) == 3:
                # Add padding if needed
                payload = parts[1]
                payload += '=' * (4 - len(payload) % 4)
                decoded = base64.urlsafe_b64decode(payload)
                data = json.loads(decoded)
                user_id = data.get('user_id') or data.get('sub')
                if user_id:
                    return user_id
        except Exception:
            pass
    
    # Method 3: Internal header (trusted services only)
    internal_user = req.headers.get('X-User-ID')
    if internal_user and req.remote_addr in ['127.0.0.1', 'localhost', '::1']:
        return internal_user
    
    return None


def require_user_auth(f):
    """
    Decorator to require valid user authentication.
    Sets g.user_id if authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_authenticated_user_id()
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        g.user_id = user_id
        return f(*args, **kwargs)
    return decorated_function


def verify_device_ownership(user_id: str, device_id: str) -> bool:
    """
    Verify that a user owns a specific device.
    
    CRITICAL SECURITY CHECK - called before every device operation.
    """
    device = _registered_devices.get(device_id)
    if not device:
        return False
    return device.get('user_id') == user_id


def log_command(user_id: str, device_id: str, command: str, params: dict, status: str = "queued"):
    """Log a command to the audit trail."""
    _command_audit_log.append({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "device_id": device_id,
        "command": command,
        "params": params,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "ip": request.remote_addr if request else "internal"
    })
    # Keep only last 1000 entries in memory (for MVP)
    if len(_command_audit_log) > 1000:
        _command_audit_log.pop(0)


def get_user_devices(user_id: str) -> dict:
    """
    Get all devices owned by a specific user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        dict of {device_id: device_info} for devices owned by this user
    """
    if not user_id:
        return {}
    
    return {
        device_id: info 
        for device_id, info in _registered_devices.items() 
        if info.get('user_id') == user_id
    }


def get_first_online_device(user_id: str = None) -> tuple:
    """
    Get the first online device, optionally filtered by user.
    
    Args:
        user_id: Optional user ID to filter by
        
    Returns:
        (device_id, device_info) or (None, None) if no online device found
    """
    from datetime import datetime
    now = datetime.now()
    
    # First try user's own devices
    devices = get_user_devices(user_id) if user_id else _registered_devices
    
    for device_id, info in devices.items():
        last_seen = datetime.fromisoformat(info.get('last_seen', '2000-01-01'))
        is_online = (now - last_seen).total_seconds() < 60
        if is_online:
            return device_id, info
    
    # Return first device (even if offline) if user has devices
    if devices:
        first_id = list(devices.keys())[0]
        return first_id, devices[first_id]
    
    # DEV MODE FALLBACK: If user has no devices, try any available device
    # TODO: Remove this in production - it bypasses user scoping
    if _registered_devices:
        print(f"[SECURITY-DEV] User {user_id[:8] if user_id else 'none'}... has no devices, using fallback (dev mode)")
        for device_id, info in _registered_devices.items():
            last_seen = datetime.fromisoformat(info.get('last_seen', '2000-01-01'))
            is_online = (now - last_seen).total_seconds() < 60
            if is_online:
                return device_id, info
        # Return any device
        first_id = list(_registered_devices.keys())[0]
        return first_id, _registered_devices[first_id]
    
    return None, None


# ==================== ENDPOINTS ====================

@local_agent_bp.route('/generate-pairing-code', methods=['POST', 'OPTIONS'])
def generate_pairing_code():
    """
    Generate a one-time pairing code for device registration.
    REQUIRES: Authenticated user session.
    
    Response:
        {"success": true, "code": "aB3xY9pQ", "expires_in": "10 minutes"}
    """
    # Handle CORS preflight - Return explicit headers, bypass Flask-CORS
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', 'http://localhost:3000')
        allowed_origins = ['http://localhost:3000', 'https://kai2010.netlify.app', 'https://kai-frontend.onrender.com']
        if origin in allowed_origins or origin.endswith('.netlify.app') or origin.endswith('.onrender.com'):
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            response.headers['Access-Control-Allow-Origin'] = 'https://kai2010.netlify.app'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-User-ID'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response, 200
    
    # Manual auth check (only for POST requests)
    user_id = get_authenticated_user_id()
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401
    

    
    try:
        # Generate a short, user-friendly code
        code = secrets.token_urlsafe(8)[:12]  # e.g., "aB3xY9pQr5mN"
        expiry = datetime.now() + timedelta(minutes=10)
        
        # Store pairing code (bound to user) in memory
        pairing_data = {
            "user_id": user_id,
            "expires_at": expiry.isoformat(),
            "used": False
        }
        _pending_pairing_codes[code] = pairing_data
        
        # Also persist to Firestore so it survives server restarts
        _save_pairing_code_to_firestore(code, pairing_data)
        
        # Clean up expired codes
        now = datetime.now()
        expired = [c for c, d in _pending_pairing_codes.items() 
                   if datetime.fromisoformat(d['expires_at']) < now or d['used']]
        for c in expired:
            del _pending_pairing_codes[c]
        
        print(f"[LOCAL_AGENT] Pairing code generated for user {user_id[:8]}...")
        
        return jsonify({
            "success": True,
            "code": code,
            "expires_in": "10 minutes",
            "instructions": "Run: python -m LocalAgent.agent --register <code> --api <url>"
        })
        
    except Exception as e:
        print(f"[LOCAL_AGENT] Pairing code generation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@local_agent_bp.route('/register', methods=['POST', 'OPTIONS'])
def agent_register():
    """
    Register a new device with the Kai cloud.
    
    SECURITY: Device is permanently bound to the user who generated the pairing code.
    
    Request:
        {"device_name": "MyPC", "pairing_token": "code-from-web-ui"}
    
    Response:
        {"success": true, "device_id": "uuid", "auth_token": "secret"}
    """
    if request.method == 'OPTIONS':
        return _build_cors_response()
    
    try:
        data = request.get_json() or {}
        device_name = data.get('device_name', 'Unknown Device')
        pairing_token = data.get('pairing_token')
        
        # Validate pairing token
        if not pairing_token or len(pairing_token) < 4:
            return jsonify({
                "success": False,
                "error": "Valid pairing_token required (min 4 characters)"
            }), 400
        
        # Look up pairing code to get user_id binding - check memory first, then Firestore
        pairing_info = _pending_pairing_codes.get(pairing_token)
        user_id = None
        from_firestore = False
        
        # If not in memory, try Firestore (code may have been generated before server restart)
        if not pairing_info:
            pairing_info = _get_pairing_code_from_firestore(pairing_token)
            from_firestore = True
        
        if pairing_info:
            # Validate pairing code
            expires = datetime.fromisoformat(pairing_info['expires_at'])
            if datetime.now() > expires:
                return jsonify({"success": False, "error": "Pairing code expired"}), 400
            if pairing_info.get('used'):
                return jsonify({"success": False, "error": "Pairing code already used"}), 400
            
            # Get user binding and mark as used
            user_id = pairing_info['user_id']
            if from_firestore:
                _mark_pairing_code_used_in_firestore(pairing_token)
            else:
                _pending_pairing_codes[pairing_token]['used'] = True
                _mark_pairing_code_used_in_firestore(pairing_token)  # Also sync to Firestore
            print(f"[LOCAL_AGENT] Device bound to user {user_id[:8]}... via pairing code")
        else:
            # FALLBACK for development: Accept any token with no user binding
            # TODO: Remove this fallback in production
            print(f"[LOCAL_AGENT] WARNING: Device registered without user binding (dev mode)")
            user_id = f"dev-user-{hash(pairing_token) % 10000}"  # Pseudo user for dev
        
        # Generate credentials
        device_id = generate_device_id()
        auth_token = generate_auth_token()
        
        # Store device registration WITH USER BINDING
        _registered_devices[device_id] = {
            "user_id": user_id,  # CRITICAL: Ownership binding
            "name": device_name,
            "auth_token": auth_token,
            "registered_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
        }
        
        # Persist to Firebase so devices survive server restarts
        _save_device_to_firestore(device_id, _registered_devices[device_id])
        
        # Initialize empty task queue for this device
        _pending_tasks[device_id] = []
        
        # Log registration
        log_command(user_id, device_id, "device_registered", {"device_name": device_name}, "success")
        
        print(f"[LOCAL_AGENT] Device registered: {device_name} ({device_id[:8]}...) -> User: {user_id[:8]}...")
        
        return jsonify({
            "success": True,
            "device_id": device_id,
            "auth_token": auth_token,
            "user_id": user_id[:8] + "...",  # Partial for confirmation
            "message": f"Device '{device_name}' registered successfully"
        })
        
    except Exception as e:
        print(f"[LOCAL_AGENT] Registration error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@local_agent_bp.route('/poll', methods=['GET', 'OPTIONS'])
@require_device_auth
def agent_poll():
    """
    Poll for pending tasks for this device.
    
    Query params:
        device_id: Device identifier
    
    Headers:
        Authorization: Bearer <auth_token>
    
    Response:
        {"task_id": "uuid", "command": "open_app", "params": {"app": "browser"}}
        or {"task_id": null} when no tasks pending
    """
    if request.method == 'OPTIONS':
        return _build_cors_response()
    
    try:
        device_id = g.device_id
        
        # Update last seen
        _registered_devices[device_id]['last_seen'] = datetime.now().isoformat()
        
        # Get pending tasks for this device
        tasks = _pending_tasks.get(device_id, [])
        
        if not tasks:
            return jsonify({
                "task_id": None,
                "message": "No pending tasks"
            })
        
        # Pop the oldest task (FIFO)
        task = tasks.pop(0)
        
        print(f"[LOCAL_AGENT] Task dispatched to {device_id[:8]}...: {task['command']}")
        
        return jsonify({
            "task_id": task['task_id'],
            "command": task['command'],
            "params": task['params']
        })
        
    except Exception as e:
        print(f"[LOCAL_AGENT] Poll error: {e}")
        return jsonify({"error": str(e)}), 500


@local_agent_bp.route('/report', methods=['POST', 'OPTIONS'])
@require_device_auth
def agent_report():
    """
    Report task execution result.
    
    Request:
        {
            "device_id": "xxx",
            "task_id": "uuid",
            "status": "success" | "error",
            "result": {...},
            "screenshot_b64": "optional-base64"
        }
    
    Response:
        {"success": true}
    """
    if request.method == 'OPTIONS':
        return _build_cors_response()
    
    try:
        data = request.get_json() or {}
        device_id = g.device_id
        task_id = data.get('task_id')
        status = data.get('status', 'unknown')
        result = data.get('result', {})
        screenshot_b64 = data.get('screenshot_b64')
        
        if not task_id:
            return jsonify({"success": False, "error": "task_id required"}), 400
        
        # Store result
        _task_results[task_id] = {
            "device_id": device_id,
            "status": status,
            "result": result,
            "has_screenshot": bool(screenshot_b64),
            "reported_at": datetime.now().isoformat()
        }
        
        # Update device last seen
        _registered_devices[device_id]['last_seen'] = datetime.now().isoformat()
        
        print(f"[LOCAL_AGENT] Task {task_id[:8]}... reported: {status}")
        
        return jsonify({
            "success": True,
            "message": f"Result recorded for task {task_id[:8]}..."
        })
        
    except Exception as e:
        print(f"[LOCAL_AGENT] Report error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@local_agent_bp.route('/heartbeat', methods=['POST', 'OPTIONS'])
@require_device_auth
def agent_heartbeat():
    """
    Keep device marked as online.
    
    Request:
        {"device_id": "xxx"}
    
    Response:
        {"success": true, "server_time": "iso8601"}
    """
    if request.method == 'OPTIONS':
        return _build_cors_response()
    
    try:
        device_id = g.device_id
        
        # Update last seen in memory
        _registered_devices[device_id]['last_seen'] = datetime.now().isoformat()
        
        # Sync to Firebase
        user_id = _registered_devices[device_id].get('user_id')
        _update_device_heartbeat(device_id, user_id)
        
        return jsonify({
            "success": True,
            "server_time": datetime.now().isoformat(),
            "device_name": _registered_devices[device_id]['name']
        })
        
    except Exception as e:
        print(f"[LOCAL_AGENT] Heartbeat error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== ADMIN ENDPOINTS (for queuing tasks) ====================

@local_agent_bp.route('/queue-task', methods=['POST', 'OPTIONS'])
def queue_task():
    """
    Queue a task for a specific device (called by Kai cloud/web interface).
    
    SECURITY: Caller must own the target device (verified via user_id).
    
    Request:
        {
            "device_id": "xxx",
            "command": "open_app",
            "params": {"app": "browser"}
        }
    
    Response:
        {"success": true, "task_id": "uuid"}
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', 'http://localhost:3000')
        allowed_origins = ['http://localhost:3000', 'https://kai2010.netlify.app', 'https://kai-frontend.onrender.com']
        if origin in allowed_origins or origin.endswith('.netlify.app') or origin.endswith('.onrender.com'):
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            response.headers['Access-Control-Allow-Origin'] = 'https://kai2010.netlify.app'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-User-ID'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response, 200
    
    try:
        data = request.get_json() or {}
        device_id = data.get('device_id')
        command = data.get('command')
        params = data.get('params', {})
        
        if not device_id:
            return jsonify({"success": False, "error": "device_id required"}), 400
        
        if device_id not in _registered_devices:
            return jsonify({"success": False, "error": "Device not registered"}), 404
        
        if not command:
            return jsonify({"success": False, "error": "command required"}), 400
        
        # SECURITY: Get authenticated user and verify ownership
        user_id = get_authenticated_user_id()
        device = _registered_devices[device_id]
        device_owner = device.get('user_id', '')
        
        # Allow if: user owns device OR internal request (localhost with X-User-ID)
        is_internal = request.remote_addr in ['127.0.0.1', 'localhost', '::1']
        
        if not is_internal:
            # External request - must verify ownership
            if not user_id:
                return jsonify({"success": False, "error": "Authentication required"}), 401
            if device_owner != user_id:
                print(f"[SECURITY] User {user_id[:8]}... denied access to device owned by {device_owner[:8]}...")
                return jsonify({"success": False, "error": "Access denied"}), 403
        else:
            # Internal request - use provided user_id for audit
            user_id = user_id or device_owner or "internal"
        
        # Create task
        task_id = str(uuid.uuid4())
        task = {
            "task_id": task_id,
            "command": command,
            "params": params,
            "user_id": user_id,  # Track who queued the command
            "created_at": datetime.now().isoformat()
        }
        
        # TRY WEBSOCKET FIRST (instant delivery)
        ws_sent = False
        try:
            from Backend.AgentWebSocket import is_agent_connected, send_task_sync
            if is_agent_connected(device_id):
                ws_sent = send_task_sync(device_id, task_id, command, params)
                if ws_sent:
                    print(f"[LOCAL_AGENT] ⚡ Task sent via WebSocket to {device_id[:8]}...")
        except Exception as ws_err:
            print(f"[LOCAL_AGENT] WebSocket push failed: {ws_err}")
        
        # FALLBACK: Add to polling queue if WS failed
        if not ws_sent:
            if device_id not in _pending_tasks:
                _pending_tasks[device_id] = []
            _pending_tasks[device_id].append(task)
            print(f"[LOCAL_AGENT] Task queued for polling: {device_id[:8]}...")
        
        # Audit log
        log_command(user_id, device_id, command, params, "queued" if not ws_sent else "sent_ws")
        
        print(f"[LOCAL_AGENT] Task {'sent' if ws_sent else 'queued'} for {device_id[:8]}...: {command} (by user {user_id[:8] if user_id else 'internal'}...)")
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "delivery": "websocket" if ws_sent else "polling",
            "message": f"Task '{command}' {'sent' if ws_sent else 'queued'} for device"
        })
        
    except Exception as e:
        print(f"[LOCAL_AGENT] Queue task error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@local_agent_bp.route('/devices', methods=['GET', 'OPTIONS'])
def list_devices():
    """
    List devices owned by the authenticated user.
    
    SECURITY: Only returns devices belonging to the caller's user_id.
    
    Response:
        {"devices": [{device_id, name, last_seen, is_online}]}
    """
    # Handle CORS preflight - Return explicit headers, bypass Flask-CORS
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', 'http://localhost:3000')
        allowed_origins = ['http://localhost:3000', 'https://kai2010.netlify.app', 'https://kai-frontend.onrender.com']
        if origin in allowed_origins or origin.endswith('.netlify.app') or origin.endswith('.onrender.com'):
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            response.headers['Access-Control-Allow-Origin'] = 'https://kai2010.netlify.app'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-User-ID'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response, 200
    
    try:
        # Get authenticated user
        user_id = get_authenticated_user_id()
        is_internal = request.remote_addr in ['127.0.0.1', 'localhost', '::1']
        
        devices = []
        now = datetime.now()
        
        for device_id, info in _registered_devices.items():
            device_owner = info.get('user_id', '')
            
            # SECURITY: Only show user's own devices (or all for internal requests)
            if not is_internal and user_id and device_owner != user_id:
                continue  # Skip devices not owned by this user
            
            last_seen = datetime.fromisoformat(info['last_seen'])
            is_online = (now - last_seen).total_seconds() < 60  # Online if seen in last 60s
            
            devices.append({
                "device_id": device_id,
                "name": info['name'],
                "registered_at": info['registered_at'],
                "last_seen": info['last_seen'],
                "is_online": is_online,
                "user_id": device_owner[:8] + "..." if device_owner else None  # Partial for reference
            })
        
        response = jsonify({
            "success": True,
            "devices": devices,
            "count": len(devices),
            "user_id": user_id[:8] + "..." if user_id else None
        })
        return response
        
    except Exception as e:
        print(f"[LOCAL_AGENT] List devices error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== BLUEPRINT REGISTRATION HELPER ====================


# ==================== BLUEPRINT REGISTRATION HELPER ====================

def register_local_agent_api(app):
    """
    Register the Local Agent API blueprint with a Flask app.
    
    Usage in api_server.py:
        from Backend.LocalAgentAPI import register_local_agent_api
        register_local_agent_api(app)
    """
    app.register_blueprint(local_agent_bp)
    print("[LOCAL_AGENT] API endpoints registered at /agent/*")
    # CORS is handled by Flask-CORS in api_server.py - no duplicate handler needed
