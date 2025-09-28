"""
Dashboard page - System status overview and quick actions.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any
from utils.logging import get_logger
from utils.helpers import handle_error

logger = get_logger(__name__)

def show_dashboard():
    """Display the main dashboard with system status and quick actions."""
    st.title("📊 Inventory Manager Dashboard")
    st.markdown("Welcome to your inventory management system overview")
    
    # System status cards
    st.subheader("🔧 System Status")
    show_system_status_cards()
    
    st.markdown("---")
    
    # Recent activity section
    st.subheader("📋 Recent Activity")
    show_recent_activity()
    
    st.markdown("---")
    
    # Quick actions section
    st.subheader("⚡ Quick Actions")
    show_quick_actions()
    
    st.markdown("---")
    
    # System metrics
    st.subheader("📈 System Metrics")
    show_system_metrics()

def show_system_status_cards():
    """Display system status cards for different components."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        show_database_status()
    
    with col2:
        show_email_status()
    
    with col3:
        show_amazon_api_status()
    
    with col4:
        show_last_update_info()

def show_database_status():
    """Display database connection status card."""
    try:
        from services.database_service import DatabaseService
        db_service = DatabaseService()
        
        if db_service.test_connection():
            st.success("🗄️ **Database**\n\n✅ Connected")
            status_info = db_service.get_connection_status()
            st.caption(f"Server: {status_info.get('server', 'Unknown')}")
        else:
            st.error("🗄️ **Database**\n\n❌ Disconnected")
            st.caption("Check network connection")
            
    except Exception as e:
        st.error("🗄️ **Database**\n\n⚠️ Error")
        st.caption("Configuration issue")
        logger.error(f"Database status check failed: {str(e)}")

def show_email_status():
    """Display email service status card."""
    try:
        from services.email_service import EmailService
        email_service = EmailService()
        
        if email_service.test_connection():
            st.success("📧 **Email**\n\n✅ Connected")
            status_info = email_service.get_connection_status()
            st.caption(f"Account: {status_info.get('email', 'Unknown')}")
        else:
            st.error("📧 **Email**\n\n❌ Disconnected")
            st.caption("Check authentication")
            
    except Exception as e:
        st.error("📧 **Email**\n\n⚠️ Error")
        st.caption("Configuration issue")
        logger.error(f"Email status check failed: {str(e)}")

def show_amazon_api_status():
    """Display Amazon API status card."""
    try:
        from services.amazon_service import AmazonService
        amazon_service = AmazonService()
        
        if amazon_service.test_connection():
            st.success("🛒 **Amazon API**\n\n✅ Connected")
            status_info = amazon_service.get_connection_status()
            st.caption(f"Marketplace: {status_info.get('marketplace', 'US')}")
        else:
            st.error("🛒 **Amazon API**\n\n❌ Disconnected")
            st.caption("Check API credentials")
            
    except Exception as e:
        st.error("🛒 **Amazon API**\n\n⚠️ Error")
        st.caption("Configuration issue")
        logger.error(f"Amazon API status check failed: {str(e)}")

def show_last_update_info():
    """Display last update information card."""
    if st.session_state.last_update_time:
        time_diff = datetime.now() - st.session_state.last_update_time
        
        if time_diff.days > 0:
            time_str = f"{time_diff.days} days ago"
            status_color = "warning" if time_diff.days > 7 else "info"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            time_str = f"{hours} hours ago"
            status_color = "info"
        else:
            minutes = time_diff.seconds // 60
            time_str = f"{minutes} minutes ago"
            status_color = "success"
        
        if status_color == "success":
            st.success(f"🕒 **Last Update**\n\n✅ {time_str}")
        elif status_color == "info":
            st.info(f"🕒 **Last Update**\n\n📅 {time_str}")
        else:
            st.warning(f"🕒 **Last Update**\n\n⚠️ {time_str}")
        
        st.caption(st.session_state.last_update_time.strftime("%Y-%m-%d %H:%M"))
    else:
        st.info("🕒 **Last Update**\n\n❓ No updates yet")
        st.caption("Run inventory update")

