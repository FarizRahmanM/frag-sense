import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton, QLineEdit,
    QHBoxLayout, QDialog, QComboBox, QSizePolicy
)
from PySide6.QtGui import QPixmap, QPainter, QPen
from PySide6.QtCore import Qt, Signal
from utils import resource_path


# Label custom agar bisa diklik
class ClickableLabel(QLabel):
    clicked = Signal(object)

    def mousePressEvent(self, event):
        self.clicked.emit(event)


class CardViewModel:
    def __init__(self, id=None, test_name=None, date=None, time=None, total_fragments=0, image=None,
                 tester_name=None, fragment_inside=0, fragment_outside=0, status="", last_edited=None):
        self.id = id
        self.test_name = test_name
        self.test_date = date or datetime.date.today().strftime("%d %B %Y")
        self.test_time = time or datetime.datetime.now().strftime("%H:%M:%S")
        self.jumlah_fragmen = total_fragments
        self.image_path = image
        self.tester_name = tester_name
        self.fragment_inside = fragment_inside
        self.fragment_outside = fragment_outside
        self.status = status
        self.last_edited = last_edited or datetime.datetime.now()
        
    @property
    def total_fragments(self):
        return self.fragment_inside + self.fragment_outside * 0.5


class CardWidget(QWidget):
    def __init__(self, vm: CardViewModel):
        super().__init__()
        self.vm = vm

        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        outer = QWidget()
        outer_layout = QGridLayout()
        outer.setLayout(outer_layout)
        outer.setStyleSheet("background-color: #F0F0F0; border-radius: 15px;")
        outer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Kiri: Gambar
        self.image_label = ClickableLabel()
        pixmap = QPixmap(resource_path(self.vm.image_path)) if self.vm.image_path else QPixmap()
        self.image_label.setPixmap(pixmap.scaled(400, 220, Qt.KeepAspectRatio))
        self.image_label.setFixedWidth(445)
        self.image_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Koneksi klik ke pop-up
        self.image_label.clicked.connect(self.show_image_popup)

        left_container = QVBoxLayout()
        left_container.addWidget(self.image_label)
        left_widget = QWidget()
        left_widget.setLayout(left_container)
        left_widget.setFixedWidth(445)

        # Kanan: Form
        form_layout = QVBoxLayout()
        

        # Nama Hasil Uji
        label_uji = QLabel("Nama Hasil Uji")
        self.input_uji = QLineEdit(self.vm.test_name or "")
        self.input_uji.setStyleSheet("""
            QLineEdit {
                border: 2px solid black;
                border-radius: 4px;
                padding: 4px;
            }
        """)

        # Nama Penguji
        label_penguji = QLabel("Nama Penguji")
        self.input_penguji = QComboBox()
        self.input_penguji.addItems([
            "G. Agus Permana Putra Sujana",
            "Sumarlin Manalu",
            "Adi Irawan",
            "Rivaldi Pamungkas",
            "Chandra Taufik Rahman"
        ])
        self.input_penguji.setStyleSheet("""
            QComboBox {
                border: 2px solid black;
                border-radius: 4px;
                padding: 4px;
            }
        """)

        # Set nilai awal jika ada data sebelumnya
        if self.vm.tester_name:
            index = self.input_penguji.findText(self.vm.tester_name)
            if index != -1:
                self.input_penguji.setCurrentIndex(index)

        # Fragmen Dalam
        fragmen_inside_label = QLabel("Fragmen Dalam")
        self.fragmen_inside_count = QLabel(str(self.vm.fragment_inside))
        self.fragmen_inside_count.setAlignment(Qt.AlignCenter)
        self.fragmen_inside_count.setStyleSheet("font-size: 25px; font-weight: bold;")

        inside_minus_btn = QPushButton("-")
        inside_minus_btn.clicked.connect(self.decrement_fragmen_inside)
        inside_plus_btn = QPushButton("+")
        inside_plus_btn.clicked.connect(self.increment_fragmen_inside)

        fragmen_inside_layout = QHBoxLayout()
        fragmen_inside_layout.addWidget(inside_minus_btn)
        fragmen_inside_layout.addWidget(self.fragmen_inside_count)
        fragmen_inside_layout.addWidget(inside_plus_btn)

        # Fragmen Tepi
        fragmen_outside_label = QLabel("Fragmen Tepi")
        self.fragmen_outside_count = QLabel(str(self.vm.fragment_outside))
        self.fragmen_outside_count.setAlignment(Qt.AlignCenter)
        self.fragmen_outside_count.setStyleSheet("font-size: 25px; font-weight: bold;")

        outside_minus_btn = QPushButton("-")
        outside_minus_btn.clicked.connect(self.decrement_fragmen_outside)
        outside_plus_btn = QPushButton("+")
        outside_plus_btn.clicked.connect(self.increment_fragmen_outside)

        fragmen_outside_layout = QHBoxLayout()
        fragmen_outside_layout.addWidget(outside_minus_btn)
        fragmen_outside_layout.addWidget(self.fragmen_outside_count)
        fragmen_outside_layout.addWidget(outside_plus_btn)

        # Total fragmen (read-only)
        total_label = QLabel("Jumlah Fragmen Total")
        self.total_fragmen_label = QLabel(str(self.vm.fragment_inside + self.vm.fragment_outside))
        self.total_fragmen_label.setAlignment(Qt.AlignCenter)
        self.total_fragmen_label.setStyleSheet("font-size: 25px; font-weight: bold;")

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 20px; font-weight: bold;")

        # Waktu
        waktu_layout = QVBoxLayout()
        waktu_layout.addWidget(QLabel(self.vm.test_date))
        waktu_layout.addWidget(QLabel(self.vm.test_time))

        
        # Tambahkan label waktu update
        self.last_edited_label = QLabel()
        self.last_edited_label.setStyleSheet("font-size: 12px; color: black; font-weight: bold;")
        self.update_last_edited_time(init=True) 
        waktu_layout.addWidget(self.last_edited_label)
        

        # Tambahkan ke form layout
        form_layout.addWidget(label_uji)
        form_layout.addWidget(self.input_uji)
        form_layout.addSpacing(10)
        form_layout.addWidget(label_penguji)
        form_layout.addWidget(self.input_penguji)
        form_layout.addSpacing(15)
        form_layout.addWidget(fragmen_inside_label)
        form_layout.addLayout(fragmen_inside_layout)
        form_layout.addSpacing(10)
        form_layout.addWidget(fragmen_outside_label)
        form_layout.addLayout(fragmen_outside_layout)
        form_layout.addSpacing(10)
        form_layout.addWidget(total_label)
        form_layout.addWidget(self.total_fragmen_label)
        form_layout.addWidget(self.status_label)
        form_layout.addSpacing(15)
        form_layout.addLayout(waktu_layout)

        # Pasang ke grid
        outer_layout.addWidget(left_widget, 0, 0)
        outer_layout.addLayout(form_layout, 0, 1)
        self.update_counts()
        self.layout.addWidget(outer)
        self.input_uji.textChanged.connect(self.update_last_edited_time)
        self.input_penguji.currentIndexChanged.connect(self.update_last_edited_time)

    def update_counts(self):
        total = self.vm.fragment_inside + 0.5 * self.vm.fragment_outside
        self.fragmen_inside_count.setText(str(self.vm.fragment_inside))
        self.fragmen_outside_count.setText(str(self.vm.fragment_outside))
        self.total_fragmen_label.setText(f"{total:.1f}")
        self.vm.jumlah_fragmen = total

        # Update status
        if 40 <= total <= 400:
            self.status_label.setText("PASS")
            self.status_label.setStyleSheet("color: green; font-size: 20px; font-weight: bold;")
        else:
            self.status_label.setText("FAIL")
            self.status_label.setStyleSheet("color: red; font-size: 20px; font-weight: bold;")

    def increment_fragmen_inside(self):
        self.vm.fragment_inside += 1
        self.update_counts()
        self.update_last_edited_time()

    def decrement_fragmen_inside(self):
        if self.vm.fragment_inside > 0:
            self.vm.fragment_inside -= 1
        self.update_counts()
        self.update_last_edited_time()

    def increment_fragmen_outside(self):
        self.vm.fragment_outside += 1
        self.update_counts()
        self.update_last_edited_time()

    def decrement_fragmen_outside(self):
        if self.vm.fragment_outside > 0:
            self.vm.fragment_outside -= 1
        self.update_counts()
        self.update_last_edited_time()

    def show_image_popup(self, event):
        if not self.vm.image_path:
            return

        popup = ImagePopup(self.vm.image_path)
        popup.exec()

    def card_data(self):
        self.vm.test_name = self.input_uji.text()
        self.vm.tester_name = self.input_penguji.currentText()
        print(f"DEBUG: Saving Card: test_name={self.vm.test_name}, tester_name={self.vm.tester_name}, inside={self.vm.fragment_inside}, outside={self.vm.fragment_outside}")
        return self.vm
        
    def update_last_edited_time(self, init=False):
        print("DEBUG - last_edited di UI:", self.vm.last_edited)

        
        if isinstance(self.vm.last_edited, str):
            try:
                self.vm.last_edited = datetime.datetime.fromisoformat(self.vm.last_edited)
            except ValueError:
                self.vm.last_edited = datetime.datetime.now()

        if not init:
            self.vm.last_edited = datetime.datetime.now()

        last_edit_str = (
            f"Terakhir diubah: {self.vm.last_edited.strftime('%d %B %Y %H:%M:%S')}"
            if self.vm.last_edited else "Terakhir diubah: -"
        )
        self.last_edited_label.setText(last_edit_str)

