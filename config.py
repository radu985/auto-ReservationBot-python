#!/usr/bin/env python3
"""
Production Configuration for VFS Global Guinea-Bissau Automation
Centralized configuration management for all components
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DOCS_DIR = BASE_DIR / "documents"
INFO_DIR = BASE_DIR / "info"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Ensure directories exist
for directory in [DATA_DIR, LOGS_DIR, DOCS_DIR, INFO_DIR, TEMPLATES_DIR, STATIC_DIR]:
    directory.mkdir(exist_ok=True)

# VFS Global Configuration
VFS_CONFIG = {
    "base_url": "https://visa.vfsglobal.com",
    "booking_url": "https://visa.vfsglobal.com/gnb/pt/prt/book-appointment",
    "login_url": "https://visa.vfsglobal.com/gnb/pt/prt/login",
    "monitoring_duration": 4,  # minutes
    "max_clients_per_session": 5,
    "check_interval": 30,  # seconds between checks
}

# Browser Configuration
BROWSER_CONFIG = {
    "headless": True,
    "use_playwright": True,
    "viewport_width": 1920,
    "viewport_height": 1080,
    "user_agent_rotation": True,
    "stealth_mode": True,
}

# Rate Limiting Configuration
RATE_LIMITING = {
    "min_delay": 3,  # seconds
    "max_delay": 8,  # seconds
    "max_retries": 5,
    "consecutive_error_limit": 3,
    "backoff_multiplier": 1.5,
}

# Cloudflare Bypass Configuration
CLOUDFLARE_BYPASS = {
    "enabled": True,
    "max_attempts": 10,
    "strategies": [
        "advanced_stealth",
        "proxy_rotation", 
        "captcha_solving",
        "browser_restart",
        "selenium_fallback",
        "basic_bypass",
        "enhanced_ua_rotation",
        "header_spoofing",
        "javascript_challenge",
        "multi_browser"
    ],
    "wait_timeout": 30,  # seconds
}

# Proxy Configuration
PROXY_CONFIG = {
    "enabled": True,
    "rotation_enabled": True,
    "test_timeout": 10,  # seconds
    "max_retries": 3,
    "fallback_to_direct": True,
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": LOGS_DIR / "vfs_automation.log",
    "max_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
}

# Mobile App Configuration
MOBILE_CONFIG = {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": False,
    "secret_key": "vfs_booking_mobile_app_2024_secure",
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "allowed_extensions": {".jpg", ".jpeg", ".png", ".pdf"},
}

# Security Configuration
SECURITY_CONFIG = {
    "encrypt_passwords": False,  # Set to True in production
    "session_timeout": 3600,  # 1 hour
    "max_login_attempts": 5,
    "password_min_length": 8,
}

# File Upload Configuration
UPLOAD_CONFIG = {
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "allowed_types": ["image/jpeg", "image/png", "application/pdf"],
    "save_path": DOCS_DIR,
    "metadata_path": DOCS_DIR / "_metadata",
}

# Database Configuration (for future SQLite migration)
DATABASE_CONFIG = {
    "type": "csv",  # "csv" or "sqlite"
    "csv_path": DATA_DIR / "clients.csv",
    "sqlite_path": DATA_DIR / "clients.db",
}

# Notification Configuration
NOTIFICATION_CONFIG = {
    "email_enabled": False,
    "telegram_enabled": False,
    "webhook_enabled": False,
    "success_notifications": True,
    "error_notifications": True,
}

# Development/Production Environment Detection
def is_production() -> bool:
    """Detect if running in production environment."""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"

def get_config() -> Dict:
    """Get complete configuration based on environment."""
    config = {
        "vfs": VFS_CONFIG,
        "browser": BROWSER_CONFIG,
        "rate_limiting": RATE_LIMITING,
        "cloudflare_bypass": CLOUDFLARE_BYPASS,
        "proxy": PROXY_CONFIG,
        "logging": LOGGING_CONFIG,
        "mobile": MOBILE_CONFIG,
        "security": SECURITY_CONFIG,
        "upload": UPLOAD_CONFIG,
        "database": DATABASE_CONFIG,
        "notification": NOTIFICATION_CONFIG,
        "production": is_production(),
    }
    
    # Override with environment variables if in production
    if is_production():
        config["mobile"]["debug"] = False
        config["logging"]["level"] = "WARNING"
        config["security"]["encrypt_passwords"] = True
    
    return config

# Export configuration
CONFIG = get_config()
