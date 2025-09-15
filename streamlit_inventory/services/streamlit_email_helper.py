"""
Streamlit-specific helper for Gmail OAuth2 authentication.
Provides UI components and workflows suitable for Streamlit apps.
"""

import streamlit as st
import os
from typing import Optional
from .email_service import EmailService


class StreamlitEmailHelper:
    """Helper class for Gmail OAuth2 in Streamlit apps."""
    
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
    
    def show_oauth2_setup_ui(self) -> bool:
        """
        Display OAuth2 setup UI in Streamlit.
        Returns True if authentication is successful.
        """
        st.subheader("📧 Gmail Authentication Setup")
        
        # Check current status
        status = self.email_service.get_connection_status()
        
        if status['connected']:
            st.success(f"✅ Connected to Gmail as: {status['email_user']}")
            st.info(f"Authentication method: {status['auth_method']}")
            return True
        
        # Show setup options
        st.warning("Gmail authentication required")
        
        setup_method = st.radio(
            "Choose setup method:",
            [
                "Upload token file (Recommended)",
                "Manual authorization code",
                "Local setup instructions"
            ]
        )
        
        if setup_method == "Upload token file (Recommended)":
            return self._handle_token_upload()
        elif setup_method == "Manual authorization code":
            return self._handle_manual_auth()
        else:
            self._show_local_setup_instructions()
            return False
    
    def _handle_token_upload(self) -> bool:
        """Handle token file upload."""
        st.markdown("### Upload Token File")
        st.info(
            "If you have a `gmail_token.json` file from a previous setup, "
            "upload it here to authenticate."
        )
        
        uploaded_file = st.file_uploader(
            "Choose gmail_token.json file",
            type=['json'],
            help="Upload the OAuth2 token file generated during local setup"
        )
        
        if uploaded_file is not None:
            try:
                # Save uploaded token file
                token_path = f'{self.email_service.root_path}appdata/gmail_token.json'
                os.makedirs(os.path.dirname(token_path), exist_ok=True)
                
                with open(token_path, 'wb') as f:
                    f.write(uploaded_file.getvalue())
                
                # Test connection
                if self.email_service.test_connection(streamlit_mode=True):
                    st.success("✅ Token uploaded and verified successfully!")
                    st.rerun()
                    return True
                else:
                    st.error("❌ Token file is invalid or expired")
                    return False
                    
            except Exception as e:
                st.error(f"❌ Error uploading token: {e}")
                return False
        
        return False
    
    def _handle_manual_auth(self) -> bool:
        """Handle manual authorization code flow."""
        st.markdown("### Manual Authorization")
        
        try:
            # Generate authorization URL
            if st.button("Generate Authorization URL"):
                auth_url = self.email_service.get_oauth2_url_for_streamlit()
                st.markdown(f"**Step 1:** Click the link below to authorize the application:")
                st.markdown(f"[🔗 Authorize Gmail Access]({auth_url})")
                st.markdown("**Step 2:** Copy the authorization code and paste it below:")
            
            # Input for authorization code
            auth_code = st.text_input(
                "Authorization Code",
                placeholder="Paste the authorization code here...",
                help="After clicking the authorization link, copy the code and paste it here"
            )
            
            if auth_code and st.button("Complete Authentication"):
                if self.email_service.complete_oauth2_with_code(auth_code.strip()):
                    st.success("✅ Authentication completed successfully!")
                    st.rerun()
                    return True
                else:
                    st.error("❌ Invalid authorization code")
                    return False
                    
        except Exception as e:
            st.error(f"❌ Error in manual authentication: {e}")
            return False
        
        return False
    
    def _show_local_setup_instructions(self):
        """Show instructions for local setup."""
        st.markdown("### Local Setup Instructions")
        st.info(
            "For the most reliable setup, run the OAuth2 flow locally "
            "and then upload the generated token file."
        )
        
        st.markdown("""
        **Steps:**
        
        1. **Run locally** (on your computer):
        ```python
        from services.email_service import EmailService
        
        email_service = EmailService("path/to/your/project/")
        token_path = email_service.setup_oauth2_locally()
        print(f"Token saved to: {token_path}")
        ```
        
        2. **Upload the token file** using the "Upload token file" option above
        
        3. **Alternative**: Copy the `gmail_token.json` file to your deployment's `appdata/` directory
        """)
        
        st.warning(
            "⚠️ Make sure you have `client_secret.json` in your `appdata/` directory "
            "before running the local setup."
        )
    
    def show_connection_status(self):
        """Display current connection status."""
        status = self.email_service.get_connection_status()
        
        if status['connected']:
            st.success(f"✅ Gmail Connected: {status['email_user']}")
        else:
            st.error("❌ Gmail Not Connected")
        
        with st.expander("Connection Details"):
            st.json(status)
    
    def test_email_download(self, supplier_code: str) -> bool:
        """Test email download for a specific supplier."""
        try:
            st.info(f"Testing email download for supplier: {supplier_code}")
            
            with st.spinner("Downloading supplier files..."):
                files = self.email_service.download_supplier_files(
                    supplier_code, 
                    streamlit_mode=True
                )
            
            if files:
                st.success(f"✅ Downloaded {len(files)} files:")
                for file_path in files:
                    st.write(f"- {os.path.basename(file_path)}")
                return True
            else:
                st.warning("No files downloaded (this might be normal)")
                return True
                
        except Exception as e:
            st.error(f"❌ Error downloading files: {e}")
            return False


def create_streamlit_email_setup(root_path: str = "") -> tuple[EmailService, StreamlitEmailHelper]:
    """
    Create EmailService and StreamlitEmailHelper for Streamlit apps.
    
    Returns:
        Tuple of (EmailService, StreamlitEmailHelper)
    """
    import streamlit as st
    from pathlib import Path
    
    try:
        # Check if appdata directory exists
        appdata_path = Path(root_path) / "appdata"
        if not appdata_path.exists():
            st.error(f"❌ appdata directory not found at: {appdata_path}")
            st.info("Creating appdata directory and sample config files...")
            
            # Create appdata directory
            appdata_path.mkdir(parents=True, exist_ok=True)
            
            # Create sample config files
            gmail_auth = {"username": "your-email@gmail.com"}
            with open(appdata_path / "gmail_auth.json", "w") as f:
                import json
                json.dump(gmail_auth, f, indent=2)
            
            supplier_config = {
                "AL": {"SUBJECT": "AL_SUBJECT", "FROM": "al@supplier.com"},
                "VF": {"SUBJECT": "VF_SUBJECT", "FROM": "vf@supplier.com"}
            }
            with open(appdata_path / "keyword_mailadd.json", "w") as f:
                json.dump(supplier_config, f, indent=2)
            
            st.success("✅ Created appdata directory with sample config files")
            st.info("Please update gmail_auth.json with your Gmail address and add client_secret.json")
        
        email_service = EmailService(root_path)
        helper = StreamlitEmailHelper(email_service)
        return email_service, helper
        
    except Exception as e:
        st.error(f"Failed to initialize email service: {e}")
        st.code(str(e))
        
        # Show helpful debug information
        st.subheader("Debug Information")
        st.write(f"Root path: {root_path}")
        st.write(f"Appdata path: {appdata_path}")
        st.write(f"Current working directory: {Path.cwd()}")
        
        st.stop()