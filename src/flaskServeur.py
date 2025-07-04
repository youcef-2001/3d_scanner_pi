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

from reconstruction.utils import apply_filter , HSV_FILTRE, RGB_FILTRE
from services.cameraManager import CameraManager
from services.TfLunaI2C import TfLunaI2C
from services.laserService import setup, turn_on_laser, turn_off_laser, cleanup
from services.acquisition import Stop_Scan
from run_full_pipeline import workflow 
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
stream_status = False  # Indique si le flux vidéo est actif

scan_status = {
    "status": False,  # Indique si l'acquisition est en cours
    "step": 0,  # Étape actuelle de l'acquisition
    "ackDone": False  # Indique si l'acquision est terminée
}
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
                    res=apply_filter(frame, 'HSV', *HSV_FILTRE)
                    fres=apply_filter(res, 'RGB', *RGB_FILTRE)
                    # Conversion RGB vers BGR pour OpenCV
                    frame_bgr = cv2.cvtColor(fres, cv2.COLOR_RGB2BGR)
                    
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

def wrapped_scan(uid,):
    """Fonction d'acquisition 3D en arrière-plan"""
    scan_status["status"] = True  # Acquisition en cours
    scan_status["step"] = 0  # Étape d'acquisition initiale
    scan_status["ackDone"] = False  # Acquisition non terminée
    try:
        workflow(uid,scan_status=scan_status)  # Démarrer l'acquisition 3D
        scan_status["ackDone"] = True  # Acquisition terminée
    finally:
        scan_status["status"] = False  # Acquisition terminée
        scan_status["step"] = 0  # Réinitialiser l'étape d'acquisition
        logger.info("Acquisition 3D terminée")
# route post pour demarrer une aquisition qui necessite de recevoir un parametre user_id
@app.route('/start-acquisition/', methods=['POST'])
def start_acquisition():
    """Démarre une acquisition 3D en arrière-plan"""
    if scan_status["status"]:
        return jsonify({"status": "error", "message": "Une acquisition est déjà en cours"}), 403
    try:
        
        auth_header = request.headers.get('Authorization', None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token JWT manquant"}), 401
        token = auth_header.split(" ")[1]
        # Décodage du JWT sans vérification de signature (juste pour extraction)
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub")
        # get distance from body request
        data = request.get_json()
        distance = data.get("distance")
        if not user_id:
            return jsonify({"status": "error", "message": "ID utilisateur manquant"}), 400
        
        Thread(target=wrapped_scan, args=(user_id,), daemon=True).start()
        return jsonify({"status": "success", "message": "Acquisition démarrée"}), 200
    
    except Exception as e:
        scan_status["status"] = False  # Réinitialiser l'état d'acquisition en cas d'erreur
        scan_status["step"] = 0  # Réinitialiser l'étape d'ac
        scan_status["ackDone"] = False  # Réinitialiser l'état d'acquision
        logger.error(f"Erreur lors du démarrage de l'acquisition: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
# route pour vérifier si une acquisition est en cours
@app.route('/acquisition-status', methods=['GET'])
def acquisition_status():
    """Vérifie si une acquisition est en cours"""
    value = False  # Valeur par défaut pour ackDone
    if scan_status["ackDone"]:
        value = True#Envoie acknowledge pour le client une seule fois 
        scan_status["ackDone"] = False  # Réinitialiser l'état d'acquision
    return jsonify({"status": scan_status["status"],
                    "step" : scan_status["step"],
                    "ackDone": value,
                    }), 200
   
    
    
# Route pour annuler l'acquisition en cours

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

@app.route('/camera/rgb-filter', methods=['POST'])
def update_rgb_filter():
    data = request.get_json()
    
    # Récupérer les paramètres
    red = data.get('red', 1.0)
    green = data.get('green', 1.0)
    blue = data.get('blue', 1.0)
    brightness = data.get('brightness', 1.0)
    contrast = data.get('contrast', 1.0)
    saturation = data.get('saturation', 1.0)
    
    # Appliquer les filtres à votre flux caméra
    # Exemple avec OpenCV :
    # frame = cv2.convertScaleAbs(frame, alpha=contrast, beta=brightness)
    # frame[:,:,0] = np.clip(frame[:,:,0] * blue, 0, 255)   # Canal bleu
    # frame[:,:,1] = np.clip(frame[:,:,1] * green, 0, 255)  # Canal vert
    # frame[:,:,2] = np.clip(frame[:,:,2] * red, 0, 255)    # Canal rouge
    
    return jsonify({"status": "success", "message": "Filtres RGB appliqués"})

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
