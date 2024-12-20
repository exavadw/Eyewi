import tkinter as tk
import tkinter.messagebox
import tkinter.filedialog
from tkinter import ttk
import cv2
from AVFoundation import AVCaptureDevice
import time
from collections import deque
import os
import threading
import copy
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
import re
import drive
import shutil

class WebcamSelectorApp:
    SAVE_DIRECTORY_FILE = "save_directory.txt"
    SAVE_LINK_FILE = "save_link.txt"
    def __init__(self, root):
        self.root = root
        self.root.title("Eyewi")

        # Create a Frame to hold the canvas and scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create a Canvas
        canvas = tk.Canvas(main_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add a vertical scrollbar to the canvas
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the canvas to use the scrollbar
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Create a frame inside the canvas for widgets
        self.content_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        # Initialize Variables
        self.drive = drive.GoogleDriveUploader()
        self.currentwidth = 0
        self.currentheight = 0
        self.currentfps = 0
        self.save_length = 1
        self.running = False
        self.capture = None
        self.delay_buffer = deque()  # To store frames for delayed playback
        self.max_save_buffer_size = 0
        self.save_buffer = deque()  # To store frames for delayed playback
        self.delay = 0.0
        self.mirror = False  # Flag to toggle mirroring
        self.upload_to_drive = False

        # Populate the content frame with widgets
        self.populate_widgets()



    def populate_widgets(self):
        # Initialize default save directory
        self.save_directory = os.getcwd()

        # Get list of webcams
        self.webcams = self.get_webcam_names()

        # Dropdown to select webcam
        self.webcamlabel = tk.Label(self.content_frame, text="Select Webcam:")
        self.webcamlabel.pack(pady=5)

        self.webcam_dropdown = ttk.Combobox(self.content_frame, state="readonly", values=self.webcams)
        self.webcam_dropdown.bind("<<ComboboxSelected>>", self.on_webcam_change)
        self.webcam_dropdown.pack(pady=5)

        if self.webcams:
            self.webcam_dropdown.current(0)  # Set default to first webcam
        else:
            self.webcam_dropdown.set("No webcams found")

        self.reslabel = tk.Label(self.content_frame, text="Select Resolution and FPS:")
        self.reslabel.pack(pady=5)

        self.resolutions = self.get_supported_resolutions_fps(0)  # Placeholder index
        self.resolution_dropdown = ttk.Combobox(self.content_frame, state="readonly", values=self.resolutions)
        self.resolution_dropdown.pack(pady=5)

        if self.resolutions:
            self.resolution_dropdown.current(len(self.resolutions) - 1)
        else:
            self.resolution_dropdown.set("N/A")

        # Slider to adjust delay
        self.slider_label = tk.Label(self.content_frame, text="Adjust Delay (0-30 seconds):")
        self.slider_label.pack(pady=5)

        self.delay_slider = tk.Scale(self.content_frame, from_=0, to=30, resolution=0.001, orient="horizontal", length=300, command=self.update_slider_label)
        self.delay_slider.set(0.0)
        self.delay_slider.pack(pady=5)

        # Label to display slider value
        self.slider_value_label = tk.Label(self.content_frame, text="Delay: 0.000 seconds")
        self.slider_value_label.pack(pady=5)

        # Entry to specify precise delay
        self.entry_label = tk.Label(self.content_frame, text="Specify Delay (0-30 seconds):")
        self.entry_label.pack(pady=5)

        self.delay_var = tk.StringVar()
        self.delay_var.set("0.0")
        self.delay_var.trace("w", self.update_slider_from_entry)

        self.delay_entry = tk.Entry(self.content_frame, width=10, textvariable=self.delay_var)
        self.delay_entry.pack(pady=5)

        # Button to toggle mirroring
        self.mirror_button = tk.Button(self.content_frame, text="Toggle Mirror", command=self.toggle_mirror)
        self.mirror_button.pack(pady=10)

        # Button to start/stop webcam
        self.control_button = tk.Button(self.content_frame, text="Start Webcam", command=self.toggle_webcam)
        self.control_button.pack(pady=10)

        # Slider to adjust save buffer values
        self.save_slider_label = tk.Label(self.content_frame, text="Adjust Video Length (Max 120 Seconds):")
        self.save_slider_label.pack(pady=5)

        self.save_slider = tk.Scale(self.content_frame, from_=1, to=120, resolution=1, orient="horizontal", length=300, command=self.update_save_slider_label)
        self.save_slider.set(1)
        self.save_slider.pack(pady=5)

        # Label to display save slider value
        self.save_slider_value_label = tk.Label(self.content_frame, text="Video Length: 1 second")
        self.save_slider_value_label.pack(pady=5)

        # Entry to specify precise video length
        self.save_entry_label = tk.Label(self.content_frame, text="Specify Video Length (0-120 seconds):")
        self.save_entry_label.pack(pady=5)

        self.save_var = tk.StringVar()
        self.save_var.set("1")
        self.save_var.trace("w", self.update_save_from_entry)

        self.save_entry = tk.Entry(self.content_frame, width=10, textvariable=self.save_var)
        self.save_entry.pack(pady=5)

        # Button to save footage
        self.save_button = tk.Button(self.content_frame, text="Save Video", command=self.save, state="disabled")
        self.save_button.pack(pady=10)

        # Label for current save directory
        self.savelabel = tk.Label(self.content_frame, text=f"Current Save Directory:")
        self.savelabel.pack(pady=5)

        self.dirlabel = tk.Label(self.content_frame, text=self.load_save_directory())
        self.dirlabel.pack(pady=5)

        # Button to change save directory
        self.change_directory_button = tk.Button(self.content_frame, text="Change Save Directory", command=self.change_save_directory)
        self.change_directory_button.pack(pady=10)
        
        # Initialize BooleanVar for the checkbox
        self.upload_to_drive_var = tk.BooleanVar(value=self.upload_to_drive)

        # Checkbox to enable/disable uploading to Google Drive
        self.drive_checkbox = tk.Checkbutton(
            self.content_frame,
            text="Upload to Drive",
            variable=self.upload_to_drive_var,
            command=self.toggle_upload_to_drive
        )
        self.drive_checkbox.pack(pady=5)

        # Button to authenticate drive
        self.authbutton = tk.Button(self.content_frame, text="Authenticate Google Drive", command=self.authenticate)
        self.authbutton.pack(pady=10)

        # Entry for Google Drive folder link
        self.drive_label = tk.Label(self.content_frame, text="Google Drive Folder Link:")
        self.drive_label.pack(pady=5)

        self.drive_var = tk.StringVar()
        self.drive_var.set(self.load_link_directory())
        
        self.drive_entry = tk.Entry(self.content_frame, width=30, textvariable=self.drive_var)
        self.drive_entry.pack(pady=5)

       # Button to save footage
        self.save_drive_button = tk.Button(self.content_frame, text="Save Drive Link", command=self.save_link, state="normal")
        self.save_drive_button.pack(pady=10)

    def toggle_upload_to_drive(self):
        self.upload_to_drive = self.upload_to_drive_var.get()

    def authenticate(self):
        self.check_and_copy_credentials()
        self.drive.authenticate()
        tkinter.messagebox.showinfo("Info", "Authentication Successful")
        
    def save_link(self):
        with open(self.SAVE_LINK_FILE, "w") as f:
            test = self.drive_var.get()
            f.write(test)

    def load_link_directory(self):
        """Load the save directory from file or initialize it."""
        if os.path.exists(self.SAVE_LINK_FILE):
            with open(self.SAVE_LINK_FILE, "r") as f:
                link = f.read().strip()
                return link
        open(self.SAVE_LINK_FILE, "w")
        return ""

    def on_webcam_change(self, event):
        selected_index = self.webcam_dropdown.current()  # Get the selected index
        self.resolutions.clear()
        self.resolutions = self.get_supported_resolutions_fps(selected_index)
        self.resolution_dropdown['values'] = self.resolutions
        self.resolution_dropdown.current(len(self.resolutions) - 1)

    def set_resolution(self):
        index = self.resolution_dropdown.current()
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolutions[index][0])
        self.currentwidth = self.resolutions[index][0]
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolutions[index][1])
        self.currentheight = self.resolutions[index][1]
        self.capture.set(cv2.CAP_PROP_FPS, self.resolutions[index][2])
        self.currentfps = self.resolutions[index][2]
        
    def update_save_directory(self):
        self.dirlabel['text'] = self.load_save_directory()

    def load_save_directory(self):
        """Load the save directory from file or initialize it."""
        if os.path.exists(self.SAVE_DIRECTORY_FILE):
            with open(self.SAVE_DIRECTORY_FILE, "r") as f:
                directory = f.read().strip()
                if os.path.isdir(directory):
                    return directory
        # Default to the current working directory
        default_directory = os.getcwd()
        self.update_save_directory_file(default_directory)
        return default_directory

    def update_save_directory_file(self, directory):
        """Update the save directory file with the new directory."""
        with open(self.SAVE_DIRECTORY_FILE, "w") as f:
            f.write(directory)

    def get_webcam_names(self):
        """Retrieve names of connected webcams using AVFoundation."""
        devices = AVCaptureDevice.devicesWithMediaType_("vide")
        return [device.localizedName() for device in devices]

    def update_save_slider_label(self, value):
        """Update the slider value label."""
        self.save_slider_value_label.config(text=f"Video Length: {int(value)} Seconds")
        self.save_length = int(value)
        self.save_var.set(f"{int(value)}")  # Update entry box without triggering infinite loop

    def update_slider_label(self, value):
        """Update the slider value label."""
        self.slider_value_label.config(text=f"Delay: {float(value):.3f} Seconds")
        self.delay = float(value)
        self.delay_var.set(f"{float(value):.3f}")  # Update entry box without triggering infinite loop

    def update_slider_from_entry(self, *args):
        """Update the slider value from the entry box."""
        try:
            delay_value = float(self.delay_var.get())
            if 0 <= delay_value <= 30:
                self.delay_slider.set(delay_value)  # Update the slider
                self.delay = delay_value
            else:
                raise ValueError
        except ValueError:
            pass  # Ignore invalid values

    def update_save_from_entry(self, *args):
        """Update the slider value from the entry box."""
        try:
            save_value = float(self.save_var.get())
            if 0 <= save_value <= 120:
                self.save_slider.set(save_value)  # Update the slider
                self.save_length = save_value
            else:
                raise ValueError
        except ValueError:
            pass  # Ignore invalid values

    def toggle_webcam(self):
        """Start or stop the webcam feed."""
        if self.running:
            self.stop_webcam()
        else:
            self.start_webcam()

    def start_webcam(self):
        """Starts the selected webcam and displays its feed."""
        selected_index = self.webcam_dropdown.current()

        if selected_index == -1 or not self.webcams:
            tkinter.messagebox.showwarning("Warning", "No webcam selected.")
            return
        
        self.capture = cv2.VideoCapture(selected_index)

        #second open check
        if not self.capture.isOpened():
            tkinter.messagebox.showerror("Error", f"Unable to open {self.webcams[selected_index]}")
            return
        
        self.set_resolution()
        self.running = True
        self.control_button.config(text="Stop Webcam")
        self.mirror_button.config(state="normal")  # Enable the mirror button
        self.save_button.config(state="normal")  # Enable the save button
        self.max_save_buffer_size = (int(self.currentfps or 30) * self.save_length)  # Maximum number of frames for a 30-second save buffer
        self.show_frame()

    def sort_resolutions(self, tuples_list):
        return sorted(tuples_list, key=lambda x: (x[0], x[1], x[2]))
    
    def get_supported_resolutions_fps(self, index):
        selected_index = index

        if selected_index == -1 or not self.webcams:
            return

        resolutions = [
            (320, 240), (640, 480), (800, 600), 
            (1280, 720), (1920, 1080), (2560, 1440), 
            (3840, 2160)  # 4K
        ]
        # Common FPS values
        fps_values = [15, 30, 60, 120, 240]
        
        supported_combinations = []

        # Initialize the webcam
        cap = cv2.VideoCapture(selected_index)

        if not cap.isOpened():
            print("Error: Could not open webcam.")
            return supported_combinations

        # Test each resolution and FPS
        for width, height in resolutions:
            for fps in fps_values:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                cap.set(cv2.CAP_PROP_FPS, fps)

                # Retrieve the settings after applying
                actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                actual_fps = int(cap.get(cv2.CAP_PROP_FPS))

                # Check if the desired settings were successfully applied
                if int(actual_width) == width and int(actual_height) == height and int(actual_fps) == fps:
                    if ((int(actual_width), int(actual_height), int(actual_fps)) not in supported_combinations):
                        supported_combinations.append((int(width), int(height), int(fps)))
                elif ((int(actual_width), int(actual_height), int(actual_fps)) not in supported_combinations):
                    supported_combinations.append((int(actual_width), int(actual_height), int(actual_fps)))

        cap.release()
        return self.sort_resolutions(supported_combinations)

    def stop_webcam(self):
        """Stops the webcam feed."""
        self.running = False
        self.control_button.config(text="Start Webcam")
        self.mirror_button.config(state="disabled")  # Disable the mirror button
        self.save_button.config(state="disabled")  # Disable the save button

        if self.capture:
            self.capture.release()

        cv2.destroyAllWindows()  # Close OpenCV window
        self.delay_buffer.clear()  # Clear the delay buffer
        self.save_buffer.clear()  # Clear the saved buffer

    def toggle_mirror(self):
        """Toggles the mirroring effect on the video feed."""
        self.mirror = not self.mirror

    def change_save_directory(self):
        """Allow the user to select a directory to save videos."""
        directory = tkinter.filedialog.askdirectory(initialdir=self.save_directory, title="Select Save Directory")
        if directory:  # If a directory is selected
            self.save_directory = directory
            self.dirlabel['text'] = directory
            tkinter.messagebox.showinfo("Info", f"Save directory changed to: {self.save_directory}")

    def get_max_res(self) -> tuple:
        HIGH_VALUE = 10000
        WIDTH = HIGH_VALUE
        HEIGHT = HIGH_VALUE

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        return int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    def check_and_copy_credentials(self):
        """
        Check if credentials.json exists in the current working directory.
        If not, prompt the user to select the file and copy it to the working directory.
        """
        current_dir = os.getcwd()
        credentials_path = os.path.join(current_dir, "credentials.json")

        # Check if the file exists
        if not os.path.exists(credentials_path):
            print("credentials.json not found in the current directory.")

            # Create a Tkinter root window (hidden)
            root = tk.Tk()
            root.withdraw()

            # Prompt the user to select a file
            tkinter.messagebox.showinfo("Select File", "Please select a credentials.json file.")
            selected_file = tkinter.filedialog.askopenfilename(
                title="Select credentials.json File",
                filetypes=[("JSON Files", "*.json")]
            )

            # If a file was selected
            if selected_file:
                try:
                    shutil.copy(selected_file, credentials_path)
                    print(f"File copied to: {credentials_path}")
                    tkinter.messagebox.showinfo("Success", "credentials.json file has been copied to the current directory.")
                except Exception as e:
                    print(f"Error copying file: {e}")
                    tkinter.messagebox.showerror("Error", f"Failed to copy file: {e}")
            else:
                print("No file selected.")
                tkinter.messagebox.showwarning("Warning", "No file was selected. credentials.json is still missing.")
        else:
            print("credentials.json already exists in the current directory.")

    def save(self):
        """Save the last 30 seconds of webcam frames to an MP4 file in a separate thread."""
        if not self.save_buffer:
            tkinter.messagebox.showinfo("Info", "No frames available to save.")
            return

        self.save_button.config(state="disabled")  # Disable the save button
        # Get FPS and resolution from the webcam
        fps = copy.deepcopy(self.currentfps)  # Default to 30 FPS if unavailable
        width = copy.deepcopy(self.currentwidth)
        height = copy.deepcopy(self.currentheight)

        # Start a new thread for saving the video, passing necessary arguments
        save_thread = threading.Thread(
            target=self._save_video,
            args=(copy.deepcopy(self.save_buffer), fps, width, height)
        )
        save_thread.daemon = True  # Ensure thread exits when the application closes
        save_thread.start()

    def _save_video(self, save_buffer, fps, width, height):
        """Worker method to save video in a separate thread."""
        # Generate a unique filename in the selected directory
        filename = os.path.join(self.save_directory, "video.mp4")
        counter = 1
        while os.path.exists(filename):
            filename = os.path.join(self.save_directory, f"video_{counter}.mp4")
            counter += 1

        # Create a VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filename, fourcc, fps, (width, height))

        # Write frames to the file
        for _, frame in save_buffer:
            out.write(frame)

        out.release()  # Release the writer
        self.root.after(0, lambda: tkinter.messagebox.showinfo("Info", f"Video saved as {filename}"))

        if (self.upload_to_drive):
            if (not self.drive.authenticated):
                self.drive.authenticate()
                self.drive.authenticated = True
            self.drive.upload_to_shared_folder(filename, self.drive_var.get())
            self.root.after(0, lambda: tkinter.messagebox.showinfo("Info", f"Video uploaded to Google Drive"))

        self.root.after(0, lambda: self.save_button.config(state="normal"))  # Enable the save button

    def show_frame(self):
        """Capture and display frames in an external OpenCV window."""
        if self.running:
            ret, frame = self.capture.read()
            if ret:
                # Apply mirroring if enabled
                if self.mirror:
                    frame = cv2.flip(frame, 1)  # Flip horizontally

                # Store frame in delay buffer
                self.delay_buffer.append((time.time(), frame))

                # Remove frames outside the delay window
                while self.delay_buffer and time.time() - self.delay_buffer[0][0] > self.delay:
                    val = self.delay_buffer.popleft()
                    self.save_buffer.append(val)

                    # Display the delayed frame in an external OpenCV window
                    cv2.imshow("Webcam Feed", val[1])

                # Limit the save buffer size to 30 seconds
                if len(self.save_buffer) > self.max_save_buffer_size:
                    self.save_buffer.popleft()

            if cv2.waitKey(1) & 0xFF == ord('s'):
                self.save()
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop_webcam()
                return

            self.root.after(1, self.show_frame)


# Create the Tkinter application
root = tk.Tk()
app = WebcamSelectorApp(root)
root.mainloop()
