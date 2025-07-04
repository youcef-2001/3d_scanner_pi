import os
import time
import logging
import getpass
from datetime import datetime

from services.TfLunaI2C import TfLunaI2C
from services.laserService import setup, turn_on_laser, turn_off_laser, cleanup
from services.cameraManager import CameraManager
TIME= 30  # Durée de la numérisation en secondes
username = getpass.getuser()
isScanning = False
scan_number = 0# serial number to identify the scan

def Stop_Scan():
    global isScanning
    print("🛑 Demande d'arrêt reçue.")
    
    isScanning = False
    

def Scan_3D(logger=logging.getLogger(__name__)):
    global scan_number
    scan_number += 1
    global isScanning
    isScanning = True
    save_dir = ''
    csv_file = ''
    image_number = 0
    try:
        setup()
        tf = TfLunaI2C()
        tf.us = False
        signature = datetime.now().strftime(f"acquisition_%d_%m_%H_{scan_number:02d}")
        save_dir = os.path.join(f"/home/{username}/images", signature)
        csv_file = os.path.join(save_dir, "distance_data.csv")
        os.makedirs(save_dir, exist_ok=True)
        with open(csv_file, "a") as f:
            f.write(f"# Index,Distance (cm),Amplitude,Temperature (°C),Ticks,Error\n")

        picammanager = CameraManager.get_instance(logger=logger)
        config = {"main":{"size": (1280, 1280)}}
        picammanager.start_camera(config)
        time.sleep(0.5)
        
        temps_Deb = time.time()
        turn_on_laser()
        logger.info("🔴 Laser allumé !")
        tfluna_acqu = []

        while isScanning and time.time() - temps_Deb < TIME:
            filename = os.path.join(save_dir, f"img_{image_number:05d}.jpeg")
            picammanager.capture_file(filename)
            distance, amplitude, temperature, ticks, error = tf.read_data()
            tfluna_acqu.append((distance, amplitude, temperature, ticks, error))
            logger.info(f"📷 Image {i:05d} capturée - Distance : {distance} cm")
            logger.info(f"⏱ Temps écoulé : {time.time() - temps_Deb:.2f} s")
            image_number += 1

        logger.info("✅ Fin de capture.")

        with open(csv_file, "a") as f:
            for j, (distance, amplitude, temperature, ticks, error) in enumerate(tfluna_acqu):
                f.write(f"{j:05d},{distance},{amplitude},{temperature},{ticks},{error}\n")

    except KeyboardInterrupt:
        logger.error("🛑 Arrêt par l'utilisateur.")

    finally:
        turn_off_laser()
        logger.info("💡 Laser éteint.")
        picammanager.stop_camera()
        logger.info("📷 Caméra arrêtée.")
        cleanup()
        logger.info("✅ Nettoyage terminé.")
        isScanning = False
        logger.info(f"📁 Images sauvegardées dans : {save_dir}")
        return save_dir,csv_file,image_number/TIME  # Retourne le répertoire de sauvegarde, le fichier CSV et le nombre d'images capturées par seconde FPS

if __name__ == "__main__":
    print("🔍 Démarrage de la numérisation 3D...")
    Scan_3D()
    print("✅ Numérisation terminée.")
