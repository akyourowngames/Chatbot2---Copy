"""
KAI OS - Rate Limiter
====================
Prevents API abuse with configurable rate limits per endpoint.
"""

import time
from collections import defaultdict
from functools import wraps
from flask import request, jsonify, g
from typing import Dict, Tuple, Optional
import threading

class RateLimiter:
    """Token bucket rate limiter with per-IP and per-user tracking."""
    
    def __init__(self, default_limit: int = 60, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            default_limit: Default requests per window
            window_seconds: Time window in seconds
        """
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = threading.Lock()
        
        # Endpoint-specific limits
        self.limits = {
            "chat": 30,           # Chat requests
            "auth": 10,           # Authentication attempts
            "image_gen": 5,       # Image generation
            "heavy": 10,          # Heavy operations
            "default": 60,        # Default limit
        }
    
    def _get_client_key(self) -> str:
        """Get unique key for the client (IP + optional user ID)."""
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip:
            ip = ip.split(',')[0].strip()  # Get first IP if behind proxy
        
        # Include user ID if authenticated
        user_id = ""
        if hasattr(request, 'current_user') and request.current_user:
            user_id = request.current_user.get('user_id', '')
        
        return f"{ip}:{user_id}"
    
    def _clean_old_requests(self, key: str, now: float) -> None:
        """Remove requests outside the current window."""
        cutoff = now - self.window_seconds
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]
    
    def is_allowed(self, category: str = "default") -> Tuple[bool, Dict]:
        """
        Check if request is allowed within rate limit.
        
        Returns:
            Tuple of (allowed, rate_info)
        """
        with self.lock:
            key = f"{self._get_client_key()}:{category}"
            now = time.time()
            
            # Clean old requests
            self._clean_old_requests(key, now)
            
            # Get limit for this category
            limit = self.limits.get(category, self.default_limit)
            current_count = len(self.requests[key])
            
            rate_info = {
                "limit": limit,
                "remaining": max(0, limit - current_count),
                "reset": int(now + self.window_seconds),
                "category": category,
            }
            
            if current_count >= limit:
                return False, rate_info
            
            # Record this request
            self.requests[key].append(now)
            rate_info["remaining"] = limit - current_count - 1
            
            return True, rate_info
    
    def get_headers(self, rate_info: Dict) -> Dict[str, str]:
        """Get rate limit headers for response."""
        return {
            "X-RateLimit-Limit": str(rate_info["limit"]),
            "X-RateLimit-Remaining": str(rate_info["remaining"]),
            "X-RateLimit-Reset": str(rate_info["reset"]),
        }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None

def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

def rate_limit(category: str = "default", enabled: bool = True):
    """
    Decorator to apply rate limiting to an endpoint.
    
    Usage:
        @app.route('/api/v1/chat', methods=['POST'])
        @rate_limit("chat")
        def chat():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not enabled:
                return f(*args, **kwargs)
            
            limiter = get_rate_limiter()
            allowed, rate_info = limiter.is_allowed(category)
            
            # Store rate info for response headers
            g.rate_limit_info = rate_info
            
            if not allowed:
                response = jsonify({
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Try again in {rate_info['reset'] - int(time.time())} seconds.",
                    "category": category,
                    "limit": rate_info["limit"],
                    "retry_after": rate_info["reset"] - int(time.time()),
                })
                response.status_code = 429
                
                # Add rate limit headers
                for key, value in limiter.get_headers(rate_info).items():
                    response.headers[key] = value
                response.headers["Retry-After"] = str(rate_info["reset"] - int(time.time()))
                
                return response
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def add_rate_limit_headers(response):
    """Add rate limit headers to response (use as after_request handler)."""
    if hasattr(g, 'rate_limit_info'):
        limiter = get_rate_limiter()
        for key, value in limiter.get_headers(g.rate_limit_info).items():
            response.headers[key] = value
    return response


# Example rate limit categories with custom limits
def configure_rate_limits(limits: Dict[str, int]) -> None:
    """Configure custom rate limits."""
    limiter = get_rate_limiter()
    limiter.limits.update(limits)


# Convenience decorators for common categories
def rate_limit_chat(f):
    """Rate limit for chat endpoints."""
    return rate_limit("chat")(f)

def rate_limit_auth(f):
    """Rate limit for auth endpoints (stricter)."""
    return rate_limit("auth")(f)

def rate_limit_heavy(f):
    """Rate limit for heavy operations."""
    return rate_limit("heavy")(f)

def rate_limit_image(f):
    """Rate limit for image generation."""
    return rate_limit("image_gen")(f)
