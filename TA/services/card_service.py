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
                tester_name=card.tester_name,
                fragment_inside=card.fragment_inside,
                fragment_outside=card.fragment_outside,
                total_fragment=card.total_fragments,
                image_path=card.image_path,
                last_edited=last_edited
            )
        except Exception as e:
            print("❌ Gagal menyimpan data:", e)

    
    def get_all_from_db(self):
        try:
            raw_data = get_all_detections()
            return [
                CardViewModel(
                    id=row[0],
                    test_name=row[1],
                    tester_name=row[2],
                    last_edited=row[3],
                    fragment_inside=row[4],
                    fragment_outside=row[5],
                    total_fragments=row[6],
                    image_path=row[7]
                )
                for row in raw_data
            ]
        except Exception as e:
            print("❌ Gagal mengambil data dari DB:", e)
            return []

    def update_to_db(self, card: CardViewModel):
        try:
            update_detection(card)
        except Exception as e:
            print("❌ Gagal update data:", e)