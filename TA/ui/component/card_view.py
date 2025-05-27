import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton, QLineEdit, QHBoxLayout
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from utils import resource_path


class CardViewModel:
    def __init__(self,id=None, test_name=None, date=None, time=None, total_fragments=0, image=None,
                 tester_name=None, fragment_inside=0, fragment_outside=0, status=""):
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

    @property
    def total_fragments(self):
        return self.fragment_inside + self.fragment_outside * 0.5


class CardWidget(QWidget):
    def __init__(self, vm: CardViewModel):
        super().__init__()
        self.vm = vm

        self.setFixedHeight(500)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        outer = QWidget()
        outer_layout = QGridLayout()
        outer.setLayout(outer_layout)
        outer.setStyleSheet("background-color: #F0F0F0; border-radius: 15px;")
        outer.setFixedSize(800, 400)

        # Kiri: Gambar
        image_label = QLabel()
        pixmap = QPixmap(resource_path(self.vm.image_path)) if self.vm.image_path else QPixmap()
        image_label.setPixmap(pixmap.scaledToHeight(220))
        image_label.setFixedWidth(445)
        image_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        left_container = QVBoxLayout()
        left_container.addWidget(image_label)
        left_widget = QWidget()
        left_widget.setLayout(left_container)
        left_widget.setFixedWidth(445)

        # Kanan: Form
        form_layout = QVBoxLayout()

        # Nama Hasil Uji
        label_uji = QLabel("Nama Hasil Uji")
        self.input_uji = QLineEdit(self.vm.test_name or "")

        # Nama Penguji
        label_penguji = QLabel("Nama Penguji")
        self.input_penguji = QLineEdit(self.vm.tester_name or "")

        # Fragmen Inside
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

        # Fragmen Outside
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

        # Tambah ke layout kanan
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

        

    def update_counts(self):
        total = self.vm.fragment_inside + 0.5 * self.vm.fragment_outside
        self.fragmen_inside_count.setText(str(self.vm.fragment_inside))
        self.fragmen_outside_count.setText(str(self.vm.fragment_outside))
        self.total_fragmen_label.setText(f"{total:.1f}")
        self.vm.jumlah_fragmen = total

        # Update status label
        if 40 <= total <= 400:
            self.status_label.setText("PASS")
            self.status_label.setStyleSheet("color: green; font-size: 20px; font-weight: bold;")
        else:
            self.status_label.setText("FAIL")
            self.status_label.setStyleSheet("color: red; font-size: 20px; font-weight: bold;")

    def increment_fragmen_inside(self):
        self.vm.fragment_inside += 1
        self.update_counts()

    def decrement_fragmen_inside(self):
        if self.vm.fragment_inside > 0:
            self.vm.fragment_inside -= 1
        self.update_counts()

    def increment_fragmen_outside(self):
        self.vm.fragment_outside += 1
        self.update_counts()

    def decrement_fragmen_outside(self):
        if self.vm.fragment_outside > 0:
            self.vm.fragment_outside -= 1
        self.update_counts()

    

    def card_data(self):
        self.vm.test_name = self.input_uji.text()
        self.vm.tester_name = self.input_penguji.text()
        print(f"DEBUG: Saving Card: test_name={self.vm.test_name}, tester_name={self.vm.tester_name}, inside={self.vm.fragment_inside}, outside={self.vm.fragment_outside}")
        return self.vm
    
    
