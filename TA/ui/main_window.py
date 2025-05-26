from PySide6.QtWidgets import QMainWindow, QStackedWidget
from ui.main_view import MainView
from ui.history_view import HistoryView
from ui.result_view import ResultView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Buat view sekali saja, kirim self supaya bisa panggil navigate()
        self.main_view = MainView(self.show_result)
        self.history_view = HistoryView(main_window=self)
        self.result_view = ResultView(main_window=self)

        # Tambahkan semua widget ke stack
        self.stack.addWidget(self.main_view)
        self.stack.addWidget(self.history_view)
        self.stack.addWidget(self.result_view)

        # Hubungkan signal tombol riwayat dari MainView/HeaderView ke method show_history
        self.main_view.header.history_clicked.connect(self.show_history)

        # Set halaman awal
        self.stack.setCurrentWidget(self.main_view)

    def navigate(self, widget):
        """Navigasi ke widget yang sudah ada di stack"""
        if self.stack.indexOf(widget) == -1:
            self.stack.addWidget(widget)
        self.stack.setCurrentWidget(widget)

    def show_history(self):
        self.history_view.refresh()  # reload data terbaru
        self.navigate(self.history_view)

    def show_result(self, image_paths, fragments_inside, fragments_outside):
        self.result_view.set_result(image_paths, fragments_inside, fragments_outside)
        self.navigate(self.result_view)

    def go_back(self):
        """Contoh method untuk kembali ke halaman utama"""
        self.navigate(self.main_view)
        
    def go_back_from_detail(self):
        """Navigasi kembali ke history_view khusus dari detail_view"""
        self.navigate(self.history_view)