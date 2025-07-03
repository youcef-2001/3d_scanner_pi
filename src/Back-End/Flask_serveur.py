from threading import Thread
from flask import Flask, jsonify, Response, request
from cameraStreamer import CameraStreamer
from TfLunaI2C import TfLunaI2C
from laserService import setup, turn_on_laser, turn_off_laser, cleanup
import jwt
from testAcquisition import Scan_3D, Stop_Scan 
from supabase import create_client, Client
import logging



app = Flask(__name__)
# Configuration Supabase
SUPABASE_URL = 'https://vwnbfnvwzfidaxfxcdqp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ3bmJmbnZ3emZpZGF4ZnhjZHFwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAwODM5NjcsImV4cCI6MjA2NTY1OTk2N30.0-vxz8pyP_KYN0TwKdlFz4k0DQlp-o16rmyQOrcLKa0'
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
camera_streamer = CameraStreamer(logger=logger)



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

import subprocess

@app.route('/start-acquisition', methods=['POST'])
def start_acquisition():
        try :
            Thread(target=Scan_3D).start()
            return jsonify({
                "status": "success",
                "message": "Acquisition démarrée"
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
        

@app.route('/annuler-acquisition', methods=['POST'])
def annuler_acquisition():
    try:
        Thread(target=Stop_Scan).start()
        return jsonify({
            "status": "success",
            "message": "Acquisition annulée"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/camera/video_feed')
def video_feed():
    """Route pour le flux vidéo MJPEG"""
    try:
        return Response(
            camera_streamer.generate_mjpeg(),
            mimetype='multipart/x-mixed-replace; boundary=frame',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'Connection': 'keep-alive'
            }
        )
    except Exception as e:
        logger.error(f"Erreur dans video_feed: {e}")
        return jsonify({'error': 'Erreur du flux vidéo'}), 500

@app.route('/camera/status')
def camera_status():
    """Route pour vérifier le statut de la caméra"""
    return jsonify({
        'connected': camera_streamer.is_streaming,
        'resolution': '1280x1280',
        'format': 'MJPEG',
        'status': 'active' if camera_streamer.is_streaming else 'inactive'
    })

@app.route('/camera/start')
def start_camera():
    """Route pour démarrer la caméra"""
    if camera_streamer.initialize_camera():
        return jsonify({'success': True, 'message': 'Caméra démarrée'})
    else:
        return jsonify({'success': False, 'message': 'Erreur de démarrage'}), 500

@app.route('/camera/stop')
def stop_camera():
    """Route pour arrêter la caméra"""
    camera_streamer.stop_camera()
    return jsonify({'success': True, 'message': 'Caméra arrêtée'})




if __name__ == '__main__':
    try:
        logger.info("Démarrage du serveur Flask sur 192.168.13.1:5000")
        app.run(
            host='192.168.13.1', 
            port=5000, 
            threaded=True,
            debug=False  # Désactivé en production
        )
    except KeyboardInterrupt:
        logger.info("Arrêt du serveur demandé")
    except Exception as e:
        logger.error(f"Erreur lors du démarrage: {e}")
    finally:
        camera_streamer.stop_camera()
        logger.info("Serveur arrêté proprement")
