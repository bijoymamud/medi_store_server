import time
from typing import Dict, List
from fastapi import Request, HTTPException, status

class RateLimiter:
    def __init__(self, limit: int, window: int):
        """
        limit: Max number of requests allowed
        window: Window size in seconds
        """
        self.limit = limit
        self.window = window
        self.requests: Dict[str, List[float]] = {}

    def __call__(self, request: Request):
        # Fall back to "unknown" if client IP cannot be determined
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Clean up old requests outside the current window
        user_requests = self.requests.get(client_ip, [])
        user_requests = [t for t in user_requests if t > now - self.window]
        self.requests[client_ip] = user_requests
        
        if len(user_requests) >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )
        
        self.requests[client_ip].append(now)
