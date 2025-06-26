"""
Sales BI Dashboard Configuration Module

This module provides centralized configuration management for:
- Database connections
- Application settings
- Authentication configuration
"""

# Import main configuration
from .settings import (
    config,
    Config,
    DB_CONFIG,
    AUTH_CONFIG,
    APP_CONFIG,
    IS_DEBUG,
    TIMEZONE
)

# Import database management
from .database import (
    DatabaseManager,
    db_manager,
    get_db_engine,
    query_data,
    with_db_retry
)

# Version info
__version__ = "1.0.0"
__author__ = "Sales BI Team"

# All exports
__all__ = [
    # Settings
    "config",
    "Config", 
    "DB_CONFIG",
    "AUTH_CONFIG",
    "APP_CONFIG",
    "IS_DEBUG",
    "TIMEZONE",
    
    # Database
    "DatabaseManager",
    "db_manager",
    "get_db_engine",
    "query_data",
    "with_db_retry",
]