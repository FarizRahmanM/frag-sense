from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QFileDialog, QSizePolicy, QSpacerItem
)
from PySide6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent, QMouseEvent
from PySide6.QtCore import Qt, QTimer
import cv2
import os
from detection.detector import run_detection
from ui.component.header_view import HeaderView
from utils import resource_path
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

        self.remove_btn = QPushButton("X")
        self.remove_btn.setStyleSheet("color: red; background: transparent; border: none;")
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
        self.image_scroll.setWidgetResizable(True)
        self.image_container = QWidget()
        self.image_container_layout = QHBoxLayout()
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

        # Footer
        self.fragment_button = QPushButton("Hitung Fragmen")
        self.fragment_button.setStyleSheet("padding: 10px; background-color: #CCCCCC; color: white;")
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
        self.image_container_layout.addWidget(card)
        self.fragment_button.setStyleSheet("background-color: #3B89FF; color: white;")

    def remove_card(self, image_path):
        self.cards = [c for c in self.cards if c != image_path]
        if not self.cards:
            self.fragment_button.setStyleSheet("background-color: #CCCCCC; color: white;")

    def take_photo_clicked(self, event: QMouseEvent):
        if self.take_photo_label.text() == "Ambil Foto Langsung":
            self.start_camera()
        else:
            self.capture_image()

    def start_camera(self):
        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            print("Kamera tidak tersedia.")
            return

        self.camera_feed.setVisible(True)
        self.upload_area.setVisible(False)
        self.take_photo_label.setText("Jepret")
        self.take_photo_label.setStyleSheet("color: #3B89FF; font-size: 12px; margin-top: 10px;")
        self.back_label.setVisible(True)

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
            # Buat folder "captured" jika belum ada
            captured_folder = os.path.join(os.getcwd(), "captured")
            if not os.path.exists(captured_folder):
                os.makedirs(captured_folder)

            # Buat nama file unik dengan timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"captured_{timestamp}.png"
            image_path = os.path.join(captured_folder, filename)

            # Simpan gambar
            cv2.imwrite(image_path, frame)

            # Tambahkan ke UI
            self.add_card(image_path)

        self.stop_camera()

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
        self.take_photo_label.setText("Ambil Foto Langsung")
        self.back_label.setVisible(False)
        
    def run_detection_on_images(self):
        if not self.cards:
            return

        image_paths = []
        fragments_inside = []
        fragments_outside = []

        for image_path in self.cards:
            abs_path = resource_path(image_path)
            output_path, fragment_inside, fragment_outside = run_detection(abs_path)
            image_paths.append(output_path)
            fragments_inside.append(fragment_inside)
            fragments_outside.append(fragment_outside)

        self.show_result_callback(image_paths, fragments_inside, fragments_outside)
            
        

    def on_back_clicked(self, event: QMouseEvent):
        self.stop_camera()
