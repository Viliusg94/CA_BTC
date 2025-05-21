"""
Servisas darbui su modeliais.
"""
import logging
from database.repository.model_repository import ModelRepository
from database.models.models import Model

# Konfigūruojame žurnalą
logger = logging.getLogger(__name__)

class ModelService:
    """
    Servisas, atsakingas už operacijas su modeliais.
    """
    
    def __init__(self, db_session):
        """
        Inicializuoja ModelService objektą.
        
        Args:
            db_session: SQLAlchemy sesija, naudojama darbui su duomenų baze
        """
        # Sukuriame modelių repozitoriją naudodami pateiktą sesija
        self.repository = ModelRepository(db_session)
        # Išsaugome sesiją ateities naudojimui
        self.session = db_session
    
    def create_model(self, model_data):
        """
        Sukuria naują modelį duomenų bazėje.
        
        Args:
            model_data (dict): Modelio duomenys (id, name, type ir kt.)
            
        Returns:
            Model: Sukurtas modelio objektas arba None, jei nepavyko sukurti
        """
        try:
            # Sukuriame modelio objektą iš duomenų žodyno
            model = Model.from_dict(model_data)
            # Išsaugome modelį duomenų bazėje per repozitoriją
            return self.repository.create(model)
        except Exception as e:
            # Įrašome klaidos informaciją į žurnalą
            logger.error(f"Klaida kuriant modelį: {str(e)}")
            # Atšaukiame transakciją, kad išvengtume duomenų nesuderinamumo
            self.session.rollback()
            # Grąžiname None, kad nurodyti, jog įvyko klaida
            return None
    
    def get_model(self, model_id):
        """
        Gauna modelį pagal jo ID.
        
        Args:
            model_id (str): Modelio ID, kurį norime gauti
            
        Returns:
            Model: Modelio objektas arba None, jei nerasta
        """
        try:
            # Grąžiname modelį pagal ID iš repozitorijos
            return self.repository.get_by_id(model_id)
        except Exception as e:
            # Įrašome klaidos informaciją į žurnalą
            logger.error(f"Klaida gaunant modelį (ID: {model_id}): {str(e)}")
            # Grąžiname None, kad nurodyti, jog įvyko klaida
            return None
    
    def update_model(self, model_id, model_data):
        """
        Atnaujina esamą modelį.
        
        Args:
            model_id (str): Modelio ID, kurį norime atnaujinti
            model_data (dict): Nauji modelio duomenys
            
        Returns:
            Model: Atnaujintas modelio objektas arba None, jei nerasta
        """
        try:
            # Atnaujina modelį naudojant repozitorijos metodą
            return self.repository.update(model_id, model_data)
        except Exception as e:
            # Įrašome klaidos informaciją į žurnalą
            logger.error(f"Klaida atnaujinant modelį (ID: {model_id}): {str(e)}")
            # Atšaukiame transakciją, kad išvengtume duomenų nesuderinamumo
            self.session.rollback()
            # Grąžiname None, kad nurodyti, jog įvyko klaida
            return None
    
    def delete_model(self, model_id):
        """
        Ištrina modelį ir visus su juo susijusius duomenis.
        
        Args:
            model_id (str): Modelio ID, kurį norime ištrinti
            
        Returns:
            bool: True, jei ištrynimas sėkmingas, False kitu atveju
        """
        try:
            # Ištriname modelį naudodami repozitorijos metodą
            return self.repository.delete(model_id)
        except Exception as e:
            # Įrašome klaidos informaciją į žurnalą
            logger.error(f"Klaida trinant modelį (ID: {model_id}): {str(e)}")
            # Atšaukiame transakciją, kad išvengtume duomenų nesuderinamumo
            self.session.rollback()
            # Grąžiname False, kad nurodyti, jog įvyko klaida
            return False
    
    def list_models(self, limit=100, offset=0, model_type=None, sort_by="created_at", sort_order="desc"):
        """
        Gauna modelių sąrašą su galimybe filtruoti ir rikiuoti.
        
        Args:
            limit (int, optional): Maksimalus grąžinamų modelių skaičius
            offset (int, optional): Praleistų įrašų skaičius (puslapis)
            model_type (str, optional): Modelio tipo filtras
            sort_by (str, optional): Laukas, pagal kurį rikiuojama
            sort_order (str, optional): Rikiavimo tvarka ("asc" arba "desc")
            
        Returns:
            list: Modelių sąrašas arba tuščias sąrašas, jei įvyko klaida
        """
        try:
            # Patikrinkime parametrų korektiškumą
            if sort_order not in ["asc", "desc"]:
                # Jei neteisingas rikiavimo būdas, naudojame numatytąjį
                sort_order = "desc"
                
            # Grąžiname modelių sąrašą naudodami repozitorijos metodą
            return self.repository.list(limit, offset, model_type, sort_by, sort_order)
        except Exception as e:
            # Įrašome klaidos informaciją į žurnalą
            logger.error(f"Klaida gaunant modelių sąrašą: {str(e)}")
            # Grąžiname tuščią sąrašą, kad nurodyti, jog įvyko klaida
            return []