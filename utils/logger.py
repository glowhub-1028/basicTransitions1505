import os
import logging
from datetime import datetime
from msal import ConfidentialClientApplication
import requests
from typing import Optional
from requests.adapters import HTTPAdapter

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from urllib3.util.retry import Retry

# Create logs directory if it doesn't exist
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Configure logging with more detailed format
log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log the start of the application
logger.info("Application started")
logger.info(f"Log file location: {os.path.abspath(log_file)}")

# Replace these with your actual Azure credentials
CLIENT_ID = "98f784a9-5e71-4e57-9543-a83bc1fec732"
TENANT_ID = "0b89b039-029d-4a76-a420-14aa6287d930"
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

if not all([CLIENT_ID, TENANT_ID, CLIENT_SECRET]):
    raise ValueError("Azure credentials environment variables are not set")

# Microsoft Graph API scope
SCOPES = ["https://graph.microsoft.com/.default"]

# Configure requests session with retry strategy
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

def get_access_token() -> Optional[str]:
    """
    Authenticate and return access token using MSAL
    """
    try:
        app = ConfidentialClientApplication(
            client_id=CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{TENANT_ID}",
            client_credential=CLIENT_SECRET
        )
        
        # Add timeout to the token request
        result = app.acquire_token_for_client(scopes=SCOPES, timeout=30)

        if "access_token" in result:
            logger.info("Successfully acquired access token")
            return result["access_token"]
        else:
            error_msg = result.get("error_description", "Unknown error")
            logger.error(f"Failed to acquire token: {error_msg}")
            return None
    except Exception as e:
        logger.error(f"Error acquiring token: {str(e)}")
        return None

def create_onedrive_folder(access_token: str) -> bool:
    """
    Creates the StreamlitLogs folder in OneDrive if it doesn't exist
    """
    try:
        create_folder_url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
        folder_data = {
            "name": "StreamlitLogs",
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
        }
        
        # Use session with retry strategy
        response = session.post(
            create_folder_url,
            headers={"Authorization": f"Bearer {access_token}"},
            json=folder_data,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            logger.info("Successfully created StreamlitLogs folder in OneDrive")
            return True
        else:
            logger.error(f"Failed to create folder: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.Timeout:
        logger.error("Timeout while creating OneDrive folder")
        return False
    except Exception as e:
        logger.error(f"Error creating OneDrive folder: {str(e)}")
        return False

def upload_to_onedrive(file_path: str, file_name: str) -> bool:
    """
    Uploads the given file to the user's OneDrive root folder in a folder called 'StreamlitLogs'
    """
    try:
        logger.info(f"Attempting to upload {file_name} to OneDrive")
        
        # Verify file exists and is readable
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
            
        file_size = os.path.getsize(file_path)
        logger.info(f"File size: {file_size} bytes")
        
        access_token = get_access_token()
        if not access_token:
            logger.error("Failed to get access token for OneDrive upload")
            return False

        # Create folder if it doesn't exist
        if not create_onedrive_folder(access_token):
            logger.error("Failed to create or verify OneDrive folder")
            return False

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "text/plain"
        }

        # Upload the file into the folder
        upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/StreamlitLogs/{file_name}:/content"
        logger.info(f"Uploading to URL: {upload_url}")

        with open(file_path, "rb") as f:
            # Use session with retry strategy
            response = session.put(
                upload_url,
                headers=headers,
                data=f,
                timeout=30
            )

        if response.status_code in [200, 201]:
            logger.info(f"Successfully uploaded {file_name} to OneDrive")
            # Log the OneDrive file URL
            file_info = response.json()
            if 'webUrl' in file_info:
                logger.info(f"OneDrive file URL: {file_info['webUrl']}")
            return True
        else:
            logger.error(f"Failed to upload file: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.Timeout:
        logger.error("Timeout while uploading to OneDrive")
        return False
    except Exception as e:
        logger.error(f"Error uploading to OneDrive: {str(e)}")
        return False

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
            logger.error(f"Failed to create file in Google Drive: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Failed to upload to Google Drive: {str(e)}")
        return None

def save_output_to_file(title: str, chapo: str, article_text: str, transitions: list[str]) -> Optional[str]:
    """
    Saves article content to local .txt file and uploads it to Google Drive
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"generated_output_{timestamp}.txt"
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        # Save locally
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Titre: {title}\n\n")
            f.write(f"Chapeau: {chapo}\n\n")
            f.write("Article:\n")
            f.write(article_text.strip() + "\n\n")
            f.write("Transitions générées:\n")
            for i, t in enumerate(transitions, 1):
                f.write(f"{i}. {t}\n")

        logger.info(f"Successfully saved output to {filepath}")

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
        logger.error(f"Error in save_output_to_file: {str(e)}")
        return None