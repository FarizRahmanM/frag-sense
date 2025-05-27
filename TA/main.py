import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils import resource_path


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QWidget {
            background-color: white;
            color: black;
        }
        QLineEdit, QLabel, QPushButton {
            background-color: white;
            color: black;
        }
    """)

    window = MainWindow()
    window.setWindowTitle("FragSense")
    window.resize(1024, 768)
    window.show()

    sys.exit(app.exec())
