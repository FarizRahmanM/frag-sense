from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox
)
from model.database import (
    get_all_testers, add_tester, get_tester_id_by_name
)
import sqlite3


class TesterCRUDDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__()
        self.setWindowTitle("Kelola Daftar Penguji")
        self.resize(400, 500)

        self.layout = QVBoxLayout(self)

        # Input nama
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Masukkan nama penguji")
        self.layout.addWidget(QLabel("Nama Penguji"))
        self.layout.addWidget(self.name_input)

        # Tombol Simpan / Tambah
        self.save_btn = QPushButton("Tambah")
        self.save_btn.clicked.connect(self.handle_save)
        self.layout.addWidget(self.save_btn)

        # Tombol Batal Edit
        self.cancel_edit_btn = QPushButton("Batal Edit")
        self.cancel_edit_btn.clicked.connect(self.reset_form)
        self.cancel_edit_btn.setStyleSheet("background-color: lightgray; font-weight: bold;")
        self.cancel_edit_btn.setVisible(False)  # Hanya muncul saat edit
        self.layout.addWidget(self.cancel_edit_btn)

        # Tombol Hapus
        self.delete_btn = QPushButton("Hapus")
        self.delete_btn.clicked.connect(self.handle_delete)
        self.delete_btn.setStyleSheet("background-color: #FFBABA; font-weight: bold;")
        self.delete_btn.setEnabled(False)  # Aktif hanya saat edit
        self.layout.addWidget(self.delete_btn)

        # List tester
        self.tester_list = QListWidget()
        self.layout.addWidget(QLabel("Daftar Penguji"))
        self.layout.addWidget(self.tester_list)

        self.current_edit_id = None  # None = Tambah mode

        self.load_testers()
        self.tester_list.itemDoubleClicked.connect(self.enter_edit_mode)

    def load_testers(self):
        self.tester_list.clear()
        for tester_id, name in get_all_testers():
            item = QListWidgetItem(name)
            item.setData(1000, tester_id)
            self.tester_list.addItem(item)

    def handle_save(self):
        name = self.name_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Validasi", "Nama penguji tidak boleh kosong.")
            return

        try:
            if self.current_edit_id is not None:
                # Edit
                from model.database import get_database_path
                with sqlite3.connect(get_database_path()) as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE testers SET name = ? WHERE id = ?", (name, self.current_edit_id))
                    conn.commit()
                QMessageBox.information(self, "Berhasil", "Data berhasil diperbarui.")
            else:
                # Tambah
                result = add_tester(name)
                if result is None:
                    QMessageBox.warning(self, "Gagal", "Nama penguji sudah ada.")
                    return
                QMessageBox.information(self, "Berhasil", "Data berhasil ditambahkan.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Terjadi kesalahan:\n{e}")

        self.reset_form()
        self.load_testers()

    def handle_delete(self):
        if self.current_edit_id is None:
            return

        confirm = QMessageBox.question(
            self, "Konfirmasi Hapus",
            "Yakin ingin menghapus penguji ini?\nData uji yang terhubung akan ikut terhapus.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                from model.database import get_database_path
                with sqlite3.connect(get_database_path()) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM testers WHERE id = ?", (self.current_edit_id,))
                    conn.commit()
                QMessageBox.information(self, "Berhasil", "Penguji berhasil dihapus.")
            except Exception as e:
                QMessageBox.critical(self, "Gagal", f"Gagal menghapus:\n{e}")

            self.reset_form()
            self.load_testers()

    def enter_edit_mode(self, item):
        self.current_edit_id = item.data(1000)
        self.name_input.setText(item.text())
        self.save_btn.setText("Simpan Perubahan")
        self.delete_btn.setEnabled(True)
        self.cancel_edit_btn.setVisible(True)

    def reset_form(self):
        self.name_input.clear()
        self.current_edit_id = None
        self.save_btn.setText("Tambah")
        self.delete_btn.setEnabled(False)
        self.cancel_edit_btn.setVisible(False)
        self.tester_list.clearSelection()

    def show_manage_testers_dialog(self):
        dialog = TesterCRUDDialog(self)
        if dialog.exec():
            self.reload_table() 