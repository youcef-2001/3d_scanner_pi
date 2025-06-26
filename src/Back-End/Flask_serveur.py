from flask import Flask, jsonify, Response, send_file, request
import RPi.GPIO as GPIO
#from picamera2 import Picamera2
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from TfLunaI2C import TfLunaI2C
import time
import io

from datetime import datetime
from supabase import create_client, Client
import cv2

app = Flask(__name__)

# Configuration Supabase
SUPABASE_URL = 'https://vwnbfnvwzfidaxfxcdqp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ3bmJmbnZ3emZpZGF4ZnhjZHFwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAwODM5NjcsImV4cCI6MjA2NTY1OTk2N30.0-vxz8pyP_KYN0TwKdlFz4k0DQlp-o16rmyQOrcLKa0'
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuration initiale
LASER_PIN = 37
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LASER_PIN, GPIO.OUT)
GPIO.output(LASER_PIN, GPIO.LOW)

# Initialisation des périphériques
#picam2 = Picamera2()
#picam2.configure(picam2.create_video_configuration(main={"size": (1080, 720)}))
#picam2.start()

tf_luna = TfLunaI2C()
tf_luna.us = False

# ======================
# Routes d'authentification
# ======================

@app.route('/auth/login', methods=['POST'])
def login():
    """Authentifie un utilisateur avec Supabase"""
    data = request.get_json()
    try:
        response = supabase.auth.sign_in_with_password({
            "email": data['email'],
            "password": data['password']
        })
        return jsonify({
            "status": "success",
            "user": response.user.dict(),
            "session": response.session.dict()
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 401

@app.route('/auth/signup', methods=['POST'])
def signup():
    """Crée un nouveau compte utilisateur"""
    data = request.get_json()
    try:
        response = supabase.auth.sign_up({
            "email": data['email'],
            "password": data['password']
        })
        return jsonify({
            "status": "success",
            "user": response.user.dict()
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/auth/logout', methods=['POST'])
def logout():
    """Déconnecte l'utilisateur"""
    try:
        supabase.auth.sign_out()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ======================
# Routes Laser
# ======================

@app.route('/laser/status', methods=['GET'])
def get_laser_status():
    status = GPIO.input(LASER_PIN)
    return jsonify({"status": "on" if status else "off"})

@app.route('/laser/on', methods=['POST'])
def turn_on_laser():
    GPIO.output(LASER_PIN, GPIO.HIGH)
    return jsonify({"status": "on"})

@app.route('/laser/off', methods=['POST'])
def turn_off_laser():
    GPIO.output(LASER_PIN, GPIO.LOW)
    return jsonify({"status": "off"})

@app.route('/laser/setup', methods=['GET'])
def laser_setup():
    return jsonify({
        "pin": LASER_PIN,
        "mode": "BOARD",
        "default_state": "off"
    })

# ======================
# Routes Camera
# ======================

def generate_frames():
    #while True:
     #   frame = picam2.capture_array("main")
      #  ret, buffer = cv2.imencode('.jpg', frame)
       # frame = buffer.tobytes()
       # yield (b'--frame\r\n'
       #        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    continue
@app.route('/camera/video_feed')
def video_feed():
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera/capture', methods=['GET'])
def capture_photo():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"photo_{timestamp}.jpg"
    
    #picam2.options["quality"] = 99
    image_data = io.BytesIO()
    #picam2.capture_file(image_data, format='jpeg')
    image_data.seek(0)
    
    return send_file(image_data, mimetype='image/jpeg', 
                   as_attachment=True, download_name=filename)

# ======================
# Routes LIDAR
# ======================

@app.route('/lidar/distance', methods=['GET'])
def get_distance():
    distance, amplitude, _, _, _ = tf_luna.read_data()
    return jsonify({
        "distance": distance,
        "amplitude": amplitude,
        "unit": "cm"
    })

@app.route('/lidar/temperature', methods=['GET'])
def get_temperature():
    _, _, temp, _, _ = tf_luna.read_data()
    temp_c = temp * 0.01
    return jsonify({
        "temperature": temp_c,
        "unit": "Celsius"
    })

@app.route('/lidar/status', methods=['GET'])
def get_lidar_status():
    return jsonify({
        "enabled": tf_luna.read_enabled() == tf_luna.TRUE,
        "mode": "continuous" if tf_luna.read_mode() == tf_luna.MODE_CONTINUOUS else "trigger",
        "fps": tf_luna.read_frame_rate()
    })

# ======================
# Route Scan (protégée)
# ======================

@app.route('/scan/start', methods=['POST'])
def start_scan():
    # Vérification de l'authentification
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Token manquant"}), 401
    
    try:
        # Vérifie le token JWT
        user = supabase.auth.get_user(auth_header.split(' ')[1])
        
        # Configuration du scan
        username = os.getlogin()
        timestamp = datetime.now().strftime("acquisition_%d_%m_%H_%M")
        save_dir = os.path.join(f"/home/{username}/images", timestamp)
        os.makedirs(save_dir, exist_ok=True)
        
        # Fichier CSV pour les données
        csv_file = os.path.join(save_dir, "distance_data.csv")
        # Démarrage du scan
        GPIO.output(LASER_PIN, GPIO.HIGH)
        start_time = time.time()
        i = 0
        
        while (time.time() - start_time) < 60:  # 60 secondes
            filename = os.path.join(save_dir, f"img_{i:05d}.jpeg")
            #picam2.options["quality"] = 99
            #picam2.capture_file(filename)
            
            distance, amplitude, temp, ticks, error = tf_luna.read_data()
            with open(csv_file, "a") as f:
                f.write(f"{i:05d},{distance},{amplitude},{temp},{ticks},{error}\n")
            
            i += 1
            time.sleep(0.1)
        
        GPIO.output(LASER_PIN, GPIO.LOW)
        
        # Enregistrement dans Supabase
        supabase.table('scans').insert({
            "user_id": user.user.id,
            "scan_date": datetime.now().isoformat(),
            "image_count": i,
            "save_directory": save_dir
        }).execute()
        
        return jsonify({
            "status": "success",
            "directory": save_dir,
            "images_captured": i
        })
    
    except Exception as e:
        GPIO.output(LASER_PIN, GPIO.LOW)
        return jsonify({"status": "error", "message": str(e)}), 500

# ======================
# Nettoyage
# ======================

@app.teardown_appcontext
def cleanup(exception=None):
    GPIO.output(LASER_PIN, GPIO.LOW)
    #picam2.stop()
    GPIO.cleanup()

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True)
    finally:
        cleanup()
