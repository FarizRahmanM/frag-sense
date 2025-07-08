from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt
from model.database import get_all_audit_logs

class AuditTrailDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Audit Trail")
        self.resize(600, 400)  # Ukuran lebih besar agar lega

        layout = QVBoxLayout(self)

        label = QLabel("Log Aktivitas")
        label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(label)

        table = QTableWidget()
        logs = get_all_audit_logs()

        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Aksi", "Waktu", "Detail"])
        table.setRowCount(len(logs))

        for i, log in enumerate(logs):
            table.setItem(i, 0, QTableWidgetItem(log['action']))
            table.setItem(i, 1, QTableWidgetItem(log['timestamp']))

            detail_item = QTableWidgetItem(log['detail'])
            detail_item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            detail_item.setFlags(detail_item.flags() ^ Qt.ItemIsEditable)  # opsional: non-editable
            table.setItem(i, 2, detail_item)

        # ✅ Pastikan teks panjang dibungkus
        table.setWordWrap(True)
        table.resizeColumnsToContents()
        table.resizeRowsToContents()

        # ✅ Scrollbar otomatis jika perlu
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        layout.addWidget(table)
