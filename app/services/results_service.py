import logging
import uuid
from datetime import datetime
from app.services.results_data_service import ResultsDataService

logger = logging.getLogger(__name__)

class ResultsService:
    """
    Servisas darbui su rezultatais
    """
    
    def __init__(self):
        """
        Inicializuoja ResultsService
        """
        self.data_service = ResultsDataService()
    
    def save_prediction(self, prediction_data):
        """
        Išsaugo prognozę
        
        Args:
            prediction_data (dict): Prognozės duomenys
            
        Returns:
            dict: Išsaugota prognozė arba None
        """
        try:
            # Jei nenurodyta, sugeneruojame ID
            if 'id' not in prediction_data:
                prediction_data['id'] = str(uuid.uuid4())
                
            # Jei nenurodyta, nustatome dabartinę datą
            if 'prediction_date' not in prediction_data:
                prediction_data['prediction_date'] = datetime.utcnow()
                
            # Išsaugome duomenų bazėje
            prediction_id = self.data_service.save_prediction(prediction_data)
            
            if prediction_id:
                return prediction_id
            return None
        except Exception as e:
            logger.error(f"Klaida išsaugant prognozę: {str(e)}")
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
            return self.data_service.get_prediction(prediction_id)
        except Exception as e:
            logger.error(f"Klaida gaunant prognozę: {str(e)}")
            return None
    
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
            return self.data_service.get_predictions_by_date_range(model_id, start_date, end_date)
        except Exception as e:
            logger.error(f"Klaida gaunant prognozes pagal datų intervalą: {str(e)}")
            return []
    
    def analyze_model(self, model_id):
        """
        Analizuoja modelį
        
        Args:
            model_id (str): Modelio ID
            
        Returns:
            dict: Analizės rezultatai
        """
        try:
            # Gauname modelio prognozes
            predictions = self.data_service.get_model_predictions(model_id)
            
            # Jei nėra prognozių, grąžinkime tuščią analizę
            if not predictions:
                return {
                    'model_id': model_id,
                    'predictions_count': 0,
                    'trend_analysis': None,
                    'chart_data': []
                }
            
            # Analizuojame tendencijas
            values = [prediction['predicted_value'] for prediction in predictions if prediction['predicted_value'] is not None]
            
            if values:
                avg_value = sum(values) / len(values)
                min_value = min(values)
                max_value = max(values)
                
                # Paprasčiausia tendencijos analizė
                if values[-1] > values[0]:
                    trend = "up"
                elif values[-1] < values[0]:
                    trend = "down"
                else:
                    trend = "stable"
                    
                trend_analysis = {
                    'trend': trend,
                    'avg_value': avg_value,
                    'min_value': min_value,
                    'max_value': max_value
                }
            else:
                trend_analysis = None
                
            # Paruošiame duomenis grafikui
            chart_data = []
            for prediction in predictions:
                # Sugrupuokime pagal datą
                chart_data.append({
                    'date': prediction['target_date'],
                    'predicted': prediction['predicted_value'],
                    'actual': prediction['actual_value']
                })
                
            # Grąžinkime analizės rezultatus
            return {
                'model_id': model_id,
                'predictions_count': len(predictions),
                'trend_analysis': trend_analysis,
                'chart_data': chart_data
            }
        except Exception as e:
            logger.error(f"Klaida analizuojant modelį: {str(e)}")
            return {
                'model_id': model_id,
                'predictions_count': 0,
                'trend_analysis': None,
                'chart_data': []
            }
    
    def compare_models(self, model_ids):
        """
        Palygina kelis modelius
        
        Args:
            model_ids (list): Modelių ID sąrašas
            
        Returns:
            dict: Palyginimo rezultatai
        """
        try:
            # Tikriname, ar yra modelių
            if not model_ids:
                return {
                    'model_ids': [],
                    'accuracy_comparison': []
                }
                
            # Gaukime kiekvieno modelio tikslumą
            accuracy_comparison = []
            for model_id in model_ids:
                accuracy = self.data_service.get_prediction_accuracy(model_id)
                accuracy_comparison.append(accuracy)
                
            # Grąžinkime palyginimo rezultatus
            return {
                'model_ids': model_ids,
                'accuracy_comparison': accuracy_comparison
            }
        except Exception as e:
            logger.error(f"Klaida lyginant modelius: {str(e)}")
            return {
                'model_ids': model_ids,
                'accuracy_comparison': []
            }
    
    def save_simulation(self, simulation_data):
        """
        Išsaugo simuliaciją
        
        Args:
            simulation_data (dict): Simuliacijos duomenys
            
        Returns:
            dict: Išsaugota simuliacija arba None
        """
        try:
            # Jei nenurodyta, sugeneruojame ID
            if 'id' not in simulation_data:
                simulation_data['id'] = str(uuid.uuid4())
                
            # Išsaugome duomenų bazėje
            simulation_id = self.data_service.save_simulation(simulation_data)
            
            if simulation_id:
                return simulation_id
            return None
        except Exception as e:
            logger.error(f"Klaida išsaugant simuliaciją: {str(e)}")
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
            return self.data_service.get_simulation(simulation_id)
        except Exception as e:
            logger.error(f"Klaida gaunant simuliaciją: {str(e)}")
            return None
    
    def save_trade(self, trade_data):
        """
        Išsaugo prekybos sandorį
        
        Args:
            trade_data (dict): Sandorio duomenys
            
        Returns:
            dict: Išsaugotas sandoris arba None
        """
        try:
            # Jei nenurodyta, sugeneruojame ID
            if 'id' not in trade_data:
                trade_data['id'] = str(uuid.uuid4())
                
            # Jei nenurodyta, nustatome dabartinę datą
            if 'date' not in trade_data:
                trade_data['date'] = datetime.utcnow()
                
            # Išsaugome duomenų bazėje
            trade_id = self.data_service.save_trade(trade_data)
            
            if trade_id:
                return trade_id
            return None
        except Exception as e:
            logger.error(f"Klaida išsaugant sandorį: {str(e)}")
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
            return self.data_service.get_trade(trade_id)
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
            return self.data_service.get_simulation_trades(simulation_id)
        except Exception as e:
            logger.error(f"Klaida gaunant simuliacijos sandorius: {str(e)}")
            return []
    
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
            return self.data_service.get_model_predictions(model_id, limit)
        except Exception as e:
            logger.error(f"Klaida gaunant modelio prognozes: {str(e)}")
            return []