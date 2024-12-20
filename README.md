# Eyewi: Instant Replay for Athletes

## Overview
Eyewi is a versatile application built with Python's Tkinter framework for capturing, displaying, and managing webcam feeds. It includes features for instant replay playback, video mirroring, resolution and FPS selection, and saving footage locally or uploading it to Google Drive.

## Features
- **Webcam Selection**: Automatically detects and lists available webcams.
- **Resolution and FPS Selection**: Allows users to select supported resolutions and frame rates.
- **Playback Delay**: Adjust playback delay between 0 to 30 seconds.
- **Video Mirroring**: Mirror video feeds horizontally.
- **Video Saving**: Save video footage locally with customizable length.
- **Google Drive Integration**: Option to upload saved videos directly to a Google Drive folder.
- **Dynamic Save Directory**: Easily change and persist the directory for saving videos.

## Requirements
- Python 3.7+
- Dependencies:
  - `tkinter`
  - `opencv-python`
  - `google-auth-oauthlib`
  - `google-auth`
  - `google-api-python-client`

Install dependencies using pip:
```bash
pip install opencv-python google-auth-oauthlib google-auth google-api-python-client
```

## Setting Up Google Cloud API
To enable Google Drive integration, you need to set up the Google Cloud API and obtain credentials.

### Step 1: Create a Project in Google Cloud Console
1. Visit the [Google Cloud Console](https://console.cloud.google.com/).
2. Click on "Select a project" and then "New Project."
3. Enter a project name and click "Create."

### Step 2: Enable the Google Drive API
1. In the Cloud Console, navigate to **APIs & Services > Library**.
2. Search for "Google Drive API" and enable it for your project.

### Step 3: Create Credentials
1. Navigate to **APIs & Services > Credentials** in the Cloud Console.
2. Click "Create Credentials" and choose "OAuth 2.0 Client IDs."
3. Configure the consent screen if prompted.
4. Choose "Desktop App" as the application type and click "Create."
5. Download the `credentials.json` file.

### Step 4: Add Credentials to the Application
1. Place the `credentials.json` file in the same directory as the Eyewi script.
2. When you run the application, it will use this file to authenticate with Google Drive.

## Running the Application
1. Launch the application by running the script:
   ```bash
   python eyewi.py
   ```
2. Use the graphical interface to select a webcam, set resolution, adjust playback delay, and save videos.
3. To enable Google Drive uploads:
   - Authenticate by clicking the "Authenticate Google Drive" button.
   - Enter the shared Google Drive folder link in the provided field.

## Shortcuts
- Press `s` in the OpenCV window to save the video buffer.
- Press `q` in the OpenCV window to stop the webcam feed.

## Additional Notes
- The application requires a stable internet connection for Google Drive uploads.
- Ensure your `credentials.json` file remains secure and private.

## License
This project is licensed under the MIT License.

