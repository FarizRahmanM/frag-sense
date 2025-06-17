from PySide6.QtCore import QThread, Signal

class DetectionWorker(QThread):
    finished = Signal(str, int, int)  # output_path, inside, outside
    error_occurred = Signal(str)

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

    def run(self):
        from detection.detector import run_detection  # Import lokal
        try:
            output_path, inside, outside = run_detection(self.image_path)
            self.finished.emit(output_path, inside, outside)
        except Exception as e:
            self.error_occurred.emit(str(e))
