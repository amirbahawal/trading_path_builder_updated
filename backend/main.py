from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Import routers
from routers import quiz, plan, checkout, auth
from routers.analytics import setup_analytics, router as analytics_router
from database.connection import init_db, SessionLocal
from core.config import settings
from core.validation import validate_and_exit
from core.logging_config import setup_logging
from middleware.security import HTTPSRedirectMiddleware, SecurityHeadersMiddleware

# Load environment variables
load_dotenv()

# Determine environment
ENV = os.getenv("ENV", "development").lower()

# Setup logging first (before validation)
setup_logging(ENV)
logger = logging.getLogger(__name__)

# Validate environment variables
try:
    validate_and_exit(ENV)
except Exception as e:
    logger.critical(f"Environment validation failed: {e}")
    if ENV == "production":
        raise
    logger.warning("Continuing in development mode despite validation warnings")

# Create FastAPI app
app = FastAPI(
    title="Trading Path Builder API",
    description="Backend API for personalized trading education paths",
    version="2.1"
)

# Store environment in app state
app.state.environment = ENV

# Initialize database
init_db()

# Setup analytics
setup_analytics(app)

# Security middleware (HTTPS enforcement and headers)
if ENV == "production":
    app.add_middleware(HTTPSRedirectMiddleware, environment=ENV)
app.add_middleware(SecurityHeadersMiddleware, environment=ENV)

# CORS Configuration
def get_allowed_origins():
    """Get allowed CORS origins based on environment"""
    origins = []
    
    if ENV == "development":
        # Development: Allow localhost on common ports and network IPs
        frontend_port = os.getenv("FRONTEND_PORT", "3000")
        origins = [
            f"http://localhost:{frontend_port}",
            f"http://localhost:3000",
            f"http://localhost:3001",
            f"http://127.0.0.1:{frontend_port}",
            f"http://127.0.0.1:3000",
            f"http://127.0.0.1:3001",
        ]
        
        # Add common network IP patterns for development (192.168.x.x, 10.x.x.x)
        # User can add specific IP via ALLOWED_ORIGINS env var
    else:
        # Production: Only allow configured frontend URL
        frontend_url = settings.FRONTEND_URL or os.getenv("FRONTEND_URL", "")
        if frontend_url:
            origins = [frontend_url]
            # Also allow without trailing slash
            if frontend_url.endswith("/"):
                origins.append(frontend_url.rstrip("/"))
            else:
                origins.append(f"{frontend_url}/")
        else:
            logger.warning("FRONTEND_URL not set - CORS may be too restrictive")
    
    # Add any additional origins from environment
    additional_origins = settings.ALLOWED_ORIGINS or os.getenv("ALLOWED_ORIGINS", "")
    if additional_origins:
        origins.extend([origin.strip() for origin in additional_origins.split(",") if origin.strip()])
    
    return list(set(origins))  # Remove duplicates

origins = get_allowed_origins()
logger.info(f"CORS allowed origins: {origins}")

# CORS Configuration
# Note: Cannot use "*" with allow_credentials=True, so we use explicit origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add global error handler for HTTPException (FastAPI's built-in exceptions)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException with CORS headers"""
    from fastapi.responses import JSONResponse
    
    # Create response with CORS headers
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error": f"HTTP {exc.status_code}"}
    )
    
    # Add CORS headers
    origin = request.headers.get("origin")
    allowed_origins = get_allowed_origins()
    if origin and (origin in allowed_origins or settings.ENV == "development"):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    return response

