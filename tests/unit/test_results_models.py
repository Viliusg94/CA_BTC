import unittest
from datetime import datetime
import json
from database.models.results_models import Prediction, Simulation, Trade, Metric

class TestResultsModels(unittest.TestCase):
    """
    Unit testai rezultatų modeliams
    """
    
    def test_prediction_to_dict(self):
        """
        Testuojame Prediction.to_dict metodą
        """
        # Sukuriame prognozės objektą
        prediction = Prediction(
            id='test-id',
            model_id='model-id',
            prediction_date=datetime(2023, 1, 1),
            target_date=datetime(2023, 1, 2),
            predicted_value=50000.0,
            actual_value=51000.0,
            interval='1d',
            confidence=0.9,
            created_at=datetime(2023, 1, 1)
        )
        
        # Gauname žodyną
        data = prediction.to_dict()
        
        # Tikriname rezultatus
        self.assertEqual(data['id'], 'test-id')
        self.assertEqual(data['model_id'], 'model-id')
        self.assertEqual(data['prediction_date'], '2023-01-01T00:00:00')
        self.assertEqual(data['target_date'], '2023-01-02T00:00:00')
        self.assertEqual(data['predicted_value'], 50000.0)
        self.assertEqual(data['actual_value'], 51000.0)
        self.assertEqual(data['interval'], '1d')
        self.assertEqual(data['confidence'], 0.9)
        self.assertEqual(data['created_at'], '2023-01-01T00:00:00')
    
    def test_prediction_from_dict(self):
        """
        Testuojame Prediction.from_dict metodą
        """
        # Sukuriame duomenų žodyną
        data = {
            'id': 'test-id',
            'model_id': 'model-id',
            'prediction_date': datetime(2023, 1, 1),
            'target_date': datetime(2023, 1, 2),
            'predicted_value': 50000.0,
            'actual_value': 51000.0,
            'interval': '1d',
            'confidence': 0.9,
            'created_at': datetime(2023, 1, 1)
        }
        
        # Sukuriame objektą iš žodyno
        prediction = Prediction.from_dict(data)
        
        # Tikriname rezultatus
        self.assertEqual(prediction.id, 'test-id')
        self.assertEqual(prediction.model_id, 'model-id')
        self.assertEqual(prediction.prediction_date, datetime(2023, 1, 1))
        self.assertEqual(prediction.target_date, datetime(2023, 1, 2))
        self.assertEqual(prediction.predicted_value, 50000.0)
        self.assertEqual(prediction.actual_value, 51000.0)
        self.assertEqual(prediction.interval, '1d')
        self.assertEqual(prediction.confidence, 0.9)
        self.assertEqual(prediction.created_at, datetime(2023, 1, 1))
    
    def test_simulation_to_dict(self):
        """
        Testuojame Simulation.to_dict metodą
        """
        # Sukuriame simuliacijos objektą
        simulation = Simulation(
            id='test-id',
            name='Test Simulation',
            initial_capital=10000.0,
            fees=0.001,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 30),
            strategy_type='simple',
            strategy_params=json.dumps({'param1': 'value1'}),
            final_balance=12000.0,
            profit_loss=2000.0,
            roi=20.0,
            max_drawdown=5.0,
            total_trades=100,
            winning_trades=60,
            losing_trades=40,
            is_completed=True,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 1, 30)
        )
        
        # Gauname žodyną
        data = simulation.to_dict()
        
        # Tikriname rezultatus
        self.assertEqual(data['id'], 'test-id')
        self.assertEqual(data['name'], 'Test Simulation')
        self.assertEqual(data['initial_capital'], 10000.0)
        self.assertEqual(data['fees'], 0.001)
        self.assertEqual(data['start_date'], '2023-01-01T00:00:00')
        self.assertEqual(data['end_date'], '2023-01-30T00:00:00')
        self.assertEqual(data['strategy_type'], 'simple')
        self.assertEqual(data['strategy_params'], {'param1': 'value1'})
        self.assertEqual(data['final_balance'], 12000.0)
        self.assertEqual(data['profit_loss'], 2000.0)
        self.assertEqual(data['roi'], 20.0)
        self.assertEqual(data['max_drawdown'], 5.0)
        self.assertEqual(data['total_trades'], 100)
        self.assertEqual(data['winning_trades'], 60)
        self.assertEqual(data['losing_trades'], 40)
        self.assertEqual(data['is_completed'], True)
        self.assertEqual(data['created_at'], '2023-01-01T00:00:00')
        self.assertEqual(data['updated_at'], '2023-01-30T00:00:00')

if __name__ == '__main__':
    unittest.main()