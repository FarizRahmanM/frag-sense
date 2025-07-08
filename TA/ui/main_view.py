from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QFileDialog, QSizePolicy, QSpacerItem, QGridLayout, QProgressBar, QInputDialog, QComboBox
)
from PySide6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent, QMouseEvent, QIcon
from PySide6.QtCore import Qt, QTimer, QSize
import os
import cv2
import datetime
from detection.detector import run_detection
from ui.component.header_view import HeaderView
from utils import resource_path
from worker.detection_worker import DetectionWorker
import datetime

class ImageCard(QFrame):
    def __init__(self, image_path, remove_callback):
        super().__init__()
        self.image_path = image_path
        self.remove_callback = remove_callback
        self.setFixedSize(150, 150)
        layout = QVBoxLayout()

        self.image_label = QLabel() 
        abs_path = resource_path(image_path)  # gunakan resource_path
        pixmap = QPixmap(abs_path).scaled(150, 150, Qt.KeepAspectRatio)
        self.image_label.setPixmap(pixmap)

        icon_path = resource_path("material/delete1.png")  # resource_path agar bisa support PyInstaller

        self.remove_btn = QPushButton()
        self.remove_btn.setIcon(QIcon(icon_path))
        self.remove_btn.setIconSize(QSize(16, 16))  # Sesuaikan ukuran ikon
        self.remove_btn.setStyleSheet("background: transparent; border: none;")
        self.remove_btn.clicked.connect(self.remove)

        layout.addWidget(self.image_label)
        layout.addWidget(self.remove_btn)
        self.setLayout(layout)
        

    def remove(self):
        self.setParent(None)
        self.deleteLater()
        self.remove_callback(self.image_path)


