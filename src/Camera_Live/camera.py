from picamera2 import Picamera2
import os

picam2 = Picamera2()
# demarrer la camera avec 5MP
picam2.configure(picam2.create_video_configuration(main={"size":  (1080, 720)}))  # 1080p
picam2.start()

#lancer le flux vidéo
picam2.start_preview()
# se mettre en tcp et http pour le streaming sur 0.0.0.0:8080
picam2.start_recording("tcp://0.0.0.0:8080")
#A tester le streaming

