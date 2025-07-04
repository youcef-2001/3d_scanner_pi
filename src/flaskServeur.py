import os
import sys
import time
import logging

from threading import Thread

import cv2
import jwt
from dotenv import load_dotenv
from flask import Flask, jsonify, Response, request
from supabase import create_client, Client

from src.services.cameraManager import CameraManager
from src.services.TfLunaI2C import TfLunaI2C
from src.services.laserService import setup, turn_on_laser, turn_off_laser, cleanup
from src.services.acquisition import Stop_Scan
from src.run_full_pipeline import workflow as Scan_3D
# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# === URL ET CLÉ DE SUPABASE ===
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')


app = Flask(__name__)
# Configuration Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
camera_manager = CameraManager.get_instance(logger)
is_acquisition_running= False
stream_status = False  # Indique si le flux vidéo est actif

#=======================
#Live streaming
#========================
def generate_mjpeg(camera_manager: CameraManager):
        global stream_status
        """Génère le flux MJPEG optimisé"""
        if not camera_manager.isCameraRunning:
            if not camera_manager.picam2:
                return
        cv2.setNumThreads(2)  # Désactive les threads OpenCV pour éviter la surcharge CPU
        try:
            # Initialisation des variables de performance
            frame_count = 0
            last_frame_time = time.time()
            logger.info("Démarrage du flux MJPEG")
            # Boucle de capture d'images
            while stream_status:
                    if not camera_manager.isCameraRunning:
                        logger.warning("La caméra n'est pas en cours d'exécution, arrêt du flux.")
                        stream_status = False
                        
                        break
                    # Capture de l'image
                    frame = camera_manager.capture_array()
                    
                    # Conversion RGB vers BGR pour OpenCV
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    # Rotation de 90 degrés (sens horaire)
                    frame_bgr = cv2.rotate(frame_bgr, cv2.ROTATE_180)
                    # Encodage JPEG avec qualité optimisée
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]  # Qualité 80 ne pas charger le CPU
                    ret, jpeg = cv2.imencode('.jpg', frame_bgr, encode_param)
                    
                    if not ret:
                        continue
                    
                    # Statistiques de performance
                    frame_count += 1
                    current_time = time.time()
                    if current_time - last_frame_time > 5:  # Log toutes les 5 secondes
                        fps = frame_count / (current_time - last_frame_time)
                        logger.info(f"FPS: {fps:.2f}")
                        frame_count = 0
                        last_frame_time = current_time
                    
                    # Yield du frame MJPEG
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(jpeg)).encode() + b'\r\n\r\n' + 
                           jpeg.tobytes() + b'\r\n')
                    
                    # Petit délai pour éviter la surcharge CPU
                    time.sleep(0.020)  # ~ 50 FPS Max 
                    
        except GeneratorExit:
            logger.info("Client déconnecté du flux vidéo")
        except Exception as e:
            logger.error(f"Erreur dans generate_mjpeg: {e}")
        finally:
           logger.info("Arrêt du flux MJPEG  " )
           stream_status = False  # Met à jour l'état du flux vidéo
           cv2.setNumThreads(0)  # Réinitialise les threads OpenCV




# ======================
# Routes d'authentification
# ======================


@app.route('/')
def index():
    return '''
    <html>
    <head><title>Flux Vidéo</title></head>
    <body>
        <h1>Flux MJPEG</h1>
        <img src="/camera/video_feed" />
    </body>
    </html>
    '''