class UploadPlaceholder(QPushButton):
    def __init__(self, file_callback):
        super().__init__("Tarik atau klik\nuntuk masukkan gambar")
        self.file_callback = file_callback
        self.setFixedSize(200, 200)
        self.setAcceptDrops(True)
        self.clicked.connect(self.open_files)

        self.setStyleSheet("""
            QPushButton {
                border: 2px solid black;
                border-radius: 8px;
                font-size: 14px;
                background-color: #f0f0f0;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.file_callback(files)

    def open_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Pilih Gambar", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if files:
            self.file_callback(files)


class MainView(QWidget):
    def __init__(self, show_result_callback):
        super().__init__()
        self.show_result_callback = show_result_callback
        self.cards = []
        self.capture = None
        self.timer = None
        self.current_index = 0
        self.detected_outputs = []
        self.detected_inside = []
        self.detected_outside = []
        self.inference_times = []
        self.init_ui()
        self.fragment_button.clicked.connect(self.run_detection_on_images)
        

    def init_ui(self):
        self.setAcceptDrops(True)
        main_layout = QVBoxLayout(self)
        
        self.header = HeaderView()
        self.header.setFixedHeight(80)
        self.header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.header)

        self.back_label = QLabel("← Kembali")
        self.back_label.setVisible(False)
        self.back_label.setStyleSheet("color: #333333; font-size: 14px;")
        self.back_label.mousePressEvent = self.on_back_clicked
        main_layout.addWidget(self.back_label)

        # Upload area
        self.upload_area = QWidget()
        upload_layout = QHBoxLayout()

        self.image_scroll = QScrollArea()
        self.image_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.image_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.image_scroll.setWidgetResizable(True)
        self.image_container = QWidget()
        self.image_container_layout = QGridLayout()
        self.image_container.setLayout(self.image_container_layout)
        self.image_scroll.setWidget(self.image_container)
        self.upload_area.setStyleSheet("background-color: #F6F6F6; border: none;")
        self.image_scroll.setStyleSheet("background-color: #F6F6F6; border: none;")
        self.image_container.setStyleSheet("background-color: #F6F6F6;")
        self.upload_placeholder = UploadPlaceholder(self.handle_dropped_files)

        upload_layout.addWidget(self.image_scroll)
        upload_layout.addWidget(self.upload_placeholder)
        self.upload_area.setLayout(upload_layout)
        main_layout.addWidget(self.upload_area)

        # Camera
        self.camera_feed = QLabel()
        self.camera_feed.setFixedSize(500, 500)
        self.camera_feed.setVisible(False)
        main_layout.addWidget(self.camera_feed, alignment=Qt.AlignCenter)


        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Footer
        self.fragment_button = QPushButton("Hitung Fragmen")
        self.fragment_button.setStyleSheet("padding: 10px; background-color: #CCCCCC; color: #000000 ;")
        main_layout.addWidget(self.fragment_button, alignment=Qt.AlignCenter)

        self.take_photo_label = QLabel("Ambil Foto Langsung")
        self.take_photo_label.setStyleSheet("color: #3B89FF; font-size: 12px;")
        self.take_photo_label.setAlignment(Qt.AlignCenter)
        self.take_photo_label.mousePressEvent = self.take_photo_clicked
        
        self.camera_footer = QHBoxLayout()
        self.camera_footer.addWidget(self.take_photo_label)
        

        # Layout
        main_layout.addLayout(self.camera_footer)
        self.result_card_area = QVBoxLayout()
        main_layout.addLayout(self.result_card_area)


        self.model_dropdown = QComboBox()

        # Ambil semua file .pt dari folder "models"
        model_folder = resource_path("models")
        model_files = []

        if os.path.exists(model_folder):
            model_files = [f for f in os.listdir(model_folder) if f.endswith(".pt")]

        # Tambahkan ke dropdown
        self.model_dropdown.addItems(model_files)

        # Styling
        self.model_dropdown.setStyleSheet("padding: 5px; font-size: 12px;")

        model_layout = QHBoxLayout()
        model_layout.addStretch()
        model_layout.addWidget(QLabel("Pilih Model:"))
        model_layout.addWidget(self.model_dropdown)

        main_layout.addLayout(model_layout)

        # Footer credit
        credit_label = QLabel("Created by: Fariz Rahman & Raihan Shidqi")
        credit_label.setStyleSheet("font-size: 15px; color: gray;")
        credit_label.setAlignment(Qt.AlignLeft)

        credit_layout = QHBoxLayout()
        credit_layout.addWidget(credit_label)
        credit_layout.addStretch()  # Agar tetap di kiri
        main_layout.addLayout(credit_layout)
    
    def back_button_click(self, event):
        self.back_and_clear_cards()

    def back_and_clear_cards(self):
        self.cards.clear()
        self.clear_stack()
        self.current_index = 0
        self.update_arrow_visibility()

        if self.main_window:
            self.main_window.go_back()

    def handle_dropped_files(self, file_paths):
        for path in file_paths:
            if os.path.isfile(path) and path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                self.add_card(path)

    def add_card(self, image_path):
        card = ImageCard(image_path, self.remove_card)
        self.cards.append(image_path)

        # Tentukan posisi grid
        index = len(self.cards) - 1
        col = index % 4   # 4 kolom per baris
        row = index // 4

        self.image_container_layout.addWidget(card, row, col)

        self.fragment_button.setStyleSheet("background-color: #3B89FF; color: white;")

    def remove_card(self, image_path):
        self.cards = [c for c in self.cards if c != image_path]
        self.refresh_grid_layout()

        if not self.cards:
            self.fragment_button.setStyleSheet("background-color: #CCCCCC; color: white;")

    def take_photo_clicked(self, event: QMouseEvent):
        if self.take_photo_label.text() == "Ambil Foto Langsung":
            self.start_camera()
        else:
            self.capture_image()

    def start_camera(self):
        selected_index = self.select_camera_index()
        if selected_index is None:
            print("Tidak ada kamera yang dipilih.")
            return

        self.capture = cv2.VideoCapture(selected_index)
        if not self.capture.isOpened():
            print("Kamera tidak bisa dibuka.")
            return

        self.camera_feed.setVisible(True)
        self.upload_area.setVisible(False)
        self.take_photo_label.setText("Jepret")
        self.take_photo_label.setStyleSheet("color: #3B89FF; font-size: 12px; margin-top: 10px;")
        self.back_label.setVisible(True)
        self.fragment_button.setVisible(False)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_camera_frame)
        self.timer.start(30)

    def update_camera_frame(self):
        ret, frame = self.capture.read()
        if not ret:
            return
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image).scaled(
            self.camera_feed.size(), Qt.KeepAspectRatio
        )
        self.camera_feed.setPixmap(pixmap)


    def capture_image(self):
        ret, frame = self.capture.read()
        if ret:
            captured_folder = self.get_captured_folder()  # ✅ gunakan folder AppData
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"captured_{timestamp}.png"
            image_path = os.path.join(captured_folder, filename)

            cv2.imwrite(image_path, frame)
            self.add_card(image_path)

        self.stop_camera()

    def get_captured_folder(self):
        appdata_dir = os.path.join(os.getenv("APPDATA"), "FragSense")
        captured_folder = os.path.join(appdata_dir, "captured")
        if not os.path.exists(captured_folder):
            os.makedirs(captured_folder)
        return captured_folder

    def stop_camera(self):
        if self.capture:
            self.capture.release()
            self.capture = None
        if self.timer:
            self.timer.stop()
            self.timer = None
        self.camera_feed.clear()
        self.camera_feed.setVisible(False)
        self.upload_area.setVisible(True)
        self.fragment_button.setVisible(True)
        self.take_photo_label.setText("Ambil Foto Langsung")
        self.back_label.setVisible(False)
        
    def run_detection_on_images(self):
        if not self.cards:
            return

        self.current_index = 0
        self.detected_outputs = []
        self.detected_inside = []
        self.detected_outside = []
        self.inference_times = []

        self.progress_bar.setMaximum(len(self.cards))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.fragment_button.setEnabled(False)

        self.process_next_image()

    def process_next_image(self):
        if self.current_index >= len(self.cards):
            # Semua selesai
            self.progress_bar.setVisible(False)
            self.fragment_button.setEnabled(True)

            self.show_result_callback(
                self.detected_outputs,
                self.detected_inside,
                self.detected_outside,
                self.inference_times
            )
            return

        image_path = self.cards[self.current_index]
        abs_path = resource_path(image_path)

        # ✅ Ambil model yang dipilih dari dropdown
        model_name = self.model_dropdown.currentText()

        # ✅ Kirim model_name ke DetectionWorker
        self.worker = DetectionWorker(abs_path, model_name=model_name)
        self.worker.finished.connect(self.on_detection_finished)
        self.worker.error_occurred.connect(self.on_detection_error)
        self.worker.start()


    def on_detection_finished(self, output_path, inside, outside, inference_time):
        self.detected_outputs.append(output_path)
        self.detected_inside.append(inside)
        self.detected_outside.append(outside)
        self.inference_times.append(inference_time)

        self.current_index += 1
        self.progress_bar.setValue(self.current_index)

        self.process_next_image()

    def on_detection_error(self, error_message):
        print("Deteksi gagal:", error_message)
        self.current_index += 1
        self.progress_bar.setValue(self.current_index)
        self.process_next_image()

    def on_back_clicked(self, event: QMouseEvent):
        self.stop_camera()


    def get_available_cameras(self, max_cameras=10):
        available = []
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available

    def select_camera_index(self):
        cameras = self.get_available_cameras()
        if not cameras:
            return None

        items = [f"Kamera {i}" for i in cameras]
        index, ok = QInputDialog.getItem(self, "Pilih Kamera", "Kamera Tersedia:", items, 0, False)
        if ok:
            selected_index = int(index.split()[-1])
            return selected_index
        return None

    def refresh_grid_layout(self):
        # Bersihkan semua item di layout
        while self.image_container_layout.count():
            item = self.image_container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        # Tambahkan ulang semua kartu yang tersisa
        for index, image_path in enumerate(self.cards):
            card = ImageCard(image_path, self.remove_card)
            row = index // 4
            col = index % 4
            self.image_container_layout.addWidget(card, row, col)