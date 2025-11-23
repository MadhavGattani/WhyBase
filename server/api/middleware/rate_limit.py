# server/api/middleware/rate_limit.py
import time
from functools import wraps
from flask import request, jsonify
from collections import defaultdict
from threading import Lock

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = Lock()
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        """
        Check if request is allowed under rate limit
        Returns: (is_allowed, retry_after_seconds)
        """
        now = time.time()
        window_start = now - window_seconds
        
        with self.lock:
            # Clean old requests
            self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]
            
            # Check limit
            if len(self.requests[key]) >= max_requests:
                oldest_request = min(self.requests[key])
                retry_after = int(oldest_request + window_seconds - now) + 1
                return False, retry_after
            
            # Add new request
            self.requests[key].append(now)
            return True, 0
    
    def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """Remove old entries to prevent memory leak"""
        now = time.time()
        cutoff = now - max_age_seconds
        
        with self.lock:
            keys_to_delete = []
            for key, times in self.requests.items():
                # Keep only recent requests
                self.requests[key] = [t for t in times if t > cutoff]
                # Mark empty keys for deletion
                if not self.requests[key]:
                    keys_to_delete.append(key)
            
            # Delete empty keys
            for key in keys_to_delete:
                del self.requests[key]

# Global rate limiter instance
rate_limiter = RateLimiter()

def get_client_key() -> str:
    """Get unique identifier for client"""
    # Try to get user ID from auth
    if hasattr(request, 'user') and request.user:
        return f"user:{request.user.get('sub', 'unknown')}"
    
    # Fall back to IP address
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    else:
        ip = request.remote_addr
    
    return f"ip:{ip}"

def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    Rate limiting decorator
    
    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            key = get_client_key()
            
            is_allowed, retry_after = rate_limiter.is_allowed(
                key, 
                max_requests, 
                window_seconds
            )
            
            if not is_allowed:
                return jsonify({
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please try again in {retry_after} seconds.",
                    "retry_after": retry_after
                }), 429
            
            return f(*args, **kwargs)
        
        return wrapped
    return decorator

def rate_limit_strict(max_requests: int = 10, window_seconds: int = 60):
    """Stricter rate limiting for sensitive endpoints"""
    return rate_limit(max_requests, window_seconds)