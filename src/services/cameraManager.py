import threading
from picamera2 import Picamera2


class CameraManager:
    _instance = None
    _instance_lock = threading.Lock()

    def __init__(self, logger):
        self.logger = logger
        self.lock = threading.Lock()         # Protège la caméra
        self.picam2 = None
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
                        config = self.picam2.create_still_configuration(main={"size": (1280, 1280)}, buffer_count=8)
                    elif config == 'streaming':
                        config = self.picam2.create_video_configuration(main={"size": (640, 480)}, buffer_count=8)
                    elif isinstance(config, dict):
                        config = self.picam2.create_still_configuration(**config)
                    self.picam2.configure(config)
                    self.picam2.start()
                    self.isCameraRunning = True
                    self.logger.info("Caméra démarrée.")
                except Exception as e:
                    self.logger.error(f"Erreur lors du démarrage de la caméra: {e}")
                    self.picam2 = None
                    self.isCameraRunning = False
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
            
    def capture_array(self):
        with self.lock:
            if not self.isCameraRunning:
                self.logger.warning("capture_array appelée alors que la caméra n'est pas démarrée.")
                return None
            try:
                frame = self.picam2.capture_array()
                return frame
            except Exception as e:
                self.logger.error(f"Erreur de capture d'array: {e}")
                return None