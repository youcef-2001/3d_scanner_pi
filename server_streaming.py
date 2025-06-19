import socket
import struct
from picamera2 import Picamera2
import cv2
import numpy as np

# Socket TCP
TCP_IP = '0.0.0.0'
TCP_PORT = 9999

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((TCP_IP, TCP_PORT))
server_socket.listen(1)
print(f"En attente de connexion TCP sur {TCP_IP}:{TCP_PORT}...")

conn, addr = server_socket.accept()
print(f"Connecté par {addr}")

# Initialisation caméra 5MP
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (2592, 1944)})
picam2.configure(config)
picam2.start()

def enhance_image(img):
    # Convertir en LAB (meilleur pour contraste)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # CLAHE sur le canal L (contraste local)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l)

    # Merge back
    limg = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    # Unsharp mask (netteté)
    gaussian = cv2.GaussianBlur(enhanced, (9,9), 10.0)
    unsharp = cv2.addWeighted(enhanced, 1.5, gaussian, -0.5, 0)

    return unsharp

try:
    while True:
        frame = picam2.capture_array()

        # Amélioration
        frame = enhance_image(frame)

        # Encode JPEG qualité 90%
        result, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        data = jpeg.tobytes()

        # Envoi taille + données
        conn.sendall(struct.pack(">L", len(data)) + data)

except Exception as e:
    print(f"Erreur : {e}")

finally:
    picam2.stop()
    conn.close()
    server_socket.close()
