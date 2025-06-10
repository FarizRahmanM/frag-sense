from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QScrollArea,
    QFrame, QGridLayout, QStackedLayout, QDialog, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox,QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QDialog

from ui.component.header_view import HeaderView
from ui.component.card_view import CardWidget
from ui.component.delete_view import DeleteDialog
from ui.component.card_view import CardViewModel
from services.card_service import CardService
from model.database import delete_detection
from ui.history_view import HistoryView
from utils import resource_path
import os
import pandas as pd


class DetailView(QWidget):
    def __init__(self, main_window=None, selected_card=None):
        super().__init__()
        self.main_window = main_window
        self.selected_card = selected_card

        self.setStyleSheet("font-family: Arial; font-size: 14px;")
        layout = QVBoxLayout(self)
        layout.setSpacing(10)  # Kurangi jarak antar elemen
        layout.setContentsMargins(0, 0, 0, 0) 

        # Header
        header = HeaderView()
        header.setMaximumHeight(80)  # atau ukuran yang lebih kecil sesuai kebutuhan
        layout.addWidget(header)

        # Back button wrapper
        back_wrapper = QWidget()
        back_layout = QHBoxLayout()
        back_layout.setContentsMargins(20, 10, 0, 10)  # (left, top, right, bottom)
        back_layout.setAlignment(Qt.AlignLeft)

        back_button = QLabel("\u2190 Kembali")
        back_button.setStyleSheet("color: #333; font-size: 13px; padding: 2px;")
        back_button.setFixedHeight(24)  # Pakai nilai kecil sesuai kebutuhan
        back_button.setCursor(QCursor(Qt.PointingHandCursor))
        back_button.mousePressEvent = self.back_button_click

        back_layout.addWidget(back_button)
        back_wrapper.setLayout(back_layout)
        layout.addWidget(back_wrapper)

        # Content grid
        content_layout = QGridLayout()
        content_layout.setContentsMargins(40, 0, 40, 0)

        # Card display
        card_container = QWidget()
        card_layout = QHBoxLayout(card_container)
        card_layout.setAlignment(Qt.AlignCenter)

        self.card_widget = CardWidget(self.selected_card)
        self.card_widget.setFixedWidth(800)  # Ubah sesuai kebutuhan
        card_layout.addWidget(self.card_widget)

        content_layout.addWidget(card_container, 0, 0, 0, 0)
        card_container.setStyleSheet("background-color: #f0f0f0;")
        
        # Fragment list (hidden by default)
        self.fragment_list = QListWidget()
        self.fragment_list.setMaximumHeight(250)
        self.fragment_list.setVisible(False)
        content_layout.addWidget(self.fragment_list, 0, 1)

        layout.addLayout(content_layout)

        # Action buttons
        # Buat layout utama tombol
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(40, 10, 40, 10)  # Margin kiri-kanan agar rapi

        # Layout untuk tombol kiri
        left_buttons = QHBoxLayout()
        left_buttons.setSpacing(20)

        delete_btn = QPushButton("Hapus")
        delete_btn.setStyleSheet("color: #FF0000; background: white; padding: 8px; font-weight: 600;")
        delete_btn.clicked.connect(self.show_delete_popup)

        save_btn = QPushButton("Simpan Hasil Edit")
        save_btn.setStyleSheet("color: white; background: #3B89FF; padding: 8px; font-weight: 600;")
        save_btn.clicked.connect(self.save_and_navigate)

        left_buttons.addWidget(delete_btn)
        left_buttons.addWidget(save_btn)

        # Spacer di tengah untuk mendorong tombol kanan ke ujung
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        # Layout untuk tombol kanan
        right_buttons = QHBoxLayout()
        export_btn = QPushButton("Unduh Data")
        export_btn.setStyleSheet("color: black; background: #C2E7FF; padding: 8px; font-weight: 600;")
        export_btn.clicked.connect(self.export_to_excel)
        right_buttons.addWidget(export_btn)

        # Tambahkan ke layout utama
        button_layout.addLayout(left_buttons)
        button_layout.addItem(spacer)
        button_layout.addLayout(right_buttons)

        # Tambahkan ke layout utama window
        layout.addLayout(button_layout)
        layout.addStretch()

    @Slot()
    def back_button_click(self, event):
        if self.main_window:
            self.main_window.go_back_from_detail()

    @Slot()
    def save_and_navigate(self):
        if self.main_window:
            edited_card = self.card_widget.card_data()

            # Update ke DB
            CardService.instance().update_to_db(edited_card)

            # Navigasi ke halaman riwayat
            self.main_window.navigate(HistoryView(main_window=self.main_window))
            

    @Slot()
    def show_delete_popup(self):
        self.card_to_delete = self.selected_card

        # Buat dialog baru
        self.delete_dialog = DeleteDialog(self)
        self.delete_dialog.delete_widget.set_nama_hasil_uji(self.card_to_delete.test_name)

        # Sambungkan sinyal ke slot
        self.delete_dialog.accepted.connect(self.on_delete_confirmed)
        self.delete_dialog.rejected.connect(self.on_delete_canceled)

        # Tampilkan dialog
        self.delete_dialog.exec()
    
    @Slot()
    def on_delete_confirmed(self):
        print("Hapus dikonfirmasi")
        if self.card_to_delete:
            print("ID yang akan dihapus:", self.card_to_delete.id)

            # Simpan path gambar sebelum dihapus dari DB
            image_path = self.card_to_delete.image_path  # Pastikan atribut ini ada

            # Hapus dari DB
            if self.card_to_delete.id:
                delete_detection(self.card_to_delete.id)
                print("Berhasil menghapus dari DB")

            # Hapus file gambar dari folder assets jika ada
            if image_path:
                abs_image_path = resource_path(image_path)
                if os.path.exists(abs_image_path):
                    try:
                        os.remove(abs_image_path)
                        print(f"File {abs_image_path} berhasil dihapus.")
                    except Exception as e:
                        print(f"Gagal menghapus file: {e}")

            # Navigasi ke HistoryView
            if self.main_window:
                self.main_window.navigate(HistoryView(main_window=self.main_window))

            self.card_to_delete = None
            self.delete_dialog.close()

    @Slot()
    def on_delete_canceled(self):
        self.card_to_delete = None
        self.delete_dialog.close()

    @Slot()
    def show_fragment_info(self, card: CardViewModel):
        self.fragment_list.clear()
        for i, frag in enumerate(CardService.instance().cards):
            item = QListWidgetItem(f"{i+1:03d} - Info")
            self.fragment_list.addItem(item)
        self.fragment_list.setVisible(True)

    
    @Slot()
    def export_to_excel(self):
        if not self.selected_card:
            QMessageBox.warning(self, "Export Gagal", "Tidak ada data yang bisa diekspor.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan sebagai Excel",
            "hasil_pengujian.xlsx",
            "Excel Files (*.xlsx)"
        )

        if not file_path:
            return

        try:
            # Siapkan data card untuk satu baris (tanpa path gambar)
            data = [{
                "Nama Pengujian": self.selected_card.test_name,
                "Nama Penguji": self.selected_card.tester_name,
                "Tanggal": self.selected_card.test_date,
                "Waktu": self.selected_card.test_time,
                "Jumlah Fragmen (Dalam)": self.selected_card.fragment_inside,
                "Jumlah Fragmen (Luar)": self.selected_card.fragment_outside,
                "Jumlah Fragmen (Total)": round(
                    self.selected_card.fragment_inside + (self.selected_card.fragment_outside / 2), 1
                )
            }]

            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)

            QMessageBox.information(self, "Export Berhasil", f"Data berhasil diekspor ke:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Gagal", f"Terjadi kesalahan saat ekspor:\n{str(e)}")