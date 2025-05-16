"""
Simuliatoriaus paleidimo skriptas
-----------------------------
Šis skriptas palengvina simuliatoriaus paleidimą su įvairiais parametrais.
"""

import argparse
import logging
import pandas as pd
from datetime import datetime
import os

# Nustatome, kad būtų naudojamas teisingas kelias iki projekto modulių
import sys
sys.path.append('d:/CA_BTC')

# Importuojame reikalingas klases
from core.app import App
from simulator.engine import SimulatorEngine
from simulator.signals.technical_indicator_signal_generator import TechnicalIndicatorSignalGenerator
from simulator.signals.model_prediction_signal_generator import ModelPredictionSignalGenerator
from simulator.signals.hybrid_signal_generator import HybridSignalGenerator
from simulator.signals.simple_test_signal_generator import SimpleTestSignalGenerator  # Naujas generatorius
from simulator.strategies.trend_following_strategy import TrendFollowingStrategy
from simulator.strategies.mean_reversion_strategy import MeanReversionStrategy

# Konfigūruojame logerio formatą
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def run_simulation(data_file, initial_capital=10000, test_mode=False):
    """
    Funkcija simuliacijos paleidimui su nurodytais parametrais.
    
    Args:
        data_file (str): Duomenų failo kelias
        initial_capital (float): Pradinis kapitalas
        test_mode (bool): Ar naudoti testavimo režimą
    
    Returns:
        dict: Simuliacijos rezultatai
    """
    # Inicializuojame aplikaciją
    app = App()  # App klasė tikriausiai inicializuojasi automatiškai konstruktoriuje
    
    # Gauname duomenų bazės sesiją
    db_session = app.container.get_session()
    
    # Įkeliame duomenis
    logger.info(f"Įkeliami duomenys iš failo: {data_file}")
    df = pd.read_csv(data_file, index_col=0, parse_dates=True)
    
    # Inicializuojame simuliatorių
    simulator = SimulatorEngine(db_session, initial_balance=initial_capital)
    
    # Įkeliame duomenis į simuliatorių
    simulator.load_data(df)
    
    # Sukuriame signalų generatorius
    generators = []
    
    if test_mode:
        # Testavimo režime naudojame paprastą testavimo generatorių
        logger.info("Naudojamas testavimo režimas su SimpleTestSignalGenerator")
        test_generator = SimpleTestSignalGenerator(interval=15)
        generators.append(test_generator)
    else:
        # Standartiniame režime naudojame įprastus generatorius
        ti_generator = TechnicalIndicatorSignalGenerator()
        ml_generator = ModelPredictionSignalGenerator(prediction_col='predicted_direction', confidence_col='confidence')
        hybrid_generator = HybridSignalGenerator([ti_generator, ml_generator])
        generators.append(hybrid_generator)
    
    # Sukuriame strategijas
    trend_strategy = TrendFollowingStrategy()
    mean_reversion_strategy = MeanReversionStrategy()
    
    # Vykdome simuliaciją
    print(f"Simuliuojama prekyba nuo {df.index[0]} iki {df.index[-1]}")
    
    results = simulator.run_simulation(
        generators=generators,
        strategy_list=[trend_strategy, mean_reversion_strategy],
        risk_params={
            'stop_loss_percentage': 0.05,
            'take_profit_percentage': 0.1
        }
    )
    
    # Rodome rezultatus
    display_results(results)
    
    # Išsaugome rezultatus
    save_results(results)
    
    # Uždarome aplikaciją
    app.cleanup()
    
    return results

def display_results(results):
    """
    Atvaizduojame simuliacijos rezultatus.
    
    Args:
        results (dict): Simuliacijos rezultatai
    """
    metrics = results['performance_metrics']
    trades = results['trade_history']
    
    print("\n--- Simuliacijos rezultatai ---")
    print(f"Iš viso operacijų: {len(trades)}")
    
    if 'win_rate' in metrics:
        print(f"Sėkmės rodiklis: {metrics['win_rate']*100:.2f}%")
        print(f"Pelningos operacijos: {metrics.get('winning_trades', 0)}")
        print(f"Nuostolingos operacijos: {metrics.get('losing_trades', 0)}")
    
    if 'total_profit' in metrics:
        print(f"Bendras pelnas: ${metrics['total_profit']:.2f}")
    
    if 'profit_factor' in metrics:
        print(f"Pelno faktorius: {metrics['profit_factor']:.2f}")
    
    if 'total_fees' in metrics:
        print(f"Iš viso mokesčių: ${metrics['total_fees']:.2f}")
    
    if 'avg_slippage' in metrics:
        print(f"Vidutinis praslydimas: ${metrics['avg_slippage']:.4f}")
    
    # Bandome sukurti grafiką
    try:
        simulator_stats = results.get('stats')
        if simulator_stats:
            simulator_stats.plot_performance()
            print("\nRezultatai išsaugoti direktorijoje 'data/simulation/'")
            print("Veiklos rezultatų grafikas: data/simulation/performance_chart.png")
    except Exception as e:
        print(f"Nepavyko sugeneruoti grafiko: {e}")

def save_results(results):
    """
    Išsaugome simuliacijos rezultatus.
    
    Args:
        results (dict): Simuliacijos rezultatai
    """
    # Sukuriame rezultatų katalogą, jei jo nėra
    os.makedirs("data/simulation", exist_ok=True)
    
    # Išsaugome prekybos istoriją
    if 'trade_history' in results and results['trade_history']:
        trade_df = pd.DataFrame(results['trade_history'])
        trade_df.to_csv("data/simulation/trade_history.csv", index=False)
    
    # Išsaugome portfelio vertės istoriją
    if 'portfolio_history' in results and not results['portfolio_history'].empty:
        results['portfolio_history'].to_csv("data/simulation/portfolio_history.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kriptovaliutų prekybos simuliatorius")
    parser.add_argument('--data', type=str, default="data/processed/btc_features.csv", help="Duomenų failo kelias")
    parser.add_argument('--capital', type=float, default=10000, help="Pradinis kapitalas")
    parser.add_argument('--test', action='store_true', help="Naudoti testavimo režimą su SimpleTestSignalGenerator")
    
    args = parser.parse_args()
    
    run_simulation(args.data, args.capital, args.test)