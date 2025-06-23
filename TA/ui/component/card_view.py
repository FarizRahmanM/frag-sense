import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton, QLineEdit,
    QHBoxLayout, QDialog, QComboBox, QSizePolicy
)
from PySide6.QtGui import QPixmap, QPainter, QPen
from PySide6.QtCore import Qt, Signal
from utils import resource_path
import re

# Label custom agar bisa diklik
class ClickableLabel(QLabel):
    clicked = Signal(object)

    def mousePressEvent(self, event):
        self.clicked.emit(event)


class CardViewModel:
    def __init__(self, id=None, test_name=None, date=None, time=None, total_fragments=0, image=None,
                 tester_name=None, fragment_inside=0, fragment_outside=0, status="", last_edited=None, tester_id=None, inference_time=None):
        self.id = id
        self.test_name = test_name
        self.test_date = date  # ❌ Hapus fallback waktu sekarang
        self.test_time = time  # ❌ Jangan isi otomatis
        self.jumlah_fragmen = total_fragments
        self.image_path = image
        self.tester_id = tester_id
        self.tester_name = tester_name
        self.fragment_inside = fragment_inside
        self.fragment_outside = fragment_outside
        self.status = status
        self.last_edited = last_edited or datetime.datetime.now()
        self.inference_time = inference_time or 0.0
        
    @property
    def total_fragments(self):
        return self.fragment_inside + self.fragment_outside * 0.5


class CardWidget(QWidget):
    validity_changed = Signal(bool)
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
        self.tester_map = {}  # id -> name
        self.input_penguji.clear()

        from model.database import get_all_testers
        for tester_id, name in get_all_testers():
            self.input_penguji.addItem(name, userData=tester_id)
            self.tester_map[name] = tester_id

        # Set nilai awal
        if self.vm.tester_name:
            index = self.input_penguji.findText(self.vm.tester_name)
            if index != -1:
                self.input_penguji.setCurrentIndex(index)
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

        # Label waktu inference
        self.inference_time_label = QLabel()
        self.inference_time_label.setStyleSheet("font-size: 12px; color: black; font-weight: bold;")
        self.update_inference_time_label()
        waktu_layout.addWidget(self.inference_time_label)
                

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
        self.input_uji.textChanged.connect(self.validate_test_name)
        self.validate_test_name()
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
        self.vm.tester_id = self.input_penguji.currentData()
        
        if not self.vm.test_time:
            self.vm.test_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        print(f"DEBUG: Saving Card: test_name={self.vm.test_name}, tester_id={self.vm.tester_id}, inside={self.vm.fragment_inside}, outside={self.vm.fragment_outside}, test_time={self.vm.test_time}")
        
        self.vm.last_edited = datetime.datetime.now()
        return self.vm
        
    def update_last_edited_time(self, init=False):
        # Jangan ubah self.vm.last_edited di sini!
        last_edited_display = self.vm.last_edited
        if not init:
            last_edited_display = datetime.datetime.now()

        if isinstance(last_edited_display, str):
            try:
                last_edited_display = datetime.datetime.fromisoformat(last_edited_display)
            except ValueError:
                last_edited_display = datetime.datetime.now()

        last_edit_str = (
            f"Terakhir diubah: {last_edited_display.strftime('%d %B %Y %H:%M:%S')}"
            if last_edited_display else "Terakhir diubah: -"
        )
        self.last_edited_label.setText(last_edit_str)
    
    def update_inference_time_label(self):
        if self.vm.inference_time is not None:
            self.inference_time_label.setText(f"Waktu Inference: {self.vm.inference_time:.3f} detik")
        else:
            self.inference_time_label.setText("Waktu Inference: -")
    
    def validate_test_name(self):
        text = self.input_uji.text()
        pattern = r"^\d{2}-\d{1,2}/[A-Z0-9]+/[A-Z]{2}-\d{2}/20\d{2}$"
        match = re.match(pattern, text)

        # Validasi bulan dan tahun
        valid = False
        if match:
            try:
                bagian = text.split("/")
                bulan = int(bagian[2].split("-")[1])
                tahun = bagian[3]
                valid = 1 <= bulan <= 12 and len(tahun) == 4
            except:
                valid = False

        # 🌟 Tambahkan feedback visual
        if not text.strip():  # kosong
            border_color = "black"
        elif valid:
            border_color = "green"
        else:
            border_color = "red"

        self.input_uji.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {border_color};
                border-radius: 4px;
                padding: 4px;
            }}
        """)

        # Kirim sinyal
        self.validity_changed.emit(valid)

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
    
