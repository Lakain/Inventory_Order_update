
import streamlit as st
import sys
import os
from pathlib import Path

# Add services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

st.title("📧 Gmail OAuth2 Test App")

# Determine the correct root path
current_dir = Path(__file__).parent
root_path = str(current_dir.parent) + "/"  # Go up one level to find appdata/

st.info(f"Looking for appdata in: {root_path}appdata/")

# Check if appdata exists and show debug info
appdata_path = Path(root_path) / "appdata"
if appdata_path.exists():
    st.success(f"✅ Found appdata directory")
    files = list(appdata_path.glob("*.json"))
    if files:
        st.write("Config files found:")
        for file in files:
            st.write(f"- {file.name}")
    else:
        st.warning("No JSON config files found in appdata/")
else:
    st.error(f"❌ appdata directory not found at: {appdata_path}")
    st.write("Current working directory:", os.getcwd())
    st.write("Script directory:", current_dir)
    st.write("Looking for appdata at:", appdata_path)

try:
    from services.streamlit_email_helper import create_streamlit_email_setup
    
    # Initialize email service with correct root path
    email_service, helper = create_streamlit_email_setup(root_path)
    
    st.header("Connection Status")
    helper.show_connection_status()
    
    st.header("OAuth2 Setup")
    if helper.show_oauth2_setup_ui():
        st.success("🎉 Gmail authentication successful!")
        
        # Test supplier file download
        st.header("Test Supplier Download")
        supplier = st.selectbox("Select Supplier", ["AL", "VF", "BY", "NBF", "OUTRE", "HZ", "SNG", "MANE"])
        
        if st.button("Test Download"):
            helper.test_email_download(supplier)
    else:
        st.info("Complete Gmail authentication to continue")

except Exception as e:
    st.error(f"Error initializing email service: {e}")
    st.code(str(e))
