from flask import request, jsonify
from functools import wraps

API_KEYS = {
    "demo_key_12345": {"name": "Demo User", "tier": "free"},
    "pro_key_67890": {"name": "Pro User", "tier": "pro"}
}

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "API key required"}), 401
        
        if api_key not in API_KEYS:
            return jsonify({"error": "Invalid API key"}), 401
            
        return f(*args, **kwargs)
    return decorated_function
