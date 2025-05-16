"""
Aplikacijos valdymo modulis
-----------------------------
Šis modulis apibrėžia App klasę, kuri valdo aplikacijos gyvenimo ciklą
ir sujungia visus komponentus į vieną sistemą.
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from core.di_container import DIContainer

# Sukuriame logerį
logger = logging.getLogger(__name__)

class App:
    """
    Aplikacijos valdymo klasė, kuri valdo visus komponentus.
    """
    def __init__(self):
        """
        Inicializuoja aplikaciją.
        """
        # Sukonfigūruojame logerius
        self._setup_logging()
        
        # Inicializuojame priklausomybių konteinerį
        self.container = DIContainer()
        
        logger.info("Aplikacija inicializuota.")
    
    def _setup_logging(self):
        """
        Sukonfigūruoja logerius.
        """
        # Sukuriame logs direktoriją, jei jos nėra
        os.makedirs('logs', exist_ok=True)
        
        # Nustatome logerio formaterį
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Sukuriame failų tvarkytuvą
        file_handler = logging.FileHandler(f'logs/app_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler.setFormatter(formatter)
        
        # Sukuriame konsolės tvarkytuvą
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # Nustatome šakninio logerio lygį ir tvarkytuvus
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def collect_data(self, start_date=None, end_date=None):
        """
        Renka BTC kainos duomenis.
        
        Args:
            start_date: Pradžios data (str arba datetime)
            end_date: Pabaigos data (str arba datetime)
        
        Returns:
            pandas.DataFrame: Surinkti duomenys
        """
        # Konvertuojame datas į reikiamą formatą, jei jos yra string
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Gauname servisą
        data_service = self.container.get('data_service')
        
        # Renkame duomenis
        from src.data.collector import collect_btc_data
        
        logger.info(f"Renkami BTC kainos duomenys nuo {start_date} iki {end_date}")
        return collect_btc_data(start_date, end_date)
    
    def process_data(self):
        """
        Apdoroja BTC kainos duomenis.
        
        Returns:
            pandas.DataFrame: Apdoroti duomenys
        """
        # Gauname servisą
        data_service = self.container.get('data_service')
        
        # Apdorojame duomenis
        from src.data.processor import process_btc_data
        
        logger.info("Apdorojami BTC kainos duomenys")
        return process_btc_data()
    
    def analyze_indicators(self):
        """
        Analizuoja techninius indikatorius.
        
        Returns:
            pandas.DataFrame: Analizės rezultatai
        """
        # Gauname servisą
        trading_service = self.container.get('trading_service')
        
        # Analizuojame indikatorius
        from src.analysis.indicators_analysis import run_indicators_analysis
        
        logger.info("Analizuojami techniniai indikatoriai")
        return run_indicators_analysis()
    
    def generate_trading_signals(self, method='combined'):
        """
        Generuoja prekybos signalus.
        
        Args:
            method: Signalų generavimo metodas
        
        Returns:
            pandas.DataFrame: Prekybos signalai
        """
        # Gauname prekybos servisą
        trading_service = self.container.get('trading_service')
        
        logger.info(f"Generuojami prekybos signalai (metodas: {method})")
        return trading_service.generate_trading_signals(method)
    
    def backtest_strategy(self, start_date=None, end_date=None, initial_capital=10000, signal_type='Combined_Signal'):
        """
        Testuoja prekybos strategiją istoriniuose duomenyse.
        
        Args:
            start_date: Pradžios data
            end_date: Pabaigos data
            initial_capital: Pradinis kapitalas
            signal_type: Signalo tipas
        
        Returns:
            pandas.DataFrame: Testavimo rezultatai
        """
        # Gauname prekybos servisą
        trading_service = self.container.get('trading_service')
        
        logger.info(f"Testuojama prekybos strategija (nuo {start_date} iki {end_date}, kapitalas: {initial_capital})")
        return trading_service.backtest_strategy(start_date, end_date, initial_capital, signal_type)
    
    def visualize_data(self):
        """
        Vizualizuoja duomenis.
        
        Returns:
            bool: True jei sėkminga, False jei ne
        """
        try:
            # Gauname duomenų servisą
            data_service = self.container.get('data_service')
            
            # Gauname duomenis
            df = data_service.get_data_for_analysis()
            
            if df.empty:
                logger.warning("Nerasti duomenys vizualizavimui.")
                return False
            
            # Sukuriame vizualizacijas
            from src.visualization.plots import plot_price_history, plot_with_indicators
            
            logger.info("Kuriamos duomenų vizualizacijos")
            
            # Kainos istorijos grafikas
            plot_price_history(df)
            
            # Grafikas su techniniais indikatoriais
            plot_with_indicators(df)
            
            return True
            
        except Exception as e:
            logger.error(f"Klaida vizualizuojant duomenis: {e}")
            return False
    
    def visualize_signals(self):
        """
        Vizualizuoja prekybos signalus.
        
        Returns:
            bool: True jei sėkminga, False jei ne
        """
        try:
            # Gauname prekybos servisą
            trading_service = self.container.get('trading_service')
            
            # Gauname signalus
            signals_df = trading_service.generate_trading_signals()
            
            if signals_df.empty:
                logger.warning("Nerasti signalai vizualizavimui.")
                return False
            
            # Sukuriame signalų vizualizacijas
            from src.visualization.signal_plots import create_all_signal_visualizations
            
            logger.info("Kuriamos signalų vizualizacijos")
            create_all_signal_visualizations(signals_df)
            
            return True
            
        except Exception as e:
            logger.error(f"Klaida vizualizuojant signalus: {e}")
            return False
    
    def analyze_results(self):
        """
        Analizuoja rezultatus.
        
        Returns:
            pandas.DataFrame: Analizės rezultatai
        """
        try:
            # Analizuojame rezultatus
            from src.analysis.results_analysis import run_results_analysis
            
            logger.info("Analizuojami rezultatai")
            return run_results_analysis()
            
        except Exception as e:
            logger.error(f"Klaida analizuojant rezultatus: {e}")
            return None
    
    def cleanup(self):
        """
        Išvalo aplikacijos resursus.
        """
        try:
            # Išvalome priklausomybių konteinerį
            self.container.cleanup()
            
            logger.info("Aplikacijos resursai išvalyti.")
            
        except Exception as e:
            logger.error(f"Klaida išvalant resursus: {e}")