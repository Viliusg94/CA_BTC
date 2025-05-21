import unittest
import logging
import time
from datetime import datetime, timedelta
from app.tests.data_generator import TestDataGenerator
from app.services.results_service import ResultsService
from app.services.results_data_service import ResultsDataService
from database.db_utils import init_db, get_engine
from sqlalchemy import text

logger = logging.getLogger(__name__)

class IntegrationTests(unittest.TestCase):
    """
    Integraciniai testai rezultatų moduliui
    Testuoja duomenų bazės įrašymo/nuskaitymo operacijas ir ryšius tarp lentelių
    """
    
    @classmethod
    def setUpClass(cls):
        """
        Paruošia testavimo aplinką
        """
        # Inicializuojame duomenų bazę
        init_db()
        
        # Inicializuojame servisus
        cls.results_service = ResultsService()
        cls.data_service = ResultsDataService()
        
        # Inicializuojame duomenų generatorių
        cls.data_generator = TestDataGenerator()
        
        # Sukaičiuojame, kiek eilučių yra lentelėse prieš testus
        cls.rows_before = cls._count_table_rows()
        
        logger.info("Testų aplinka paruošta")
    
    @classmethod
    def tearDownClass(cls):
        """
        Išvalome testavimo aplinką
        """
        # Galima pridėti duomenų valymą po testų, jei reikia
        logger.info("Testų aplinka išvalyta")
    
    @classmethod
    def _count_table_rows(cls):
        """
        Suskaičiuoja eilučių skaičių kiekvienoje lentelėje
        
        Returns:
            dict: Lentelių eilučių skaičiai
        """
        engine, _ = init_db()
        counts = {}
        
        with engine.connect() as conn:
            for table in ['predictions', 'simulations', 'trades', 'metrics']:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                counts[table] = result.scalar()
                
        return counts
    
    def test_01_save_prediction(self):
        """
        Testuoja prognozės išsaugojimą
        """
        # Generuojame testinę prognozę
        prediction_data = self.data_generator.generate_prediction()
        
        # Išsaugome prognozę
        prediction_id = self.results_service.save_prediction(prediction_data)
        
        # Tikriname, ar gautas ID
        self.assertIsNotNone(prediction_id, "Nebuvo gautas prognozės ID")
        
        # Nuskaitome prognozę iš duomenų bazės
        saved_prediction = self.results_service.get_prediction(prediction_id)
        
        # Tikriname, ar duomenys teisingi
        self.assertEqual(saved_prediction['model_id'], prediction_data['model_id'])
        self.assertAlmostEqual(saved_prediction['predicted_value'], prediction_data['predicted_value'], delta=0.01)
        
        logger.info(f"Prognozė sėkmingai išsaugota ir nuskaityta, ID: {prediction_id}")
    
    def test_02_save_simulation_with_trades(self):
        """
        Testuoja simuliacijos su sandoriais išsaugojimą
        Tikrina ryšius tarp simuliacijos ir sandorių
        """
        # Generuojame testinę simuliaciją su sandoriais
        simulation_data, trades_data = self.data_generator.generate_simulation_with_trades(10)
        
        # Išsaugome simuliaciją
        simulation_id = self.results_service.save_simulation(simulation_data)
        
        # Tikriname, ar gautas ID
        self.assertIsNotNone(simulation_id, "Nebuvo gautas simuliacijos ID")
        
        # Išsaugome sandorius
        for trade_data in trades_data:
            trade_data['simulation_id'] = simulation_id
            trade_id = self.results_service.save_trade(trade_data)
            self.assertIsNotNone(trade_id, "Nebuvo gautas sandorio ID")
        
        # Nuskaitome simuliaciją iš duomenų bazės
        saved_simulation = self.results_service.get_simulation(simulation_id)
        
        # Tikriname, ar duomenys teisingi
        self.assertEqual(saved_simulation['name'], simulation_data['name'])
        self.assertAlmostEqual(saved_simulation['initial_capital'], simulation_data['initial_capital'], delta=0.01)
        
        # Nuskaitome simuliacijos sandorius
        saved_trades = self.results_service.get_simulation_trades(simulation_id)
        
        # Tikriname, ar sandoriai susieti su simuliacija
        self.assertEqual(len(saved_trades), len(trades_data))
        for trade in saved_trades:
            self.assertEqual(trade['simulation_id'], simulation_id)
        
        logger.info(f"Simuliacija su {len(trades_data)} sandoriais sėkmingai išsaugota ir nuskaityta, ID: {simulation_id}")
    
    def test_03_filter_predictions_by_date(self):
        """
        Testuoja prognozių filtravimą pagal datą
        """
        # Generuojame modelio ID ir prognozes
        model_id, predictions = self.data_generator.generate_model_with_predictions(predictions_count=20)
        
        # Išsaugome prognozes
        for prediction_data in predictions:
            self.results_service.save_prediction(prediction_data)
        
        # Nustatome datų intervalą
        start_date = datetime.now() - timedelta(days=60)
        end_date = datetime.now()
        
        # Gauname prognozes pagal datų intervalą
        filtered_predictions = self.results_service.get_predictions_by_date_range(
            model_id, start_date, end_date
        )
        
        # Tikriname, ar buvo gautos bent kelios prognozės
        self.assertGreater(len(filtered_predictions), 0, "Nebuvo rasta prognozių pagal datų intervalą")
        
        # Tikriname, ar visos prognozės atitinka modelio ID
        for prediction in filtered_predictions:
            self.assertEqual(prediction['model_id'], model_id)
            
            # Tikriname, ar data patenka į intervalą
            target_date = prediction['target_date']
            if isinstance(target_date, str):
                target_date = datetime.fromisoformat(target_date)
            self.assertTrue(start_date <= target_date <= end_date)
        
        logger.info(f"Sėkmingai filtruotos prognozės pagal datą, rasta: {len(filtered_predictions)}")
    
    def test_04_analyze_model(self):
        """
        Testuoja modelio analizę
        """
        # Generuojame modelio ID ir prognozes
        model_id, predictions = self.data_generator.generate_model_with_predictions(predictions_count=30)
        
        # Išsaugome prognozes
        for prediction_data in predictions:
            self.results_service.save_prediction(prediction_data)
        
        # Analizuojame modelį
        analysis_results = self.results_service.analyze_model(model_id)
        
        # Tikriname, ar analizės rezultatai turi visus reikiamus laukus
        self.assertEqual(analysis_results['model_id'], model_id)
        self.assertIn('predictions_count', analysis_results)
        self.assertIn('trend_analysis', analysis_results)
        self.assertIn('chart_data', analysis_results)
        
        logger.info(f"Sėkmingai atlikta modelio analizė, ID: {model_id}")
    
    def test_05_compare_models(self):
        """
        Testuoja modelių palyginimą
        """
        # Generuojame du modelius su prognozėmis
        model_id1, predictions1 = self.data_generator.generate_model_with_predictions(predictions_count=20)
        model_id2, predictions2 = self.data_generator.generate_model_with_predictions(predictions_count=20)
        
        # Išsaugome prognozes
        for prediction_data in predictions1:
            self.results_service.save_prediction(prediction_data)
        
        for prediction_data in predictions2:
            self.results_service.save_prediction(prediction_data)
        
        # Lyginame modelius
        comparison_results = self.results_service.compare_models([model_id1, model_id2])
        
        # Tikriname, ar palyginimo rezultatai turi visus reikiamus laukus
        self.assertIn('model_ids', comparison_results)
        self.assertIn('accuracy_comparison', comparison_results)
        
        logger.info(f"Sėkmingai palyginti modeliai: {model_id1}, {model_id2}")