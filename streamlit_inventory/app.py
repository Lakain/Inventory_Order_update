"""
Main Streamlit application entry point for Inventory Management System.
Provides navigation and routing to different functional modules.
"""

import streamlit as st
from utils.logging import setup_logging
from utils.helpers import check_system_health

# Configure page settings
st.set_page_config(
    page_title="Inventory Manager",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application entry point with navigation."""
    # Initialize logging
    setup_logging()
    
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
    
    # System health check indicator
    health_status = check_system_health()
    if health_status["status"] == "healthy":
        st.sidebar.success("🟢 System Online")
    else:
        st.sidebar.error("🔴 System Issues Detected")
        st.sidebar.write(health_status["message"])
    
    # Route to appropriate page
    try:
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
        st.error(f"❌ Error loading page: {str(e)}")
        st.info("💡 Please refresh the page or contact support if this persists.")

if __name__ == "__main__":
    main()