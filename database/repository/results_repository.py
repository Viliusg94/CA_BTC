import logging
import uuid
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc

# Bandome tiesiogiai importuoti, be paketų
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Alternatyvus importavimas
try:
    from database.models.results_models import Prediction, Simulation, Trade, Metric
except ImportError:
    # Jei nepavyksta importuoti per paketą, bandome naudoti tiesioginį kelią
    import os
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(current_dir, '..', 'models')
    if models_dir not in sys.path:
        sys.path.insert(0, models_dir)
    from results_models import Prediction, Simulation, Trade, Metric

logger = logging.getLogger(__name__)

class BaseRepository:
    """
    Bazinė repozitorijos klasė, kuri realizuoja bendrus metodus
    """
    
    def __init__(self, session):
        """
        Inicializuoja repozitoriją
        
        Args:
            session (Session): SQLAlchemy sesija
        """
        self.session = session
    
    def save(self, obj):
        """
        Išsaugo objektą duomenų bazėje
        
        Args:
            obj: Duomenų bazės modelio objektas
            
        Returns:
            bool: Ar pavyko išsaugoti
        """
        try:
            self.session.add(obj)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida išsaugant objektą: {str(e)}")
            return False
    
    def delete(self, obj):
        """
        Ištrina objektą iš duomenų bazės
        
        Args:
            obj: Duomenų bazės modelio objektas
            
        Returns:
            bool: Ar pavyko ištrinti
        """
        try:
            self.session.delete(obj)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida ištrinant objektą: {str(e)}")
            return False


