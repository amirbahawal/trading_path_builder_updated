"""
Security middleware for production deployment
Includes HTTPS enforcement and security headers
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce HTTPS in production.
    Redirects HTTP requests to HTTPS.
    """
    def __init__(self, app, environment: str = "development"):
        super().__init__(app)
        self.environment = environment
    
    async def dispatch(self, request: Request, call_next):
        # Only enforce HTTPS in production
        if self.environment == "production":
            # Check if request is over HTTPS
            if request.url.scheme != "https":
                # Check for proxy headers (common in production environments)
                forwarded_proto = request.headers.get("X-Forwarded-Proto", "")
                if forwarded_proto != "https":
                    # Get the host from the request
                    host = request.headers.get("Host", request.url.hostname)
                    # Build HTTPS URL
                    https_url = f"https://{host}{request.url.path}"
                    if request.url.query:
                        https_url += f"?{request.url.query}"
                    
                    logger.warning(f"HTTPS redirect: {request.url} -> {https_url}")
                    
                    # Return redirect response
                    from starlette.responses import RedirectResponse
                    return RedirectResponse(url=https_url, status_code=301)
        
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    """
    def __init__(self, app, environment: str = "development"):
        super().__init__(app)
        self.environment = environment
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Only add HSTS in production
        if self.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        
        return response

