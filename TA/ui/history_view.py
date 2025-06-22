from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QPushButton,
    QFileDialog, QMessageBox, QHBoxLayout, QSizePolicy, QComboBox, QLineEdit, QCheckBox
)
from PySide6.QtCore import Qt, Slot
import pandas as pd
from functools import partial
from datetime import datetime
from ui.component.header_view import HeaderView
from ui.component.table_view import TableWidget
from ui.component.delete_view import DeleteDialog
from services.card_service import CardService  # bisa dihapus kalau tidak dipakai
from model.database import get_all_detections, delete_detection
from ui.component.card_view import CardViewModel

class HistoryView(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.items_per_page = 20
        self.current_page = 0
        self.max_page_buttons = 5
        self.filtered_cards = []

        main_layout = QVBoxLayout(self)

        # Header di bagian atas
        self.header = HeaderView()
        self.header.set_history_button_visible(False)  # Awalnya diset False
        main_layout.addWidget(self.header)

        # Dialog konfirmasi hapus
        self.delete_dialog = DeleteDialog(self)
        self.delete_dialog.accepted.connect(self.on_delete_confirmed)
        self.delete_dialog.rejected.connect(self.on_delete_canceled)

        # Area scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 20, 40, 20)
        content_layout.setSpacing(24)

        # Tombol kembali ke beranda
        back_btn = QLabel("← Beranda")
        back_btn.setStyleSheet("color: #333; font-size: 14px;")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.mousePressEvent = self.back_button_click
        content_layout.addWidget(back_btn)

        # Judul dan tombol ekspor
        header_layout = QHBoxLayout()
        title = QLabel("Riwayat Pengujian")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.export_btn = QPushButton("Unduh Data")
        self.export_btn.setFixedWidth(150)
        self.export_btn.setStyleSheet(
            "color: black; background: #C2E7FF; padding: 8px; font-weight: bold;"
        )
        self.export_btn.clicked.connect(self.export_selected_to_excel)

        header_layout.addWidget(title)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Urutkan: Tanggal Terbaru",
            "Urutkan: Tanggal Terlama",
            "Urutkan: Nama A-Z",
            "Urutkan: Nama Z-A",
            "Urutkan: Hasil Uji - PASS",
            "Urutkan: Hasil Uji - FAIL",
        ])
        self.sort_combo.setFixedWidth(200)
        self.sort_combo.currentIndexChanged.connect(self.apply_filters)

        manage_testers_btn = QPushButton("Kelola Penguji")
        manage_testers_btn.setStyleSheet(
            "color: black; background: #FCE38A; padding: 8px; font-weight: bold;"
        )
        manage_testers_btn.setFixedWidth(150)
        manage_testers_btn.clicked.connect(self.show_manage_testers_dialog)


        # Tombol Hapus
        self.delete_btn = QPushButton("Hapus Data")
        self.delete_btn.setFixedWidth(120)
        self.delete_btn.setStyleSheet(
            "color: black; background: #FFBABA; padding: 8px; font-weight: bold;"
        )
        self.delete_btn.clicked.connect(self.delete_selected_rows)
        


        header_layout.addWidget(self.sort_combo)
        # Checkbox indikator status (tidak bisa diklik)
        self.select_all_checkbox = QCheckBox("Status Centang")
        self.select_all_checkbox.setEnabled(False)
        self.select_all_checkbox.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.select_all_checkbox)
        header_layout.addWidget(manage_testers_btn)
        header_layout.addWidget(self.export_btn)
        header_layout.addWidget(self.delete_btn)
        content_layout.addLayout(header_layout)

        # Select All - Halaman Saat Ini
        select_page_btn = QPushButton("Pilih Semua (Halaman Ini)")
        select_page_btn.setStyleSheet("color: black; background: #D2F8D2; padding: 6px; font-weight: bold;")
        select_page_btn.clicked.connect(self.toggle_select_all_on_current_page)
        header_layout.addWidget(select_page_btn)

        # Select All - Semua Halaman
        select_all_btn = QPushButton("Pilih Semua (Semua Data)")
        select_all_btn.setStyleSheet("color: black; background: #FFD2D2; padding: 6px; font-weight: bold;")
        select_all_btn.clicked.connect(self.toggle_select_all_across_all_pages)
        header_layout.addWidget(select_all_btn)

        # Table widget dengan data awal
        self.table = TableWidget([])
        self.table.checkbox_changed.connect(self.update_action_buttons_state)
        self.table.delete_requested.connect(self.on_table_delete_requested)
        self.table.info_requested.connect(self.on_table_info_requested)
        content_layout.addWidget(self.table)

        # Navigasi halaman
        pagination_container = QHBoxLayout()
        pagination_container.setAlignment(Qt.AlignCenter)

        self.pagination_layout = QHBoxLayout()
        self.pagination_layout.setSpacing(4)  # spacing antar tombol
        pagination_container.addStretch()
        pagination_container.addLayout(self.pagination_layout)
        pagination_container.addStretch()

        content_layout.addLayout(pagination_container)

        # Tambahkan konten ke scroll area
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Load data dari database
        self.reload_table()

    def reload_table(self):
        raw_cards = get_all_detections()
        card_viewmodels = []

        for row in raw_cards:
            total_fragmen = row.fragment_inside + (row.fragment_outside / 2)

            # Hitung status secara dinamis tanpa perlu kolom di database
            if total_fragmen < 40 or total_fragmen > 400:
                status = "FAIL"
            else:
                status = "PASS"
            
            try:
                test_time_dt = datetime.fromisoformat(row.last_edited)
            except ValueError:
                test_time_dt = datetime.now()

            card_viewmodels.append(
                CardViewModel(
                    id=row.id,
                    test_name=row.test_name,
                    tester_name=row.tester_name,
                    fragment_inside=row.fragment_inside,
                    fragment_outside=row.fragment_outside,
                    image=row.image_path,
                    date = test_time_dt.strftime("%d %B %Y"),
                    time = test_time_dt.strftime("%H:%M:%S"),
                    status=status,
                    last_edited=row.last_edited,
                    inference_time=row.inference_time
                )
            )

        self.filtered_cards = card_viewmodels
        self.current_page = 0
        self.update_table_view()

    @Slot(object)
    def on_table_delete_requested(self, card):
        self.card_to_delete = card
        self.delete_dialog.open()

    @Slot()
    def on_delete_confirmed(self):
        if self.card_to_delete:
            raw_cards = get_all_detections()
            for row in raw_cards:
                try:
                    test_time_dt = datetime.fromisoformat(row.last_edited)
                except ValueError:
                    test_time_dt = datetime.now()
                if (
                    row.test_name == self.card_to_delete.test_name and
                    row.tester_name == self.card_to_delete.tester_name and
                    test_time_dt.strftime("%d %B %Y") == self.card_to_delete.test_date and
                    test_time_dt.strftime("%H:%M:%S") == self.card_to_delete.test_time
                ):
                    delete_detection(row.id)
                    break

            self.reload_table()
            self.card_to_delete = None
            self.delete_dialog.close()

    @Slot()
    def on_delete_canceled(self):
        self.delete_dialog.close()

    def back_button_click(self, event):
        if self.main_window:
            self.main_window.navigate(self.main_window.main_view)

    def on_table_info_requested(self, card):
        from ui.detail_view import DetailView  # Import lokal sesuai strukturmu
        detail_view = DetailView(main_window=self.main_window, selected_card=card)
        if self.main_window:
            self.main_window.navigate(detail_view)

    def export_selected_to_excel(self):
        selected_cards = self.table.get_selected_cards()

        if not selected_cards:
            QMessageBox.warning(self, "Tidak Ada Data", "Pilih minimal satu baris untuk diekspor.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Simpan File", "riwayat_pengujian.xlsx", "Excel Files (*.xlsx)"
        )
        if not path:
            return

        try:
            data = []
            for card in selected_cards:
                data.append({
                    "Nama Pengujian": card.test_name,
                    "Nama Penguji": card.tester_name,
                    "Tanggal": card.test_date,
                    "Waktu": card.test_time,
                    "Jumlah Fragmen (Dalam)": card.fragment_inside,
                    "Jumlah Fragmen (Luar)": card.fragment_outside,
                    "Jumlah Fragmen (Total)": round(card.fragment_inside + (card.fragment_outside / 2), 1),
                    "Path Gambar": card.image_path
                })

            df = pd.DataFrame(data)
            df.to_excel(path, index=False)

            QMessageBox.information(self, "Sukses", f"Data berhasil diekspor ke:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Gagal Ekspor", f"Terjadi kesalahan saat ekspor:\n{e}")

    
    def apply_filters(self):
        raw_cards = get_all_detections()
        card_viewmodels = []

        for row in raw_cards:
            total_fragmen = row.fragment_inside + (row.fragment_outside / 2)
            status = "FAIL" if total_fragmen < 40 or total_fragmen > 400 else "PASS"

            try:
                test_time_dt = datetime.fromisoformat(row.last_edited)
            except ValueError:
                test_time_dt = datetime.now()

            card_viewmodels.append(CardViewModel(
                id=row.id,
                test_name=row.test_name,
                tester_name=row.tester_name,
                fragment_inside=row.fragment_inside,
                fragment_outside=row.fragment_outside,
                image=row.image_path,
                date=test_time_dt.strftime("%d %B %Y"),
                time=test_time_dt.strftime("%H:%M:%S"),
                status=status,
                last_edited=row.last_edited,
                inference_time=row.inference_time
            ))

        current_sort = self.sort_combo.currentText()
        self.sort_combo.setStyleSheet("padding: 6px; font-weight: bold; border: 1px solid black;")

        if current_sort == "Urutkan: Tanggal Terbaru":
            card_viewmodels.sort(key=lambda x: (x.last_edited), reverse=True)
        elif current_sort == "Urutkan: Tanggal Terlama":
            card_viewmodels.sort(key=lambda x: (x.last_edited))
        elif current_sort == "Urutkan: Nama A-Z":
            card_viewmodels.sort(key=lambda x: x.tester_name.lower())
        elif current_sort == "Urutkan: Nama Z-A":
            card_viewmodels.sort(key=lambda x: x.tester_name.lower(), reverse=True)
        elif current_sort == "Urutkan: Hasil Uji - PASS":
            card_viewmodels.sort(key=lambda x: (x.status != "PASS", x.last_edited), reverse=False)
        elif current_sort == "Urutkan: Hasil Uji - FAIL":
            card_viewmodels.sort(key=lambda x: (x.status != "FAIL", x.last_edited), reverse=False)

        # Set hasil sortir ke filtered_cards dan reset ke halaman pertama
        self.filtered_cards = card_viewmodels
        self.current_page = 0
        self.update_table_view()

    def delete_selected_rows(self):
        selected_cards = self.table.get_selected_cards()

        if not selected_cards:
            QMessageBox.warning(self, "Tidak Ada Data", "Pilih minimal satu baris yang ingin dihapus.")
            return

        confirm = QMessageBox.question(
            self,
            "Konfirmasi Hapus",
            f"Apa kamu yakin ingin menghapus {len(selected_cards)} data terpilih?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            raw_cards = get_all_detections()
            for card in selected_cards:
                for row in raw_cards:
                    try:
                        test_time_dt = datetime.fromisoformat(row.last_edited)
                    except ValueError:
                        test_time_dt = datetime.now()
                    if (
                        row.test_name == card.test_name and
                        row.tester_name == card.tester_name and
                        test_time_dt.strftime("%d %B %Y") == card.test_date and
                        test_time_dt.strftime("%H:%M:%S") == card.test_time
                    ):
                        delete_detection(row.id)
                        break

            self.reload_table()
            self.apply_filters()

    def update_table_view(self):
        start_index = self.current_page * self.items_per_page
        end_index = start_index + self.items_per_page
        page_cards = self.filtered_cards[start_index:end_index]

        self.table.cards = page_cards
        self.table.populate_cards()

        self.table.checkbox_map.clear()  # Bersihkan dulu sebelum membuat checkbox baru
        self.table.cards = page_cards
        self.table.populate_cards()

        # Sinkronisasi checkbox setelah populate
        for card in page_cards:
            card_id = str(card.id)

            if card_id not in self.table.card_selection_map:
                self.table.card_selection_map[card_id] = False

            if card_id in self.table.checkbox_map:
                checkbox = self.table.checkbox_map[card_id]
                selected = self.table.card_selection_map.get(card_id, False)
                checkbox.blockSignals(True)
                checkbox.setChecked(selected)
                checkbox.blockSignals(False)

        self.update_select_all_status()

        total_items = len(self.filtered_cards)
        total_pages = (total_items - 1) // self.items_per_page + 1
 
        # Hitung indeks tampilan
        display_start = start_index + 1
        display_end = min(end_index, total_items)

        # Hapus layout lama
        while self.pagination_layout.count():
            child = self.pagination_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Tombol ke halaman pertama
        first_btn = QPushButton("«")
        first_btn.clicked.connect(lambda: self.go_to_page(0))
        first_btn.setFixedSize(32, 32)  # ← Tambah ukuran kecil
        self.pagination_layout.addWidget(first_btn)

        # Tombol ke halaman sebelumnya
        prev_btn = QPushButton("‹")
        prev_btn.clicked.connect(self.go_to_prev_page)
        prev_btn.setFixedSize(32, 32)  # ← Tambah ukuran kecil
        self.pagination_layout.addWidget(prev_btn)

        # Tampilkan 5 halaman di sekitar halaman aktif
        half_range = self.max_page_buttons // 2
        start_page = max(0, self.current_page - half_range)
        end_page = min(total_pages, start_page + self.max_page_buttons)

        # Pastikan tidak keluar dari batas awal
        if end_page - start_page < self.max_page_buttons:
            start_page = max(0, end_page - self.max_page_buttons)

        for i in range(start_page, end_page):
            btn = QPushButton(str(i + 1))
            btn.setFixedSize(32, 32)
            if i == self.current_page:
                btn.setStyleSheet("background-color: #007bff; color: white; border-radius: 15px; font-weight: bold;")
            btn.clicked.connect(partial(self.go_to_page, i))  # ✅ binding i dengan benar
            self.pagination_layout.addWidget(btn)

        # Tombol ke halaman selanjutnya
        next_btn = QPushButton("›")
        next_btn.clicked.connect(self.go_to_next_page)
        next_btn.setFixedSize(32, 32)
        self.pagination_layout.addWidget(next_btn)

        last_btn = QPushButton("»")
        last_btn.clicked.connect(lambda: self.go_to_page(total_pages - 1))
        last_btn.setFixedSize(32, 32)
        self.pagination_layout.addWidget(last_btn)

        total_label = QLabel(f"Total: {total_items} data")
        total_label.setAlignment(Qt.AlignCenter)
        total_label.setStyleSheet("font-weight: bold;")
        self.pagination_layout.addWidget(total_label)

        # Input langsung ke halaman
        page_input = QLineEdit()
        page_input.setFixedWidth(40)
        page_input.setPlaceholderText("...")
        page_input.setStyleSheet("border: 1px solid gray; padding: 2px;")
        page_input.returnPressed.connect(lambda: self.go_to_input_page(page_input.text(), total_pages))
        self.pagination_layout.addWidget(page_input)
        self.update_action_buttons_state()

    
    def go_to_prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_table_view()

    def go_to_next_page(self):
        total_pages = (len(self.filtered_cards) - 1) // self.items_per_page + 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_table_view()
            
    def go_to_page(self, page_number):
        """Pindah ke halaman tertentu dan update tampilan tabel."""
        total_pages = (len(self.filtered_cards) - 1) // self.items_per_page + 1
        if 0 <= page_number < total_pages:
            self.current_page = page_number
            self.update_table_view()
    
    def go_to_input_page(self, text, total_pages):
        try:
            page = int(text) - 1
            if 0 <= page < total_pages:
                self.current_page = page
                self.update_table_view()
        except ValueError:
            pass


    def show_manage_testers_dialog(self):
        from services.testers_service import TesterCRUDDialog
        dialog = TesterCRUDDialog(self)
        dialog.exec()
        # Setelah dialog ditutup, bisa reload data jika perlu:
        self.reload_table()
        self.apply_filters()

    def select_all_on_current_page(self):
        for card in self.table.cards:
            card_id = str(card.id)
            self.table.card_selection_map[card_id] = True
            if card_id in self.table.checkbox_map:
                checkbox = self.table.checkbox_map[card_id]
                checkbox.blockSignals(True)
                checkbox.setChecked(True)
                checkbox.blockSignals(False)
        self.update_select_all_status()

    def toggle_select_all_across_all_pages(self):
        all_selected = all(bool(v) for v in self.table.card_selection_map.values())
        new_state = not all_selected  # Toggle state

        # Update semua state map (semua data)
        for card in self.filtered_cards:
            card_id = str(card.id)
            self.table.card_selection_map[card_id] = new_state

        # ✅ Update checkbox yang terlihat (halaman ini saja)
        for card_id, checkbox in self.table.checkbox_map.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(new_state)
            checkbox.blockSignals(False)

        self.update_select_all_status()
        self.table.checkbox_changed.emit()
        self.update_table_view()

    def toggle_select_all_on_current_page(self):
        # Pastikan map untuk halaman ini sudah siap
        for card in self.table.cards:
            card_id = str(card.id)
            if card_id not in self.table.card_selection_map:
                self.table.card_selection_map[card_id] = False

        visible_ids = [str(cid) for cid in self.table.checkbox_map.keys()]
        all_visible_selected = all(self.table.card_selection_map.get(cid, False) for cid in visible_ids)
        new_state = not all_visible_selected

        for cid in visible_ids:
            self.table.card_selection_map[cid] = new_state
            checkbox = self.table.checkbox_map[cid]
            checkbox.blockSignals(True)
            checkbox.setChecked(new_state)
            checkbox.blockSignals(False)

        self.update_select_all_status()
        self.table.checkbox_changed.emit()
        

    def update_select_all_status(self):
        total_checkboxes = len(self.table.card_selection_map)
        total_selected = sum(1 for selected in self.table.card_selection_map.values() if selected)

        if total_checkboxes == 0:
            self.select_all_checkbox.setText("Status Centang: Kosong")
        elif total_selected == total_checkboxes:
            self.select_all_checkbox.setText("Status Centang: Semua Terpilih")
        elif total_selected == 0:
            self.select_all_checkbox.setText("Status Centang: Tidak Ada Terpilih")
        else:
            self.select_all_checkbox.setText(f"Status Centang: {total_selected}/{total_checkboxes}")

    def update_action_buttons_state(self):
        selected = self.table.get_selected_cards()
        print("Selected cards count:", len(selected))  # Debug
        enable = len(selected) > 0
        self.export_btn.setEnabled(enable)
        self.delete_btn.setEnabled(enable)

    def refresh(self):
        """Metode ini dipanggil agar tabel terupdate saat kembali dari DetailView"""
        self.reload_table()
        self.apply_filters()