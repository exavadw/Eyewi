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


class WebcamSelectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Instant Replay with Adjustable Delay")

        # Initialize default save directory
        self.save_directory = os.getcwd()

        # Get list of webcams
        self.webcams = self.get_webcam_names()

        # Dropdown to select webcam
        self.label = tk.Label(root, text="Select Webcam:")
        self.label.pack(pady=5)

        self.webcam_dropdown = ttk.Combobox(root, state="readonly", values=self.webcams)
        self.webcam_dropdown.pack(pady=5)

        if self.webcams:
            self.webcam_dropdown.current(0)  # Set default to first webcam
        else:
            self.webcam_dropdown.set("No webcams found")

        # Slider to adjust delay
        self.slider_label = tk.Label(root, text="Adjust Delay (0-30 seconds):")
        self.slider_label.pack(pady=5)

        self.delay_slider = tk.Scale(root, from_=0, to=30, resolution=0.001, orient="horizontal", length=300, command=self.update_slider_label)
        self.delay_slider.set(0.0)
        self.delay_slider.pack(pady=5)

        # Label to display slider value
        self.slider_value_label = tk.Label(root, text="Delay: 0.000 seconds")
        self.slider_value_label.pack(pady=5)

        # Entry to specify precise delay
        self.entry_label = tk.Label(root, text="Specify Delay (0-30 seconds):")
        self.entry_label.pack(pady=5)

        self.delay_var = tk.StringVar()
        self.delay_var.set("0.0")
        self.delay_var.trace("w", self.update_slider_from_entry)

        self.delay_entry = tk.Entry(root, width=10, textvariable=self.delay_var)
        self.delay_entry.pack(pady=5)

        # Button to toggle mirroring
        self.mirror_button = tk.Button(root, text="Toggle Mirror", command=self.toggle_mirror)
        self.mirror_button.pack(pady=10)

        # Button to start/stop webcam
        self.control_button = tk.Button(root, text="Start Webcam", command=self.toggle_webcam)
        self.control_button.pack(pady=10)

        # Button to save footage
        self.save_button = tk.Button(root, text="Save Last 30 Seconds", command=self.save, state="disabled")
        self.save_button.pack(pady=10)

        # Button to change save directory
        self.change_directory_button = tk.Button(root, text="Change Save Directory", command=self.change_save_directory)
        self.change_directory_button.pack(pady=10)

        self.running = False
        self.capture = None
        self.delay_buffer = deque()  # To store frames for delayed playback
        self.max_save_buffer_size = 0
        self.save_buffer = deque()  # To store frames for delayed playback
        self.delay = 0.0
        self.mirror = False  # Flag to toggle mirroring

    def get_webcam_names(self):
        """Retrieve names of connected webcams using AVFoundation."""
        devices = AVCaptureDevice.devicesWithMediaType_("vide")
        return [device.localizedName() for device in devices]

    def update_slider_label(self, value):
        """Update the slider value label."""
        self.slider_value_label.config(text=f"Delay: {float(value):.3f} seconds")
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
        if not self.capture.isOpened():
            tkinter.messagebox.showerror("Error", f"Unable to open {self.webcams[selected_index]}")
            return

        self.running = True
        self.control_button.config(text="Stop Webcam")
        self.mirror_button.config(state="normal")  # Enable the mirror button
        self.save_button.config(state="normal")  # Enable the save button
        self.max_save_buffer_size = int((self.capture.get(cv2.CAP_PROP_FPS) or 30) * 30)  # Maximum number of frames for a 30-second save buffer
        self.show_frame()

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
            tkinter.messagebox.showinfo("Info", f"Save directory changed to: {self.save_directory}")

    def save(self):
        """Save the last 30 seconds of webcam frames to an MP4 file in a separate thread."""
        if not self.save_buffer:
            tkinter.messagebox.showinfo("Info", "No frames available to save.")
            return

        self.save_button.config(state="disabled")  # Disable the save button
        # Get FPS and resolution from the webcam
        fps = copy.deepcopy(self.capture.get(cv2.CAP_PROP_FPS) or 30)  # Default to 30 FPS if unavailable
        width = copy.deepcopy(int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)))
        height = copy.deepcopy(int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))

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

        # Inform the user
        self.root.after(0, lambda: self.save_button.config(state="normal"))  # Enable the save button
        self.root.after(0, lambda: tkinter.messagebox.showinfo("Info", f"Video saved as {filename}"))

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
