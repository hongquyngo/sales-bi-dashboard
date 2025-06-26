
"""
Database connection and query management for Sales BI Dashboard
Handles connection pooling, retries, and query execution
"""
import pandas as pd
from sqlalchemy import create_engine, pool, text
from sqlalchemy.engine import Engine
from urllib.parse import quote_plus
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import time
from functools import wraps
import streamlit as st

from .settings import DB_CONFIG

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and queries with pooling and caching"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or DB_CONFIG
        self._engine: Optional[Engine] = None
        self._connection_retries = 3
        self._retry_delay = 1  # seconds
        
    def _create_connection_url(self) -> str:
        """Create database connection URL"""
        user = self.config["user"]
        password = quote_plus(str(self.config["password"]))
        host = self.config["host"]
        port = self.config["port"]
        database = self.config["database"]
        
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    
    def get_engine(self) -> Engine:
        """Get or create SQLAlchemy engine with connection pooling"""
        if self._engine is None:
            logger.info("🔌 Creating new database engine...")
            
            connection_url = self._create_connection_url()
            
            # Connection pool configuration
            pool_config = {
                "pool_size": self.config.get("pool_size", 5),
                "max_overflow": self.config.get("max_overflow", 10),
                "pool_recycle": self.config.get("pool_recycle", 3600),
                "pool_pre_ping": True,  # Verify connections before using
            }
            
            self._engine = create_engine(
                connection_url,
                **pool_config,
                echo=False,  # Set to True for debugging
                connect_args={
                    "connect_timeout": 10,
                    "charset": "utf8mb4"
                }
            )
            
            logger.info("✅ Database engine created successfully")
            
        return self._engine
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        engine = self.get_engine()
        connection = None
        
        try:
            connection = engine.connect()
            yield connection
        except Exception as e:
            logger.error(f"❌ Database connection error: {str(e)}")
            raise
        finally:
            if connection:
                connection.close()
    
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> pd.DataFrame:
        """Execute query with retry logic and return DataFrame"""
        last_error = None
        
        for attempt in range(self._connection_retries):
            try:
                with self.get_connection() as conn:
                    df = pd.read_sql(
                        sql=text(query),
                        con=conn,
                        params=params or {}
                    )
                    return df
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Query attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self._connection_retries - 1:
                    time.sleep(self._retry_delay * (attempt + 1))
                    
        logger.error(f"❌ Query failed after {self._connection_retries} attempts")
        raise last_error
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes by default
    def cached_query(_self, query: str, params: Dict[str, Any] = None, 
                     cache_key: str = None, ttl: int = 300) -> pd.DataFrame:
        """Execute query with Streamlit caching"""
        return _self.execute_query(query, params)
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                logger.info("✅ Database connection test successful")
                return True
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {str(e)}")
            return False
    
    def get_table_info(self, table_name: str) -> pd.DataFrame:
        """Get table structure information"""
        query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            CHARACTER_MAXIMUM_LENGTH,
            COLUMN_COMMENT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = :database
        AND TABLE_NAME = :table_name
        ORDER BY ORDINAL_POSITION
        """
        
        return self.execute_query(
            query, 
            params={
                "database": self.config["database"],
                "table_name": table_name
            }
        )
    
    def list_views(self, pattern: str = None) -> List[str]:
        """List all views in database, optionally filtered by pattern"""
        query = """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.VIEWS
        WHERE TABLE_SCHEMA = :database
        """
        
        params = {"database": self.config["database"]}
        
        if pattern:
            query += " AND TABLE_NAME LIKE :pattern"
            params["pattern"] = f"%{pattern}%"
            
        query += " ORDER BY TABLE_NAME"
        
        df = self.execute_query(query, params)
        return df['TABLE_NAME'].tolist()
    
    def close(self):
        """Close database engine and cleanup connections"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            logger.info("Database engine closed")


# Create singleton instance
db_manager = DatabaseManager()


# Convenience functions for backward compatibility
def get_db_engine() -> Engine:
    """Get database engine (backward compatibility)"""
    return db_manager.get_engine()


def query_data(query: str, params: Dict[str, Any] = None, 
               use_cache: bool = True, ttl: int = 300) -> pd.DataFrame:
    """
    Execute query and return DataFrame
    
    Args:
        query: SQL query string
        params: Query parameters
        use_cache: Whether to use Streamlit caching
        ttl: Cache time-to-live in seconds
    
    Returns:
        pd.DataFrame: Query results
    """
    if use_cache:
        return db_manager.cached_query(query, params, ttl=ttl)
    else:
        return db_manager.execute_query(query, params)


# Query retry decorator
def with_db_retry(retries: int = 3, delay: float = 1.0):
    """Decorator for database operations with retry logic"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {str(e)}")
                    
                    if attempt < retries - 1:
                        time.sleep(delay * (attempt + 1))
                        
            logger.error(f"{func.__name__} failed after {retries} attempts")
            raise last_error
            
        return wrapper
    return decorator