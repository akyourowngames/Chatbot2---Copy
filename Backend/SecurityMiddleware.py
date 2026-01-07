"""
KAI OS - Security Middleware
===========================
Security headers, request validation, and protection middleware.
"""

import os
import re
import time
import hashlib
from functools import wraps
from flask import request, jsonify, g
from typing import Callable, Optional, Dict, Any
from datetime import datetime

# ==================== SECURITY HEADERS ====================

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(self), camera=(self)",
    "Cache-Control": "no-store, no-cache, must-revalidate, private",
}

# Add HSTS in production
IS_PRODUCTION = os.getenv("FLASK_ENV") == "production"
if IS_PRODUCTION:
    SECURITY_HEADERS["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"


def add_security_headers(response):
    """
    Add security headers to response.
    Use as Flask after_request handler.
    """
    for header, value in SECURITY_HEADERS.items():
        if header not in response.headers:
            response.headers[header] = value
    return response


# ==================== REQUEST VALIDATION ====================

# Patterns for input validation
DANGEROUS_PATTERNS = [
    r'<script[^>]*>',           # Script tags
    r'javascript:',              # JavaScript protocol
    r'on\w+\s*=',               # Event handlers
    r'data:text/html',          # Data URL with HTML
    r'\beval\s*\(',             # eval() calls
    r'\bexec\s*\(',             # exec() calls
    r'__import__',              # Python imports
    r'subprocess',              # Subprocess calls
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERNS]


def is_safe_input(value: str) -> bool:
    """Check if input doesn't contain dangerous patterns."""
    if not isinstance(value, str):
        return True
    
    for pattern in COMPILED_PATTERNS:
        if pattern.search(value):
            return False
    return True


def sanitize_input(value: Any) -> Any:
    """Recursively sanitize input data."""
    if isinstance(value, str):
        # Remove null bytes
        value = value.replace('\x00', '')
        # Limit length
        if len(value) > 50000:  # 50KB max
            value = value[:50000]
        return value
    elif isinstance(value, dict):
        return {k: sanitize_input(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [sanitize_input(v) for v in value]
    return value


def validate_request():
    """
    Validate incoming request for security issues.
    Use as Flask before_request handler.
    """
    # Skip validation for certain paths
    if request.path.startswith('/health') or request.path.startswith('/static'):
        return None
    
    # Skip validation for Local Agent endpoints (trusted)
    if request.path.startswith('/agent/'):
        return None
    
    # Check request size (10MB limit)
    if request.content_length and request.content_length > 10 * 1024 * 1024:
        return jsonify({"error": "Request too large", "max_size": "10MB"}), 413
    
    # Validate JSON body
    if request.is_json:
        try:
            data = request.get_json(silent=True)
            if data:
                # Check for dangerous patterns in string values
                def check_recursive(obj, path=""):
                    if isinstance(obj, str):
                        if not is_safe_input(obj):
                            return f"Dangerous pattern detected in {path}"
                    elif isinstance(obj, dict):
                        for k, v in obj.items():
                            result = check_recursive(v, f"{path}.{k}")
                            if result:
                                return result
                    elif isinstance(obj, list):
                        for i, v in enumerate(obj):
                            result = check_recursive(v, f"{path}[{i}]")
                            if result:
                                return result
                    return None
                
                error = check_recursive(data)
                if error:
                    return jsonify({"error": "Invalid input", "detail": error}), 400
                    
        except Exception:
            return jsonify({"error": "Invalid JSON"}), 400
    
    return None


# ==================== IP BLOCKING ====================

class IPBlocker:
    """Simple IP blocking for repeated abuse."""
    
    def __init__(self, max_violations: int = 10, block_duration: int = 3600):
        self.violations: Dict[str, list] = {}
        self.blocked: Dict[str, float] = {}
        self.max_violations = max_violations
        self.block_duration = block_duration
    
    def get_client_ip(self) -> str:
        """Get client IP from request."""
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip:
            ip = ip.split(',')[0].strip()
        return ip or "unknown"
    
    def record_violation(self, ip: str, reason: str = "") -> None:
        """Record a security violation."""
        now = time.time()
        if ip not in self.violations:
            self.violations[ip] = []
        
        # Clean old violations (last hour only)
        self.violations[ip] = [v for v in self.violations[ip] if v[0] > now - 3600]
        self.violations[ip].append((now, reason))
        
        # Block if too many violations
        if len(self.violations[ip]) >= self.max_violations:
            self.blocked[ip] = now + self.block_duration
            print(f"[SECURITY] Blocked IP {ip} for {self.block_duration}s due to violations")
    
    def is_blocked(self, ip: str) -> bool:
        """Check if IP is blocked."""
        if ip in self.blocked:
            if time.time() < self.blocked[ip]:
                return True
            else:
                # Block expired
                del self.blocked[ip]
        return False
    
    def unblock(self, ip: str) -> None:
        """Manually unblock an IP."""
        self.blocked.pop(ip, None)
        self.violations.pop(ip, None)


# Global IP blocker
_ip_blocker: Optional[IPBlocker] = None

def get_ip_blocker() -> IPBlocker:
    global _ip_blocker
    if _ip_blocker is None:
        _ip_blocker = IPBlocker()
    return _ip_blocker


def check_ip_block():
    """
    Check if client IP is blocked.
    Use as Flask before_request handler.
    """
    # Skip IP check for Local Agent endpoints
    if request.path.startswith('/agent/') or request.path.startswith('/health'):
        return None
    
    # Skip IP check for localhost in development
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip in ['127.0.0.1', 'localhost', '::1']:
        return None
    
    blocker = get_ip_blocker()
    ip = blocker.get_client_ip()
    
    if blocker.is_blocked(ip):
        return jsonify({
            "error": "Access denied",
            "message": "Your IP has been temporarily blocked due to suspicious activity.",
        }), 403
    
    return None


# ==================== REQUEST LOGGING ====================

def log_request():
    """
    Log request details for security auditing.
    Use as Flask before_request handler.
    """
    g.request_start_time = time.time()
    g.request_id = hashlib.md5(f"{time.time()}{request.remote_addr}".encode()).hexdigest()[:12]


def log_response(response):
    """
    Log response details for security auditing.
    Use as Flask after_request handler.
    """
    if hasattr(g, 'request_start_time'):
        duration = time.time() - g.request_start_time
        
        # Log slow requests
        if duration > 5.0:
            print(f"[SLOW] {request.method} {request.path} took {duration:.2f}s")
        
        # Log errors
        if response.status_code >= 400:
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            print(f"[ERROR] {response.status_code} {request.method} {request.path} from {client_ip}")
            
            # Record violation for 4xx errors that might indicate abuse
            # IMPORTANT: Skip OPTIONS requests (CORS preflight) - they are expected to fail auth
            # Also skip agent endpoints since they have their own security model
            if response.status_code in [401, 403, 429]:
                if request.method != 'OPTIONS' and not request.path.startswith('/agent/'):
                    blocker = get_ip_blocker()
                    blocker.record_violation(blocker.get_client_ip(), f"HTTP {response.status_code}")
    
    return response


# ==================== CSRF PROTECTION ====================

def generate_csrf_token() -> str:
    """Generate a CSRF token."""
    if '_csrf_token' not in g:
        g._csrf_token = hashlib.sha256(os.urandom(32)).hexdigest()
    return g._csrf_token


def verify_csrf_token(token: str) -> bool:
    """Verify a CSRF token."""
    expected = g.get('_csrf_token')
    if not expected:
        return False
    return token == expected


def csrf_protect(f: Callable) -> Callable:
    """
    Decorator to require CSRF token for state-changing operations.
    Token should be sent in X-CSRF-Token header.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            token = request.headers.get('X-CSRF-Token')
            if not token or not verify_csrf_token(token):
                return jsonify({"error": "Invalid or missing CSRF token"}), 403
        return f(*args, **kwargs)
    return decorated_function


# ==================== SETUP FUNCTION ====================

def setup_security_middleware(app):
    """
    Set up all security middleware for a Flask app.
    
    Usage:
        from Backend.SecurityMiddleware import setup_security_middleware
        setup_security_middleware(app)
    """
    # Before request handlers
    app.before_request(log_request)
    app.before_request(check_ip_block)
    app.before_request(validate_request)
    
    # After request handlers
    app.after_request(log_response)
    app.after_request(add_security_headers)
    
    print("[OK] Security middleware initialized")
