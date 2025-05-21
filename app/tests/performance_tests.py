import logging
import time
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from app.tests.data_generator import TestDataGenerator
from app.services.results_service import ResultsService
from app.services.results_data_service import ResultsDataService
from database.db_utils import init_db, get_engine

logger = logging.getLogger(__name__)

class PerformanceTests:
    """
    Našumo testų klasė
    Testuoja užklausų efektyvumą su dideliais duomenų kiekiais
    """
    
    def __init__(self):
        """
        Inicializuoja testavimo aplinką
        """
        # Inicializuojame duomenų bazę
        init_db()
        
        # Inicializuojame servisus
        self.results_service = ResultsService()
        self.data_service = ResultsDataService()
        
        # Inicializuojame duomenų generatorių
        self.data_generator = TestDataGenerator()
        
        # Testų rezultatų saugojimui
        self.results = []
    
    def generate_large_dataset(self, predictions_count=1000, simulations_count=100, trades_per_simulation=50):
        """
        Generuoja didelį duomenų rinkinį
        
        Args:
            predictions_count (int): Prognozių skaičius
            simulations_count (int): Simuliacijų skaičius
            trades_per_simulation (int): Sandorių skaičius vienai simuliacijai
            
        Returns:
            tuple: (model_ids, simulation_ids) - sugeneruotų objektų ID
        """
        logger.info(f"Generuojami testiniai duomenys: {predictions_count} prognozės, {simulations_count} simuliacijos")
        start_time = time.time()
        
        # Generuojame modelių ID
        model_ids = [self.data_generator.generate_random_uuid() for _ in range(5)]
        
        # Generuojame ir išsaugome prognozes
        predictions_per_model = predictions_count // len(model_ids)
        for model_id in model_ids:
            model_predictions = self.data_generator.generate_bulk_predictions(predictions_per_model, model_id)
            for prediction_data in model_predictions:
                self.results_service.save_prediction(prediction_data)
        
        # Generuojame ir išsaugome simuliacijas su sandoriais
        simulation_ids = []
        for _ in range(simulations_count):
            simulation_data, trades_data = self.data_generator.generate_simulation_with_trades(trades_per_simulation)
            simulation_id = self.results_service.save_simulation(simulation_data)
            simulation_ids.append(simulation_id)
            
            for trade_data in trades_data:
                trade_data['simulation_id'] = simulation_id
                self.results_service.save_trade(trade_data)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Duomenų generavimas užbaigtas per {elapsed_time:.2f} sekundes")
        
        return (model_ids, simulation_ids)
    
    def measure_query_performance(self, query_function, *args, iterations=5, **kwargs):
        """
        Matuoja užklausos vykdymo laiką
        
        Args:
            query_function: Funkcija, kurią testuosime
            iterations (int): Iteracijų skaičius
            *args, **kwargs: Parametrai funkcijai
            
        Returns:
            dict: Našumo rezultatai
        """
        execution_times = []
        
        for i in range(iterations):
            start_time = time.time()
            result = query_function(*args, **kwargs)
            elapsed_time = time.time() - start_time
            execution_times.append(elapsed_time)
            
            # Trumpas pauzės laikas, kad išvengti DB perkrovimo
            time.sleep(0.1)
        
        avg_time = sum(execution_times) / iterations
        min_time = min(execution_times)
        max_time = max(execution_times)
        
        # Rezultatų žodynas
        performance = {
            'function': query_function.__name__,
            'iterations': iterations,
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'result_size': len(result) if isinstance(result, list) else 1
        }
        
        # Pridedame rezultatus į bendrą sąrašą
        self.results.append(performance)
        
        logger.info(f"Funkcija {query_function.__name__}: vid. laikas {avg_time:.4f}s, rezultatų: {performance['result_size']}")
        
        return performance
    
    def run_performance_tests(self, dataset_size='medium'):
        """
        Vykdo visus našumo testus
        
        Args:
            dataset_size (str): Duomenų rinkinio dydis ('small', 'medium', 'large')
            
        Returns:
            pd.DataFrame: Našumo testų rezultatai
        """
        # Duomenų rinkinio dydžiai
        sizes = {
            'small': (100, 10, 20),
            'medium': (1000, 50, 50),
            'large': (10000, 200, 100)
        }
        
        # Generuojame duomenis
        predictions_count, simulations_count, trades_per_simulation = sizes.get(dataset_size, sizes['medium'])
        model_ids, simulation_ids = self.generate_large_dataset(predictions_count, simulations_count, trades_per_simulation)
        
        # Testavimo laikas
        test_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Testuojame įvairias užklausas
        logger.info("Pradedami našumo testai...")
        
        # 1. Prognozių gavimas pagal modelį
        for model_id in model_ids[:2]:  # Testuojame tik pirmus 2 modelius
            self.measure_query_performance(
                self.results_service.get_model_predictions,
                model_id
            )
        
        # 2. Prognozių filtravimas pagal datą
        for model_id in model_ids[:2]:
            start_date = datetime(2023, 1, 1)
            end_date = datetime(2023, 6, 30)
            self.measure_query_performance(
                self.results_service.get_predictions_by_date_range,
                model_id, start_date, end_date
            )
        
        # 3. Simuliacijos sandorių gavimas
        for simulation_id in simulation_ids[:3]:  # Testuojame tik pirmas 3 simuliacijas
            self.measure_query_performance(
                self.results_service.get_simulation_trades,
                simulation_id
            )
        
        # 4. Modelio analizė
        for model_id in model_ids[:2]:
            self.measure_query_performance(
                self.results_service.analyze_model,
                model_id
            )
        
        # 5. Modelių palyginimas
        self.measure_query_performance(
            self.results_service.compare_models,
            model_ids[:3]  # Lyginame pirmus 3 modelius
        )
        
        # Konvertuojame rezultatus į DataFrame
        results_df = pd.DataFrame(self.results)
        
        # Išsaugome rezultatus į CSV failą
        csv_filename = f"performance_test_{dataset_size}_{test_time}.csv"
        results_df.to_csv(csv_filename, index=False)
        logger.info(f"Našumo testų rezultatai išsaugoti: {csv_filename}")
        
        # Vizualizuojame rezultatus
        self.visualize_results(results_df, dataset_size, test_time)
        
        return results_df
    
    def visualize_results(self, results_df, dataset_size, test_time):
        """
        Vizualizuoja našumo testų rezultatus
        
        Args:
            results_df (pd.DataFrame): Rezultatų DataFrame
            dataset_size (str): Duomenų rinkinio dydis
            test_time (str): Testo vykdymo laikas
        """
        plt.figure(figsize=(12, 6))
        
        # Sugrupuojame pagal funkcijos pavadinimą
        grouped = results_df.groupby('function')
        
        # Nubraižome stulpelinę diagramą su vidutiniu vykdymo laiku
        grouped['avg_time'].mean().plot(kind='bar', yerr=grouped['avg_time'].std())
        
        plt.title(f"Užklausų vykdymo laikas ({dataset_size} duomenų rinkinys)")
        plt.xlabel("Funkcija")
        plt.ylabel("Vidutinis vykdymo laikas (s)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Išsaugome grafiką
        plt.savefig(f"performance_test_{dataset_size}_{test_time}.png")
        logger.info(f"Našumo testų grafikas išsaugotas: performance_test_{dataset_size}_{test_time}.png")