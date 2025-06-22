import sqlite3
from datetime import datetime
from ui.component.card_view import CardViewModel
import os
import sys
import shutil

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
                     image_path, inference_time=None, last_edited=None):
    with connect() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        last_edited = last_edited or now

        cursor.execute("""
            INSERT INTO detection_results (
                test_name, tester_id, test_time, fragment_inside,
                fragment_outside, total_fragment, image_path, last_edited, inference_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_name, tester_id, now, fragment_inside,
            fragment_outside, total_fragment, image_path, last_edited, inference_time
        ))
        conn.commit()
        return cursor.lastrowid

def get_all_detections():
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
            last_edited_dt = datetime.fromisoformat(row[8])
            date_str = last_edited_dt.strftime("%d %B %Y")
            time_str = last_edited_dt.strftime("%H:%M:%S")
        except ValueError:
            date_str = "Invalid"
            time_str = "Invalid"

        result.append(CardViewModel(
            id=row[0],
            test_name=row[1],
            tester_name=row[10],  # nama dari tabel testers
            last_edited=row[8],
            fragment_inside=row[4],
            fragment_outside=row[5],
            total_fragments=row[6],
            image=row[7],
            date=date_str,
            time=time_str,
            status=status,
            inference_time=row[9]
        ))

    return result

def get_detection(detection_id):
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM detection_results WHERE id = ?", (detection_id,))
        return cursor.fetchone()

def update_detection(card_model):
    with connect() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            UPDATE detection_results
            SET test_name = ?, tester_id = ?, fragment_inside = ?,
                fragment_outside = ?, total_fragment = ?, image_path = ?, last_edited = ?
            WHERE id = ?
        """, (
            card_model.test_name, card_model.tester_id, card_model.fragment_inside,
            card_model.fragment_outside, card_model.total_fragments,
            card_model.image_path, now, card_model.id
        ))
        conn.commit()

def delete_detection(detection_id):
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM detection_results WHERE id = ?", (detection_id,))
        conn.commit()
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


get_all_results = get_all_detections
