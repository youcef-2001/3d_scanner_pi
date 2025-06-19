from picamera2 import Picamera2
import os
import RPi.GPIO as GPIO
import time

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
        picam2 = Picamera2()
        picam2.configure(picam2.create_video_configuration())
        picam2.start()
        time.sleep(2)

        os.makedirs("./images", exist_ok=True)
        i = 0
        while f"image{i}.jpg" in os.listdir("./images"):
            i += 1

        temps_Deb = time.time()
        turn_on_laser()
        print("🔴 Laser allumé !")

        while (time.time() - temps_Deb) < 120:
            filename = f"./images/image{i}.jpg"
            picam2.options["quality"] = 95
            picam2.capture_file(filename)
            print(f"📸 Image capturée : {filename}")
            temps_totale = time.time() - temps_Deb
            print(f"⏱ Temps écoulé : {temps_totale:.2f} secondes")
            i += 1
            time.sleep(0.001)

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