def show_recent_activity():
    """Display recent activity log."""
    if st.session_state.recent_activities:
        # Create a container for activities
        activity_container = st.container()
        
        with activity_container:
            for i, activity in enumerate(st.session_state.recent_activities[:5]):  # Show last 5
                timestamp = activity['timestamp'].strftime("%H:%M:%S")
                activity_type = activity['type']
                description = activity['description']
                
                # Choose icon based on activity type
                if activity_type == "error":
                    icon = "❌"
                    color = "red"
                elif activity_type == "success":
                    icon = "✅"
                    color = "green"
                elif activity_type == "navigation":
                    icon = "🔄"
                    color = "blue"
                else:
                    icon = "ℹ️"
                    color = "gray"
                
                st.markdown(f"**{timestamp}** {icon} {description}")
        
        # Show all activities button
        if len(st.session_state.recent_activities) > 5:
            with st.expander(f"Show all {len(st.session_state.recent_activities)} activities"):
                for activity in st.session_state.recent_activities:
                    timestamp = activity['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                    st.text(f"{timestamp} - {activity['type']}: {activity['description']}")
    else:
        st.info("No recent activity to display")

def show_quick_actions():
    """Display quick action buttons for common tasks."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Quick Inventory Check", use_container_width=True):
            run_quick_inventory_check()
    
    with col2:
        if st.button("📊 System Health Check", use_container_width=True):
            run_system_health_check()
    
    with col3:
        if st.button("🧹 Clear Activity Log", use_container_width=True):
            clear_activity_log()

def run_quick_inventory_check():
    """Run a quick inventory status check."""
    try:
        with st.spinner("Running quick inventory check..."):
            from services.inventory_service import InventoryService
            inventory_service = InventoryService()
            
            # Get basic inventory status
            status = inventory_service.get_system_status()
            
            st.success("✅ Quick inventory check completed!")
            
            # Display results
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Email Status", "✅ Connected" if status['email'] else "❌ Disconnected")
            with col2:
                st.metric("Database Status", "✅ Connected" if status['database'] else "❌ Disconnected")
            with col3:
                st.metric("Amazon API Status", "✅ Connected" if status['amazon'] else "❌ Disconnected")
            
            # Add to activity log
            if hasattr(st.session_state, 'add_activity'):
                st.session_state.add_activity("success", "Quick inventory check completed")
            
    except Exception as e:
        handle_error(e, "quick inventory check")
        if hasattr(st.session_state, 'add_activity'):
            st.session_state.add_activity("error", f"Quick inventory check failed: {str(e)}")

def run_system_health_check():
    """Run a comprehensive system health check."""
    try:
        with st.spinner("Running system health check..."):
            from utils.helpers import check_system_health, validate_required_files
            
            # Check system health
            health_status = check_system_health()
            
            # Validate required files
            file_validation = validate_required_files()
            
            st.success("✅ System health check completed!")
            
            # Display results
            st.write("**System Status:**", health_status['status'].upper())
            if health_status['message']:
                st.write("**Message:**", health_status['message'])
            
            # Show file validation results
            st.write("**Required Files:**")
            for file_path, exists in file_validation.items():
                status_icon = "✅" if exists else "❌"
                st.write(f"{status_icon} {file_path}")
            
            # Update session state
            st.session_state.system_health = health_status
            
            # Add to activity log
            if hasattr(st.session_state, 'add_activity'):
                st.session_state.add_activity("success", "System health check completed")
            
    except Exception as e:
        handle_error(e, "system health check")
        if hasattr(st.session_state, 'add_activity'):
            st.session_state.add_activity("error", f"System health check failed: {str(e)}")

def clear_activity_log():
    """Clear the activity log."""
    st.session_state.recent_activities = []
    st.success("✅ Activity log cleared!")
    st.rerun()

def show_system_metrics():
    """Display system metrics and statistics."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Session Information")
        st.write(f"**Session Started:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"**Current Operation:** {st.session_state.current_operation or 'Dashboard'}")
        st.write(f"**Activities Logged:** {len(st.session_state.recent_activities)}")
    
    with col2:
        st.subheader("💾 Data Status")
        
        # Check if we have cached data
        inventory_status = "✅ Loaded" if st.session_state.inventory_data is not None else "❌ Not loaded"
        amazon_status = "✅ Loaded" if st.session_state.amazon_orders is not None else "❌ Not loaded"
        sales_status = "✅ Loaded" if st.session_state.sales_data is not None else "❌ Not loaded"
        
        st.write(f"**Inventory Data:** {inventory_status}")
        st.write(f"**Amazon Orders:** {amazon_status}")
        st.write(f"**Sales Data:** {sales_status}")