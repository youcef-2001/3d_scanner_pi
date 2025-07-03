import threading
import time
from picamera2 import Picamera2
import cv2

class CameraManager:
    _instance = None
    _instance_lock = threading.Lock()

    def __init__(self, logger):
        self.logger = logger
        self.lock = threading.Lock()         # Protège la caméra
        self.picam2 = None
        self.isStreaming = False
        self.isCameraRunning = False
        

    @classmethod
    def get_instance(cls, logger):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = CameraManager(logger)
                
            return cls._instance

    def start_camera(self, config):
        with self.lock:
            if self.picam2 is None:
                try:
                    self.picam2 = Picamera2()
                    if config == 'default':
                        config = self.picam2.create_still_configuration(main={"size": (1280, 1280)})
                    elif config == 'streaming':
                        config = self.picam2.create_video_configuration(main={"size": (1280, 1280)}, buffer_count=4)
                        self.isStreaming = True
                    elif isinstance(config, dict):
                        config = self.picam2.create_still_configuration(**config)
                    self.picam2.configure(config)
                    self.picam2.start()
                    self.isCameraRunning = True
                    self.logger.info("Caméra démarrée.")
                except Exception as e:
                    self.logger.error(f"Erreur lors du démarrage de la caméra: {e}")
                    self.picam2 = None
                    self.running = False
                    raise

    def stop_camera(self):
        with self.lock:
            if self.picam2:
                self.picam2.stop()
                self.picam2.close()
                self.picam2 = None
                self.isCameraRunning = False
                self.logger.info("Caméra arrêtée.")

    def capture_frame(self):
        with self.lock:
            if not self.isCameraRunning:
                self.logger.warning("capture_frame appelée alors que la caméra n'est pas démarrée.")
                return None
            try:
                frame = self.picam2.capture_array()
                return frame
            except Exception as e:
                self.logger.error(f"Erreur de capture: {e}")
                return None
    def capture_file(self, filename):
        with self.lock:
            if not self.isCameraRunning:
                self.logger.warning("capture_file appelée alors que la caméra n'est pas démarrée.")
                return False
            try:
                self.picam2.capture_file(filename)
                self.logger.info(f"Image capturée et enregistrée dans {filename}")
                return True
            except Exception as e:
                self.logger.error(f"Erreur de capture de fichier: {e}")
                return False
    def generate_mjpeg(self):
        """Génère le flux MJPEG optimisé"""
        if not self.isStreaming :
            self.logger.error("La caméra n'est pas en mode streaming.")
            return
        
        try:
            while self.isStreaming:
                with self.lock:
                    if not self.isCameraRunning:
                        break
                        
                    # Capture de l'image
                    frame = self.picam2.capture_array()
                    # Conversion RGB vers BGR pour OpenCV
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    # Encodage JPEG avec qualité optimisée
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 99]  # Qualité 85%
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