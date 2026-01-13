import os
import io
import time
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from django.conf import settings

logger = logging.getLogger(__name__)

class GoogleTemplateService:
    """Service to handle fetching templates from Google Drive"""
    
    def __init__(self):
        self.credentials_file = os.path.join(settings.BASE_DIR, settings.GOOGLE_SERVICE_ACCOUNT_FILE)
        self.template_id = settings.GOOGLE_DOCS_TEMPLATE_ID
        self.scopes = ['https://www.googleapis.com/auth/drive.readonly']
        self.service = self._get_drive_service()
        
    def _get_drive_service(self):
        """Initialize Google Drive API service"""
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_file, scopes=self.scopes
            )
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {e}")
            raise e
            
    def get_template_path(self):
        """
        Fetches the template from Google Drive and saves it locally as a cache.
        Returns the path to the local .docx file.
        """
        # Define cache path
        cache_dir = os.path.join(settings.MEDIA_ROOT, 'templates')
        os.makedirs(cache_dir, exist_ok=True)
        local_path = os.path.join(cache_dir, f"{self.template_id}.docx")
        
        # Check if we should use cached version (e.g., cache for 5 minutes)
        # For simplicity, we'll download it every time for now to ensure freshness,
        # but in a production environment, we'd add more robust caching.
        
        try:
            request = self.service.files().export_media(
                fileId=self.template_id,
                mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                
            with open(local_path, 'wb') as f:
                f.write(fh.getvalue())
                
            return local_path
        except Exception as e:
            logger.error(f"Error downloading template from Google Drive: {e}")
            # Fallback to local template if configured
            if hasattr(settings, 'QUOTATION_TEMPLATE_PATH') and os.path.exists(settings.QUOTATION_TEMPLATE_PATH):
                logger.info("Falling back to local template")
                return settings.QUOTATION_TEMPLATE_PATH
            raise e
