import unittest
from datetime import datetime, timedelta
from app.services.results_analysis_service import ResultsAnalysisService

class TestResultsAnalysisService(unittest.TestCase):
    """
    Unit testai ResultsAnalysisService klasei
    """
    
    def setUp(self):
        """
        Paruošia testų aplinką
        """
        self.service = ResultsAnalysisService()
        
        # Testiniai duomenys
        self.test_predictions = [
            {
                'id': 'pred1',
                'model_id': 'model1',
                'prediction_date': datetime(2023, 1, 1).isoformat(),
                'target_date': datetime(2023, 1, 5).isoformat(),
                'predicted_value': 50000.0,
                'actual_value': 51000.0,
                'interval': '1d',
                'confidence': 0.9
            },
            {
                'id': 'pred2',
                'model_id': 'model1',
                'prediction_date': datetime(2023, 1, 2).isoformat(),
                'target_date': datetime(2023, 1, 6).isoformat(),
                'predicted_value': 52000.0,
                'actual_value': 50000.0,
                'interval': '1d',
                'confidence': 0.8
            },
            {
                'id': 'pred3',
                'model_id': 'model1',
                'prediction_date': datetime(2023, 1, 3).isoformat(),
                'target_date': datetime(2023, 1, 7).isoformat(),
                'predicted_value': 51000.0,
                'actual_value': None,  # Dar nėra faktinės vertės
                'interval': '1d',
                'confidence': 0.7
            }
        ]
        
        self.test_simulations = [
            {
                'id': 'sim1',
                'name': 'Simulation 1',
                'strategy_type': 'macd',
                'initial_capital': 10000.0,
                'final_balance': 12000.0,
                'roi': 20.0,
                'max_drawdown': 5.0
            },
            {
                'id': 'sim2',
                'name': 'Simulation 2',
                'strategy_type': 'rsi',
                'initial_capital': 10000.0,
                'final_balance': 11000.0,
                'roi': 10.0,
                'max_drawdown': 8.0
            },
            {
                'id': 'sim3',
                'name': 'Simulation 3',
                'strategy_type': 'macd',
                'initial_capital': 10000.0,
                'final_balance': 9000.0,
                'roi': -10.0,
                'max_drawdown': 15.0
            }
        ]
    
    def test_filter_by_date_range(self):
        """
        Testuoja filtravimą pagal datų intervalą
        """
        # Testuojame filtravimą
        start_date = datetime(2023, 1, 5)
        end_date = datetime(2023, 1, 6)
        
        filtered = self.service.filter_by_date_range(
            self.test_predictions, start_date, end_date
        )
        
        # Tikriname rezultatus
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]['id'], 'pred1')
        self.assertEqual(filtered[1]['id'], 'pred2')
    
    def test_filter_by_accuracy(self):
        """
        Testuoja filtravimą pagal tikslumą
        """
        # Testuojame filtravimą
        filtered = self.service.filter_by_accuracy(
            self.test_predictions, min_accuracy=95
        )
        
        # Tikriname rezultatus
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['id'], 'pred1')
    
    def test_filter_simulations_by_performance(self):
        """
        Testuoja simuliacijų filtravimą pagal našumo rodiklius
        """
        # Testuojame filtravimą
        filtered = self.service.filter_simulations_by_performance(
            self.test_simulations, min_roi=15, max_drawdown=10
        )
        
        # Tikriname rezultatus
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['id'], 'sim1')
    
    def test_group_simulations_by_strategy(self):
        """
        Testuoja simuliacijų grupavimą pagal strategiją
        """
        # Testuojame grupavimą
        grouped = self.service.group_simulations_by_strategy(
            self.test_simulations
        )
        
        # Tikriname rezultatus
        self.assertEqual(len(grouped), 2)  # 2 strategijos (macd, rsi)
        self.assertEqual(len(grouped['macd']), 2)
        self.assertEqual(len(grouped['rsi']), 1)
        self.assertEqual(grouped['macd'][0]['id'], 'sim1')
        self.assertEqual(grouped['rsi'][0]['id'], 'sim2')
    
    def test_to_dataframe(self):
        """
        Testuoja konvertavimą į DataFrame
        """
        # Testuojame konvertavimą
        df = self.service.to_dataframe(self.test_predictions)
        
        # Tikriname rezultatus
        self.assertEqual(len(df), 3)
        self.assertTrue('model_id' in df.columns)
        self.assertTrue('predicted_value' in df.columns)
        self.assertEqual(df.iloc[0]['id'], 'pred1')

if __name__ == '__main__':
    unittest.main()