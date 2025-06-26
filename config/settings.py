"""
Main configuration module for Sales BI Dashboard
Handles environment detection and configuration loading
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    """Configuration management for Sales BI Dashboard"""
    
    def __init__(self):
        self.is_cloud = self._detect_streamlit_cloud()
        self.config = self._load_config()
        
    def _detect_streamlit_cloud(self) -> bool:
        """Detect if running on Streamlit Cloud"""
        try:
            import streamlit as st
            return hasattr(st, 'secrets') and "DB_CONFIG" in st.secrets
        except Exception:
            return False
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration based on environment"""
        if self.is_cloud:
            return self._load_cloud_config()
        else:
            return self._load_local_config()
    
    def _load_cloud_config(self) -> Dict[str, Any]:
        """Load configuration from Streamlit secrets"""
        import streamlit as st
        
        logger.info("☁️ Loading Streamlit Cloud configuration")
        
        return {
            "database": dict(st.secrets["DB_CONFIG"]),
            "api": {
                "exchange_rate_key": st.secrets.get("API", {}).get("EXCHANGE_RATE_API_KEY", ""),
            },
            "auth": dict(st.secrets.get("AUTH_CONFIG", {})),
            "app": dict(st.secrets.get("APP_CONFIG", {})),
            "gcp": dict(st.secrets.get("gcp_service_account", {}))
        }
    
    def _load_local_config(self) -> Dict[str, Any]:
        """Load configuration from .env file"""
        load_dotenv()
        
        logger.info("💻 Loading local configuration")
        
        # Helper function to safely convert to int
        def safe_int(value: str, default: int) -> int:
            """Convert string to int, handling comments and errors"""
            if value:
                # Remove inline comments
                value = value.split('#')[0].strip()
                try:
                    return int(value)
                except ValueError:
                    logger.warning(f"Invalid integer value: {value}, using default: {default}")
            return default
        
        # Load GCP credentials if exists
        gcp_creds = {}
        creds_path = Path("credentials.json")
        if creds_path.exists():
            with open(creds_path) as f:
                gcp_creds = json.load(f)
        
        return {
            "database": {
                "host": os.getenv("DB_HOST", "erp-all-production.cx1uaj6vj8s5.ap-southeast-1.rds.amazonaws.com"),
                "port": safe_int(os.getenv("DB_PORT"), 3306),
                "user": os.getenv("DB_USER", "streamlit_user"),
                "password": os.getenv("DB_PASSWORD", ""),
                "database": os.getenv("DB_NAME", "prostechvn"),
                "pool_size": safe_int(os.getenv("DB_POOL_SIZE"), 5),
                "pool_recycle": safe_int(os.getenv("DB_POOL_RECYCLE"), 3600),
            },
            "api": {
                "exchange_rate_key": os.getenv("EXCHANGE_RATE_API_KEY", ""),
            },
            "auth": {
                "session_timeout": safe_int(os.getenv("SESSION_TIMEOUT"), 3600),
                "max_attempts": safe_int(os.getenv("MAX_LOGIN_ATTEMPTS"), 3),
                "lockout_duration": safe_int(os.getenv("LOCKOUT_DURATION"), 900),
            },
            "app": {
                "name": os.getenv("APP_NAME", "Sales BI Dashboard"),
                "version": os.getenv("APP_VERSION", "1.0.0"),
                "debug": os.getenv("DEBUG", "False").lower() == "true",
                "timezone": os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh"),
                "cache_ttl": safe_int(os.getenv("CACHE_TTL"), 300),
            },
            "gcp": gcp_creds
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_db_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.config.get("database", {})
    
    def get_auth_config(self) -> Dict[str, Any]:
        """Get authentication configuration"""
        return self.config.get("auth", {})
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration"""
        return self.config.get("app", {})
    
    def __repr__(self) -> str:
        env = "CLOUD" if self.is_cloud else "LOCAL"
        return f"<Config env={env}>"


# Create singleton instance
config = Config()

# Export commonly used values
DB_CONFIG = config.get_db_config()
AUTH_CONFIG = config.get_auth_config()
APP_CONFIG = config.get_app_config()
IS_DEBUG = config.get("app.debug", False)
TIMEZONE = config.get("app.timezone", "Asia/Ho_Chi_Minh")