from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout,QDialog
)
from PySide6.QtCore import Signal, Qt

class DeleteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Konfirmasi Hapus")
        self.setFixedSize(500, 200)

        layout = QVBoxLayout(self)
        self.delete_widget = Delete()
        layout.addWidget(self.delete_widget)

        # Forward sinyal keluar
        self.delete_widget.cancel_clicked.connect(self.reject)
        self.delete_widget.delete_clicked.connect(self.accept)

class Delete(QWidget):
    cancel_clicked = Signal()
    delete_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedSize(500, 150)
        self.setStyleSheet("background-color: white; border-radius: 12px;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Informasi nomor pengujian
        info_layout = QVBoxLayout()

        label_info1 = QLabel("Hapus Nomor Pengujian")
        label_info1.setStyleSheet("font-size: 15px; font-weight: 400;")
        label_info1.setAlignment(Qt.AlignLeft)

        # Definisikan label_info2 di sini
        self.label_info2 = QLabel()  # Inisialisasi dulu
        self.label_info2.setStyleSheet("font-size: 15px; font-weight: 600;")
        self.label_info2.setAlignment(Qt.AlignLeft)

        info_layout.addWidget(label_info1)
        info_layout.addWidget(self.label_info2)

        # Tombol Batal & Hapus
        button_layout = QGridLayout()

        batal_button = QPushButton("Batal")
        batal_button.setFixedSize(80, 40)
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

        hapus_button = QPushButton("Hapus")
        hapus_button.setFixedSize(90, 40)
        hapus_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid red;
                border-radius: 5px;
                font-size: 19px;
                font-weight: 500;
                color: red;
            }
        """)
        hapus_button.clicked.connect(self.on_delete_clicked)

        button_layout.addWidget(batal_button, 0, 0, alignment=Qt.AlignLeft)
        button_layout.addWidget(hapus_button, 0, 1, alignment=Qt.AlignRight)

        # Susun ke main layout
        main_layout.addLayout(info_layout)
        main_layout.addSpacing(20)
        main_layout.addLayout(button_layout)

    # Tambahkan method untuk update label_info2 dari luar, misal:
    def set_nama_hasil_uji(self, nama_hasil_uji):
        self.label_info2.setText(nama_hasil_uji)

    def on_cancel_clicked(self):
        self.cancel_clicked.emit()

    def on_delete_clicked(self):
        self.delete_clicked.emit()