# Add global error handler for all other exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with CORS headers"""
    from fastapi.responses import JSONResponse
    
    timestamp = datetime.utcnow().isoformat()
    path = str(request.url)
    
    logger.error(f"[{timestamp}] Error on {path}: {exc}", exc_info=True)
    
    # Hide stack traces in production
    if settings.ENV == "development":
        detail = {
            "error": "Internal Server Error",
            "message": str(exc),
            "type": type(exc).__name__,
            "path": path,
            "timestamp": timestamp
        }
    else:
        detail = {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    
    # Return JSONResponse with CORS headers
    response = JSONResponse(
        status_code=500,
        content={"detail": detail}
    )
    
    # Add CORS headers for general exception responses
    origin = request.headers.get("origin")
    allowed_origins = get_allowed_origins()
    
    # In development, be more permissive with CORS
    if settings.ENV == "development":
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
        else:
            # Fallback: allow common development origins
            response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    else:
        # Production: only allow configured origins
        if origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    return response

# Include routers
app.include_router(quiz.router, prefix="/quiz", tags=["Quiz"])
app.include_router(plan.router, prefix="/plan", tags=["Plan"])
app.include_router(checkout.router, prefix="/checkout", tags=["Checkout"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(analytics_router, tags=["Analytics"])

# Add debug router only in development
if settings.ENV == "development":
    try:
        from routers import debug
        app.include_router(debug.router, prefix="/debug", tags=["Debug"])
        logger.info("Debug router loaded (development mode)")
    except Exception as e:
        logger.warning(f"Could not load debug router: {e}")

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - API health check
    """
    return {
        "message": "Trading Path Builder API",
        "status": "running",
        "version": "2.1",
        "endpoints": {
            "docs": "/docs",
            "quiz": "/quiz",
            "plan": "/plan",
            "checkout": "/checkout",
            "auth": "/auth",
            "health": "/health"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint with system status
    """
    db_connected = False
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_connected = True
    except Exception as e:
        logger.error(f"Database check failed: {e}")
    
    return {
        "status": "healthy",
        "unlock_mode": "instant",  # Instant unlock - no payment required
        "database_connected": db_connected,
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "version": "v2.1",
        "environment": settings.ENV
    }


# Uptime monitoring endpoint
@app.get("/uptime")
async def uptime_check():
    """
    Uptime monitoring endpoint for external monitoring services.
    Returns minimal response for quick health checks.
    """
    import time
    from datetime import datetime, timedelta
    
    # Check database connectivity
    db_healthy = False
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_healthy = True
    except:
        pass
    
    # Calculate uptime (simplified - in production, store startup time)
    startup_time = getattr(app.state, "startup_time", datetime.utcnow())
    uptime_seconds = int((datetime.utcnow() - startup_time).total_seconds())
    
    return {
        "status": "up" if db_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime_seconds,
        "database": "connected" if db_healthy else "disconnected"
    }

# 404 handler is now handled by HTTPException handler above
# No need for separate 404 handler - FastAPI will raise HTTPException(404) automatically

# Startup event
@app.on_event("startup")
async def startup_event():
    """Print startup information and validate configuration"""
    from datetime import datetime
    
    # Store startup time for uptime calculation
    app.state.startup_time = datetime.utcnow()
    
    logger.info("=" * 50)
    logger.info("Trading Path Builder API Starting")
    logger.info("=" * 50)
    logger.info(f"Environment: {ENV}")
    logger.info(f"Unlock mode: Instant unlock (no payment required)")
    logger.info(f"Database: {settings.DATABASE_URL[:50]}..." if len(settings.DATABASE_URL) > 50 else f"Database: {settings.DATABASE_URL}")
    logger.info(f"OpenAI model: {settings.OPENAI_MODEL}")
    logger.info(f"Template version: {settings.TEMPLATE_VERSION}")
    logger.info(f"Frontend URL: {settings.FRONTEND_URL}")
    logger.info(f"Backend Host: {settings.BACKEND_HOST}")
    logger.info(f"CORS Origins: {len(origins)} configured")
    
    if ENV == "production":
        logger.info("🔒 Production mode: HTTPS enforcement enabled")
        logger.info("🔒 Security headers enabled")
        logger.info("📝 Logging to files enabled")
    else:
        logger.info("🔧 Development mode: Relaxed security")
    
    logger.info("=" * 50)
    
    # Email delivery config check (Gmail SMTP)
    gmail_address = os.getenv("GMAIL_ADDRESS", "")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "")
    
    if not gmail_address or not gmail_app_password:
        logger.warning("GMAIL_ADDRESS or GMAIL_APP_PASSWORD missing: Email sends will operate in mock mode only!")
        logger.warning("To enable email: Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env file")
    else:
        logger.info(f"Gmail SMTP configured: Using {gmail_address}")
        logger.info("Email OTP codes will be sent via Gmail SMTP")
    
    # Log validation status
    from core.validation import validate_environment
    validation_results = validate_environment(ENV)
    if validation_results["warnings"]:
        logger.warning(f"Configuration warnings: {len(validation_results['warnings'])}")
    if validation_results["errors"]:
        logger.error(f"Configuration errors: {len(validation_results['errors'])}")
    
    logger.info("✅ Application startup complete")