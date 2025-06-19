import sqlite3
from datetime import datetime
from ui.component.card_view import CardViewModel

DB_PATH = "detection_app.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detection_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT,
                tester_name TEXT,
                test_time TEXT,
                fragment_inside INTEGER,
                fragment_outside INTEGER,
                total_fragment INTEGER,
                image_path TEXT,
                last_edited TEXT
            )
        """)
        conn.commit()

def create_detection(test_name, tester_name, fragment_inside, fragment_outside, total_fragment, image_path, last_edited=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        last_edited = last_edited or now
        cursor.execute("""
            INSERT INTO detection_results (
                test_name, tester_name, test_time, fragment_inside,
                fragment_outside, total_fragment, image_path, last_edited
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_name, tester_name, now, fragment_inside,
            fragment_outside, total_fragment, image_path, last_edited
        ))
        conn.commit()
        return cursor.lastrowid

def get_all_detections():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM detection_results")
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
            print(f"❌ Format waktu salah: {row[8]}")
            date_str = "Invalid"
            time_str = "Invalid"

        result.append(CardViewModel(
            id=row[0],
            test_name=row[1],
            tester_name=row[2],
            last_edited=row[8], 
            fragment_inside=row[4],
            fragment_outside=row[5],
            total_fragments=row[6],
            image=row[7],
            date=date_str,
            time=time_str,
            status=status
        ))

    return result

def get_detection(detection_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM detection_results WHERE id = ?", (detection_id,))
        return cursor.fetchone()

def update_detection(card_model):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE detection_results
            SET test_name = ?, tester_name = ?, fragment_inside = ?,
                fragment_outside = ?, total_fragment = ?, image_path = ?, last_edited = ?
            WHERE id = ?
        """, (
            card_model.test_name, card_model.tester_name, card_model.fragment_inside,
            card_model.fragment_outside, card_model.total_fragments, card_model.image_path,
            now, card_model.id
        ))
        conn.commit()

def delete_detection(detection_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM detection_results WHERE id = ?", (detection_id,))
        conn.commit()
        return cursor.rowcount > 0


get_all_results = get_all_detections
