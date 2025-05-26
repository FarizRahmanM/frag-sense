from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout, QHBoxLayout
)
from PySide6.QtCore import Signal, Qt


class Confirmation(QWidget):
    # Sinyal pengganti event .NET
    cancel_clicked = Signal()
    save_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedSize(500, 150)
        self.setStyleSheet("background-color: white; border-radius: 12px;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Teks konfirmasi
        label = QLabel("Yakin ingin menyimpan?")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 20px; font-weight: 600;")
        main_layout.addWidget(label)

        # Tombol Batal & Simpan
        button_layout = QGridLayout()
        batal_button = QPushButton("Batal")
        batal_button.setFixedSize(90, 40)
        batal_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #A0A0A0;
                border-radius: 5px;
                font-size: 20px;
                font-weight: 500;
                color: #1A1A1A;
            }
        """)
        batal_button.clicked.connect(self.on_cancel_clicked)

        simpan_button = QPushButton("Simpan")
        simpan_button.setFixedSize(90, 40)
        simpan_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #3B89FF;
                border-radius: 5px;
                font-size: 20px;
                font-weight: 500;
                color: #3B89FF;
            }
        """)
        simpan_button.clicked.connect(self.on_save_clicked)

        # Tambahkan ke grid
        button_layout.addWidget(batal_button, 0, 0, alignment=Qt.AlignLeft)
        button_layout.addWidget(simpan_button, 0, 1, alignment=Qt.AlignRight)
        main_layout.addLayout(button_layout)

    def on_cancel_clicked(self):
        self.cancel_clicked.emit()

    def on_save_clicked(self):
        self.save_clicked.emit()
