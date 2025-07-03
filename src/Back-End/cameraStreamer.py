import cv2
from picamera2 import Picamera2
import threading
import time





class CameraStreamer:
    def __init__(self,logger):
        self.picam2 = None
        self.is_streaming = False
        self.lock = threading.Lock()
        self.frame_count = 0
        self.last_frame_time = time.time()
        self.logger = logger
        
    def initialize_camera(self):
        """Initialise la caméra avec les paramètres optimisés"""
        try:
            self.picam2 = Picamera2()
            
            # Configuration pour 1280x1280 (format carré)
            config = self.picam2.create_video_configuration(
                main={"size": (640, 480), "format": "RGB888"},
                controls={
                    "FrameRate": 15,  # Réduit pour éviter la surcharge réseau
                    "ExposureTime": 33000,  # Optimise l'exposition
                    "AnalogueGain": 1.0,
                    "Brightness": 0.0,
                    "Contrast": 1.0
                }
            )
            
            self.picam2.configure(config)
            self.picam2.start()
            self.is_streaming = True
            self.logger.info("Caméra initialisée avec succès - Résolution 1280x1280")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation de la caméra: {e}")
            return False
    
    def stop_camera(self):
        """Arrête la caméra proprement"""
        with self.lock:
            if self.picam2 and self.is_streaming:
                self.picam2.stop()
                self.is_streaming = False
                self.logger.info("Caméra arrêtée")

    def generate_mjpeg(self):
        """Génère le flux MJPEG optimisé"""
        if not self.is_streaming:
            if not self.initialize_camera():
                self.logger.error("Initialisation caméra échouée")
                yield b''  # ou simplement "break" si plus clair
                return
            
        try:
            while self.is_streaming:
                with self.lock:
                    if not self.picam2:
                        break 
                    # Capture de l'image
                    frame = self.picam2.capture_array("main")
                    # Conversion RGB vers BGR pour OpenCV
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    # Encodage JPEG avec qualité optimisée
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 99]  # Qualité 99%
                    ret, jpeg = cv2.imencode('.jpg', frame_bgr, encode_param)
                    
                    if not ret:
                        continue
                    
                    # Statistiques de performance
                    self.frame_count += 1
                    current_time = time.time()
                    if current_time - self.last_frame_time > 5:  # Log toutes les 5 secondes
                        fps = self.frame_count / (current_time - self.last_frame_time)
                        self.logger.info(f"FPS: {fps:.2f}")
                        self.frame_count = 0
                        self.last_frame_time = current_time
                    
                    # Yield du frame MJPEG
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(jpeg)).encode() + b'\r\n\r\n' + 
                           jpeg.tobytes() + b'\r\n')
                    
                    # Petit délai pour éviter la surcharge CPU
                    time.sleep(0.033)  # ~30 FPS max
                    
        except GeneratorExit:
            self.logger.info("Client déconnecté du flux vidéo")
        except Exception as e:
            self.logger.error(f"Erreur dans generate_mjpeg: {e}")
        finally:
            self.stop_camera()
