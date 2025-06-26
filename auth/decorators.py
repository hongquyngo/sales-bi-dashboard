"""
Decorators for authentication and authorization
"""
import streamlit as st
from functools import wraps
from typing import Callable, List, Optional

from .handlers import auth_handler
from .models import UserRole


def requires_auth(func: Callable) -> Callable:
    """Decorator to require authentication for a function or page"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not auth_handler.is_authenticated():
            st.error("🔒 Authentication required")
            st.info("Please login to access this page")
            st.stop()
        
        # Refresh session on activity
        auth_handler.refresh_session()
        
        return func(*args, **kwargs)
    
    return wrapper


def requires_role(allowed_roles: List[str]) -> Callable:
    """Decorator to require specific roles for a function or page"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not auth_handler.is_authenticated():
                st.error("🔒 Authentication required")
                st.info("Please login to access this page")
                st.stop()
            
            user = auth_handler.get_current_user()
            if not user or not user.has_any_role(allowed_roles):
                st.error("🚫 Access Denied")
                st.warning(f"This page requires one of these roles: {', '.join(allowed_roles)}")
                st.info(f"Your current role: {user.role if user else 'None'}")
                st.stop()
            
            # Refresh session on activity
            auth_handler.refresh_session()
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def requires_admin(func: Callable) -> Callable:
    """Decorator to require admin role"""
    return requires_role([UserRole.ADMIN.value])(func)


def requires_manager_or_above(func: Callable) -> Callable:
    """Decorator to require manager or admin role"""
    return requires_role([UserRole.ADMIN.value, UserRole.MANAGER.value])(func)


def check_permission(permission: str) -> bool:
    """Check if current user has specific permission"""
    user = auth_handler.get_current_user()
    if not user:
        return False
    
    # Define permission mapping
    permissions = {
        "view_all_data": [UserRole.ADMIN.value, UserRole.MANAGER.value],
        "export_data": [UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.SALES.value, UserRole.SUPPLY_CHAIN.value],
        "manage_users": [UserRole.ADMIN.value],
        "view_costs": [UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.SUPPLY_CHAIN.value],
        "edit_settings": [UserRole.ADMIN.value],
    }
    
    allowed_roles = permissions.get(permission, [])
    return user.has_any_role(allowed_roles)


def with_user_context(func: Callable) -> Callable:
    """Decorator to inject current user into function arguments"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = auth_handler.get_current_user()
        kwargs['current_user'] = user
        return func(*args, **kwargs)
    
    return wrapper