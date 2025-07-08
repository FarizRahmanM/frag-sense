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
                test_name TEXT,
                tester_id INTEGER,
                test_time TEXT,
                fragment_inside INTEGER,
                fragment_outside INTEGER,
                total_fragment INTEGER,
                image_path TEXT,
                last_edited TEXT,
                inference_time REAL,
                FOREIGN KEY (tester_id) REFERENCES testers(id)
            )
        """)

        # ✅ Tambahkan tabel audit_log di sini
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                detection_id INTEGER,
                tester_id INTEGER,
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
                     image_path, inference_time=None, last_edited=None, test_time=None):  # 🆕 Tambahkan test_time
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
                    fragment_outside, total_fragment, image_path, last_edited, inference_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_name, tester_id, test_time, fragment_inside,
                fragment_outside, total_fragment, image_path, last_edited, inference_time
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
        cur = conn.cursor()

        cur.execute("""
            SELECT d.*, t.name FROM detection_results d
            LEFT JOIN testers t ON d.tester_id = t.id
        """)
        rows = cur.fetchall()
        conn.close()

        result = []
        for row in rows:
            total_fragmen = row[4] + (row[5] / 2)
            status = "PASS" if 40 <= total_fragmen <= 400 else "FAIL"

            try:
                # Gunakan last_edited untuk ambil tanggal
                last_edited_dt = datetime.fromisoformat(row[8])
                test_date_str = last_edited_dt.strftime("%d %B %Y")
            except ValueError:
                test_date_str = "Invalid"

            # Ambil waktu langsung dari string test_time
            test_time_str = row[3] if row[3] else "Invalid"
            try:
                last_edited_dt = datetime.fromisoformat(row[8])
            except ValueError:
                last_edited_dt = datetime.now()
            print(f"✅ Loaded from DB: ID={row[0]} | test_time={row[3]}")
            print(f"✅ ID: {row[0]} | test_time: {test_time_str} | last_edited: {last_edited_dt}")
            result.append(CardViewModel(
                id=row[0],
                test_name=row[1],
                tester_name=row[10],
                last_edited=last_edited_dt,
                fragment_inside=row[4],
                fragment_outside=row[5],
                image=row[7],
                date=test_date_str,
                test_time=test_time_str,
                status=status,
                inference_time=row[9],
                tester_id=row[2]  # ⬅️ tambahkan ini agar update tidak gagal
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
        cursor.execute("DELETE FROM detection_results WHERE id = ?", (detection_id,))
        conn.commit()
        log_action(
            action="delete",
            detection_id=detection_id,
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

    if external_conn:
        cursor = external_conn.cursor()
        cursor.execute("""
            INSERT INTO audit_log (action, detection_id, tester_id, timestamp, detail)
            VALUES (?, ?, ?, ?, ?)
        """, (action, detection_id, tester_id, timestamp, detail))
    else:
        with db_lock:
            with connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_log (action, detection_id, tester_id, timestamp, detail)
                    VALUES (?, ?, ?, ?, ?)
                """, (action, detection_id, tester_id, timestamp, detail))
                conn.commit()

    
def get_all_audit_logs():
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.action, a.detection_id, a.tester_id, a.timestamp, a.detail, t.name
            FROM audit_log a
            LEFT JOIN testers t ON a.tester_id = t.id
            ORDER BY a.timestamp DESC
        """)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                'id': row[0],
                'action': row[1],
                'detection_id': row[2],
                'tester_id': row[3],
                'timestamp': row[4],
                'detail': row[5],
                'tester_name': row[6]
            })

        return result
    
def connect():
    print("📡 Opening DB connection...")
    conn = sqlite3.connect(get_database_path(), timeout=10.0)
    print("✅ Connection opened.")
    return conn


get_all_results = get_all_detections
