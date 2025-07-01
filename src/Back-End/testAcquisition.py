from picamera2 import Picamera2
import RPi.GPIO as GPIO
from picamera2.utils import Transform
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

# Récupérer le nom de l'utilisateur courant
username = getpass.getuser()


if __name__ == "__main__":
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
        print(f"📊 Fichier CSV pour les données de distance : {csv_file}")
        os.makedirs(save_dir, exist_ok=True)
        with open(csv_file, "a") as f:
                f.write(f"# Index,Distance (cm),Amplitude,Temperature (°C),Ticks,Error\n")
        picam2 = Picamera2()
        mytransform = Transform(rotation=180)
        #5mp = (2592, 1944) ratio 4/3
        #4mp = (1440, 1080) ratio 
        #3mp = (1296, 972)
        #2mp = (1920, 1080)
        #1mp = (1280, 720)
        #ratio = 6/5
        #4 mp  with ratio 6/5 = 
        config = picam2.create_still_configuration(main={"size": (1280, 1280)})
        picam2.set_transform(mytransform)
        picam2.start()
        time.sleep(1)
        i = 0
        temps_Deb = time.time()
        turn_on_laser()
        print("🔴 Laser allumé !")
        tfluna_acqu = []
        while time.time()-temps_Deb < 20:  # Durée de capture de 20 secondes
            filename = os.path.join(save_dir, f"img_{i:05d}.jpeg")
            # Capture d'image avec la caméra
            picam2.capture_file(filename)
            # capture egalement les donnees du capteur de distance
            distance,amplitude,temperature,ticks,error = tf.read_data()
            tfluna_acqu.append((distance,amplitude,temperature,ticks,error))
            print(f"📷 Image {i:05d} capturée : {filename} - Distance : {distance} cm")
            temps_totale = time.time() - temps_Deb
            print(f"⏱ Temps écoulé : {temps_totale:.2f} secondes")
            i += 1
        print("✅ Durée de capture atteinte.")

        with open(csv_file, "a") as f:
            for j, (distance, amplitude, temperature, ticks, error) in enumerate(tfluna_acqu):
                # Écriture des données dans le fichier CSV
                f.write(f"{i:05d},{distance},{amplitude},{temperature},{ticks},{error}\n")
    except KeyboardInterrupt:
        print("🛑 Arrêt par l'utilisateur.")

    finally:
        turn_off_laser()

        print("💡 Laser éteint.")

        if 'picam2' in locals():
            picam2.stop()

        cleanup()
        print("✅ GPIO nettoyé. Caméra arrêtée.")
