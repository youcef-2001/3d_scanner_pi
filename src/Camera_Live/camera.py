from picamera2 import Picamera2
import os


#Live camera of 2K quality
# flux can be accessible with ffplay
def live_camera():
    picam2 = Picamera2()
    config = picam2.create_video_configuration(
        main={"size": (1920, 1080)},  # 2K resolution
        controls={
            "FrameRate": 30,  # 30 FPS for smooth video
            "ExposureTime": 5000,  # Adjust exposure time as needed
            "AnalogueGain": 1.0,  # Set gain to a reasonable level
            "NoiseReductionMode": 1,  # High quality noise reduction
        }
    )
    picam2.configure(config)
    picam2.start()
    # Set the camera to stream mode
    picam2.options["streaming"] = True
    picam2.start_preview()
    print("📷 Live camera started. Press Ctrl+C to stop.")
    
    try:
        while True:
            pass  # Keep the script running to maintain the live feed
    except KeyboardInterrupt:
        print("Stopping live camera...")
        picam2.stop()