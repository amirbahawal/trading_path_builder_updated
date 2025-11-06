"""
Production logging configuration
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
import os


def setup_logging(env: str, log_dir: str = "./logs"):
    """
    Configure logging based on environment.
    
    Args:
        env: Environment name ('development' or 'production')
        log_dir: Directory for log files
    """
    # Create log directory if it doesn't exist
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if env == "development" else logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler (always active)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if env == "development" else logging.INFO)
    
    # Console formatter
    if env == "development":
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # File handlers (production only)
    if env == "production":
        # Application log
        app_log_file = os.path.join(log_dir, "app.log")
        app_handler = RotatingFileHandler(
            app_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        app_handler.setLevel(logging.INFO)
        app_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        root_logger.addHandler(app_handler)
        
        # Error log
        error_log_file = os.path.join(log_dir, "error.log")
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        root_logger.addHandler(error_handler)
        
        # Access log (HTTP requests)
        access_log_file = os.path.join(log_dir, "access.log")
        access_handler = RotatingFileHandler(
            access_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        access_handler.setLevel(logging.INFO)
        access_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        
        # Create access logger
        access_logger = logging.getLogger("access")
        access_logger.addHandler(access_handler)
        access_logger.setLevel(logging.INFO)
        access_logger.propagate = False
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str):
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

