from flask import Flask, jsonify, Response, send_file, request
#import RPi.GPIO as GPIO
#from picamera2 import Picamera2
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from TfLunaI2C import TfLunaI2C
from laserService import setup, turn_on_laser, turn_off_laser, cleanup
import time
import io
import jwt
import subprocess

#from datetime import datetime
from supabase import create_client, Client

#import cv2

app = Flask(__name__)

# Configuration Supabase
SUPABASE_URL = 'https://vwnbfnvwzfidaxfxcdqp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ3bmJmbnZ3emZpZGF4ZnhjZHFwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAwODM5NjcsImV4cCI6MjA2NTY1OTk2N30.0-vxz8pyP_KYN0TwKdlFz4k0DQlp-o16rmyQOrcLKa0'
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


#picam2 = Picamera2()
#picam2.configure(picam2.create_video_configuration(main={"size": (1080, 720)}))
#picam2.start()



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

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True)
    finally:
        print("Server stopped.")

#start_acquisition

@app.route('/start-acquisition', methods=['POST'])
def start_acquisition():
    try:
        acquisition_path = os.path.join(os.path.dirname(__file__), 'testAcquisition.py')
        result = subprocess.run(['python3', acquisition_path], capture_output=True, text=True)
        
        if result.returncode != 0:
            return jsonify({
                "status": "error",
                "message": result.stderr
            }), 500

        return jsonify({
            "status": "success",
            "message": "Acquisition lancée avec succès",
            "stdout": result.stdout
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500