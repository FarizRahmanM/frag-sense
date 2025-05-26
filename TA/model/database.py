from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

# Ganti ke SQLite connection
engine = create_engine("sqlite:///detection_app.db", echo=True)

Session = sessionmaker(bind=engine)

class DetectionResult(Base):
    __tablename__ = "detection_results"

    id = Column(Integer, primary_key=True)
    test_name = Column(String(255))
    tester_name = Column(String(255))
    test_time = Column(DateTime, default=datetime.now)
    fragment_inside = Column(Integer)
    fragment_outside = Column(Integer)
    total_fragment= Column(Integer)
    image_path = Column(String(255))

Base.metadata.create_all(engine)

# CRUD functions

def create_detection(test_name, tester_name, fragment_inside, fragment_outside, total_fragment, image_path):
    session = Session()
    new_detection = DetectionResult(
        test_name=test_name,
        tester_name=tester_name,
        test_time=datetime.now(),
        fragment_inside=fragment_inside,
        fragment_outside=fragment_outside,
        total_fragment=total_fragment,
        image_path=image_path
    )
    session.add(new_detection)
    session.commit()
    session.close()
    return new_detection

def get_detection(detection_id):
    session = Session()
    detection = session.query(DetectionResult).filter(DetectionResult.id == detection_id).first()
    session.close()
    return detection

def get_all_detections():
    session = Session()
    results = session.query(DetectionResult).order_by(DetectionResult.test_time.desc()).all()
    session.close()
    return results

def update_detection(card_model):
    session = Session()
    try:
        detection = session.query(DetectionResult).get(card_model.id)
        if detection:
            detection.test_name = card_model.test_name
            detection.tester_name = card_model.tester_name
            detection.fragment_inside = card_model.fragment_inside
            detection.fragment_outside = card_model.fragment_outside
            detection.total_fragment = card_model.total_fragments
            detection.image_path = card_model.image_path  
            session.commit()
    finally:
        session.close()

def delete_detection(detection_id):
    session = Session()
    try:
        detection = session.query(DetectionResult).filter(DetectionResult.id == detection_id).first()
        if not detection:
            print("Data dengan ID", detection_id, "tidak ditemukan.")
            return False
        session.delete(detection)
        session.commit()
        print("Data berhasil dihapus")
        return True
    except Exception as e:
        print("Gagal menghapus data:", e)
        session.rollback()
        return False
    finally:
        session.close()

# Alias untuk cocok dengan GUI kamu
get_all_results = get_all_detections
