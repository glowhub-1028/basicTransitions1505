from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import streamlit as st
from utils.logger import logger
from google.oauth2 import service_account
import io

# Google Drive API setup
# SCOPES are typically inferred or managed by sharing in Google Drive for service accounts.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/drive.file']

def get_google_drive_service():
    """Get or create Google Drive service using a service account key from Streamlit secrets."""
    try:
        # Get service account info from Streamlit secrets
        # Reading from the correct key: gcp_service_account
        service_account_info = st.secrets["gcp_service_account"]
        
        # Create credentials from service account info
        creds = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES # Use the defined scopes
        )
        
        # Build the service
        service = build('drive', 'v3', credentials=creds)
        logger.info("Successfully created Google Drive service using service account.")
        return service
        
    except KeyError as e:
        st.error(f"""
        ⚠️ Google Drive secrets not found or incorrectly formatted!
        Please ensure your Streamlit secrets (.streamlit/secrets.toml) are configured correctly.
        Expected structure:        
        Make sure the '[gcp_service_account]' section and its keys (type, project_id, etc.) and 'gdrive_folder_id' exist.
        Detail Error: {e}
        """)
        logger.error(f"Google Drive secrets KeyError: {e}")
        return None
    except Exception as e:
        st.error(f"""
        ⚠️ Error initializing Google Drive service: {str(e)}
        
        Please check your service account credentials and ensure the Google Drive API is enabled for the service account.
        Detail Error: {e}
        """)
        logger.error(f"Error initializing Google Drive service: {e}")
        return None

def list_folder_contents(service, folder_id):
    """List all files and folders in a Google Drive folder."""
    results = service.files().list(
        q=f"'{folder_id}' in parents",
        fields="files(id, name, mimeType)",
        pageSize=1000
    ).execute()
    return results.get('files', [])

def download_file_content(service, file_id):
    """Download content of a Google Drive file."""
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    return fh.getvalue().decode('utf-8')

def is_folder(mime_type):
    """Check if the item is a folder based on its MIME type."""
    return mime_type == 'application/vnd.google-apps.folder'

def process_folder(service, folder_id):
    """Process all files in a folder and its subfolders recursively."""
    results = []
    items = list_folder_contents(service, folder_id)
    
    for item in items:
        if is_folder(item['mimeType']):
            # Recursively process subfolders
            subfolder_results = process_folder(service, item['id'])
            results.extend(subfolder_results)
        elif item['mimeType'] == 'text/plain':
            # Process individual files
            try:
                content = download_file_content(service, item['id'])
                transitions = extract_transitions(content)
                if transitions:
                    results.append((item['name'], transitions))
            except Exception as e:
                logger.error(f"Error processing file {item['name']}: {str(e)}")
                continue
    
    return results

def extract_transitions(content):
    """Extract transitions from file content."""
    transitions = []
    lines = content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith("Transitions générées:"):
            continue
        if line and line[0].isdigit() and ". " in line:
            transition = line.split(". ", 1)[1].strip()
            transitions.append(transition)
    
    return transitions

def process_drive_files(service, files):
    """Process multiple Google Drive files and return a list of (filename, transitions) tuples."""
    results = []
    
    for file in files:
        try:
            if is_folder(file.get('mimeType')):
                # Process folder
                folder_results = process_folder(service, file['id'])
                results.extend(folder_results)
            else:
                # Process individual file
                content = download_file_content(service, file['id'])
                transitions = extract_transitions(content)
                if transitions:
                    results.append((file['name'], transitions))
                
        except Exception as e:
            logger.error(f"Error processing file/folder {file['name']}: {str(e)}")
            continue
            
    return results 