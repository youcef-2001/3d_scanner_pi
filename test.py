from picamera2 import Picamera2
import os
import RPi.GPIO as GPIO
import time
from datetime import datetime

# Configuration des broches physiques (BOARD)
LASER_PIN = 37  # GPIO26

def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(LASER_PIN, GPIO.OUT)
    GPIO.output(LASER_PIN, GPIO.LOW)

def turn_on_laser():
    GPIO.output(LASER_PIN, GPIO.HIGH)

def turn_off_laser():
    GPIO.output(LASER_PIN, GPIO.LOW)

def cleanup():
    GPIO.cleanup()

if __name__ == "__main__":
    try:
        setup()
        timestamp = datetime.now().strftime("acquisition_%d_%m_%H_%M")
        save_dir = os.path.join("../images", timestamp)
        os.makedirs(save_dir, exist_ok=True)
        picam2 = Picamera2()
        config = picam2.create_still_configuration(
        main={"size": (2592, 1944)},  # 5MP
        controls={
        "ExposureTime": 5000,        # Légèrement plus long (12 ms) = plus de lumière sans trop de flou
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

        while (time.time() - temps_Deb) < 60:
            filename = os.path.join(save_dir, f"img_{i:04d}.jpeg")
            picam2.options["quality"] = 100
            picam2.capture_file(filename)
            print(f"📸 Image capturée : {filename}")
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
        cleanup()
        print("✅ GPIO nettoyé. Caméra arrêtée.")
