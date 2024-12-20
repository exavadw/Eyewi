from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle

class GoogleDriveUploader:
    def __init__(self, credentials_file='credentials.json', token_file='token.pickle'):
        self.scopes = ['https://www.googleapis.com/auth/drive.file']
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None
        self.authenticated = False

    def authenticate(self):
        """Authenticate and create the Google Drive service."""
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                self.creds = pickle.load(token)
        
        # If no valid credentials are available, log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.scopes)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for later use
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.creds, token)

        # Build the Google Drive service
        self.service = build('drive', 'v3', credentials=self.creds)

    def upload_to_shared_folder(self, file_path, folder_link):
        """
        Uploads a file to a shared folder given its Google Drive link.
        Args:
            file_path (str): Local path to the file to be uploaded.
            folder_link (str): Shared folder link.
        """

        # Extract the folder ID from the shared folder link
        folder_id = self.extract_folder_id(folder_link)
        if not folder_id:
            print("Error: Invalid shared folder link.")
            return

        file_name = os.path.basename(file_path)

        file_metadata = {
            'name': file_name,
            'parents': [folder_id]  # Upload to the specified shared folder
        }

        media = MediaFileUpload(file_path, resumable=True)

        # Upload the file
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        print(f"File '{file_name}' uploaded successfully with ID: {file.get('id')}")

    def extract_folder_id(self, folder_link):
        """
        Extracts the folder ID from a shared Google Drive link.
        """
        import re
        match = re.search(r'folders/([a-zA-Z0-9_-]+)', folder_link)
        return match.group(1) if match else None