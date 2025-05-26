from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QGridLayout
)
from PySide6.QtGui import QPixmap, QCursor
from PySide6.QtCore import Qt, Signal
from utils import resource_path

class HeaderView(QWidget):
    history_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # Container
        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(20, 14, 20, 14)
        container_layout.setSpacing(0)

        # Grid Layout
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        container_layout.addLayout(grid)

        # === Left Logo ===
        left_layout = QHBoxLayout()
        logo1 = QLabel()
        logo1.setPixmap(QPixmap(resource_path("material/logo-kemenperin.png")).scaledToHeight(40, Qt.SmoothTransformation))
        left_layout.addWidget(logo1)

        logo2 = QLabel()
        logo2.setPixmap(QPixmap(resource_path("material/logo-bbk.png")).scaledToHeight(40, Qt.SmoothTransformation))
        logo2.setContentsMargins(14, 0, 0, 0)
        left_layout.addWidget(logo2)

        grid.addLayout(left_layout, 0, 0)

        # === Title Center ===
        title = QLabel("Laboratorium Pengujian Kaca")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        grid.addWidget(title, 0, 1)

        # === Right Button Riwayat ===
        right_layout = QHBoxLayout()

        icon = QLabel()
        icon.setPixmap(QPixmap(resource_path("material/history.png")).scaledToHeight(12, Qt.SmoothTransformation))
        icon.setContentsMargins(4, 0, 4, 0)
        right_layout.addWidget(icon)

        label = QLabel("Riwayat")
        label.setCursor(QCursor(Qt.PointingHandCursor))
        label.setStyleSheet("font-size: 14px;")
        label.mousePressEvent = self.on_history_click
        right_layout.addWidget(label)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        right_layout.setAlignment(Qt.AlignRight)

        grid.addWidget(right_widget, 0, 2)

        # Optional: background and shadow (requires QFrame or QGraphicsDropShadowEffect for true shadow)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)

    def on_history_click(self, event):
        self.history_clicked.emit()
