import sqlite3
from datetime import datetime
from ui.component.card_view import CardViewModel
import os
import sys
import shutil
from threading import RLock

db_lock = RLock()

def get_database_path():
    # Tentukan lokasi aman untuk database
    from pathlib import Path
    appdata_dir = Path(os.getenv("APPDATA")) / "FragSense"
    appdata_dir.mkdir(parents=True, exist_ok=True)

    db_target = appdata_dir / "detection_app.db"

    # Jika belum ada, salin dari bundle PyInstaller (resource_path)
    if not db_target.exists():
        try:
            from utils import resource_path
            db_source = Path(resource_path("detection_app.db"))
            if db_source.exists():
                shutil.copy(db_source, db_target)
        except Exception as e:
            print("Gagal menyalin database default:", e)

    return str(db_target)

def connect():
    return sqlite3.connect(get_database_path())

def init_db():
    with connect() as conn:
        cursor = conn.cursor()

        # Buat tabel testers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS testers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)

        # Buat tabel detection_results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detection_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT NOT NULL,
            tester_id INTEGER NOT NULL,
            test_time TEXT,                         -- waktu saat uji dilakukan (format: HH:MM:SS)
            fragment_inside INTEGER DEFAULT 0,
            fragment_outside INTEGER DEFAULT 0,
            total_fragment REAL DEFAULT 0,
            image_path TEXT,                        -- gambar hasil deteksi dengan titik
            numbered_image_path TEXT,              -- 🔁 gambar hasil deteksi dengan angka
            last_edited TEXT,                       -- timestamp ISO format
            inference_time REAL DEFAULT 0,          -- durasi proses deteksi
            FOREIGN KEY (tester_id) REFERENCES testers(id)
        );
        """)

        # ✅ Tambahkan tabel audit_log di sini
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            detection_id INTEGER,
            tester_id INTEGER,
            tester_name TEXT,
            timestamp TEXT NOT NULL,
            detail TEXT
        )
        """)

        # Tambahkan nama-nama tester default
        default_testers = [
            "G. Agus Permana Putra Sujana",
            "Sumarlin Manalu",
            "Adi Irawan",
            "Rivaldi Pamungkas",
            "Chandra Taufik Rahman"
        ]

        for name in default_testers:
            try:
                cursor.execute("INSERT INTO testers (name) VALUES (?)", (name,))
            except sqlite3.IntegrityError:
                pass

        conn.commit()

def create_detection(test_name, tester_id, fragment_inside, fragment_outside, total_fragment,
                     image_path, numbered_image_path=None, inference_time=None, last_edited=None, test_time=None):  # 🆕 Tambahkan test_time
    print("🔵 INSERT (create_detection) dipanggil")
    with db_lock:
        with connect() as conn:
            cursor = conn.cursor()
            now = datetime.now()

            test_time = test_time or now.strftime("%H:%M:%S")  # 🆕 Gunakan test_time jika sudah diberikan
            last_edited = last_edited or now.isoformat()

            cursor.execute("""
                INSERT INTO detection_results (
                    test_name, tester_id, test_time, fragment_inside,
                    fragment_outside, total_fragment, image_path, 
                    numbered_image_path, last_edited, inference_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_name, tester_id, test_time, fragment_inside,
                fragment_outside, total_fragment, image_path, 
                numbered_image_path, last_edited, inference_time
            ))
            conn.commit()
            detection_id = cursor.lastrowid
            log_action(
                action="add",
                detection_id=detection_id,
                tester_id=tester_id,
                detail=f"Menambahkan data uji '{test_name}'"
            )
            return detection_id


def get_all_detections():
    with db_lock:
        conn = sqlite3.connect(get_database_path())
        conn.row_factory = sqlite3.Row  # 🆕 Akses kolom pakai nama
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                d.id,
                d.test_name,
                d.tester_id,
                d.test_time,
                d.fragment_inside,
                d.fragment_outside,
                d.total_fragment,
                d.image_path,
                d.numbered_image_path,
                d.last_edited,
                d.inference_time,
                t.name AS tester_name
            FROM detection_results d
            LEFT JOIN testers t ON d.tester_id = t.id
        """)
        rows = cur.fetchall()
        conn.close()

        result = []
        for row in rows:
            total_fragmen = row["fragment_inside"] + (row["fragment_outside"] / 2)
            status = "PASS" if 40 <= total_fragmen <= 400 else "FAIL"

            try:
                last_edited_dt = datetime.fromisoformat(row["last_edited"])
                test_date_str = last_edited_dt.strftime("%d %B %Y")
            except Exception:
                test_date_str = "Invalid"
                last_edited_dt = datetime.now()

            result.append(CardViewModel(
                id=row["id"],
                test_name=row["test_name"],
                tester_id=row["tester_id"],
                test_time=row["test_time"] or "Invalid",
                fragment_inside=row["fragment_inside"],
                fragment_outside=row["fragment_outside"],
                image=row["image_path"],
                numbered_image=row["numbered_image_path"],
                last_edited=last_edited_dt,
                inference_time=row["inference_time"],
                tester_name=row["tester_name"],
                date=test_date_str,
                status=status
            ))

        return result


