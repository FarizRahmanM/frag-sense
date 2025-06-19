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
        self.right_widget = None
        self.setup_ui()

    def setup_ui(self):
        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(20, 14, 20, 14)
        container_layout.setSpacing(0)

        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        container_layout.addLayout(grid)

        # === Left Logo ===
        left_layout = QHBoxLayout()

        # Logo Polban 
        logo_polban = QLabel()
        logo_polban.setPixmap(QPixmap(resource_path("material/logopolban.png")).scaledToHeight(40, Qt.SmoothTransformation))
        logo_polban.setContentsMargins(0, 0, 14, 0)  # Jarak ke kanan
        left_layout.addWidget(logo_polban)

        # Logo Kemenperin
        logo1 = QLabel()
        logo1.setPixmap(QPixmap(resource_path("material/logo-kemenperin.png")).scaledToHeight(85, Qt.SmoothTransformation))
        logo1.setContentsMargins(0, 0, 14, 0)  # Jarak ke kanan
        left_layout.addWidget(logo1)

        # Logo BBK
        logo2 = QLabel()
        logo2.setPixmap(QPixmap(resource_path("material/logo-bbk.png")).scaledToHeight(60, Qt.SmoothTransformation))
        logo2.setContentsMargins(0, 0, 0, 0)  # Tidak perlu margin jika paling kanan
        left_layout.addWidget(logo2)

        # Tambahkan ke grid
        grid.addLayout(left_layout, 0, 0)

        # === Title ===
        title = QLabel("FragSense")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")

        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.addStretch()
        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.setContentsMargins(0, 0, 0, 0)

        grid.addWidget(title_container, 0, 1)

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

        self.right_widget = QWidget()
        self.right_widget.setLayout(right_layout)
        right_layout.setAlignment(Qt.AlignRight)

        grid.addWidget(self.right_widget, 0, 2)

        self.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)

    def on_history_click(self, event):
        self.history_clicked.emit()

    def set_history_button_visible(self, visible: bool):
        if self.right_widget:
            self.right_widget.setVisible(visible)