@app.route('/appairer', methods=['POST'])
def appairer():
    try:
        auth_header = request.headers.get('Authorization', None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token JWT manquant"}), 401

        token = auth_header.split(" ")[1]

        # Décodage du JWT sans vérification de signature (juste pour extraction)
        payload = jwt.decode(token, options={"verify_signature": False})
        user_email = payload.get("email")
        user_id = payload.get("sub")

        print(f"[Appairage] Utilisateur : {user_email}, ID: {user_id}")

        return jsonify({
            "status": "success",
            "message": "Appairage réussi",
            "user_id": user_id,
            "email": user_email,
            "laser": "off"  # si tu veux renvoyer un état de laser par défaut
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400
        
   #route deconnecter     
@app.route('/deconnecter', methods=['POST'])
def deconnecter():
    try:
        auth_header = request.headers.get('Authorization', None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token JWT manquant"}), 401

        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, options={"verify_signature": False})
        user_email = payload.get("email")
        user_id = payload.get("sub")

        print(f"[Déconnexion] Utilisateur : {user_email}, ID: {user_id}")

        return jsonify({
            "status": "success",
            "message": "Déconnexion réussie"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Allumer le laser
@app.route('/laser/on', methods=['POST'])
def laser_on():
    try:
        setup()
        turn_on_laser()
        return jsonify({"status": "success", "message": "Laser allumé"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Éteindre le laser
@app.route('/laser/off', methods=['POST'])
def laser_off():
    try:
        turn_off_laser()
        cleanup()
        return jsonify({"status": "success", "message": "Laser éteint et GPIO nettoyé"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Lire une mesure du capteur TfLuna
@app.route('/tfluna/read', methods=['GET'])
def read_tfluna():
    try:
        tf = TfLunaI2C()
        tf.set_mode_continuous()
        distance, amplitude, temperature, ticks, error = tf.read_data()
        return jsonify({
            "distance_cm": distance,
            "amplitude": amplitude,
            "temperature_c": temperature,
            "ticks": ticks,
            "error": error
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

#start_acquisition

def wrapped_scan():
    global is_acquisition_running 
    try:
        Scan_3D()
    finally:
        is_acquisition_running = False

@app.route('/start-acquisition', methods=['POST'])
def start_acquisition():
    global is_acquisition_running
    if is_acquisition_running:
        return jsonify({"status": "error", "message": "Une acquisition est déjà en cours"}), 403
    try:
        is_acquisition_running = True
        Thread(target=wrapped_scan).start()
        return jsonify({"status": "success", "message": "Acquisition démarrée"}), 200
    except Exception as e:
        is_acquisition_running = False
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/annuler-acquisition', methods=['POST'])
def annuler_acquisition():
    try:
        Stop_Scan()
        return jsonify({"status": "success", "message": "Acquisition annulée"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Get ou POst
@app.route('/camera/video_feed')
def video_feed():
    global stream_status
    camera = CameraManager.get_instance(logger)
    try:
        if not camera.isCameraRunning:
            config = 'streaming'  # Configuration par défaut pour la caméra
            camera.start_camera(config)
            logger.info("Caméra démarrée pour le flux vidéo")
        stream_status = True  # Indique que le flux est actif
        return Response(
           generate_mjpeg(camera_manager=camera),
            mimetype='multipart/x-mixed-replace; boundary=frame',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'Connection': 'keep-alive'
            }
        ), 200
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du flux vidéo: {e}")
        return "Erreur", 500
@app.route('/camera/status')
def camera_status():
    
    """Route pour vérifier le statut de la caméra, la demmarer si elle n'est pas en cours d'utilisation, et renvoyer les détails de la caméra"""
    
    if not camera_manager.isCameraRunning:
        try:
            config = 'streaming'  # Configuration par défaut pour la caméra
            camera_manager.start_camera(config)
            logger.info("Caméra démarrée pour le statut")
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de la caméra: {e}")
           
    logger.info(f"camera_streamer.is_streaming: {camera_manager.isCameraRunning}")
    resolution = 'N/A'
    if camera_manager.picam2:
        w, h = camera_manager.picam2.camera_config["main"]["size"]
        resolution = f'{w}X{h}'
    return jsonify({
        'connected': camera_manager.isCameraRunning,
        'resolution': resolution,
        'format': 'MJPEG',
        'status': 'active' if stream_status else 'inactive'
    }), 200


if __name__ == '__main__':
    try:
        logger.info("Démarrage du serveur Flask sur 192.168.13.1:80")
        app.run(
            host='192.168.13.1', 
            port=80, 
            threaded=True,
            debug=True  # Désactivé en production
        )
    except KeyboardInterrupt:
        logger.info("Arrêt du serveur demandé")
    except Exception as e:
        logger.error(f"Erreur lors du démarrage: {e}")
    finally:
        camera_manager.stop_camera()
        cleanup()  # Nettoyage des GPIO
        logger.info("Serveur arrêté proprement")
