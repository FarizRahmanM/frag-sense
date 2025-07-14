from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt
from model.database import get_all_audit_logs

class AuditTrailDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Audit Trail")
        self.resize(700, 400)  # Tambah lebar agar muat kolom nama

        layout = QVBoxLayout(self)

        label = QLabel("Log Aktivitas")
        label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(label)

        table = QTableWidget()
        logs = get_all_audit_logs()

        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Aksi", "Waktu", "Penguji", "Detail"])
        table.setRowCount(len(logs))

        for i, log in enumerate(logs):
            table.setItem(i, 0, QTableWidgetItem(log.get('action', '-')))
            table.setItem(i, 1, QTableWidgetItem(log.get('timestamp', '-')))

            # Nama penguji aman
            tester_name = log.get('tester_name') or "-"
            table.setItem(i, 2, QTableWidgetItem(tester_name))

            detail_item = QTableWidgetItem(log.get('detail', '-'))
            detail_item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            detail_item.setFlags(detail_item.flags() ^ Qt.ItemIsEditable)
            table.setItem(i, 3, detail_item)

        table.setWordWrap(True)
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        layout.addWidget(table) 