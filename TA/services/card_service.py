from model.database import create_detection, get_all_detections
from ui.component.card_view import CardViewModel

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

    def save_to_database(self, card_vm):
        try:
            total_fragment = card_vm.fragment_inside + (card_vm.fragment_outside * 0.5)
            create_detection(
                test_name=card_vm.test_name,
                tester_name=card_vm.tester_name,
                fragment_inside=card_vm.fragment_inside,
                fragment_outside=card_vm.fragment_outside,
                total_fragment=total_fragment,
                image_path=card_vm.image_path
            )
            print("✅ Data berhasil disimpan ke database.")
        except Exception as e:
            print("❌ Gagal menyimpan data:", e)
            
    def get_all_from_db(self):
        try:
            records = get_all_detections()
            cards = []
            for rec in records:
                card = CardViewModel(
                    id=rec.id,
                    test_name=rec.test_name,
                    date=rec.test_time.strftime("%d %B %Y") if rec.test_time else None,
                    time=rec.test_time.strftime("%H:%M:%S") if rec.test_time else None,
                    total_fragments=rec.total_fragment,
                    image=rec.image_path,
                    tester_name=rec.tester_name,
                    fragment_inside=rec.fragment_inside,
                    fragment_outside=rec.fragment_outside
                )
                cards.append(card)
            return cards
        except Exception as e:
            print("❌ Gagal mengambil data dari DB:", e)
            return []
        
    def update_to_db(self, card: CardViewModel):
        from model.database import update_detection
        update_detection(card)
