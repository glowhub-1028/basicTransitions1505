import streamlit as st
from openai import OpenAI
from utils.logger import get_access_token, create_onedrive_folder
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_openai_connection():
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # Make a simple API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, this is a test message."}],
            max_tokens=5
        )
        
        print("✅ OpenAI API connection successful!")
        print(f"Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ OpenAI API connection failed: {str(e)}")
        return False

def test_onedrive_connection():
    try:
        # Test OneDrive authentication
        access_token = get_access_token()
        if not access_token:
            print("❌ Failed to get OneDrive access token")
            return False
            
        # Test folder creation
        if create_onedrive_folder(access_token):
            print("✅ OneDrive connection successful!")
            return True
        else:
            print("❌ Failed to create OneDrive folder")
            return False
    except Exception as e:
        print(f"❌ OneDrive connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n=== Testing OpenAI API Connection ===")
    openai_success = test_openai_connection()
    
    print("\n=== Testing OneDrive Connection ===")
    onedrive_success = test_onedrive_connection()
    
    print("\n=== Test Summary ===")
    print(f"OpenAI API: {'✅ Success' if openai_success else '❌ Failed'}")
    print(f"OneDrive: {'✅ Success' if onedrive_success else '❌ Failed'}") 