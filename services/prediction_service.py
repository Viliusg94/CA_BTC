"""
Servisas darbui su prognozėmis.
"""
import logging
from database.repository.prediction_repository import PredictionRepository
from database.models.results_models import Prediction

# Konfigūruojame žurnalą
logger = logging.getLogger(__name__)

class PredictionService:
    """
    Servisas, atsakingas už operacijas su prognozėmis.
    """
    
    def __init__(self, db_session):
        """
        Inicializuoja PredictionService objektą.
        
        Args:
            db_session: SQLAlchemy sesija, naudojama darbui su duomenų baze
        """
        # Sukuriame prognozių repozitoriją naudodami pateiktą sesiją
        self.repository = PredictionRepository(db_session)
        # Išsaugome sesiją ateities naudojimui
        self.session = db_session
    
    def create_prediction(self, prediction_data):
        """
        Sukuria naują prognozę duomenų bazėje.
        
        Args:
            prediction_data (dict): Prognozės duomenys
            
        Returns:
            Prediction: Sukurtas prognozės objektas arba None, jei nepavyko sukurti
        """
        try:
            # Sukuriame prognozės objektą iš duomenų žodyno
            prediction = Prediction.from_dict(prediction_data)
            # Išsaugome prognozę duomenų bazėje per repozitoriją
            return self.repository.create(prediction)
        except Exception as e:
            # Įrašome klaidos informaciją į žurnalą
            logger.error(f"Klaida kuriant prognozę: {str(e)}")
            # Atšaukiame transakciją, kad išvengtume duomenų nesuderinamumo
            self.session.rollback()
            # Grąžiname None, kad nurodyti, jog įvyko klaida
            return None
    
    def get_prediction(self, prediction_id):
        """
        Gauna prognozę pagal jos ID.
        
        Args:
            prediction_id (str): Prognozės ID, kurią norime gauti
            
        Returns:
            Prediction: Prognozės objektas arba None, jei nerasta
        """
        try:
            # Grąžiname prognozę pagal ID iš repozitorijos
            return self.repository.get_by_id(prediction_id)
        except Exception as e:
            # Įrašome klaidos informaciją į žurnalą
            logger.error(f"Klaida gaunant prognozę (ID: {prediction_id}): {str(e)}")
            # Grąžiname None, kad nurodyti, jog įvyko klaida
            return None
    
    def update_prediction(self, prediction_id, prediction_data):
        """
        Atnaujina esamą prognozę.
        
        Args:
            prediction_id (str): Prognozės ID, kurią norime atnaujinti
            prediction_data (dict): Nauji prognozės duomenys
            
        Returns:
            Prediction: Atnaujintas prognozės objektas arba None, jei nerasta
        """
        try:
            # Atnaujina prognozę naudojant repozitorijos metodą
            return self.repository.update(prediction_id, prediction_data)
        except Exception as e:
            # Įrašome klaidos informaciją į žurnalą
            logger.error(f"Klaida atnaujinant prognozę (ID: {prediction_id}): {str(e)}")
            # Atšaukiame transakciją, kad išvengtume duomenų nesuderinamumo
            self.session.rollback()
            # Grąžiname None, kad nurodyti, jog įvyko klaida
            return None
    
    def delete_prediction(self, prediction_id):
        """
        Ištrina prognozę.
        
        Args:
            prediction_id (str): Prognozės ID, kurią norime ištrinti
            
        Returns:
            bool: True, jei ištrynimas sėkmingas, False kitu atveju
        """
        try:
            # Ištriname prognozę naudodami repozitorijos metodą
            return self.repository.delete(prediction_id)
        except Exception as e:
            # Įrašome klaidos informaciją į žurnalą
            logger.error(f"Klaida trinant prognozę (ID: {prediction_id}): {str(e)}")
            # Atšaukiame transakciją, kad išvengtume duomenų nesuderinamumo
            self.session.rollback()
            # Grąžiname False, kad nurodyti, jog įvyko klaida
            return False
    
    def list_predictions(self, limit=100, offset=0, model_id=None, interval=None, date_from=None, date_to=None, sort_by="prediction_date", sort_order="desc"):
        """
        Gauna prognozių sąrašą su galimybe filtruoti ir rikiuoti.
        
        Args:
            limit (int, optional): Maksimalus grąžinamų prognozių skaičius
            offset (int, optional): Praleistų įrašų skaičius (puslapis)
            model_id (str, optional): Filtravimas pagal modelio ID
            interval (str, optional): Filtravimas pagal laiko intervalą
            date_from (datetime, optional): Filtravimas pagal pradžios datą
            date_to (datetime, optional): Filtravimas pagal pabaigos datą
            sort_by (str, optional): Laukas, pagal kurį rikiuojama
            sort_order (str, optional): Rikiavimo tvarka ("asc" arba "desc")
            
        Returns:
            list: Prognozių sąrašas arba tuščias sąrašas, jei įvyko klaida
        """
        try:
            # Patikrinkime parametrų korektiškumą
            if sort_order not in ["asc", "desc"]:
                sort_order = "desc"
                
            # Grąžiname prognozių sąrašą naudodami repozitorijos metodą
            return self.repository.list(limit, offset, model_id, interval, date_from, date_to, sort_by, sort_order)
        except Exception as e:
            # Įrašome klaidos informaciją į žurnalą
            logger.error(f"Klaida gaunant prognozių sąrašą: {str(e)}")
            # Grąžiname tuščią sąrašą, kad nurodyti, jog įvyko klaida
            return []
    
    def update_actual_value(self, prediction_id, actual_value):
        """
        Atnaujina prognozės faktinę vertę (kada jau žinoma tikroji kaina).
        
        Args:
            prediction_id (str): Prognozės ID, kurią norime atnaujinti
            actual_value (float): Faktinė (tikroji) kaina
            
        Returns:
            Prediction: Atnaujintas prognozės objektas arba None, jei nerasta
        """
        try:
            # Gauname esamą prognozę
            prediction = self.repository.get_by_id(prediction_id)
            if not prediction:
                logger.warning(f"Prognozė su ID {prediction_id} nerasta")
                return None
            
            # Atnaujina faktinę vertę
            return self.repository.update(prediction_id, {"actual_value": actual_value})
        except Exception as e:
            # Įrašome klaidos informaciją į žurnalą
            logger.error(f"Klaida atnaujinant prognozės (ID: {prediction_id}) faktinę vertę: {str(e)}")
            # Atšaukiame transakciją, kad išvengtume duomenų nesuderinamumo
            self.session.rollback()
            # Grąžiname None, kad nurodyti, jog įvyko klaida
            return None