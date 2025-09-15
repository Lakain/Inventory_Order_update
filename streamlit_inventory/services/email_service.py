"""
Email service for handling Gmail IMAP operations and supplier file downloads.
Extracted from invUpdateWindow.py update methods (update_AL, update_VF, etc.).
Updated to use OAuth2 authentication instead of deprecated username/password.
"""

import json
import imaplib
import email
import datetime
import os
import logging
from typing import Dict, List, Optional, Tuple
from time import sleep
import tempfile

# Google Auth imports for OAuth2
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)

# Gmail OAuth2 scope for full access
SCOPES = ['https://mail.google.com/']


class EmailService:
    """Service for managing Gmail connections and supplier file downloads."""
    
    def __init__(self, root_path: str = ''):
        self.root_path = root_path
        self._load_configs()
    
    def _load_configs(self):
        """Load email authentication and supplier configurations."""
        try:
            # Load Gmail authentication (still need username for OAuth2)
            with open(f'{self.root_path}appdata/gmail_auth.json') as f:
                gmail_config = json.load(f)
                self.email_user = gmail_config['username']
                # Note: password no longer used with OAuth2, but kept for compatibility
                self.email_password = gmail_config.get('password', '')
            
            # Load supplier email configurations
            with open(f'{self.root_path}appdata/keyword_mailadd.json') as f:
                self.supplier_configs = json.load(f)
                
        except FileNotFoundError as e:
            logger.error(f"Configuration file not found: {e}")
            raise
        except KeyError as e:
            logger.error(f"Missing configuration key: {e}")
            raise
    
    def get_credentials(self, streamlit_mode: bool = False) -> Credentials:
        """
        Get OAuth2 credentials for Gmail access.
        
        Args:
            streamlit_mode: If True, uses manual OAuth flow suitable for Streamlit apps
        """
        creds = None
        
        # Load existing tokens, if any
        token_path = f'{self.root_path}appdata/gmail_token.json'
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        # If no valid credentials, run the flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Save refreshed credentials
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                    logger.info("OAuth2 credentials refreshed successfully")
                except Exception as e:
                    logger.warning(f"Failed to refresh token: {e}, will re-authenticate")
                    creds = None
            
            if not creds:
                if streamlit_mode:
                    # For Streamlit apps, we need manual OAuth flow
                    raise ValueError(
                        "OAuth2 credentials not available. For Streamlit apps, you need to:\n"
                        "1. Run the initial OAuth setup locally using setup_oauth2_locally()\n"
                        "2. Copy the generated gmail_token.json to your deployment\n"
                        "3. Or use service account authentication instead"
                    )
                else:
                    # Desktop/local development flow
                    client_secrets_path = f'{self.root_path}appdata/client_secret.json'
                    if not os.path.exists(client_secrets_path):
                        raise FileNotFoundError(f"Client secrets file not found: {client_secrets_path}")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                    
                    # Save the credentials for the next run
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                    logger.info("OAuth2 credentials obtained and saved")
        
        return creds
    
    def test_connection(self, streamlit_mode: bool = False) -> bool:
        """Test Gmail IMAP connection using OAuth2."""
        try:
            creds = self.get_credentials(streamlit_mode=streamlit_mode)
            auth_string = f"user={self.email_user}\x01auth=Bearer {creds.token}\x01\x01"
            
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.authenticate('XOAUTH2', lambda x: auth_string)
            mail.logout()
            return True
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False
    
    def _connect_to_gmail(self, streamlit_mode: bool = False) -> imaplib.IMAP4_SSL:
        """Create and return Gmail IMAP connection using OAuth2."""
        try:
            creds = self.get_credentials(streamlit_mode=streamlit_mode)
            auth_string = f"user={self.email_user}\x01auth=Bearer {creds.token}\x01\x01"
            
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.authenticate('XOAUTH2', lambda x: auth_string)
            return mail
        except Exception as e:
            logger.error(f"Failed to connect to Gmail: {e}")
            raise
    
    def download_supplier_files(self, supplier_code: str, update_history: Optional[object] = None, 
                              streamlit_mode: bool = False) -> List[str]:
        """
        Download files for specific supplier.
        Extracted and generalized from individual update_XX() methods.
        
        Args:
            supplier_code: Code for the supplier (AL, VF, etc.)
            update_history: Optional history object to update
            streamlit_mode: If True, uses Streamlit-compatible authentication
        """
        if supplier_code not in self.supplier_configs:
            raise ValueError(f"Unknown supplier code: {supplier_code}")
        
        supplier_config = self.supplier_configs[supplier_code]
        downloaded_files = []
        
        try:
            mail = self._connect_to_gmail(streamlit_mode=streamlit_mode)
            
            # Select appropriate mailbox based on supplier
            if supplier_code in ['OUTRE']:
                mail.select('Company/Outre')
            elif supplier_code in ['HZ']:
                mail.select('Company/Sensationnel')
            else:
                mail.select('"[Gmail]/All Mail"')
            
            # Build search criteria
            search_criteria = self._build_search_criteria(supplier_code, supplier_config)
            status, messages = mail.search(None, search_criteria)
            
            if status == 'OK' and messages[0]:
                messages = messages[0].split()
                downloaded_files = self._process_emails(
                    mail, messages, supplier_code, supplier_config, update_history
                )
            else:
                logger.warning(f"No emails found for supplier {supplier_code}")
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            logger.error(f"Error downloading files for supplier {supplier_code}: {e}")
            raise
        
        return downloaded_files
    
    def _build_search_criteria(self, supplier_code: str, config: Dict) -> str:
        """Build IMAP search criteria based on supplier configuration."""
        if supplier_code in ['OUTRE', 'HZ']:
            # These suppliers only use SUBJECT
            return f'SUBJECT {config["SUBJECT"]}'
        else:
            # Most suppliers use both SUBJECT and FROM
            return f'SUBJECT {config["SUBJECT"]} FROM {config["FROM"]}'
    
    def _process_emails(self, mail: imaplib.IMAP4_SSL, messages: List[bytes], 
                       supplier_code: str, config: Dict, update_history: Optional[object]) -> List[str]:
        """Process emails and download attachments."""
        downloaded_files = []
        
        if supplier_code == 'SNG':
            # Special handling for SNG - search for specific filename pattern
            downloaded_files = self._process_sng_emails(mail, messages, update_history)
        else:
            # Standard processing for other suppliers
            if messages:
                # Get the latest email
                res, msg = mail.fetch(messages[-1], '(RFC822)')
                decoded_msg = email.message_from_bytes(msg[0][1])
                
                # Update history if provided
                if update_history is not None:
                    date_received = self._parse_email_date(decoded_msg.get('Date'), supplier_code)
                    self._update_history_date(update_history, supplier_code, date_received)
                
                # Download attachments
                downloaded_files = self._download_attachments(decoded_msg, supplier_code)
        
        return downloaded_files
    
    def _process_sng_emails(self, mail: imaplib.IMAP4_SSL, messages: List[bytes], 
                           update_history: Optional[object]) -> List[str]:
        """Special processing for SNG emails - search for specific filename pattern."""
        downloaded_files = []
        downloaded = False
        
        # Start from the most recent email and work backwards
        for i in range(len(messages) - 1, -1, -1):
            if downloaded:
                break
                
            try:
                res, msg = mail.fetch(messages[i], '(RFC822)')
                decoded_msg = email.message_from_bytes(msg[0][1])
                
                # Update history (only for the first/most recent email processed)
                if update_history is not None and i == len(messages) - 1:
                    date_received = self._parse_email_date(decoded_msg.get('Date'), 'SNG')
                    self._update_history_date(update_history, 'SNG', date_received)
                
                # Look for attachment with specific filename pattern
                for part in decoded_msg.walk():
                    if part.get('Content-Disposition'):
                        filename = part.get_filename()
                        # SNG specific condition: look for Excel files with specific naming pattern
                        if filename and (len(filename) == 9 or filename.endswith('.xlsx')):
                            # Create inv_data directory if it doesn't exist
                            import os
                            os.makedirs(f'{self.root_path}inv_data', exist_ok=True)
                            
                            file_path = f'{self.root_path}inv_data/SNG_inv.xlsx'
                            with open(file_path, 'wb') as f:
                                f.write(part.get_payload(decode=True))
                            logger.info(f'SNG - {filename} downloaded to {file_path}')
                            downloaded_files.append(file_path)
                            downloaded = True
                            break
                            
            except Exception as e:
                logger.error(f"Error processing SNG email at position {i}: {e}")
                continue
        
        if not downloaded_files:
            logger.info(f"No SNG files found with the expected filename pattern. Processed {len(messages)} emails.")
        
        return downloaded_files
    
    def _parse_email_date(self, date_str: str, supplier_code: str) -> datetime.datetime:
        """Parse email date string based on supplier format."""
        try:
            if supplier_code in ['OUTRE', 'HZ']:
                return datetime.datetime.strptime(date_str, "%d %b %Y %X %z")
            else:
                return datetime.datetime.strptime(date_str, "%a, %d %b %Y %X %z")
        except Exception as e:
            logger.error(f"Error parsing date for {supplier_code}: {e}")
            return datetime.datetime.now()
    
    def _update_history_date(self, update_history: object, supplier_code: str, date_received: datetime.datetime):
        """Update the history object with received date."""
        try:
            if hasattr(update_history, 'loc'):
                update_history.loc[update_history['Initial'] == supplier_code, 'Date'] = date_received.strftime("%d-%b")
        except Exception as e:
            logger.error(f"Error updating history for {supplier_code}: {e}")
    
    def _download_attachments(self, decoded_msg: email.message.Message, supplier_code: str) -> List[str]:
        """Download attachments from email message."""
        downloaded_files = []
        
        for part in decoded_msg.walk():
            if part.get('Content-Disposition') or (supplier_code in ['OUTRE', 'HZ'] and 'name=' in part.get('Content-Type', '')):
                filename = self._get_attachment_filename(part, supplier_code)
                if filename and self._should_download_file(filename, supplier_code):
                    file_path = self._get_file_path(filename, supplier_code)
                    
                    try:
                        with open(file_path, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        logger.info(f'{supplier_code} - {filename} downloaded')
                        downloaded_files.append(file_path)
                    except Exception as e:
                        logger.error(f"Error downloading {filename} for {supplier_code}: {e}")
        
        return downloaded_files
    
    def _get_attachment_filename(self, part: email.message.Message, supplier_code: str) -> Optional[str]:
        """Extract filename from email part."""
        if supplier_code in ['OUTRE', 'HZ']:
            # Special handling for OUTRE and HZ
            content_type = part.get('Content-Type', '')
            if 'name=' in content_type:
                return content_type.split('name=')[-1]
        else:
            return part.get_filename()
        return None
    
    def _should_download_file(self, filename: str, supplier_code: str) -> bool:
        """Determine if file should be downloaded based on supplier rules."""
        if supplier_code == 'AL':
            return 'brs' in filename or 'inv' in filename
        elif supplier_code == 'VF':
            return True  # Download all Excel files
        elif supplier_code == 'NBF':
            return filename.endswith('.xlsx')
        elif supplier_code in ['OUTRE', 'HZ']:
            return filename.endswith('.csv')
        else:
            return True
    
    def _get_file_path(self, filename: str, supplier_code: str) -> str:
        """Get the file path where attachment should be saved."""
        file_mapping = {
            'AL': {
                'brs': 'AL_brs inv.xls',
                'inv': 'AL_inv.xls'
            },
            'VF': 'VF_Inventory.xls',
            'BY': 'BY_InventoryListAll.xls',
            'NBF': 'NBF_Chade Fashions.xlsx',
            'OUTRE': 'OUTRE_StockAvailability.csv',
            'HZ': 'HZ_StockAvailability.csv',
            'SNG': 'SNG_inv.xlsx',
            'MANE': 'MANE_inv.xlsx'
        }
        
        if supplier_code == 'AL':
            if 'brs' in filename:
                return f'{self.root_path}inv_data/{file_mapping["AL"]["brs"]}'
            else:
                return f'{self.root_path}inv_data/{file_mapping["AL"]["inv"]}'
        else:
            return f'{self.root_path}inv_data/{file_mapping[supplier_code]}'
    
    def setup_oauth2(self) -> bool:
        """
        Setup OAuth2 authentication for Gmail.
        This will trigger the OAuth2 flow if credentials are not available.
        Only works in local/desktop environments.
        """
        try:
            creds = self.get_credentials(streamlit_mode=False)
            logger.info("OAuth2 credentials obtained successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to setup OAuth2: {e}")
            return False
    
    def setup_oauth2_locally(self) -> str:
        """
        Setup OAuth2 authentication locally for later use in Streamlit.
        Returns the path to the generated token file.
        
        Use this method to generate credentials locally, then copy the 
        gmail_token.json file to your Streamlit deployment.
        """
        try:
            client_secrets_path = f'{self.root_path}appdata/client_secret.json'
            if not os.path.exists(client_secrets_path):
                raise FileNotFoundError(f"Client secrets file not found: {client_secrets_path}")
            
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
            token_path = f'{self.root_path}appdata/gmail_token.json'
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            
            logger.info(f"OAuth2 credentials saved to: {token_path}")
            print(f"✅ OAuth2 setup complete!")
            print(f"📁 Token saved to: {token_path}")
            print(f"📋 Copy this file to your Streamlit deployment's appdata/ directory")
            
            return token_path
        except Exception as e:
            logger.error(f"Failed to setup OAuth2 locally: {e}")
            raise
    
    def get_oauth2_url_for_streamlit(self) -> str:
        """
        Generate OAuth2 authorization URL for manual Streamlit flow.
        Returns URL that user can visit to authorize the application.
        """
        try:
            client_secrets_path = f'{self.root_path}appdata/client_secret.json'
            if not os.path.exists(client_secrets_path):
                raise FileNotFoundError(f"Client secrets file not found: {client_secrets_path}")
            
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'  # For manual copy-paste flow
            
            auth_url, _ = flow.authorization_url(prompt='consent')
            return auth_url
        except Exception as e:
            logger.error(f"Failed to generate OAuth2 URL: {e}")
            raise
    
    def complete_oauth2_with_code(self, auth_code: str) -> bool:
        """
        Complete OAuth2 flow using authorization code from manual flow.
        Use this in Streamlit apps where users paste the authorization code.
        """
        try:
            client_secrets_path = f'{self.root_path}appdata/client_secret.json'
            if not os.path.exists(client_secrets_path):
                raise FileNotFoundError(f"Client secrets file not found: {client_secrets_path}")
            
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            
            token_path = f'{self.root_path}appdata/gmail_token.json'
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            
            logger.info("OAuth2 credentials saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to complete OAuth2 with code: {e}")
            return False
    
    def refresh_credentials(self) -> bool:
        """Force refresh of OAuth2 credentials."""
        try:
            token_path = f'{self.root_path}appdata/gmail_token.json'
            if os.path.exists(token_path):
                os.remove(token_path)
                logger.info("Removed existing token file")
            
            creds = self.get_credentials()
            logger.info("OAuth2 credentials refreshed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to refresh credentials: {e}")
            return False
    
    def get_connection_status(self) -> Dict[str, any]:
        """Get email connection status information."""
        try:
            is_connected = self.test_connection()
            
            # Check if we have valid credentials
            token_path = f'{self.root_path}appdata/gmail_token.json'
            has_token = os.path.exists(token_path)
            
            client_secrets_path = f'{self.root_path}appdata/client_secret.json'
            has_client_secrets = os.path.exists(client_secrets_path)
            
            return {
                'connected': is_connected,
                'email_user': self.email_user,
                'has_token': has_token,
                'has_client_secrets': has_client_secrets,
                'auth_method': 'OAuth2',
                'last_check': datetime.datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e),
                'auth_method': 'OAuth2',
                'last_check': datetime.datetime.now().isoformat()
            }
    
    def get_supplier_configs(self) -> Dict[str, Dict]:
        """Get all supplier email configurations."""
        return self.supplier_configs.copy()
    
    def retry_download(self, supplier_code: str, max_retries: int = 3, delay: int = 5) -> List[str]:
        """Download supplier files with retry logic."""
        for attempt in range(max_retries):
            try:
                return self.download_supplier_files(supplier_code)
            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed for {supplier_code}: {e}")
                if attempt < max_retries - 1:
                    sleep(delay)
                else:
                    raise
        return []