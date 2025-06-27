from picamera2 import Picamera2
import RPi.GPIO as GPIO
from datetime import datetime
import socket
import getpass
import sys
import os
# Ajoute le dossier racine du projet au path (celui qui contient Laser/)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from TfLunaI2C import TfLunaI2C
from laserService import setup, turn_on_laser, turn_off_laser, cleanup
import time


def Scan_with_CLL(duration = 10):
    # Récupérer le nom de l'utilisateur courant
    username = getpass.getuser()
    try:
        setup()
        # initialisation du capteur de distance
        tf = TfLunaI2C()
        tf.us = False
        print(tf)
        # Création du dossier de sauvegarde avec un timestamp
        timestamp = datetime.now().strftime("acquisition_%d_%m_%H_%M")
        save_dir = os.path.join(f"/home/{username}/images", timestamp)
        print(f"📂 Dossier de sauvegarde : {save_dir}")
        # fichier csv pour les donnees du capteur de distance
        csv_file = os.path.join(save_dir, "distance_data.csv")
        with open(csv_file, "a") as f:
                f.write(f"# Index,Distance (cm),Amplitude,Temperature (°C),Ticks,Error\n")
        print(f"📊 Fichier CSV pour les données de distance : {csv_file}")
        os.makedirs(save_dir, exist_ok=True)
        picam2 = Picamera2()
        config = picam2.create_still_configuration(
        main={"size": (2592, 1944)},  # 5MP
        controls={
        "ExposureTime": 5000,         # Légèrement plus long (12 ms) = plus de lumière sans trop de flou
        "AnalogueGain": 0.5,          # Gain minimum = bruit minimal (mais dépend de l'éclairage)
        "NoiseReductionMode": 1,      # High quality (tu es bon ici)
        "Sharpness": 1.7,             # Pousse un peu plus pour renforcer les bords
        "Contrast": 1.1,              # Un léger contraste renforce la perception de netteté
        "Saturation": 1.2,            # Améliore le réalisme de l’image (optionnel)
        "AwbMode": 1,                 # Auto white balance (correct sauf si tu veux du fixe)
        "AeExposureMode": "Short",    # Continue à forcer les expositions courtes
        "MeteringMode": 1             }
        )
        picam2.start()
        time.sleep(1)
        i = 0
        temps_Deb = time.time()
        turn_on_laser()
        print("🔴 Laser allumé !")

        while (time.time() - temps_Deb) < duration:
            filename = os.path.join(save_dir, f"img_{i:05d}.jpeg")
            picam2.options["quality"] = 100
            # Capture d'image avec la caméra
            picam2.capture_file(filename)
            # capture egalement les donnees du capteur de distance
            distance,amplitude,temperature,ticks,error = tf.read_data()
            with open(csv_file, "a") as f:
                f.write(f"{i:05d},{distance},{amplitude},{temperature},{ticks},{error}\n")
            print(f"📷 Image {i:05d} capturée : {filename} - Distance : {distance} cm")
            #compteur de temps
            temps_totale = time.time() - temps_Deb
            #compteur d'images
            i += 1
        print("✅ Durée de capture atteinte.")

    except KeyboardInterrupt:
        print("🛑 Arrêt par l'utilisateur.")

    finally:
        turn_off_laser()

        print("💡 Laser éteint.")

        if 'picam2' in locals():
            picam2.stop()
        cleanup()
        print("✅ GPIO nettoyé. Caméra arrêtée.")
