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
    
    """Authentifie un utilisateur avec Supabase"""
    data = request.get_json()
    try:
        response = supabase.auth.sign_in_with_password({
            "email": data['email'],
            "user_id": data['user_id'],
            "isDeviceConnected": data['isDeviceConnected'],
        })
        return jsonify({
            "status": "success",
            "user": response.user.dict(),
            "session": response.session.dict()
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 401
if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True)
    finally:
        print("Server stopped.")
        
        
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