def get_detection(detection_id):
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM detection_results WHERE id = ?", (detection_id,))
        return cursor.fetchone()

def update_detection(card_model):
    print("🟡 UPDATE (update_detection) dipanggil untuk ID:", card_model.id)
    with db_lock:
        with connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE detection_results
                SET test_name = ?, 
                    tester_id = ?,
                    fragment_inside = ?,
                    fragment_outside = ?, 
                    total_fragment = ?, 
                    image_path = ?, 
                    numbered_image_path = ?,
                    last_edited = ?, 
                    inference_time = ?
                WHERE id = ?
            """, (
                card_model.test_name,
                card_model.tester_id,
                card_model.fragment_inside,
                card_model.fragment_outside,
                card_model.total_fragments,
                card_model.image_path,
                card_model.numbered_image_path,
                card_model.last_edited.isoformat() if isinstance(card_model.last_edited, datetime) else card_model.last_edited,
                card_model.inference_time,
                card_model.id
            ))

            # 🟢 log_action pakai koneksi yang sama
            log_action(
                action="edit",
                detection_id=card_model.id,
                tester_id=card_model.tester_id,
                detail=f"Mengedit data uji '{card_model.test_name}'",
                external_conn=conn  # 🆕
            )

            conn.commit()

def delete_detection(detection_id):
    with connect() as conn:
        cursor = conn.cursor()

        # Ambil tester_id dulu sebelum dihapus
        cursor.execute("SELECT tester_id FROM detection_results WHERE id = ?", (detection_id,))
        row = cursor.fetchone()
        tester_id = row[0] if row else None

        # Hapus data
        cursor.execute("DELETE FROM detection_results WHERE id = ?", (detection_id,))
        conn.commit()

        # Log lengkap termasuk tester_id
        log_action(
            action="delete",
            detection_id=detection_id,
            tester_id=tester_id,
            detail=f"Menghapus data uji dengan ID {detection_id}"
        )

        return cursor.rowcount > 0
    

def get_all_testers():
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM testers ORDER BY name")
        return cursor.fetchall()  # list of (id, name)

def add_tester(name):
    with connect() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO testers (name) VALUES (?)", (name,))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # tester sudah ada

def get_tester_id_by_name(name):
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM testers WHERE name = ?", (name,))
        row = cursor.fetchone()
        return row[0] if row else None

def get_tester_name_by_id(tester_id):
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM testers WHERE id = ?", (tester_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    

def log_action(action, detection_id=None, tester_id=None, detail="", external_conn=None):
    timestamp = datetime.now().isoformat()

    # Ambil nama penguji sekarang juga, agar tetap ada meskipun pengujinya dihapus nanti
    tester_name = get_tester_name_by_id(tester_id) if tester_id else None

    if external_conn:
        cursor = external_conn.cursor()
        cursor.execute("""
            INSERT INTO audit_log (action, detection_id, tester_id, tester_name, timestamp, detail)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (action, detection_id, tester_id, tester_name, timestamp, detail))
    else:
        with db_lock:
            with connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_log (action, detection_id, tester_id, tester_name, timestamp, detail)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (action, detection_id, tester_id, tester_name, timestamp, detail))
                conn.commit()

    
def get_all_audit_logs():
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, action, detection_id, tester_id, tester_name, timestamp, detail
            FROM audit_log
            ORDER BY timestamp DESC
        """)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                'id': row[0],
                'action': row[1],
                'detection_id': row[2],
                'tester_id': row[3],
                'tester_name': row[4],  # sudah langsung dari kolom
                'timestamp': row[5],
                'detail': row[6]
            })

        return result
    
def connect():
    print("📡 Opening DB connection...")
    conn = sqlite3.connect(get_database_path(), timeout=10.0)
    print("✅ Connection opened.")
    return conn


get_all_results = get_all_detections
