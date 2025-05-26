
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow  # Pastikan file ini benar (main_window.py)
from utils import resource_path  # Tambahkan ini di atas


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.setWindowTitle("Deteksi Fragmen Kaca")
    window.resize(1024, 768)  # Atur ukuran jendela sesuai kebutuhan
    window.show()

    sys.exit(app.exec())
