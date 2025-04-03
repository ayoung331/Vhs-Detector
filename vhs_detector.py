import subprocess
import time
import cv2
import numpy as np
import signal
from datetime import datetime

# Function to detect if playback has started
def has_playback_started(capture_device_name):
    ffmpeg_cmd = [
        'ffmpeg',
        '-f', 'dshow',
        '-i', f'video={capture_device_name}',
        '-t', '1',  # Capture for 1 second as a test
        '-f', 'rawvideo',
        '-pix_fmt', 'rgb24',
        '-'
    ]
    try:
        # Run FFmpeg command and capture output
        process = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = process.stdout
        if len(output) > 0:
            return True
    except Exception as e:
        print(f"Error: {e}")
    return False

# Function to check if the capture device is still connected
def is_device_connected(capture_device_name):
    ffmpeg_cmd = [
        'ffmpeg',
        '-f', 'dshow',
        '-list_devices', 'true',
        '-i', 'dummy'
    ]
    try:
        # Run FFmpeg command and capture output
        process = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = process.stderr
        return capture_device_name in output
    except Exception as e:
        print(f"Error: {e}")
    return False

# Function to check if a specific color is present in the frame
def is_color_present(frame, target_color_rgb, threshold=30):
    # Convert the frame to RGB color space
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Define the range for the target color
    lower_bound = np.array(target_color_rgb) - threshold
    upper_bound = np.array(target_color_rgb) + threshold
    # Create a mask for the target color
    mask = cv2.inRange(rgb_frame, lower_bound, upper_bound)
    # Check if the target color is present in the frame
    if cv2.countNonZero(mask) > 0:
        return True
    return False

# Capture device name
capture_device_name = "USB Video"
# Target color in RGB (when the stop button is pressed)
target_color_rgb = [37, 150, 190]

# Generate a unique filename using the current timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_filename = f'V:/Young, Alex/Movies/output_{timestamp}.mp4'

# Wait for playback to start
playback_started = False
while not playback_started:
    playback_started = has_playback_started(capture_device_name)
    if not playback_started:
        time.sleep(1)  # Wait for 1 second before checking again

print("Playback started, recording video...")

# Use FFmpeg to record the video feed
ffmpeg_cmd = [
    'ffmpeg',
    '-f', 'dshow',  # For Windows
    '-i', f'video={capture_device_name}',  # Change this to the capture device name
    '-c:v', 'libx264',  # Use H.264 codec for video
    '-preset', 'ultrafast',  # Encoding speed
    '-crf', '23',  # Quality (lower is better)
    '-pix_fmt', 'yuv420p',  # Pixel format
    output_filename  # Save the output to the specified directory with a unique filename
]

# Start the FFmpeg recording process
process = subprocess.Popen(ffmpeg_cmd)

# Open a video capture to monitor the video feed
cap = cv2.VideoCapture(f'video={capture_device_name}', cv2.CAP_DSHOW)

# Check if the device is still connected and stop recording if it is unplugged or the target color is detected
start_time = time.time()
recording_duration = 3600  # Maximum recording duration in seconds (1 hour)
while time.time() - start_time < recording_duration:
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture video feed")
        break
    if not is_device_connected(capture_device_name):
        print("Capture device disconnected, stopping recording...")
        process.send_signal(signal.SIGINT)  # Gracefully terminate the FFmpeg process
        break
    if is_color_present(frame, target_color_rgb):
        print("Target color detected, stopping recording...")
        process.send_signal(signal.SIGINT)  # Gracefully terminate the FFmpeg process
        break
    time.sleep(1)

# If the recording duration is reached, gracefully terminate the FFmpeg process
if process.poll() is None:
    process.send_signal(signal.SIGINT)

# Wait for the process to complete
process.wait()

# Release the video capture
cap.release()
cv2.destroyAllWindows()