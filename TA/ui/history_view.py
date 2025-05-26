from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PySide6.QtCore import Qt, Slot
from ui.component.header_view import HeaderView
from ui.component.table_view import TableWidget
from ui.component.delete_view import DeleteDialog
from services.card_service import CardService
from model.database import get_all_detections, delete_detection
from ui.component.card_view import CardViewModel

class HistoryView(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        
        main_layout = QVBoxLayout(self)

        header = HeaderView()
        main_layout.addWidget(header)

        self.delete_dialog = DeleteDialog(self)
        self.delete_dialog.accepted.connect(self.on_delete_confirmed)
        self.delete_dialog.rejected.connect(self.on_delete_canceled)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 20, 40, 20)
        content_layout.setSpacing(24)

        back_btn = QLabel("← Beranda")
        back_btn.setStyleSheet("color: #333; font-size: 14px;")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.mousePressEvent = self.back_button_click
        content_layout.addWidget(back_btn)

        title = QLabel("Riwayat Pengujian")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        content_layout.addWidget(title)

        raw_cards = get_all_detections()
        card_viewmodels = [
            CardViewModel(
                id=row.id,
                test_name=row.test_name,
                tester_name=row.tester_name,
                fragment_inside=row.fragment_inside,
                fragment_outside=row.fragment_outside,
                image=row.image_path,
                date=row.test_time.strftime("%d %B %Y"),
                time=row.test_time.strftime("%H:%M:%S"),
            )
            for row in raw_cards
        ]

        self.table = TableWidget(card_viewmodels)
        self.table.delete_requested.connect(self.on_table_delete_requested)
        self.table.info_requested.connect(self.on_table_info_requested)
        content_layout.addWidget(self.table)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Panggil load_data() atau reload_table() setelah self.table sudah ada
        self.reload_table()

    @Slot(object)
    def on_table_delete_requested(self, card):
        self.card_to_delete = card
        self.delete_dialog.open()


    @Slot()
    def on_delete_confirmed(self):
        if self.card_to_delete:
            # Ambil data detection berdasarkan nama dan waktu
            raw_cards = get_all_detections()
            for row in raw_cards:
                if (
                    row.test_name == self.card_to_delete.test_name
                    and row.tester_name == self.card_to_delete.tester_name
                    and row.test_time.strftime("%d %B %Y") == self.card_to_delete.test_date
                    and row.test_time.strftime("%H:%M:%S") == self.card_to_delete.test_time
                ):
                    delete_detection(row.id)
                    break

            # Refresh tampilan
            self.reload_table()
            self.card_to_delete = None
            self.delete_dialog.close()

    @Slot()
    def on_delete_canceled(self):
        self.delete_dialog.close()

    def back_button_click(self, event):
        if self.main_window:
            # Navigasi kembali ke main_view yang sudah dibuat di MainWindow
            self.main_window.navigate(self.main_window.main_view)
            
    def reload_table(self):
        raw_cards = get_all_detections()
        card_viewmodels = [
            CardViewModel(
                id=row.id,
                test_name=row.test_name,
                tester_name=row.tester_name,
                fragment_inside=row.fragment_inside,
                fragment_outside=row.fragment_outside,
                image=row.image_path,
                date=row.test_time.strftime("%d %B %Y"),
                time=row.test_time.strftime("%H:%M:%S"),
            )
            for row in raw_cards
        ]
        self.table.cards = card_viewmodels
        self.table.populate_cards()
        
    def on_table_info_requested(self, card):
        from ui.detail_view import DetailView  # Pastikan import sesuai dengan struktur proyekmu
        detail_view = DetailView(main_window=self.main_window, selected_card=card)
        if self.main_window:
            self.main_window.navigate(detail_view)

    def load_data(self):
        self.records = CardService.instance().get_all_from_db()
        self.populate_table()

    def populate_table(self):
        if hasattr(self, 'table'):
            self.table.cards = self.records
            self.table.populate_cards()
            
    def refresh(self):
        self.load_data()
