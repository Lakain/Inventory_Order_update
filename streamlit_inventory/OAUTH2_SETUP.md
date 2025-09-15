# Gmail OAuth2 Setup Guide

The EmailService now uses OAuth2 authentication instead of the deprecated username/password method. This provides better security and compliance with Google's current authentication requirements.

## Prerequisites

1. **Google Cloud Project**: You need a Google Cloud Project with Gmail API enabled
2. **OAuth2 Credentials**: Download the `client_secret.json` file from Google Cloud Console

## Setup Steps

### 1. Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

### 2. Create OAuth2 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Choose "Desktop application"
4. Download the JSON file and rename it to `client_secret.json`
5. Place it in the `appdata/` directory

### 3. Configure Email Settings

Update your `appdata/gmail_auth.json` file:
```json
{
    "username": "your-email@gmail.com"
}
```

Note: The `password` field is no longer required but can be kept for compatibility.

### 4. First-Time Authentication

When you first run the application:

1. The OAuth2 flow will automatically start
2. A browser window will open asking you to sign in to Google
3. Grant the necessary permissions
4. The authentication token will be saved to `appdata/gmail_token.json`

## File Structure

After setup, you should have these files in `appdata/`:

```
appdata/
├── client_secret.json      # OAuth2 client credentials (from Google Cloud)
├── gmail_auth.json         # Email configuration
├── gmail_token.json        # OAuth2 tokens (auto-generated)
└── keyword_mailadd.json    # Supplier email configurations
```

## Troubleshooting

### Token Refresh Issues

If you encounter authentication errors:

```python
from services.email_service import EmailService

email_service = EmailService("path/to/root/")
email_service.refresh_credentials()  # This will force re-authentication
```

### Missing Client Secrets

If you get a "Client secrets file not found" error:
1. Make sure `client_secret.json` is in the `appdata/` directory
2. Verify the file is valid JSON downloaded from Google Cloud Console

### Permission Errors

If you get permission errors:
1. Check that Gmail API is enabled in your Google Cloud Project
2. Verify the OAuth2 consent screen is configured
3. Make sure your email address is added as a test user (if in testing mode)

## Security Notes

- The `client_secret.json` file contains sensitive information - keep it secure
- The `gmail_token.json` file contains access tokens - don't share it
- Tokens are automatically refreshed when they expire
- The application requests full Gmail access (`https://mail.google.com/`) scope

## Migration from Old Authentication

If you're migrating from the old username/password authentication:

1. Install the new dependencies: `pip install google-auth google-auth-oauthlib`
2. Set up OAuth2 credentials as described above
3. The old `password` field in `gmail_auth.json` is ignored but can remain
4. First run will trigger the OAuth2 setup flow

The service will automatically handle the OAuth2 flow and token management.

## Streamlit App Deployment

For Streamlit apps, the OAuth2 flow requires special handling since `run_local_server()` doesn't work in cloud deployments.

### Option 1: Pre-generate Token Locally (Recommended)

1. **Run locally** to generate the token:
```python
from services.email_service import EmailService

email_service = EmailService("./")
token_path = email_service.setup_oauth2_locally()
```

2. **Copy the token file** to your Streamlit deployment:
   - Upload `gmail_token.json` to your deployment's `appdata/` directory
   - Or use the Streamlit file uploader in the app

### Option 2: Use Streamlit Helper UI

```python
import streamlit as st
from services.streamlit_email_helper import create_streamlit_email_setup

# Create email service and helper
email_service, helper = create_streamlit_email_setup("./")

# Show OAuth2 setup UI
if not helper.show_oauth2_setup_ui():
    st.stop()  # Stop if authentication fails

# Use the email service
files = email_service.download_supplier_files("AL", streamlit_mode=True)
```

### Option 3: Manual Authorization Flow

```python
# In your Streamlit app
email_service = EmailService("./")

# Generate authorization URL
auth_url = email_service.get_oauth2_url_for_streamlit()
st.markdown(f"[Authorize Gmail Access]({auth_url})")

# User pastes authorization code
auth_code = st.text_input("Authorization Code")
if auth_code:
    email_service.complete_oauth2_with_code(auth_code)
```

### Streamlit Cloud Deployment

For Streamlit Cloud or other cloud deployments:

1. **Secrets Management**: Store sensitive files in Streamlit secrets:
```toml
# .streamlit/secrets.toml
[gmail]
client_secret = '''
{
  "installed": {
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    ...
  }
}
'''

token = '''
{
  "token": "your-access-token",
  "refresh_token": "your-refresh-token",
  ...
}
'''
```

2. **Load from secrets**:
```python
import json
import streamlit as st

# Save secrets to files
os.makedirs("appdata", exist_ok=True)
with open("appdata/client_secret.json", "w") as f:
    f.write(st.secrets["gmail"]["client_secret"])
with open("appdata/gmail_token.json", "w") as f:
    f.write(st.secrets["gmail"]["token"])
```