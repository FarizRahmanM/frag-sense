from model.database import create_detection, get_all_detections, update_detection
from ui.component.card_view import CardViewModel
import datetime



class CardService:
    _instance = None

    def __init__(self):
        self.cards = []

    @staticmethod
    def instance():
        if CardService._instance is None:
            CardService._instance = CardService()
        return CardService._instance

    def add_card(self, card_vm):
        self.cards.append(card_vm)


    def save_to_database(self, card: CardViewModel):
        try:
            last_edited = card.last_edited
            if isinstance(last_edited, datetime.datetime):
                last_edited = last_edited.isoformat()

            create_detection(
            test_name=card.test_name,
            tester_id=card.tester_id,
            fragment_inside=card.fragment_inside,
            fragment_outside=card.fragment_outside,
            total_fragment=card.total_fragments,
            image_path=card.image_path,
            numbered_image_path=card.numbered_image_path,  # 🆕 ditambahkan
            inference_time=card.inference_time,
            last_edited=last_edited,
            test_time=card.test_time
        )
        except Exception as e:
            print("❌ Gagal menyimpan data:", e)

    
    def get_all_from_db(self):
        try:
            raw_data = get_all_detections()
            return raw_data  # ⬅️ langsung kembalikan hasil dari get_all_detections
        except Exception as e:
            print("❌ Gagal mengambil data dari DB:", e)
            return []

    def update_to_db(self, card: CardViewModel):
        try:
            update_detection(card)
        except Exception as e:
            print("❌ Gagal update data:", e)

    def save_or_update(self, card: CardViewModel):
        print(f"📝 Akan Simpan: ID={card.id}, test_time={card.test_time}")
        if card.id is None:
            print("🟢 Menyimpan data baru...")
            self.save_to_database(card)
        else:
            print("🟡 Memperbarui data lama (id =", card.id, ")...")
            self.update_to_db(card)