class PredictionRepository(BaseRepository):
    """
    Repozitorija darbui su prognozėmis
    """
    
    def get_by_id(self, prediction_id):
        """
        Gauna prognozę pagal ID
        
        Args:
            prediction_id (str): Prognozės ID
            
        Returns:
            Prediction: Prognozės objektas arba None
        """
        try:
            return self.session.query(Prediction).filter_by(id=prediction_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant prognozę pagal ID: {str(e)}")
            return None
    
    def get_by_model_id(self, model_id, limit=100):
        """
        Gauna modelio prognozes
        
        Args:
            model_id (str): Modelio ID
            limit (int): Maksimalus įrašų skaičius
            
        Returns:
            list: Prognozių sąrašas
        """
        try:
            return self.session.query(Prediction).filter_by(model_id=model_id).order_by(desc(Prediction.target_date)).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant modelio prognozes: {str(e)}")
            return []
    
    def get_recent_predictions(self, limit=100):
        """
        Gauna naujausias prognozes
        
        Args:
            limit (int): Maksimalus įrašų skaičius
            
        Returns:
            list: Prognozių sąrašas
        """
        try:
            return self.session.query(Prediction).order_by(desc(Prediction.prediction_date)).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant naujausias prognozes: {str(e)}")
            return []
    
    # Pakeistas create metodas
    def create(self, data):
        """
        Sukuria naują prognozę
        
        Args:
            data (dict): Prognozės duomenys
            
        Returns:
            Prediction: Sukurtas prognozės objektas arba None
        """
        try:
            # Jei nenurodyta, sugeneruojame ID
            if 'id' not in data:
                data['id'] = str(uuid.uuid4())
                
            # Jei perduota date reikšmė yra string formatu, konvertuojame
            date_fields = ['prediction_date', 'target_date', 'created_at']
            for field in date_fields:
                if field in data and isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
        
            # Sukuriame naują prognozės objektą
            from database.models.results_models import Prediction
            prediction = Prediction(**data)
            
            # Išsaugome
            if self.save(prediction):
                return prediction
            return None
        except Exception as e:
            logger.error(f"Klaida kuriant prognozę: {str(e)}")
            return None

    def update_actual_value(self, prediction_id, actual_value):
        """
        Atnaujina faktinę prognozės vertę
        
        Args:
            prediction_id (str): Prognozės ID
            actual_value (float): Faktinė vertė
            
        Returns:
            bool: Ar pavyko atnaujinti
        """
        try:
            prediction = self.get_by_id(prediction_id)
            if prediction:
                prediction.actual_value = actual_value
                return self.save(prediction)
            return False
        except Exception as e:
            logger.error(f"Klaida atnaujinant faktinę vertę: {str(e)}")
            return False


class SimulationRepository(BaseRepository):
    """
    Repozitorija darbui su simuliacijomis
    """
    
    def get_by_id(self, simulation_id):
        """
        Gauna simuliaciją pagal ID
        
        Args:
            simulation_id (str): Simuliacijos ID
            
        Returns:
            Simulation: Simuliacijos objektas arba None
        """
        try:
            return self.session.query(Simulation).filter_by(id=simulation_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant simuliaciją pagal ID: {str(e)}")
            return None
    
    def get_all(self, limit=100):
        """
        Gauna visas simuliacijas
        
        Args:
            limit (int): Maksimalus įrašų skaičius
            
        Returns:
            list: Simuliacijų sąrašas
        """
        try:
            return self.session.query(Simulation).order_by(desc(Simulation.created_at)).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant simuliacijas: {str(e)}")
            return []
    
    def create(self, data):
        """
        Sukuria naują simuliaciją
        
        Args:
            data (dict): Simuliacijos duomenys
            
        Returns:
            Simulation: Sukurtas simuliacijos objektas arba None
        """
        try:
            # Jei nenurodyta, sugeneruojame ID
            if 'id' not in data:
                data['id'] = str(uuid.uuid4())
                
            # Sukuriame naują simuliacijos objektą
            simulation = Simulation(**data)
            
            # Išsaugome
            if self.save(simulation):
                return simulation
            return None
        except Exception as e:
            logger.error(f"Klaida kuriant simuliaciją: {str(e)}")
            return None
    
    def update(self, simulation_id, data):
        """
        Atnaujina simuliaciją
        
        Args:
            simulation_id (str): Simuliacijos ID
            data (dict): Atnaujinimo duomenys
            
        Returns:
            bool: Ar pavyko atnaujinti
        """
        try:
            simulation = self.get_by_id(simulation_id)
            if simulation:
                # Atnaujiname laukus
                for key, value in data.items():
                    if hasattr(simulation, key):
                        setattr(simulation, key, value)
                
                # Atnaujiname updated_at lauką
                simulation.updated_at = datetime.utcnow()
                
                return self.save(simulation)
            return False
        except Exception as e:
            logger.error(f"Klaida atnaujinant simuliaciją: {str(e)}")
            return False


class TradeRepository(BaseRepository):
    """
    Repozitorija darbui su sandoriais
    """
    
    def get_by_id(self, trade_id):
        """
        Gauna sandorį pagal ID
        
        Args:
            trade_id (str): Sandorio ID
            
        Returns:
            Trade: Sandorio objektas arba None
        """
        try:
            return self.session.query(Trade).filter_by(id=trade_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant sandorį pagal ID: {str(e)}")
            return None
    
    def get_by_simulation_id(self, simulation_id):
        """
        Gauna simuliacijos sandorius
        
        Args:
            simulation_id (str): Simuliacijos ID
            
        Returns:
            list: Sandorių sąrašas
        """
        try:
            return self.session.query(Trade).filter_by(simulation_id=simulation_id).order_by(Trade.date).all()
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant simuliacijos sandorius: {str(e)}")
            return []
    
    def create(self, data):
        """
        Sukuria naują sandorį
        
        Args:
            data (dict): Sandorio duomenys
            
        Returns:
            Trade: Sukurtas sandorio objektas arba None
        """
        try:
            # Jei nenurodyta, sugeneruojame ID
            if 'id' not in data:
                data['id'] = str(uuid.uuid4())
                
            # Sukuriame naują sandorio objektą
            trade = Trade(**data)
            
            # Išsaugome
            if self.save(trade):
                return trade
            return None
        except Exception as e:
            logger.error(f"Klaida kuriant sandorį: {str(e)}")
            return None


class MetricRepository(BaseRepository):
    """
    Repozitorija darbui su metrikomis
    """
    
    def get_by_id(self, metric_id):
        """
        Gauna metriką pagal ID
        
        Args:
            metric_id (str): Metrikos ID
            
        Returns:
            Metric: Metrikos objektas arba None
        """
        try:
            return self.session.query(Metric).filter_by(id=metric_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant metriką pagal ID: {str(e)}")
            return None
    
    def get_by_model_id(self, model_id):
        """
        Gauna modelio metrikas
        
        Args:
            model_id (str): Modelio ID
            
        Returns:
            list: Metrikų sąrašas
        """
        try:
            return self.session.query(Metric).filter_by(model_id=model_id).order_by(desc(Metric.date)).all()
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant modelio metrikas: {str(e)}")
            return []
    
    def get_by_simulation_id(self, simulation_id):
        """
        Gauna simuliacijos metrikas
        
        Args:
            simulation_id (str): Simuliacijos ID
            
        Returns:
            list: Metrikų sąrašas
        """
        try:
            return self.session.query(Metric).filter_by(simulation_id=simulation_id).order_by(desc(Metric.date)).all()
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant simuliacijos metrikas: {str(e)}")
            return []
    
    def create(self, data):
        """
        Sukuria naują metriką
        
        Args:
            data (dict): Metrikos duomenys
            
        Returns:
            Metric: Sukurtas metrikos objektas arba None
        """
        try:
            # Jei nenurodyta, sugeneruojame ID
            if 'id' not in data:
                data['id'] = str(uuid.uuid4())
                
            # Jei nenurodyta data, nustatome dabartinę
            if 'date' not in data:
                data['date'] = datetime.utcnow()
                
            # Sukuriame naują metrikos objektą
            metric = Metric(**data)
            
            # Išsaugome
            if self.save(metric):
                return metric
            return None
        except Exception as e:
            logger.error(f"Klaida kuriant metriką: {str(e)}")
            return None