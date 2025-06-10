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
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        title_row = QGridLayout()
        title_row.setColumnStretch(0, 1)
        title_row.setColumnStretch(1, 1)  
        title_row.setColumnStretch(2, 1)  
        title_row.setColumnStretch(3, 1)  
        title_row.setColumnStretch(4, 1)    
        title_row.setColumnStretch(5, 1)    
        title_row.setColumnStretch(6, 0)  

        title_row.addWidget(QLabel(""), 0, 0, Qt.AlignCenter)
        title_row.addWidget(QLabel("Pengujian"), 0, 0.5, Qt.AlignCenter)
        title_row.addWidget(QLabel("Tanggal"), 0, 1.7, Qt.AlignCenter)
        title_row.addWidget(QLabel("Waktu"), 0, 2.7, Qt.AlignCenter)
        title_row.addWidget(QLabel("Jumlah Fragmen"), 0, 3.8, Qt.AlignCenter)
        title_row.addWidget(QLabel("Aksi"), 0, 5.5, Qt.AlignCenter)
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
            self.add_card(card)

    def add_card(self, card):
        container = QFrame()
        container.setFrameShape(QFrame.StyledPanel)
        container.setMinimumHeight(100)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        grid = QGridLayout(container)
        grid.setContentsMargins(10, 5, 10, 5)
        grid.setColumnStretch(0, 0.5)  # Checkbox
        grid.setColumnStretch(1, 2.8)  # Pengujian
        grid.setColumnStretch(2, 2.5)    # Tanggal
        grid.setColumnStretch(3, 3.5)    # Waktu
        grid.setColumnStretch(4, 5.7)    # Jumlah Fragmen
        grid.setColumnStretch(5, 1)    # Spacer
        grid.setColumnStretch(6, 1)    # Aksi

        # === Kolom 0: Checkbox ===
        checkbox = QCheckBox()
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
        self.checkbox_map[card] = checkbox

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

        # === Kolom 5: Spacer ===
        spacer = QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)
        grid.addItem(spacer, 0, 5)

        # === Kolom 6: Aksi ===
        button_layout = QHBoxLayout()
        delete_btn = QPushButton("Delete")
        info_btn = QPushButton("Info")
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(info_btn)
        button_layout.setAlignment(Qt.AlignCenter)
        grid.addLayout(button_layout, 0, 6)

        # === Tombol Event ===
        delete_btn.clicked.connect(lambda _, c=card: self.delete_requested.emit(c))
        info_btn.clicked.connect(lambda _, c=card: self.info_requested.emit(c))

        self.cards_layout.addWidget(container)

    def get_selected_cards(self):
        selected = []
        for card, checkbox in self.checkbox_map.items():
            if checkbox.isChecked():
                selected.append(card)
        return selected
