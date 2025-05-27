from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QStackedWidget, QHBoxLayout,
)
from PySide6.QtCore import Qt, Slot
from ui.component.header_view import HeaderView
from ui.component.card_view import CardWidget, CardViewModel
from ui.component.delete_view import DeleteDialog
from services.card_service import CardService
import datetime
from typing import List  # opsional, jika kamu mau
from utils import resource_path


class ResultView(QWidget):
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
        main_layout.addWidget(HeaderView())

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
        self.left_button.setStyleSheet("background: transparent;")
        self.left_button.clicked.connect(self.previous)
        middle_layout.addWidget(self.left_button, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        # Carousel di tengah
        self.carousel = QStackedWidget()
        middle_layout.addWidget(self.carousel, stretch=1)

        # Tombol kanan
        self.right_button = QPushButton("→")
        self.right_button.setFixedWidth(50)
        self.right_button.setStyleSheet("background: transparent;")
        self.right_button.clicked.connect(self.next)
        middle_layout.addWidget(self.right_button, alignment=Qt.AlignRight | Qt.AlignVCenter)

        main_layout.addLayout(middle_layout)

        # Tombol simpan dan hapus
        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        save_button = QPushButton("Simpan Hasil")
        save_button.setStyleSheet("padding: 8px; background-color: #3B89FF; color: white; font-weight: 600;")
        save_button.clicked.connect(self.save_button_click)
        button_layout.addWidget(save_button)

        delete_button = QPushButton("Hapus")
        delete_button.setStyleSheet(
            "padding: 8px; background-color: white; color: #FF0000; font-weight: 600; border: 1px solid #FF0000;"
        )
        delete_button.clicked.connect(self.delete_button_click)
        button_layout.addWidget(delete_button)

        main_layout.addLayout(button_layout)
        self.update_arrow_visibility()

    def set_result(self, image_paths: List[str], fragments_inside: List[int], fragments_outside: List[int]):
        test_date = datetime.date.today().strftime("%d %B %Y")
        test_time = datetime.datetime.now().strftime("%H:%M:%S")

        for i, image_path in enumerate(image_paths):
            fragment_inside = fragments_inside[i]
            fragment_outside = fragments_outside[i]
            total_fragments = fragment_inside + (fragment_outside * 0.5)

            status = "PASS" if 40 <= total_fragments <= 400 else "FAIL"

            image_path_full = resource_path(image_path)  # satu per satu

            card_vm = CardViewModel(
            test_name=f"Hasil Deteksi {i + 1}",
            date=test_date,
            time=test_time,
            total_fragments=total_fragments,
            image=image_path_full,
            fragment_inside=fragment_inside,
            fragment_outside=fragment_outside,
            status=status  # Tambahkan ini
        )
            # Simpan data model ke service
            CardService.instance().add_card(card_vm)


        self.cards = CardService.instance().cards
        self.populate_cards()
        self.current_index = self.carousel.count() - 1  # set ke terakhir
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
        for card_vm in self.cards:
            card_widget = CardWidget(card_vm)

            container = QWidget()
            h_layout = QHBoxLayout(container)
            h_layout.setContentsMargins(0, 0, 0, 0)
            h_layout.addStretch()
            h_layout.addWidget(card_widget)
            h_layout.addStretch()

            container.setMinimumWidth(600)
            container.setMinimumHeight(card_widget.sizeHint().height())

            self.carousel.addWidget(container)

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
        if self.main_window:
            self.main_window.go_back()

    def save_button_click(self):
        # Lazy import agar PyInstaller tidak otomatis include HistoryView kecuali dipakai
        from ui.history_view import HistoryView

        for i in range(self.carousel.count()):
            container = self.carousel.widget(i)
            card_widget = container.layout().itemAt(1).widget()  # Ambil CardWidget dari container
            card_vm = card_widget.card_data()
            CardService.instance().save_to_database(card_vm)

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
