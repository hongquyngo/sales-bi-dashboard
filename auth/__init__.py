"""
Authentication Module for Sales BI Dashboard

This module provides:
- User authentication (login/logout)
- Session management
- Role-based access control
- Authentication decorators
"""

from .models import User, UserRole, LoginAttempt
from .handlers import AuthHandler, auth_handler, AuthenticationError
from .decorators import (
    requires_auth,
    requires_role,
    requires_admin,
    requires_manager_or_above,
    check_permission,
    with_user_context
)
from .ui import (
    render_login_form,
    render_user_menu,
    protect_page,
    get_current_user,
    check_access
)

__all__ = [
    # Models
    "User",
    "UserRole", 
    "LoginAttempt",
    
    # Handlers
    "AuthHandler",
    "auth_handler",
    "AuthenticationError",
    
    # Decorators
    "requires_auth",
    "requires_role",
    "requires_admin",
    "requires_manager_or_above",
    "check_permission",
    "with_user_context",
    
    # UI components
    "render_login_form",
    "render_user_menu",
    "protect_page",
    "get_current_user",
    "check_access"
]