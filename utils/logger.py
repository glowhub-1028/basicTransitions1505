import os
import logging
from datetime import datetime
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Create logs directory if it doesn't exist
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Configure logging with more detailed format
log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Only show the message
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log the start of the application
logger.info("Application started")
logger.info(f"Log file location: {os.path.abspath(log_file)}")

def upload_to_gdrive(file_path: str, file_name: str, folder_id=None) -> Optional[str]:
    """
    Uploads the given file to Google Drive (optionally into a specific folder).
    Uses Streamlit secrets for authentication when deployed on Streamlit.io
    """
    try:
        logger.info(f"Attempting to upload {file_name} to Google Drive")

        # Verify file exists and is readable
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        # Use broader scope for full drive access
        SCOPES = ['https://www.googleapis.com/auth/drive']
        
        # Use Streamlit secrets for Google Drive credentials
        try:
            import streamlit as st
            service_account_info = st.secrets["gcp_service_account"]
            logger.info(f"Service account email: {service_account_info.get('client_email')}")
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info, scopes=SCOPES)
        except Exception as e:
            logger.error(f"Failed to load Google Drive credentials: {str(e)}")
            return None

        service = build('drive', 'v3', credentials=credentials)

        # Get folder ID from Streamlit secrets or use default
        try:
            folder_id = st.secrets.get("gdrive_folder_id")
            if not folder_id:
                logger.error("No folder ID found in Streamlit secrets")
                return None
                
            logger.info(f"Using folder ID: {folder_id}")
            
            # Set folder permissions to be accessible to anyone with the link
            folder_permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            service.permissions().create(
                fileId=folder_id,
                body=folder_permission,
                fields='id'
            ).execute()
            logger.info(f"Set folder permissions for folder ID: {folder_id}")
            
        except Exception as e:
            logger.error(f"Failed to get folder ID or set permissions: {str(e)}")
            return None

        file_metadata = {
            'name': file_name,
            'parents': [folder_id] if folder_id else []
        }

        media = MediaFileUpload(file_path, resumable=True)
        try:
            # Create the file
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink',
                supportsAllDrives=True
            ).execute()

            # Set the file to be accessible to anyone with the link
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            service.permissions().create(
                fileId=file.get('id'),
                body=permission,
                fields='id'
            ).execute()

            logger.info(f"Successfully uploaded {file_name} to Google Drive")
            logger.info(f"File ID: {file.get('id')}")
            logger.info(f"Web View Link: {file.get('webViewLink')}")
            
            return file.get('id')
        except Exception as e:
            logger.error(f"Failed to create file or set permissions: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Error uploading to Google Drive: {str(e)}")
        return None

def save_output_to_file(title: str, chapo: str, article_text: str, transitions: list[str]) -> Optional[str]:
    """
    Saves the generated article and transitions to a file and uploads it to Google Drive.
    Returns the Google Drive URL if successful, None otherwise.
    """
    try:
        # Create outputs directory if it doesn't exist
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"article_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)

        # Write content to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Titre: {title}\n\n")
            f.write(f"Chapeau: {chapo}\n\n")
            f.write("Article:\n")
            f.write(article_text.strip() + "\n\n")
            f.write("Transitions générées:\n")
            for i, t in enumerate(transitions, 1):
                f.write(f"{i}. {t}\n")

        logger.info(f"Successfully saved article to {filepath}")

        # Upload to Google Drive
        gdrive_file_id = upload_to_gdrive(filepath, filename)
        if gdrive_file_id:
            logger.info(f"Successfully uploaded to Google Drive with file ID: {gdrive_file_id}")
            return filepath
        else:
            logger.warning("File saved locally but upload to Google Drive failed")
            # return filepath  # Return filepath even if upload fails
            return None

    except Exception as e:
        logger.error(f"Error saving output: {str(e)}")
        return None