import RPi.GPIO as GPIO
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

def wait(seconds):
    """Attend pendant un nombre de secondes spécifié."""
    time.sleep(seconds)

if __name__ == "__main__":
    setup()
    try:
        turn_on_laser()
        print("Laser allumé pendant 5 secondes.")
        wait(5)
        turn_off_laser()
        print("Laser éteint.")
    finally:
        cleanup()
        print("GPIO nettoyé.")
