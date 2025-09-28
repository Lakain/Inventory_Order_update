"""
Main Streamlit application entry point for Inventory Management System.
Provides navigation and routing to different functional modules.
"""

import streamlit as st
from datetime import datetime
from utils.logging import setup_logging
from utils.helpers import check_system_health

# Configure page settings
st.set_page_config(
    page_title="Inventory Manager",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables for user data management."""
    # Core application data
    if 'inventory_data' not in st.session_state:
        st.session_state.inventory_data = None
    
    if 'amazon_orders' not in st.session_state:
        st.session_state.amazon_orders = None
    
    if 'sales_data' not in st.session_state:
        st.session_state.sales_data = None
    
    # Operation tracking
    if 'current_operation' not in st.session_state:
        st.session_state.current_operation = None
    
    if 'last_update_time' not in st.session_state:
        st.session_state.last_update_time = None
    
    # System status
    if 'system_health' not in st.session_state:
        st.session_state.system_health = None
    
    # User preferences
    if 'selected_suppliers' not in st.session_state:
        st.session_state.selected_suppliers = {}
    
    # Activity tracking
    if 'recent_activities' not in st.session_state:
        st.session_state.recent_activities = []

def add_activity(activity_type: str, description: str):
    """Add an activity to the recent activities log."""
    activity = {
        'timestamp': datetime.now(),
        'type': activity_type,
        'description': description
    }
    
    # Add to beginning of list and keep only last 10 activities
    st.session_state.recent_activities.insert(0, activity)
    st.session_state.recent_activities = st.session_state.recent_activities[:10]

# Make add_activity available globally for other modules
st.session_state.add_activity = add_activity

def main():
    """Main application entry point with navigation."""
    # Initialize logging
    setup_logging()
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar navigation
    st.sidebar.title("📦 Inventory Manager")
    
    # Navigation menu
    page = st.sidebar.selectbox(
        "Select Function",
        [
            "Dashboard",
            "Inventory Update", 
            "Amazon Order Analysis",
            "Sales Reports"
        ]
    )
    
    # System health check and status indicators
    st.sidebar.markdown("---")
    st.sidebar.subheader("System Status")
    
    # Perform health check and cache in session state
    if st.session_state.system_health is None or st.sidebar.button("🔄 Refresh Status"):
        st.session_state.system_health = check_system_health()
    
    health_status = st.session_state.system_health
    
    # Display overall system status
    if health_status["status"] == "healthy":
        st.sidebar.success("🟢 System Online")
    elif health_status["status"] == "warning":
        st.sidebar.warning("🟡 System Warning")
        st.sidebar.write(health_status["message"])
    else:
        st.sidebar.error("🔴 System Issues Detected")
        st.sidebar.write(health_status["message"])
    
    # Display individual component status
    with st.sidebar.expander("Component Status"):
        # Database status
        try:
            from services.database_service import DatabaseService
            db_service = DatabaseService()
            if db_service.test_connection():
                st.write("🟢 Database: Connected")
            else:
                st.write("🔴 Database: Disconnected")
        except Exception:
            st.write("🔴 Database: Error")
        
        # Email service status
        try:
            from services.email_service import EmailService
            email_service = EmailService()
            if email_service.test_connection():
                st.write("🟢 Email: Connected")
            else:
                st.write("🔴 Email: Disconnected")
        except Exception:
            st.write("🔴 Email: Error")
        
        # Amazon API status
        try:
            from services.amazon_service import AmazonService
            amazon_service = AmazonService()
            if amazon_service.test_connection():
                st.write("🟢 Amazon API: Connected")
            else:
                st.write("🔴 Amazon API: Disconnected")
        except Exception:
            st.write("🔴 Amazon API: Error")
    
    # Display last update time if available
    if st.session_state.last_update_time:
        st.sidebar.info(f"Last Update: {st.session_state.last_update_time.strftime('%Y-%m-%d %H:%M')}")
    
    st.sidebar.markdown("---")
    
    # Route to appropriate page
    try:
        # Log page navigation
        if st.session_state.current_operation != page:
            st.session_state.add_activity("navigation", f"Navigated to {page}")
            st.session_state.current_operation = page
        
        if page == "Dashboard":
            from pages.dashboard import show_dashboard
            show_dashboard()
        elif page == "Inventory Update":
            from pages.inventory_update import show_inventory_update
            show_inventory_update()
        elif page == "Amazon Order Analysis":
            from pages.amazon_orders import show_amazon_orders
            show_amazon_orders()
        elif page == "Sales Reports":
            from pages.sales_reports import show_sales_reports
            show_sales_reports()
    except Exception as e:
        from utils.helpers import handle_error
        handle_error(e, f"loading {page} page")
        st.session_state.add_activity("error", f"Error loading {page}: {str(e)}")
        
        # Provide fallback navigation
        st.markdown("---")
        st.info("You can try navigating to a different page using the sidebar menu.")

if __name__ == "__main__":
    main()