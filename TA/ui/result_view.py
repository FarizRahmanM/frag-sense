from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QStackedWidget, QHBoxLayout,
)
from PySide6.QtCore import Qt, Slot, Signal
from ui.component.header_view import HeaderView
from ui.component.card_view import CardWidget, CardViewModel
from ui.component.delete_view import DeleteDialog
from services.card_service import CardService
import datetime
from typing import List  # opsional, jika kamu mau
from utils import resource_path
import re

class ResultView(QWidget):
    validity_changed = Signal(bool)
    def __init__(self, main_window=None):

        super().__init__()
        self.main_window = main_window
        self.cards = CardService.instance().cards
        self.current_index = 0
        

        self.delete_dialog = DeleteDialog()
        self.delete_dialog.accepted.connect(self.on_delete_confirmed)
        self.delete_dialog.rejected.connect(self.on_delete_canceled)

        # Layout utama
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        self.header = HeaderView()
        self.header.set_history_button_visible(False)  # ⬅️ Sembunyikan tombol Riwayat
        main_layout.addWidget(self.header)

        # Tombol back
        back_label = QLabel("← Kembali")
        back_label.setStyleSheet("font-size: 14px; color: #333; margin-left: 40px; margin-top: 40px;")
        back_label.setCursor(Qt.PointingHandCursor)
        back_label.mousePressEvent = self.back_button_click
        main_layout.addWidget(back_label)

        # Layout tengah untuk carousel dan tombol navigasi
        middle_layout = QHBoxLayout()
        middle_layout.setContentsMargins(40, 20, 40, 20)

        # Tombol kiri
        self.left_button = QPushButton("←")
        self.left_button.setFixedWidth(50)
        self.left_button.setStyleSheet("""
            background: transparent;
            font-size: 24px;
            font-weight: bold;
        """)
        self.left_button.clicked.connect(self.previous)
        middle_layout.addWidget(self.left_button, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        # Carousel di tengah
        self.carousel = QStackedWidget()
        middle_layout.addWidget(self.carousel, stretch=1)

        # Tombol kanan
        self.right_button = QPushButton("→")
        self.right_button.setFixedWidth(50)
        self.right_button.setStyleSheet("""
            background: transparent;
            font-size: 24px;
            font-weight: bold;
        """)
        self.right_button.clicked.connect(self.next)
        middle_layout.addWidget(self.right_button, alignment=Qt.AlignRight | Qt.AlignVCenter)

        main_layout.addLayout(middle_layout)

        # Tombol simpan dan hapus
        main_layout.addStretch()

        # Tombol simpan dan hapus (di tengah horizontal, naik dari bawah)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        button_layout.setContentsMargins(0, 0, 0, 20)  # beri margin bawah

        self.save_button = QPushButton("Simpan Hasil")
        self.save_button.setStyleSheet("padding: 8px 16px; background-color: #3B89FF; color: white; font-weight: 600;")
        self.save_button.clicked.connect(self.save_button_click)

        delete_button = QPushButton("Hapus")
        delete_button.setStyleSheet(
            "padding: 8px 16px; background-color: white; color: #FF0000; font-weight: 600; border: 1px solid #FF0000;"
        )
        delete_button.clicked.connect(self.delete_button_click)

        button_layout.addStretch()
        button_layout.addWidget(delete_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)
        self.update_arrow_visibility()
        self.card_widgets = []

    def set_result(self, image_paths: List[str], fragments_inside: List[int],
               fragments_outside: List[int], inference_times: List[float],
               last_edited=None, preserve_existing_time=False):

        now = datetime.datetime.now()
        test_date = now.strftime("%d %B %Y")
        test_time = now.strftime("%H:%M:%S")

        for i, image_path in enumerate(image_paths):
            fragment_inside = fragments_inside[i]
            fragment_outside = fragments_outside[i]
            inference_time = inference_times[i]
            total_fragments = fragment_inside + (fragment_outside * 0.5)

            status = "PASS" if 40 <= total_fragments <= 400 else "FAIL"

            image_path_full = resource_path(image_path)

            card_vm = CardViewModel(
                test_name=f"Hasil Deteksi {i + 1}",
                date=self.cards[i].test_date if preserve_existing_time and i < len(self.cards) else test_date,
                test_time=self.cards[i].test_time if preserve_existing_time and i < len(self.cards) else test_time,
                total_fragments=total_fragments,
                image=image_path_full,
                fragment_inside=fragment_inside,
                fragment_outside=fragment_outside,
                last_edited=last_edited,
                status=status,
                inference_time=inference_time  # ✅
            )
            CardService.instance().add_card(card_vm)

        self.cards = CardService.instance().cards
        self.populate_cards()
        self.current_index = self.carousel.count() - 1
        self.carousel.setCurrentIndex(self.current_index)
        self.update_arrow_visibility()

    def clear_stack(self):
        # Hapus semua widget di carousel dengan aman
        while self.carousel.count() > 0:
            widget = self.carousel.widget(0)
            if widget:
                self.carousel.removeWidget(widget)
                widget.deleteLater()

    def populate_cards(self):
        self.clear_stack()
        self.card_widgets = []  # ✅ Reset

        for card_vm in self.cards:
            card_widget = CardWidget(card_vm)

            # Connect signal validasi
            card_widget.validity_changed.connect(self.update_save_button_state)

            self.card_widgets.append(card_widget)  # ✅ Simpan referensi

            container = QWidget()
            h_layout = QHBoxLayout(container)
            h_layout.setContentsMargins(0, 0, 0, 0)
            h_layout.addStretch()
            h_layout.addWidget(card_widget)
            h_layout.addStretch()

            container.setMinimumWidth(600)
            container.setMinimumHeight(card_widget.sizeHint().height())

            self.carousel.addWidget(container)

        self.update_save_button_state()

    @Slot()
    def next(self):
        if self.current_index < self.carousel.count() - 1:
            self.current_index += 1
            self.carousel.setCurrentIndex(self.current_index)
            self.update_arrow_visibility()

    @Slot()
    def previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.carousel.setCurrentIndex(self.current_index)
            self.update_arrow_visibility()

    def update_arrow_visibility(self):
        self.left_button.setVisible(self.current_index > 0)
        self.right_button.setVisible(self.current_index < self.carousel.count() - 1)

    def back_button_click(self, event):
        # Hapus semua card yang belum disimpan
        self.clear_stack()  # Bersihkan dari carousel
        CardService.instance().cards.clear()  # Bersihkan dari service
        self.cards = []  # Kosongkan variabel lokal juga
        self.current_index = 0
        self.update_arrow_visibility()

        # Navigasi kembali
        if self.main_window:
            self.main_window.go_back()

    def save_button_click(self):
        # Lazy import agar PyInstaller tidak otomatis include HistoryView kecuali dipakai
        from ui.history_view import HistoryView

        # Simpan semua card yang ada di carousel
        for i in range(self.carousel.count()):
            container = self.carousel.widget(i)
            card_widget = container.layout().itemAt(1).widget()  # Ambil CardWidget dari container
            card_vm = card_widget.card_data()
            CardService.instance().save_or_update(card_vm)

        # Hapus semua card dari service dan UI
        CardService.instance().cards.clear()  # Kosongkan daftar card
        self.clear_stack()  # Bersihkan tampilan card di carousel
        self.cards = []  # Pastikan properti lokal juga kosong
        self.current_index = 0
        self.update_arrow_visibility()

        # Arahkan ke halaman riwayat setelah simpan
        if self.main_window:
            self.main_window.navigate(HistoryView(self.main_window))

    def delete_button_click(self):
        if self.cards:
            current_card = self.cards[self.current_index]
            self.delete_dialog.delete_widget.label_info2.setText(current_card.test_name)
            self.delete_dialog.exec()

    def on_delete_confirmed(self):
        if not self.cards:
            return

        # Hapus kartu yang sedang aktif
        deleted_card = self.cards.pop(self.current_index)
        widget_to_remove = self.carousel.widget(self.current_index)
        if widget_to_remove:
            self.carousel.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()

        if len(self.cards) == 0:
            if self.main_window:
                self.main_window.go_back()
            return

        # Update current_index agar valid
        if self.current_index >= len(self.cards):
            self.current_index = max(0, len(self.cards) - 1)

        self.carousel.setCurrentIndex(self.current_index)
        self.update_arrow_visibility()
        CardService.instance().cards = self.cards
        self.delete_dialog.close()

    def on_delete_canceled(self):
        self.delete_dialog.close()


    def update_save_button_state(self):
        all_valid = all([
            widget.input_uji and re.match(r"^\d{2}-\d{1,2}/[A-Z0-9]+/[A-Z]{2}-\d{2}/20\d{2}$", widget.input_uji.text())
            for widget in self.card_widgets
        ])

        # Cek validasi tambahan (bulan dan tahun)
        for widget in self.card_widgets:
            text = widget.input_uji.text()
            try:
                bagian = text.split("/")
                bulan = int(bagian[2].split("-")[1])
                tahun = bagian[3]
                if not (1 <= bulan <= 12 and len(tahun) == 4):
                    all_valid = False
            except:
                all_valid = False

        self.save_button.setEnabled(all_valid)


    def update_inference_time_label(self):
        if self.vm.inference_time is not None:
            self.inference_time_label.setText(f"Waktu Inference: {self.vm.inference_time:.3f} detik")
        else:
            self.inference_time_label.setText("Waktu Inference: -")