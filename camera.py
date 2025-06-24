from picamera2 import Picamera2
import os

picam2 = Picamera2()
# demarrer la camera avec 5MP
picam2.configure(picam2.create_video_configuration(main={"size":  (2592, 1944)
picam2.start()

os.makedirs("./images", exist_ok=True)

for i in range (50):
        filename = f"./images/img{i}.jpg"
        # Qualité JPEG
        picam2.options["quality"] = 90
        # Capture rapide
        picam2.capture_file(filename)
        print(f"Image capturée : {filename}")