class ImagePopup(QDialog):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Perbesar Gambar")
        self.setStyleSheet("background-color: white;")

        self.pixmap = QPixmap(resource_path(image_path))
        self.grid_enabled = False

        self.image_label = QLabel()
        self.image_label.setPixmap(self.pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)

        self.grid_checkbox = QPushButton("Tampilkan Grid")
        self.grid_checkbox.setCheckable(True)
        self.grid_checkbox.clicked.connect(self.toggle_grid)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.grid_checkbox)
        self.setLayout(layout)

        self.update_image()

    def toggle_grid(self):
        self.grid_enabled = not self.grid_enabled
        self.grid_checkbox.setText("Sembunyikan Grid" if self.grid_enabled else "Tampilkan Grid")
        self.update_image()

    def update_image(self):
        if not self.grid_enabled:
            self.image_label.setPixmap(self.pixmap)
            return

        temp_pixmap = QPixmap(self.pixmap)
        painter = QPainter(temp_pixmap)
        pen = QPen(Qt.red, 1, Qt.SolidLine)
        painter.setPen(pen)

        step = 128  # contoh jarak antar garis grid, sesuaikan
        width = temp_pixmap.width()
        height = temp_pixmap.height()

        for x in range(0, width, step):
            painter.drawLine(x, 0, x, height)
        for y in range(0, height, step):
            painter.drawLine(0, y, width, y)

        painter.end()
        self.image_label.setPixmap(temp_pixmap)