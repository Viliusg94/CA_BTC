import logging
import uuid
from datetime import datetime, timedelta
from database.db_utils import init_db
from database.repository.results_repository import PredictionRepository, SimulationRepository, TradeRepository, MetricRepository

logger = logging.getLogger(__name__)

class ResultsDataService:
    """
    Servisas darbui su rezultatų duomenimis
    """
    
    def __init__(self):
        """
        Inicializuoja ResultsDataService
        """
        # Inicializuojame duomenų bazę
        _, Session = init_db()
        self.session = Session()
        
        # Inicializuojame repozitorijas
        self.prediction_repo = PredictionRepository(self.session)
        self.simulation_repo = SimulationRepository(self.session)
        self.trade_repo = TradeRepository(self.session)
        self.metric_repo = MetricRepository(self.session)
    
    def save_prediction(self, prediction_data):
        """
        Išsaugo prognozę
        
        Args:
            prediction_data (dict): Prognozės duomenys
            
        Returns:
            str: Prognozės ID arba None
        """
        try:
            # Sukuriame naują prognozės objektą
            prediction = self.prediction_repo.create(prediction_data)
            
            if prediction:
                return prediction.id
            return None
        except Exception as e:
            logger.error(f"Klaida išsaugojant prognozę: {str(e)}")
            return None
    
    def get_prediction(self, prediction_id):
        """
        Gauna prognozę pagal ID
        
        Args:
            prediction_id (str): Prognozės ID
            
        Returns:
            dict: Prognozės duomenys arba None
        """
        try:
            prediction = self.prediction_repo.get_by_id(prediction_id)
            
            if prediction:
                return prediction.to_dict()
            return None
        except Exception as e:
            logger.error(f"Klaida gaunant prognozę: {str(e)}")
            return None
    
    def get_model_predictions(self, model_id, limit=100):
        """
        Gauna modelio prognozes
        
        Args:
            model_id (str): Modelio ID
            limit (int): Maksimalus įrašų skaičius
            
        Returns:
            list: Prognozių sąrašas
        """
        try:
            predictions = self.prediction_repo.get_by_model_id(model_id, limit)
            return [prediction.to_dict() for prediction in predictions]
        except Exception as e:
            logger.error(f"Klaida gaunant modelio prognozes: {str(e)}")
            return []
    
    def get_predictions_by_date_range(self, model_id, start_date, end_date):
        """
        Gauna prognozes pagal datų intervalą
        
        Args:
            model_id (str): Modelio ID
            start_date (datetime): Pradžios data
            end_date (datetime): Pabaigos data
            
        Returns:
            list: Prognozių sąrašas
        """
        try:
            # Gaukime visas modelio prognozes
            all_predictions = self.get_model_predictions(model_id, limit=1000)
            
            # Filtruokime pagal datų intervalą
            filtered_predictions = []
            for prediction in all_predictions:
                target_date = prediction['target_date']
                if isinstance(target_date, str):
                    target_date = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
                    
                if start_date <= target_date <= end_date:
                    filtered_predictions.append(prediction)
                    
            return filtered_predictions
        except Exception as e:
            logger.error(f"Klaida gaunant prognozes pagal datų intervalą: {str(e)}")
            return []
    
    def get_prediction_accuracy(self, model_id, days=30):
        """
        Gauna modelio prognozių tikslumą
        
        Args:
            model_id (str): Modelio ID
            days (int): Dienų skaičius atgal
            
        Returns:
            dict: Tikslumo metrikos
        """
        try:
            # Gaukime visas modelio prognozes su faktinėmis reikšmėmis
            predictions = self.get_model_predictions(model_id, limit=1000)
            
            # Filtruokime pagal laikotarpį ir faktines reikšmes
            start_date = datetime.now() - timedelta(days=days)
            filtered_predictions = []
            
            for prediction in predictions:
                # Jei nėra faktinės reikšmės, praleiskime
                if prediction['actual_value'] is None:
                    continue
                    
                # Jei data sena, praleiskime
                target_date = prediction['target_date']
                if isinstance(target_date, str):
                    target_date = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
                    
                if target_date < start_date:
                    continue
                    
                filtered_predictions.append(prediction)
            
            # Jei nėra prognozių su faktinėmis reikšmėmis, grąžinkime tuščią metriką
            if not filtered_predictions:
                return {
                    'model_id': model_id,
                    'accuracy': 0,
                    'error': 0,
                    'predictions_count': 0
                }
            
            # Skaičiuojame tikslumo metrikas
            total_error = 0
            for prediction in filtered_predictions:
                predicted = prediction['predicted_value']
                actual = prediction['actual_value']
                
                # Jei reikšmės neaiškios, praleiskime
                if predicted is None or actual is None:
                    continue
                    
                # Skaičiuojame procentinę paklaidą
                if actual != 0:
                    error = abs((predicted - actual) / actual) * 100
                else:
                    error = 100
                    
                total_error += error
            
            avg_error = total_error / len(filtered_predictions)
            accuracy = max(0, 100 - avg_error)
            
            return {
                'model_id': model_id,
                'accuracy': accuracy,
                'error': avg_error,
                'predictions_count': len(filtered_predictions)
            }
        except Exception as e:
            logger.error(f"Klaida skaičiuojant modelio tikslumą: {str(e)}")
            return {
                'model_id': model_id,
                'accuracy': 0,
                'error': 0,
                'predictions_count': 0
            }
    
    def save_simulation(self, simulation_data):
        """
        Išsaugo simuliaciją
        
        Args:
            simulation_data (dict): Simuliacijos duomenys
            
        Returns:
            str: Simuliacijos ID arba None
        """
        try:
            # Sukuriame naują simuliacijos objektą
            simulation = self.simulation_repo.create(simulation_data)
            
            if simulation:
                return simulation.id
            return None
        except Exception as e:
            logger.error(f"Klaida išsaugojant simuliaciją: {str(e)}")
            return None
    
    def get_simulation(self, simulation_id):
        """
        Gauna simuliaciją pagal ID
        
        Args:
            simulation_id (str): Simuliacijos ID
            
        Returns:
            dict: Simuliacijos duomenys arba None
        """
        try:
            simulation = self.simulation_repo.get_by_id(simulation_id)
            
            if simulation:
                return simulation.to_dict()
            return None
        except Exception as e:
            logger.error(f"Klaida gaunant simuliaciją: {str(e)}")
            return None
    
    def save_trade(self, trade_data):
        """
        Išsaugo prekybos sandorį
        
        Args:
            trade_data (dict): Sandorio duomenys
            
        Returns:
            str: Sandorio ID arba None
        """
        try:
            # Sukuriame naują sandorio objektą
            trade = self.trade_repo.create(trade_data)
            
            if trade:
                return trade.id
            return None
        except Exception as e:
            logger.error(f"Klaida išsaugojant sandorį: {str(e)}")
            return None
    
    def get_trade(self, trade_id):
        """
        Gauna sandorį pagal ID
        
        Args:
            trade_id (str): Sandorio ID
            
        Returns:
            dict: Sandorio duomenys arba None
        """
        try:
            trade = self.trade_repo.get_by_id(trade_id)
            
            if trade:
                return trade.to_dict()
            return None
        except Exception as e:
            logger.error(f"Klaida gaunant sandorį: {str(e)}")
            return None
    
    def get_simulation_trades(self, simulation_id):
        """
        Gauna simuliacijos sandorius
        
        Args:
            simulation_id (str): Simuliacijos ID
            
        Returns:
            list: Sandorių sąrašas
        """
        try:
            trades = self.trade_repo.get_by_simulation_id(simulation_id)
            return [trade.to_dict() for trade in trades]
        except Exception as e:
            logger.error(f"Klaida gaunant simuliacijos sandorius: {str(e)}")
            return []