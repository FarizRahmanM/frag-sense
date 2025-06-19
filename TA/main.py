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
    # Ambil ukuran layar
    screen = app.primaryScreen()
    screen_size = screen.availableGeometry()  # Menghindari area yang tertutup taskbar

    # Kurangi sedikit biar tidak menutupi tombol window (X, minimize, dll.)
    margin = 50
    width = screen_size.width() - margin
    height = screen_size.height() - margin

    # Atur ukuran jendela
    window.resize(width, height)
    window.move(
        (screen_size.width() - width) // 2,
        (screen_size.height() - height) // 2
    )

    window.show()

    sys.exit(app.exec())
