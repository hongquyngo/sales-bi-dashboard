"""
Authentication UI components
"""
import streamlit as st
from typing import Optional

from .handlers import auth_handler
from .models import User


def render_login_form():
    """Render login form"""
    st.markdown("## 🔐 Login to Sales BI Dashboard")
    
    with st.form("login_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                submit = st.form_submit_button("Login", type="primary", use_container_width=True)
            with col_btn2:
                st.form_submit_button("Forgot Password?", use_container_width=True, disabled=True)
        
        with col2:
            st.markdown("### Need Help?")
            st.info("""
            - Contact IT Support
            - Email: it@company.com
            - Ext: 1234
            """)
    
    if submit:
        if not username or not password:
            st.error("Please enter both username and password")
        else:
            with st.spinner("Authenticating..."):
                if auth_handler.login(username, password):
                    st.success(f"Welcome, {username}!")
                    st.balloons()
                    # Force rerun to refresh the page
                    st.rerun()
                else:
                    # Error messages are handled in auth_handler
                    pass


def render_user_menu():
    """Render user menu in sidebar"""
    user = auth_handler.get_current_user()
    if not user:
        return
    
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 👤 User Info")
        st.markdown(f"**User:** {user.username}")
        st.markdown(f"**Role:** {user.role.replace('_', ' ').title()}")
        st.markdown(f"**Email:** {user.email}")
        
        if st.button("🚪 Logout", use_container_width=True):
            auth_handler.logout()
            st.rerun()


def protect_page():
    """Protect a page by requiring authentication"""
    # Initialize session state if needed
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not auth_handler.is_authenticated():
        render_login_form()
        st.stop()
    else:
        # Refresh session
        auth_handler.refresh_session()
        # Render user menu
        render_user_menu()


def get_current_user() -> Optional[User]:
    """Get current logged in user"""
    return auth_handler.get_current_user()


def check_access(allowed_roles: list[str]) -> bool:
    """Check if current user has access based on roles"""
    user = get_current_user()
    if not user:
        return False
    return user.has_any_role(allowed_roles)