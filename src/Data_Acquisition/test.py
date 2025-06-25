from picamera2 import Picamera2
import os
import RPi.GPIO as GPIO
from datetime import datetime
import socket
import getpass
#from TfLunaI2C import TfLunaI2C
import time

# Configuration
LASER_PIN = 37  # Broche physique (BOARD numbering) => GPIO26

def setup():
    """Initialise les paramètres GPIO."""
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(LASER_PIN, GPIO.OUT)
    GPIO.output(LASER_PIN, GPIO.LOW)  # Éteint le laser par défaut

def turn_on_laser():
    """Allume le laser."""
    GPIO.output(LASER_PIN, GPIO.HIGH)

def turn_off_laser():
    """Éteint le laser."""
    GPIO.output(LASER_PIN, GPIO.LOW)

def cleanup():
    """Nettoie les paramètres GPIO."""
    GPIO.cleanup()
# Récupérer le nom d'hôte (hostname)
#hostname = socket.gethostname()
#print(f"Nom d'hôte de la machine : {hostname}")

# Récupérer le nom de l'utilisateur courant
username = getpass.getuser()


if __name__ == "__main__":
    try:
        setup()
        # Basic Usage:
        #tf = TfLunaI2C()
        #tf.us = False
        #print(tf)
        
        #data = tf.read_data()
        #tf.print_data()
        timestamp = datetime.now().strftime("acquisition_%d_%m_%H_%M")
        save_dir = os.path.join(f"/home/{username}/images", timestamp)
        print(f"📂 Dossier de sauvegarde : {save_dir}")
        # fichier csv pour les donnees du capteur de distance
        #csv_file = os.path.join(save_dir, "distance_data.csv")
        #print(f"📊 Fichier CSV pour les données de distance : {csv_file}")
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

        while (time.time() - temps_Deb) < 10:
            filename = os.path.join(save_dir, f"img_{i:05d}.jpeg")
            picam2.options["quality"] = 99
            # Capture d'image avec la caméra
            picam2.capture_file(filename)
            # capture egalement les donnees du capteur de distance

            #distance,amplitude,temperature,ticks,error = tf.read_data()
            #with open(csv_file, "a") as f:
             #   f.write(f"{i:05d},{distance},{amplitude},{temperature},{ticks},{error}\n")
            #print(f"📷 Image {i:05d} capturée : {filename} - Distance : {distance} cm")
            temps_totale = time.time() - temps_Deb
            print(f"⏱ Temps écoulé : {temps_totale:.2f} secondes")
            i += 1
        print("✅ Durée de capture atteinte.")

    except KeyboardInterrupt:
        print("🛑 Arrêt par l'utilisateur.")

    finally:
        turn_off_laser()

        print("💡 Laser éteint.")

        if 'picam2' in locals():
            picam2.stop()

        #if 'tf' in locals():
        #    tf.cleanup()
        cleanup()
        print("✅ GPIO nettoyé. Caméra arrêtée.")
