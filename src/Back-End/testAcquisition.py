from cameraManager import CameraManager
from picamera2.utils import Transform
import logging
from datetime import datetime
import socket
import getpass
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from TfLunaI2C import TfLunaI2C
from laserService import setup, turn_on_laser, turn_off_laser, cleanup
import time

username = getpass.getuser()
isScanning = False

def Stop_Scan():
    global isScanning
    print("🛑 Demande d'arrêt reçue.")
    
    isScanning = False
    

def Scan_3D():
    global isScanning
    isScanning = True
    try:
        setup()
        tf = TfLunaI2C()
        tf.us = False
        timestamp = datetime.now().strftime("acquisition_%d_%m_%H_%M")
        save_dir = os.path.join(f"/home/{username}/images", timestamp)
        csv_file = os.path.join(save_dir, "distance_data.csv")
        os.makedirs(save_dir, exist_ok=True)
        with open(csv_file, "a") as f:
            f.write(f"# Index,Distance (cm),Amplitude,Temperature (°C),Ticks,Error\n")

        picammanager = CameraManager.get_instance( logging.getLogger(__name__))
        mytransform = Transform(rotation=180)
        config = {"main":{"size": (1280, 1280)}, "transform":mytransform}
        picammanager.start_camera(config)
        time.sleep(0.5)
        i = 0
        temps_Deb = time.time()
        turn_on_laser()
        print("🔴 Laser allumé !")
        tfluna_acqu = []

        while isScanning and time.time() - temps_Deb < 30:
            filename = os.path.join(save_dir, f"img_{i:05d}.jpeg")
            picammanager.capture_file(filename)
            distance, amplitude, temperature, ticks, error = tf.read_data()
            tfluna_acqu.append((distance, amplitude, temperature, ticks, error))
            print(f"📷 Image {i:05d} capturée - Distance : {distance} cm")
            print(f"⏱ Temps écoulé : {time.time() - temps_Deb:.2f} s")
            i += 1

        print("✅ Fin de capture.")

        with open(csv_file, "a") as f:
            for j, (distance, amplitude, temperature, ticks, error) in enumerate(tfluna_acqu):
                f.write(f"{j:05d},{distance},{amplitude},{temperature},{ticks},{error}\n")

    except KeyboardInterrupt:
        print("🛑 Arrêt par l'utilisateur.")

    finally:
        turn_off_laser()
        print("💡 Laser éteint.")
        picammanager.stop_camera()
        print("📷 Caméra arrêtée.")
        cleanup()
        print("✅ Nettoyage terminé.")

if __name__ == "__main__":
    print("🔍 Démarrage de la numérisation 3D...")
    Scan_3D()
    print("✅ Numérisation terminée.")
