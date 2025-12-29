"""
Google Drive API Integration
=============================
OAuth 2.0 authentication and Drive file operations for KAI file sharing.

Features:
- OAuth 2.0 flow for user authentication
- List user's Drive files
- Download and cache files in Firebase
- Get file metadata
"""

import os
import io
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Google API imports
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    logging.warning("[DRIVE] Google API libraries not installed")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class GoogleDriveAPI:
    """
    Google Drive API wrapper for OAuth and file operations.
    
    Usage:
        drive_api = GoogleDriveAPI()
        
        # Get OAuth URL
        auth_url, state = drive_api.get_auth_url()
        
        # After user authorizes, exchange code
        tokens = drive_api.exchange_code(code, state)
        
        # List user's files
        files = drive_api.list_files(tokens['access_token'])
        
        # Download a file
        content = drive_api.download_file(file_id, tokens['access_token'])
    """
    
    # OAuth scopes - only read access needed
    SCOPES = [
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/drive.metadata.readonly'
    ]
    
    # Supported file types for import
    SUPPORTED_TYPES = {
        'application/pdf': 'pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
        'text/plain': 'txt',
        'text/csv': 'csv',
        'application/json': 'json',
        'image/png': 'png',
        'image/jpeg': 'jpg',
        'application/vnd.google-apps.document': 'gdoc',  # Export as DOCX
        'application/vnd.google-apps.spreadsheet': 'gsheet',  # Export as XLSX
        'application/vnd.google-apps.presentation': 'gslides'  # Export as PPTX
    }
    
    def __init__(self):
        """Initialize Google Drive API with credentials from environment."""
        self.client_id = os.getenv('GOOGLE_DRIVE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_DRIVE_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GOOGLE_DRIVE_REDIRECT_URI', 'http://localhost:5000/api/v1/drive/callback')
        
        if not self.client_id or not self.client_secret:
            logger.warning("[DRIVE] Google Drive credentials not configured")
            self.configured = False
        else:
            self.configured = True
            logger.info("[DRIVE] Google Drive API initialized")
    
    def is_available(self) -> bool:
        """Check if Drive API is available and configured."""
        return GOOGLE_API_AVAILABLE and self.configured
    
    def get_auth_url(self, state: Optional[str] = None) -> tuple:
        """
        Generate OAuth 2.0 authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Tuple of (auth_url, state)
        """
        if not self.is_available():
            raise RuntimeError("Google Drive API not configured")
        
        import secrets
        if not state:
            state = secrets.token_urlsafe(32)
        
        # Create OAuth flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri
        )
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent'
        )
        
        logger.info(f"[DRIVE] Generated auth URL with state: {state[:8]}...")
        return auth_url, state
    
    def exchange_code(self, code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access tokens.
        
        Args:
            code: Authorization code from OAuth callback
            state: State parameter for verification
            
        Returns:
            Dict with access_token, refresh_token, expiry
        """
        if not self.is_available():
            raise RuntimeError("Google Drive API not configured")
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri,
            state=state
        )
        
        # Exchange code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        tokens = {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None,
            'scopes': list(credentials.scopes or [])
        }
        
        logger.info(f"[DRIVE] Successfully exchanged code for tokens")
        return tokens
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            Dict with new access_token and expiry
        """
        if not self.is_available():
            raise RuntimeError("Google Drive API not configured")
        
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        
        credentials.refresh(Request())
        
        return {
            'access_token': credentials.token,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
    
    def list_files(
        self,
        access_token: str,
        page_size: int = 25,
        page_token: Optional[str] = None,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List user's Drive files.
        
        Args:
            access_token: Valid access token
            page_size: Number of files per page
            page_token: Token for pagination
            query: Search query (e.g., "name contains 'report'")
            
        Returns:
            Dict with files list and nextPageToken
        """
        if not self.is_available():
            raise RuntimeError("Google Drive API not configured")
        
        credentials = Credentials(token=access_token)
        service = build('drive', 'v3', credentials=credentials)
        
        # Build query to show supported files only
        mime_types = list(self.SUPPORTED_TYPES.keys())
        mime_query = " or ".join([f"mimeType='{mt}'" for mt in mime_types])
        
        full_query = f"({mime_query})"
        if query:
            full_query = f"{full_query} and {query}"
        
        # Exclude trashed files
        full_query += " and trashed=false"
        
        results = service.files().list(
            q=full_query,
            pageSize=page_size,
            pageToken=page_token,
            fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, iconLink, thumbnailLink, webViewLink)",
            orderBy="modifiedTime desc"
        ).execute()
        
        files = results.get('files', [])
        logger.info(f"[DRIVE] Listed {len(files)} files")
        
        return {
            'files': files,
            'next_page_token': results.get('nextPageToken')
        }
    
    def get_file_metadata(self, file_id: str, access_token: str) -> Dict[str, Any]:
        """
        Get metadata for a specific file.
        
        Args:
            file_id: Google Drive file ID
            access_token: Valid access token
            
        Returns:
            File metadata dict
        """
        if not self.is_available():
            raise RuntimeError("Google Drive API not configured")
        
        credentials = Credentials(token=access_token)
        service = build('drive', 'v3', credentials=credentials)
        
        file = service.files().get(
            fileId=file_id,
            fields="id, name, mimeType, size, modifiedTime, iconLink, thumbnailLink, webViewLink, owners"
        ).execute()
        
        return file
    
    def download_file(self, file_id: str, access_token: str) -> tuple:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            access_token: Valid access token
            
        Returns:
            Tuple of (file_bytes, mime_type, filename)
        """
        if not self.is_available():
            raise RuntimeError("Google Drive API not configured")
        
        credentials = Credentials(token=access_token)
        service = build('drive', 'v3', credentials=credentials)
        
        # Get file metadata first
        metadata = self.get_file_metadata(file_id, access_token)
        mime_type = metadata.get('mimeType', '')
        filename = metadata.get('name', 'unknown')
        
        # Handle Google Docs native formats (need export)
        export_map = {
            'application/vnd.google-apps.document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        }
        
        buffer = io.BytesIO()
        
        if mime_type in export_map:
            # Export Google Docs format
            export_mime = export_map[mime_type]
            request = service.files().export_media(fileId=file_id, mimeType=export_mime)
            
            # Update filename extension
            ext_map = {'document': '.docx', 'spreadsheet': '.xlsx', 'presentation': '.pptx'}
            for key, ext in ext_map.items():
                if key in mime_type:
                    if not filename.endswith(ext):
                        filename = filename.rsplit('.', 1)[0] + ext
                    break
            
            mime_type = export_mime
        else:
            # Download binary file
            request = service.files().get_media(fileId=file_id)
        
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        
        buffer.seek(0)
        file_bytes = buffer.read()
        
        logger.info(f"[DRIVE] Downloaded file: {filename} ({len(file_bytes)} bytes)")
        return file_bytes, mime_type, filename


# Global instance
_drive_api = None

def get_drive_api() -> GoogleDriveAPI:
    """Get global GoogleDriveAPI instance."""
    global _drive_api
    if _drive_api is None:
        _drive_api = GoogleDriveAPI()
    return _drive_api


# Convenience functions
def drive_auth_url(state: Optional[str] = None) -> tuple:
    """Get OAuth authorization URL."""
    return get_drive_api().get_auth_url(state)

def drive_exchange_code(code: str, state: str) -> Dict[str, Any]:
    """Exchange OAuth code for tokens."""
    return get_drive_api().exchange_code(code, state)

def drive_list_files(access_token: str, **kwargs) -> Dict[str, Any]:
    """List user's Drive files."""
    return get_drive_api().list_files(access_token, **kwargs)

def drive_download(file_id: str, access_token: str) -> tuple:
    """Download a file from Drive."""
    return get_drive_api().download_file(file_id, access_token)


if __name__ == "__main__":
    # Test initialization
    print("\nGoogle Drive API Test\n" + "=" * 50)
    
    api = GoogleDriveAPI()
    
    if not api.is_available():
        print("❌ Google Drive API not available")
        print("   Make sure GOOGLE_DRIVE_CLIENT_ID and GOOGLE_DRIVE_CLIENT_SECRET are set")
    else:
        print("✅ Google Drive API initialized")
        print(f"   Client ID: {api.client_id[:20]}...")
        print(f"   Redirect URI: {api.redirect_uri}")
        
        # Generate auth URL
        try:
            auth_url, state = api.get_auth_url()
            print(f"\n📎 Auth URL: {auth_url[:80]}...")
            print(f"   State: {state}")
        except Exception as e:
            print(f"❌ Failed to generate auth URL: {e}")
