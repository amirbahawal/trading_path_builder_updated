"""
Environment variable validation for production deployment
"""
import os
import sys
from typing import List, Dict, Optional
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when environment variable validation fails"""
    pass


def validate_required_vars(env: str) -> List[str]:
    """
    Validate required environment variables based on environment.
    
    Args:
        env: Environment name ('development' or 'production')
        
    Returns:
        List of missing required variables
    """
    missing = []
    
    # Core required variables (always needed)
    core_required = [
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "JWT_SECRET",
    ]
    
    # Production-specific requirements
    if env == "production":
        production_required = [
            "FRONTEND_URL",
            "BACKEND_HOST",
        ]
        
        # Payment integration removed - instant unlock only
        pass
        
        # Check for production JWT secret (should not be default)
        if settings.JWT_SECRET == "dev_secret_change_in_production":
            missing.append("JWT_SECRET (must be changed from default in production)")
        
        # Check for HTTPS in production URLs
        frontend_url = os.getenv("FRONTEND_URL", "")
        backend_host = os.getenv("BACKEND_HOST", "")
        
        if frontend_url and not frontend_url.startswith("https://"):
            logger.warning(f"FRONTEND_URL should use HTTPS in production: {frontend_url}")
        
        if backend_host and not backend_host.startswith("https://"):
            logger.warning(f"BACKEND_HOST should use HTTPS in production: {backend_host}")
        
        required_vars = core_required + production_required
    else:
        required_vars = core_required
    
    # Check each required variable
    for var in required_vars:
        value = os.getenv(var, "")
        if not value or value.strip() == "":
            missing.append(var)
    
    return missing


def validate_environment(env: str) -> Dict[str, any]:
    """
    Comprehensive environment validation.
    
    Args:
        env: Environment name
        
    Returns:
        Dictionary with validation results
        
    Raises:
        ValidationError: If critical validation fails
    """
    results = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "missing_vars": []
    }
    
    # Validate required variables
    missing = validate_required_vars(env)
    if missing:
        results["missing_vars"] = missing
        if env == "production":
            results["valid"] = False
            results["errors"].extend([f"Missing required variable: {var}" for var in missing])
        else:
            results["warnings"].extend([f"Missing recommended variable: {var}" for var in missing])
    
    # Validate database URL format
    db_url = settings.DATABASE_URL
    if db_url and not db_url.startswith(("sqlite:///", "postgresql://", "postgres://", "mysql://")):
        results["warnings"].append(f"DATABASE_URL format may be invalid: {db_url[:50]}...")
    
    # Validate JWT secret strength in production
    if env == "production":
        jwt_secret = settings.JWT_SECRET
        if len(jwt_secret) < 32:
            results["errors"].append("JWT_SECRET must be at least 32 characters in production")
            results["valid"] = False
    
    # Validate OpenAI API key format
    openai_key = settings.OPENAI_API_KEY
    if openai_key and not openai_key.startswith("sk-"):
        results["warnings"].append("OPENAI_API_KEY format may be invalid")
    
    # Payment validation removed - instant unlock only (no Stripe/payment checks)
    
    # Validate URLs
    frontend_url = settings.FRONTEND_URL
    if frontend_url and "://" not in frontend_url:
        results["warnings"].append(f"FRONTEND_URL should include protocol: {frontend_url}")
    
    # Check for production safety issues
    if env == "production":
        # Warn about debug mode
        if settings.ENV == "development":
            results["errors"].append("ENV should be 'production' in production deployment")
            results["valid"] = False
    
    return results


def validate_and_exit(env: str):
    """
    Validate environment and exit if critical errors found.
    
    Args:
        env: Environment name
        
    Raises:
        SystemExit: If validation fails in production
    """
    results = validate_environment(env)
    
    # Log warnings
    for warning in results["warnings"]:
        logger.warning(f"[VALIDATION] {warning}")
    
    # Log errors
    for error in results["errors"]:
        logger.error(f"[VALIDATION] {error}")
    
    # Log missing variables
    if results["missing_vars"]:
        logger.error(f"[VALIDATION] Missing required variables: {', '.join(results['missing_vars'])}")
    
    # Exit if validation fails in production
    if env == "production" and not results["valid"]:
        logger.critical("[VALIDATION] Environment validation failed. Application will not start.")
        logger.critical("[VALIDATION] Please fix the errors above and restart.")
        raise ValidationError("Environment validation failed. See logs for details.")
    
    # Log success
    if results["valid"]:
        logger.info("[VALIDATION] Environment validation passed")
    else:
        logger.warning("[VALIDATION] Environment validation passed with warnings")

