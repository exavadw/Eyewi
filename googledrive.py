import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc

def upload_to_shared_folder(file_path, upload_link):
    cwd = os.getcwd()
    chrome_driver_path = os.path.join(cwd, "chromedriver", "chromedriver")  # ChromeDriver path
    chromium_path = os.path.join(cwd, "Thorium", "Thorium.app/Contents/MacOS/Thorium")  # Local Chrome binary

    # Set up options to use bundled Chromium
    options = webdriver.ChromeOptions()
    options.binary_location = chromium_path  # Point to custom Chromium binary
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Use the Service class to specify the ChromeDriver path
    service = Service(chrome_driver_path)
    driver = uc.Chrome(service=service, options=options, version_main=126)

    try:
        print("Opening Google Drive folder...")
        driver.get(upload_link)
        print("Please log in to your Google account if prompted.")
        
        # Wait for the user to manually log in (you can increase the sleep duration)
        input("Press Enter after you have logged in to your Google account...")

        print("Starting file upload...")
        time.sleep(3)  # Small wait after login

        # Simulate right-click to open the upload menu
        actions = ActionChains(driver)
        actions.context_click().perform()
        time.sleep(1)

        # Use arrow keys to select 'File Upload'
        actions.send_keys(Keys.ARROW_DOWN).perform()
        time.sleep(0.5)
        actions.send_keys(Keys.ARROW_DOWN).perform()
        time.sleep(0.5)
        actions.send_keys(Keys.ENTER).perform()
        time.sleep(2)

        # Inject the file path directly into the file input
        file_input = driver.find_element(By.CSS_SELECTOR, 'input[type="file"]')
        file_input.send_keys(file_path)  # Set the file path
        print("File uploaded successfully!")

        time.sleep(10)  # Wait for upload completion
    except Exception as e:
        print(f"Error during file upload: {e}")
    finally:
        driver.quit()
        print("Driver closed.")

if __name__ == "__main__":
    upload_to_shared_folder("video_1.mp4", "https://drive.google.com/drive/folders/1qfcbZ7uyjFxclAqohwvyCMuwaNlWeWTo?usp=sharing")
