"""
Servisas darbui su prekybos sandoriais.
"""
import logging
from database.repository.trade_repository import TradeRepository
from database.models.results_models import Trade

# Konfigūruojame žurnalą
logger = logging.getLogger(__name__)

class TradeService:
    """
    Servisas, atsakingas už operacijas su prekybos sandoriais.
    """
    
    def __init__(self, db_session):
        """
        Inicializuoja TradeService objektą.
        
        Args:
            db_session: SQLAlchemy sesija, naudojama darbui su duomenų baze
        """
        # Sukuriame sandorių repozitoriją naudodami pateiktą sesiją
        self.repository = TradeRepository(db_session)
        # Išsaugome sesiją ateities naudojimui
        self.session = db_session
    
    def create_trade(self, trade_data):
        """
        Sukuria naują prekybos sandorį duomenų bazėje.
        
        Args:
            trade_data (dict): Prekybos sandorio duomenys
            
        Returns:
            Trade: Sukurtas sandorio objektas arba None, jei nepavyko sukurti
        """
        try:
            # Patikriname, ar yra portfolio_id, kuris yra privalomas
            if 'portfolio_id' not in trade_data or trade_data['portfolio_id'] is None:
                logger.warning("Bandome sukurti sandorį be portfolio_id reikšmės")
                
            # Sukuriame sandorio objektą iš duomenų žodyno
            trade = Trade.from_dict(trade_data)
            # Išsaugome sandorį duomenų bazėje per repozitoriją
            return self.repository.create(trade)
        except Exception as e:
            # Įrašome klaidos informaciją į žurnalą
            logger.error(f"Klaida: {str(e)}")
            # Atšaukiame transakciją, kad išvengtume duomenų nesuderinamumo
            self.session.rollback()
            # Grąžiname None, kad nurodyti, jog įvyko klaida
            return None
    
    def get_trade(self, trade_id):
        """
        Gauna prekybos sandorį pagal jo ID.
        
        Args:
            trade_id (int): Prekybos sandorio ID, kurį norime gauti
            
        Returns:
            Trade: Sandorio objektas arba None, jei nerasta
        """
        try:
            # Grąžiname sandorį pagal ID iš repozitorijos
            return self.repository.get_by_id(trade_id)
        except Exception as e:
            # Įrašome klaidos informaciją į žurnalą
            logger.error(f"Klaida gaunant prekybos sandorį (ID: {trade_id}): {str(e)}")
            # Grąžiname None, kad nurodyti, jog įvyko klaida
            return None
    
    def update_trade(self, trade_id, trade_data):
        """
        Atnaujina esamą prekybos sandorį.
        
        Args:
            trade_id (int): Sandorio ID, kurį norime atnaujinti
            trade_data (dict): Nauji sandorio duomenys
            
        Returns:
            Trade: Atnaujintas sandorio objektas arba None, jei nerasta
        """
        try:
            # Atnaujina sandorį naudojant repozitorijos metodą
            return self.repository.update(trade_id, trade_data)
        except Exception as e:
            # Įrašome klaidos informaciją į žurnalą
            logger.error(f"Klaida atnaujinant prekybos sandorį (ID: {trade_id}): {str(e)}")
            # Atšaukiame transakciją, kad išvengtume duomenų nesuderinamumo
            self.session.rollback()
            # Grąžiname None, kad nurodyti, jog įvyko klaida
            return None
    
    def delete_trade(self, trade_id):
        """
        Ištrina prekybos sandorį.
        
        Args:
            trade_id (int): Sandorio ID, kurį norime ištrinti
            
        Returns:
            bool: True, jei ištrynimas sėkmingas, False kitu atveju
        """
        try:
            # Ištriname sandorį naudodami repozitorijos metodą
            return self.repository.delete(trade_id)
        except Exception as e:
            # Įrašome klaidos informaciją į žurnalą
            logger.error(f"Klaida trinant prekybos sandorį (ID: {trade_id}): {str(e)}")
            # Atšaukiame transakciją, kad išvengtume duomenų nesuderinamumo
            self.session.rollback()
            # Grąžiname False, kad nurodyti, jog įvyko klaida
            return False
    
    def list_trades(self, limit=100, offset=0, simulation_id=None, trade_type=None, date_from=None, date_to=None, sort_by="date", sort_order="desc"):
        """
        Gauna prekybos sandorių sąrašą su galimybe filtruoti ir rikiuoti.
        
        Args:
            limit (int, optional): Maksimalus grąžinamų sandorių skaičius
            offset (int, optional): Praleistų įrašų skaičius (puslapis)
            simulation_id (str, optional): Filtravimas pagal simuliacijos ID
            trade_type (str, optional): Filtravimas pagal sandorio tipą
            date_from (datetime, optional): Filtravimas pagal pradžios datą
            date_to (datetime, optional): Filtravimas pagal pabaigos datą
            sort_by (str, optional): Laukas, pagal kurį rikiuojama
            sort_order (str, optional): Rikiavimo tvarka ("asc" arba "desc")
            
        Returns:
            list: Sandorių sąrašas arba tuščias sąrašas, jei įvyko klaida
        """
        try:
            # Patikrinkime parametrų korektiškumą
            if sort_order not in ["asc", "desc"]:
                sort_order = "desc"
                
            # Grąžiname sandorių sąrašą naudodami repozitorijos metodą
            return self.repository.list(limit, offset, simulation_id, trade_type, date_from, date_to, sort_by, sort_order)
        except Exception as e:
            # Įrašome klaidos informaciją į žurnalą
            logger.error(f"Klaida gaunant prekybos sandorių sąrašą: {str(e)}")
            # Grąžiname tuščią sąrašą, kad nurodyti, jog įvyko klaida
            return []