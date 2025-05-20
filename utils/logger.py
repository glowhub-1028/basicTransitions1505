import os
import logging
from datetime import datetime
from msal import ConfidentialClientApplication
import requests
from typing import Optional
from requests.adapters import HTTPAdapter


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
CLIENT_ID = os.getenv('CLIENT_ID')
TENANT_ID = os.getenv('TENANT_ID') 
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

def save_output_to_file(title: str, chapo: str, article_text: str, transitions: list[str]) -> Optional[str]:
    """
    Saves article content to local .txt file and uploads it to OneDrive
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

        # Upload to OneDrive
        if upload_to_onedrive(filepath, filename):
            logger.info("Successfully uploaded to OneDrive")
            return filepath
        else:
            logger.error("Failed to upload to OneDrive")
            return None
    except Exception as e:
        logger.error(f"Error saving output: {str(e)}")
        return None
