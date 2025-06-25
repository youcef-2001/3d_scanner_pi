from flask import Flask, jsonify, Response, send_file
import RPi.GPIO as GPIO
from picamera2 import Picamera2
from TfLunaI2C import TfLunaI2C
import time
import io
import os
from datetime import datetime

app = Flask(__name__)

# Configuration initiale
LASER_PIN = 37
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LASER_PIN, GPIO.OUT)
GPIO.output(LASER_PIN, GPIO.LOW)

# Initialisation des périphériques
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (1080, 720)}))
picam2.start()

tf_luna = TfLunaI2C()
tf_luna.us = False

# Routes Laser
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

# Routes Camera
def generate_frames():
    while True:
        frame = picam2.capture_array("main")
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/camera/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera/capture', methods=['GET'])
def capture_photo():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"photo_{timestamp}.jpg"
    
    # Capture avec haute qualité
    picam2.options["quality"] = 99
    image_data = io.BytesIO()
    picam2.capture_file(image_data, format='jpeg')
    image_data.seek(0)
    
    return send_file(image_data, mimetype='image/jpeg', as_attachment=True, download_name=filename)

# Routes TF-Luna (LIDAR)
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

# Route pour démarrer un scan (basé sur test.py)
@app.route('/scan/start', methods=['POST'])
def start_scan():
    try:
        # Création du répertoire de sauvegarde
        username = os.getlogin()
        timestamp = datetime.now().strftime("acquisition_%d_%m_%H_%M")
        save_dir = os.path.join(f"/home/{username}/images", timestamp)
        os.makedirs(save_dir, exist_ok=True)
        
        # Fichier CSV pour les données
        csv_file = os.path.join(save_dir, "distance_data.csv")
        
        # Configuration de la caméra
        config = picam2.create_still_configuration(
            main={"size": (2592, 1944)},
            controls={
                "ExposureTime": 5000,
                "AnalogueGain": 0.5,
                "NoiseReductionMode": 1,
                "Sharpness": 1.7,
                "Contrast": 1.1,
                "Saturation": 1.2,
                "AwbMode": 1,
                "AeExposureMode": "Short",
                "MeteringMode": 1
            }
        )
        
        # Allumage du laser
        GPIO.output(LASER_PIN, GPIO.HIGH)
        
        # Capture des données
        start_time = time.time()
        i = 0
        
        while (time.time() - start_time) < 60:  # 60 secondes de capture
            filename = os.path.join(save_dir, f"img_{i:05d}.jpeg")
            picam2.options["quality"] = 99
            picam2.capture_file(filename)
            
            distance, amplitude, temp, ticks, error = tf_luna.read_data()
            with open(csv_file, "a") as f:
                f.write(f"{i:05d},{distance},{amplitude},{temp},{ticks},{error}\n")
            
            i += 1
            time.sleep(0.1)  # Petit délai entre les captures
        
        GPIO.output(LASER_PIN, GPIO.LOW)
        return jsonify({
            "status": "success",
            "message": "Scan completed",
            "directory": save_dir,
            "images_captured": i,
            "data_points": i
        })
    
    except Exception as e:
        GPIO.output(LASER_PIN, GPIO.LOW)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Nettoyage à la fermeture
@app.teardown_appcontext
def cleanup(exception=None):
    GPIO.output(LASER_PIN, GPIO.LOW)
    picam2.stop()
    GPIO.cleanup()

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True)
    finally:
        cleanup()