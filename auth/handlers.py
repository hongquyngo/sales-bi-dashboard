"""
Authentication handlers for login, logout, and session management
"""
import hashlib
import secrets
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging
from sqlalchemy import text

from config import db_manager, AUTH_CONFIG
from .models import User, LoginAttempt

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass


class AuthHandler:
    """Handle authentication operations"""
    
    def __init__(self):
        self.max_attempts = AUTH_CONFIG.get("max_attempts", 3)
        self.lockout_duration = AUTH_CONFIG.get("lockout_duration", 900)  # 15 minutes
        self.session_timeout = AUTH_CONFIG.get("session_timeout", 3600)  # 1 hour
        
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password with salt using SHA256 (matching existing database)"""
        if not salt:
            salt = secrets.token_hex(32)
        
        pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return pwd_hash, salt
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash and salt using SHA256"""
        try:
            pwd_hash, _ = self.hash_password(password, salt)
            return pwd_hash == password_hash
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            return False
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user from database by username"""
        query = """
        SELECT 
            id, username, email, role, employee_id,
            is_active, last_login, created_date
        FROM users
        WHERE username = :username
        AND delete_flag = 0
        """
        
        try:
            df = db_manager.execute_query(query, {"username": username})
            if df.empty:
                return None
                
            row = df.iloc[0]
            
            # Handle potential None values and type conversions
            return User(
                id=int(row['id']),
                username=str(row['username']),
                email=str(row['email']) if row['email'] else '',
                role=str(row['role']) if row['role'] else 'viewer',
                employee_id=int(row['employee_id']) if pd.notna(row['employee_id']) else None,
                is_active=bool(row['is_active']) if pd.notna(row['is_active']) else True,
                last_login=pd.to_datetime(row['last_login']) if pd.notna(row['last_login']) else None,
                created_date=pd.to_datetime(row['created_date']) if pd.notna(row['created_date']) else None
            )
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        # Check if account is locked
        if self.is_account_locked(username):
            raise AuthenticationError("Account is temporarily locked due to multiple failed attempts")
        
        # Get user credentials
        query = """
        SELECT username, password_hash, password_salt, is_active
        FROM users
        WHERE username = :username
        AND delete_flag = 0
        """
        
        try:
            df = db_manager.execute_query(query, {"username": username})
            if df.empty:
                self.record_failed_attempt(username)
                return None
            
            row = df.iloc[0]
            
            # Check if user is active
            if not bool(row['is_active']):
                raise AuthenticationError("Account is deactivated")
            
            # Get password hash and salt
            password_hash = str(row['password_hash']) if row['password_hash'] else ''
            password_salt = str(row['password_salt']) if row['password_salt'] else ''
            
            # Verify password
            if self.verify_password(password, password_hash, password_salt):
                # Clear failed attempts
                self.clear_failed_attempts(username)
                
                # Update last login
                self.update_last_login(username)
                
                # Get full user data
                return self.get_user(username)
            else:
                self.record_failed_attempt(username)
                return None
                
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise AuthenticationError("Authentication failed")
    
    def is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed attempts"""
        key = f"failed_attempts_{username}"
        attempts = st.session_state.get(key, [])
        
        if len(attempts) >= self.max_attempts:
            last_attempt = datetime.fromisoformat(attempts[-1])
            lockout_end = last_attempt + timedelta(seconds=self.lockout_duration)
            
            if datetime.now() < lockout_end:
                return True
            else:
                # Lockout period expired, clear attempts
                st.session_state[key] = []
                
        return False
    
    def record_failed_attempt(self, username: str):
        """Record failed login attempt"""
        key = f"failed_attempts_{username}"
        attempts = st.session_state.get(key, [])
        attempts.append(datetime.now().isoformat())
        
        # Keep only recent attempts
        cutoff = datetime.now() - timedelta(seconds=self.lockout_duration)
        attempts = [a for a in attempts if datetime.fromisoformat(a) > cutoff]
        
        st.session_state[key] = attempts
        
        remaining = self.max_attempts - len(attempts)
        if remaining > 0:
            st.warning(f"Invalid credentials. {remaining} attempts remaining.")
        else:
            st.error(f"Account locked for {self.lockout_duration // 60} minutes.")
    
    def clear_failed_attempts(self, username: str):
        """Clear failed login attempts"""
        key = f"failed_attempts_{username}"
        if key in st.session_state:
            del st.session_state[key]
    
    def update_last_login(self, username: str):
        """Update user's last login timestamp"""
        query = """
        UPDATE users 
        SET last_login = NOW()
        WHERE username = :username
        """
        
        try:
            with db_manager.get_connection() as conn:
                conn.execute(text(query), {"username": username})
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating last login: {str(e)}")
    
    def login(self, username: str, password: str) -> bool:
        """Login user and create session"""
        try:
            user = self.authenticate(username, password)
            if user:
                # Store user in session
                st.session_state['user'] = user.to_dict()
                st.session_state['authenticated'] = True
                st.session_state['login_time'] = datetime.now().isoformat()
                
                logger.info(f"User {username} logged in successfully")
                return True
            else:
                return False
                
        except AuthenticationError as e:
            st.error(str(e))
            return False
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            st.error("An error occurred during login")
            return False
    
    def logout(self):
        """Logout user and clear session"""
        if 'user' in st.session_state:
            username = st.session_state['user'].get('username', 'Unknown')
            logger.info(f"User {username} logged out")
        
        # Clear session
        keys_to_remove = ['user', 'authenticated', 'login_time']
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        if not st.session_state.get('authenticated', False):
            return False
        
        # Check session timeout
        if 'login_time' in st.session_state:
            login_time = datetime.fromisoformat(st.session_state['login_time'])
            if datetime.now() - login_time > timedelta(seconds=self.session_timeout):
                self.logout()
                st.warning("Session expired. Please login again.")
                return False
        
        return True
    
    def get_current_user(self) -> Optional[User]:
        """Get current logged in user"""
        if self.is_authenticated() and 'user' in st.session_state:
            return User.from_dict(st.session_state['user'])
        return None
    
    def refresh_session(self):
        """Refresh session timeout"""
        if self.is_authenticated():
            st.session_state['login_time'] = datetime.now().isoformat()


# Create singleton instance
auth_handler = AuthHandler()