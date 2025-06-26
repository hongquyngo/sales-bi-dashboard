"""
Demo app showing authentication in action
Run: streamlit run demo_auth.py
"""
import streamlit as st
from auth import (
    protect_page, 
    get_current_user, 
    requires_role, 
    UserRole,
    check_permission
)

# Set page config
st.set_page_config(
    page_title="Sales BI Dashboard - Demo",
    page_icon="📊",
    layout="wide"
)

# Protect page - this will show login form if not authenticated
protect_page()

# After this point, user is authenticated
user = get_current_user()

# Safety check
if not user:
    st.error("Authentication error. Please refresh the page.")
    st.stop()

# Main content
st.title("🎯 Sales BI Dashboard")
st.markdown(f"Welcome, **{user.username}**! You are logged in as **{user.role}**.")

# Show different content based on role
st.markdown("---")
st.markdown("## 📊 Available Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 👁️ View Sales Data")
    if st.button("Open Sales Dashboard", use_container_width=True):
        st.info("Sales dashboard would open here...")

with col2:
    st.markdown("### 📈 View Analytics")
    if check_permission("view_all_data"):
        if st.button("Open Analytics", use_container_width=True):
            st.info("Analytics dashboard would open here...")
    else:
        st.warning("You need Manager or Admin role")

with col3:
    st.markdown("### ⚙️ Admin Panel")
    if user.is_admin:
        if st.button("Open Admin Panel", use_container_width=True):
            st.info("Admin panel would open here...")
    else:
        st.warning("Admin access only")

# Role-based content examples
st.markdown("---")
st.markdown("## 🔐 Role-Based Content")

# Example 1: Content for all authenticated users
st.markdown("### Public Dashboard")
st.success("✅ This content is visible to all logged-in users")

# Example 2: Manager and above only
if check_permission("view_all_data"):
    st.markdown("### Manager Dashboard")
    st.info("📊 This section is only visible to Managers and Admins")
    
    # Demo data
    import pandas as pd
    import numpy as np
    
    df = pd.DataFrame({
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
        'Sales': np.random.randint(100000, 500000, 5),
        'Orders': np.random.randint(100, 500, 5)
    })
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Sales", f"${df['Sales'].sum():,.0f}")
    with col2:
        st.metric("Total Orders", f"{df['Orders'].sum():,.0f}")
    
    st.dataframe(df, use_container_width=True)

# Example 3: Admin only
if user.is_admin:
    st.markdown("### Admin Controls")
    st.warning("⚠️ This section is only visible to Admins")
    
    with st.expander("User Management"):
        st.markdown("""
        - Add new users
        - Reset passwords  
        - Manage roles
        - View login history
        """)

# Example 4: Export functionality
st.markdown("---")
st.markdown("## 📥 Export Data")

if check_permission("export_data"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("Export to Excel", use_container_width=True)
    with col2:
        st.button("Export to PDF", use_container_width=True)
    with col3:
        st.button("Export to CSV", use_container_width=True)
else:
    st.info("💡 Export feature is not available for Viewer role")

# Show session info in sidebar
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔍 Debug Info")
    st.markdown(f"**Session State Keys:** {len(st.session_state)}")
    
    with st.expander("Permissions"):
        permissions = [
            "view_all_data",
            "export_data", 
            "manage_users",
            "view_costs",
            "edit_settings"
        ]
        
        for perm in permissions:
            if check_permission(perm):
                st.success(f"✅ {perm}")
            else:
                st.error(f"❌ {perm}")