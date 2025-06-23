from flask import Flask, request

#import RPi.GPIO as GPIO

# Remplace ceci par le numéro réel de ton pin GPIO pour le laser
LASER_PIN = 18

app = Flask(__name__)  # ✅ Utilise __name__ ici

@app.route('/laser', methods=['POST'])
def control_laser():
    state = request.json.get('state')
   # GPIO.output(LASER_PIN, GPIO.HIGH if state == 'on' else GPIO.LOW)
    return {'status': 'ok'}

@app.route('/camera', methods=['POST'])
def control_camera():
    state = request.json.get('state')
    # TODO: lancer une action sur la caméra, ex: via subprocess
    return {'status': 'ok'}

@app.route('/tf-luna', methods=['GET'])
def get_distance():
    # TODO: implémenter la lecture du capteur TF-Luna via UART
    distance = read_tf_luna()  # Cette fonction doit être définie
    return {'distance': distance}

def read_tf_luna():
    # Dummy exemple : à remplacer par ton code UART
    return 123.45

if __name__ == '__main__':  # ✅ Bonne syntaxe
    #GPIO.setmode(GPIO.BCM)
    #GPIO.setup(LASER_PIN, GPIO.OUT)
    app.run(host='0.0.0.0', port=5000, debug=True)
