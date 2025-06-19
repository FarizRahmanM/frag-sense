from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QHBoxLayout,
    QPushButton, QGridLayout, QSizePolicy, QSpacerItem, QCheckBox
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Signal, Qt
from utils import resource_path

class TableWidget(QWidget):
    delete_requested = Signal(object)
    info_requested = Signal(object)

    def __init__(self, cards=None):
        super().__init__()
        self.cards = cards or []
        self.checkbox_map = {}
        self.card_selection_map = {}
        self.card_data_map = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        title_row = QGridLayout()
        title_row.setColumnStretch(0, 1)  # Checkbox
        title_row.setColumnStretch(1, 3)  # Nama Pengujian (dengan gambar)
        title_row.setColumnStretch(2, 2)  # Tanggal
        title_row.setColumnStretch(3, 2)  # Waktu
        title_row.setColumnStretch(4, 2)  # Jumlah Fragmen
        title_row.setColumnStretch(5, 2)  # Nama Penguji
        title_row.setColumnStretch(6, 2)  # Hasil Uji
        title_row.setColumnStretch(7, 2)  # Aksi 

        # Ganti label pertama dari "Nama Pengujian" menjadi Checkbox Select All
        self.select_all_checkbox = QCheckBox()
        self.select_all_checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #888;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d7;
                border: 1px solid #005999;
            }
        """)
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)

        title_row.addWidget(self.select_all_checkbox, 0, 0, Qt.AlignCenter)
        title_row.addWidget(QLabel("Nama Pengujian"), 0, 1, Qt.AlignCenter)
        title_row.addWidget(QLabel("Tanggal"), 0, 2, Qt.AlignCenter)
        title_row.addWidget(QLabel("Waktu"), 0, 3, Qt.AlignCenter)
        title_row.addWidget(QLabel("Jumlah Fragmen"), 0, 4, Qt.AlignCenter)
        title_row.addWidget(QLabel("Nama Penguji"), 0, 5, Qt.AlignCenter)
        title_row.addWidget(QLabel("Hasil Uji"), 0, 6, Qt.AlignCenter)    
        title_row.addWidget(QLabel("Aksi"), 0, 7, Qt.AlignCenter)
        layout.addLayout(title_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(5)
        self.cards_container.setLayout(self.cards_layout)
        scroll.setWidget(self.cards_container)

        layout.addWidget(scroll)
        self.populate_cards()

    def populate_cards(self):
        for i in reversed(range(self.cards_layout.count())):
            widget = self.cards_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        self.checkbox_map = {}

        for card in self.cards:
            card_id = card.id  # <- pakai id unik
            self.card_data_map[card_id] = card

            if card_id not in self.card_selection_map:
                self.card_selection_map[card_id] = False

            self.add_card(card, card_id)

        # Connect AFTER all checkboxes added
        self.select_all_checkbox.stateChanged.disconnect()
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)

    def add_card(self, card, card_id):
        container = QFrame()
        container.setFrameShape(QFrame.StyledPanel)
        container.setMinimumHeight(100)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        grid = QGridLayout(container)
        grid.setColumnStretch(0, 1)  # Checkbox
        grid.setColumnStretch(1, 3)  # Nama Pengujian
        grid.setColumnStretch(2, 2)  # Tanggal
        grid.setColumnStretch(3, 2)  # Waktu
        grid.setColumnStretch(4, 2)  # Jumlah Fragmen
        grid.setColumnStretch(5, 2)  # Nama Penguji
        grid.setColumnStretch(6, 2)  # Status
        grid.setColumnStretch(7, 2)  # Aksi

        # === Kolom 0: Checkbox ===
        checkbox = QCheckBox()
        is_checked = self.card_selection_map.get(card_id, False)
        checkbox.setChecked(is_checked)
        checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #888;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d7;
                border: 1px solid #005999;
            }
        """)
        grid.addWidget(checkbox, 0, 0, alignment=Qt.AlignCenter)
        checkbox.stateChanged.connect(lambda state, c_id=card_id: self.checkbox_state_changed(c_id, state))
        self.checkbox_map[card_id] = checkbox

        # === Kolom 1: Pengujian (Nama & Gambar) ===
        pengujian_layout = QVBoxLayout()
        pengujian_layout.setAlignment(Qt.AlignCenter)
        nama_label = QLabel(card.test_name)
        nama_label.setAlignment(Qt.AlignCenter)

        image_label = QLabel()
        image_label.setFixedSize(60, 60)
        if card.image_path:
            pixmap = QPixmap(resource_path(card.image_path))
            if not pixmap.isNull():
                pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                pixmap = QPixmap(60, 60)
                pixmap.fill(Qt.gray)
        else:
            pixmap = QPixmap(60, 60)
            pixmap.fill(Qt.gray)
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignCenter)

        pengujian_layout.addWidget(nama_label)
        pengujian_layout.addWidget(image_label)
        pengujian_widget = QWidget()
        pengujian_widget.setLayout(pengujian_layout)
        grid.addWidget(pengujian_widget, 0, 1)

        # === Kolom 2: Tanggal ===
        tanggal_label = QLabel(card.test_date)
        tanggal_label.setAlignment(Qt.AlignCenter)
        grid.addWidget(tanggal_label, 0, 2)

        # === Kolom 3: Waktu ===
        waktu_label = QLabel(card.test_time)
        waktu_label.setAlignment(Qt.AlignCenter)
        grid.addWidget(waktu_label, 0, 3)

        # === Kolom 4: Jumlah Fragmen ===
        fragmen_label = QLabel(str(card.total_fragments))
        fragmen_label.setAlignment(Qt.AlignCenter)
        grid.addWidget(fragmen_label, 0, 4)

        # === Kolom 5: Nama Penguji ===
        tester_label = QLabel(card.tester_name)
        tester_label.setAlignment(Qt.AlignCenter)
        grid.addWidget(tester_label, 0, 5)


        # === Kolom 6: Hasil (Pass/Fail) ===
        status_label = QLabel(card.status)
        status_label.setAlignment(Qt.AlignCenter)

        # Tambahkan warna (opsional)
        status_clean = card.status.strip().lower()
        if status_clean == "pass":
            status_label.setStyleSheet("color: green; font-weight: bold;")
        elif status_clean == "fail":
            status_label.setStyleSheet("color: red; font-weight: bold;")

        grid.addWidget(status_label, 0, 6)

        # === Kolom 7: Aksi ===
        button_layout = QHBoxLayout()
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid black;
                padding: 5px 10px;
            }
        """)

        info_btn = QPushButton("Info")
        info_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid black;
                padding: 5px 10px;
            }
        """)

        button_layout.addWidget(delete_btn)
        button_layout.addWidget(info_btn)
        button_layout.setAlignment(Qt.AlignCenter)
        grid.addLayout(button_layout, 0, 7)

        # === Tombol Event ===
        delete_btn.clicked.connect(lambda _, c=card: self.delete_requested.emit(c))
        info_btn.clicked.connect(lambda _, c=card: self.info_requested.emit(c))

        self.cards_layout.addWidget(container)

    def get_selected_cards(self):
        return [self.card_data_map[cid] for cid, selected in self.card_selection_map.items() if selected]
        
    def toggle_select_all(self, state):
        check = (state == Qt.Checked.value)
        print(f"Toggle select all: {check}, checkbox map size: {len(self.checkbox_map)}")

        # Update semua status di card_selection_map (semua data)
        for card_id in self.card_selection_map:
            self.card_selection_map[card_id] = check

        # Hanya checkbox yang tampil (di halaman aktif) yang bisa diset langsung
        for card_id, checkbox in self.checkbox_map.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(check)
            checkbox.blockSignals(False)

        self.update_select_all_state(state)
        
    def update_select_all_state(self, _):
        all_checked = all(self.card_selection_map.values())
        any_checked = any(self.card_selection_map.values())
        print(f"update_select_all_state called: all_checked={all_checked}, any_checked={any_checked}")

        self.select_all_checkbox.blockSignals(True)
        if all_checked:
            self.select_all_checkbox.setCheckState(Qt.Checked)
        elif any_checked:
            self.select_all_checkbox.setCheckState(Qt.PartiallyChecked)
        else:
            self.select_all_checkbox.setCheckState(Qt.Unchecked)
        self.select_all_checkbox.blockSignals(False)

    def checkbox_state_changed(self, card_id, state):
        self.card_selection_map[card_id] = (state == Qt.Checked)
        self.update_select_all_state(state)
