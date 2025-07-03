from threading import Thread
from flask import Flask, jsonify, Response, request
from cameraManager import CameraManager
from TfLunaI2C import TfLunaI2C
from laserService import setup, turn_on_laser, turn_off_laser, cleanup
import jwt
from testAcquisition import Scan_3D, Stop_Scan 
from supabase import create_client, Client
import logging
import cv2
import time



app = Flask(__name__)
# Configuration Supabase
SUPABASE_URL = 'https://vwnbfnvwzfidaxfxcdqp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ3bmJmbnZ3emZpZGF4ZnhjZHFwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAwODM5NjcsImV4cCI6MjA2NTY1OTk2N30.0-vxz8pyP_KYN0TwKdlFz4k0DQlp-o16rmyQOrcLKa0'
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
                    
                    # Encodage JPEG avec qualité optimisée
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]  # Qualité 80 ne pas charger le CPU
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
                    time.sleep(0.033)  # ~30 FPS max
                    
        except GeneratorExit:
            logger.info("Client déconnecté du flux vidéo")
        except Exception as e:
            logger.error(f"Erreur dans generate_mjpeg: {e}")
        finally:
           camera_manager.stop_camera()
           stream_status = False  # Met à jour l'état du flux vidéo
           cv2.setNumThreads(0)  # Réinitialise les threads OpenCV




# ======================
# Routes d'authentification
# ======================

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
        })
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
        return jsonify({"status": "error", "message": "Une acquisition est déjà en cours"}), 400
    try:
        is_acquisition_running = True
        Thread(target=wrapped_scan).start()
        return jsonify({"status": "success", "message": "Acquisition démarrée"})
    except Exception as e:
        is_acquisition_running = False
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/annuler-acquisition', methods=['POST'])
def annuler_acquisition():
    try:
        Stop_Scan()
        return jsonify({"status": "success", "message": "Acquisition annulée"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Get ou POst
@app.route('/camera/video_feed')
def video_feed():
    camera = CameraManager.get_instance(logger)
    try:
        if not camera.isCameraRunning:
            config = {"main": {"size": (1280, 1280)},"format": "RGB888"}
            camera.start_camera(config)
            logger.info("Caméra démarrée pour le flux vidéo")
        stream_status = True  # Indique que le flux est actif
        return Response( 
                        generate_mjpeg(camera,stream_status) # Capture une image pour le flux
            ,
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du flux vidéo: {e}")
        return "Erreur", 500
@app.route('/camera/status')
def camera_status():
    
    """Route pour vérifier le statut de la caméra, la demmarer si elle n'est pas en cours d'utilisation, et renvoyer les détails de la caméra"""
    
    
    logger.info(f"camera_streamer.is_streaming: {camera_manager.isCameraRunning}")
    return jsonify({
        'connected': camera_manager.isCameraRunning,
        'resolution': '1280x1280',
        'format': 'MJPEG',
        'status': 'active' if stream_status else 'inactive'
    })


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
