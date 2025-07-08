from PySide6.QtCore import QThread, Signal

class DetectionWorker(QThread):
    finished = Signal(str, str, int, int, float)  # output_path, inside, outside, inference_time
    error_occurred = Signal(str)

    def __init__(self, image_path, model_name="best.pt"):
        super().__init__()
        self.image_path = image_path
        self.model_name = model_name

    def run(self):
        from detection.detector import run_detection  # Import lokal
        try:
            dot_path, numbered_path, inside, outside, inference_time = run_detection(
                self.image_path, model_name=self.model_name
            )
            self.finished.emit(dot_path, numbered_path, inside, outside, inference_time)
        except Exception as e:
            self.error_occurred.emit(str(e))