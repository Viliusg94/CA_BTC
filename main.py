"""
Pagrindinis programos failas
-----------------------------
Šis failas yra pagrindinis programos įėjimo taškas, kuris apdoroja komandinės
eilutės argumentus ir vykdo atitinkamas operacijas naudodamas aplikacijos logiką.
"""

import argparse
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
from core.app import App

def create_all_visualizations(df):
    """
    Sukuria visas vizualizacijas
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su techniniais indikatoriais
    """
    print("Kuriamos vizualizacijos...")
    
    # Kainos istorijos grafikas
    from src.visualization.plots import plot_price_history, plot_with_indicators
    
    plot_price_history(df)
    
    # Grafikas su techniniais indikatoriais
    plot_with_indicators(df)
    
    print("Pagrindinės vizualizacijos sukurtos.")

def test_simulator(args):
    """
    Testuoja prekybos simuliatoriaus veikimą
    """
    print("\n=== Testuojamas prekybos simuliatorius ===")
    
    from core.app import App
    from simulator.signals.technical_indicator_signal_generator import TechnicalIndicatorSignalGenerator
    from simulator.signals.model_prediction_signal_generator import ModelPredictionSignalGenerator
    from simulator.signals.hybrid_signal_generator import HybridSignalGenerator
    from simulator.strategies.trend_following_strategy import TrendFollowingStrategy
    from simulator.strategies.mean_reversion_strategy import MeanReversionStrategy
    
    # Inicializuojame aplikaciją
    app = App()
    
    # Gauname duomenis
    data_service = app.container.get('data_service')
    df = data_service.get_data_for_analysis()
    
    if df.empty:
        print("Nerasta duomenų simuliatoriaus testavimui.")
        return
    
    # Inicializuojame simuliatorių
    db_session = app.container.get_session()
    from simulator.engine import SimulatorEngine
    
    simulator = SimulatorEngine(db_session, initial_balance=args.initial_capital)
    
    # Įkeliame duomenis į simuliatorių
    simulator.load_data(df)
    
    # Sukuriame signalų generatorius
    ti_generator = TechnicalIndicatorSignalGenerator()
    ml_generator = ModelPredictionSignalGenerator(prediction_col='predicted_direction', confidence_col='confidence')
    hybrid_generator = HybridSignalGenerator([ti_generator, ml_generator])
    
    # Sukuriame strategijas
    trend_strategy = TrendFollowingStrategy()
    mean_reversion_strategy = MeanReversionStrategy()
    
    # Vykdome simuliaciją
    print(f"Simuliuojama prekyba nuo {df.index[0]} iki {df.index[-1]}")
    
    results = simulator.run_simulation(
        generators=[hybrid_generator],  # Teisingas parametras 'generators'
        strategy_list=[trend_strategy, mean_reversion_strategy],  # Teisingas parametras 'strategy_list'
        risk_params={  # Teisingas parametras 'risk_params'
            'stop_loss_percentage': 0.05,
            'take_profit_percentage': 0.1
        }
    )
    
    # Rodome rezultatus
    metrics = results['performance_metrics']
    trades = results['trade_history']
    
    print("\n--- Simuliacijos rezultatai ---")
    print(f"Iš viso operacijų: {metrics.get('total_trades', 0)}")
    print(f"Sėkmės rodiklis: {metrics.get('win_rate', 0)*100:.2f}%")
    print(f"Pelningos operacijos: {metrics.get('profitable_trades', 0)}")
    print(f"Nuostolingos operacijos: {metrics.get('losing_trades', 0)}")
    print(f"Bendras pelnas: ${metrics.get('net_profit', 0):.2f}")
    print(f"Pelno faktorius: {metrics.get('profit_factor', 0):.2f}")
    print(f"Iš viso mokesčių: ${metrics.get('total_fees', 0):.2f}")
    print(f"Vidutinis praslydimas: ${metrics.get('average_slippage', 0):.4f}")
    
    # Sukuriame grafiką
    stats = simulator.stats
    stats.plot_performance(save_path="data/simulation/performance_chart.png")
    
    print(f"\nRezultatai išsaugoti direktorijoje 'data/simulation/'")
    print(f"Veiklos rezultatų grafikas: data/simulation/performance_chart.png")
    
    # Išvalome sesijos resursus
    db_session.close()

def main():
    """
    Pagrindinė programos funkcija, kuri apdoroja komandinės eilutės argumentus
    ir vykdo atitinkamas operacijas.
    """
    parser = argparse.ArgumentParser(description='Bitcoin kainų analizės sistema')
    
    parser.add_argument('--collect', action='store_true', help='Rinkti BTC kainos duomenis')
    parser.add_argument('--process', action='store_true', help='Apdoroti duomenis ir skaičiuoti indikatorius')
    parser.add_argument('--visualize', action='store_true', help='Vizualizuoti duomenis')
    parser.add_argument('--analyze', action='store_true', help='Analizuoti techninius indikatorius')
    parser.add_argument('--signals', action='store_true', help='Generuoti prekybos signalus')
    parser.add_argument('--backtest', action='store_true', help='Testuoti prekybos strategiją')
    parser.add_argument('--all', action='store_true', help='Vykdyti visas operacijas')
    parser.add_argument('--test-simulator', action='store_true', help='Testuoti prekybos simuliatorių')
    
    parser.add_argument('--start-date', type=str, help='Pradžios data (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='Pabaigos data (YYYY-MM-DD)')
    parser.add_argument('--signal-method', type=str, default='combined', help='Signalų generavimo metodas')
    parser.add_argument('--initial-capital', type=float, default=10000, help='Pradinis kapitalas backtest-ui')
    
    args = parser.parse_args()
    
    # Inicializuojame aplikaciją
    app = App()
    
    try:
        # Nustatome pradžios ir pabaigos datas
        start_date = args.start_date if args.start_date else (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date = args.end_date if args.end_date else datetime.now().strftime('%Y-%m-%d')
        
        # Vykdome operacijas pagal nurodytus argumentus
        if args.collect or args.all:
            print("\n=== Renkami BTC kainos duomenys ===")
            app.collect_data(start_date, end_date)
        
        if args.process or args.all:
            print("\n=== Apdorojami duomenys ir skaičiuojami indikatoriai ===")
            df = app.process_data()
            
            if df is not None:
                print(f"Duomenys sėkmingai apdoroti: {len(df)} eilutės.")
        
        if args.visualize or args.all:
            print("\n=== Vizualizuojami duomenys ===")
            app.visualize_data()
        
        if args.analyze or args.all:
            print("\n=== Analizuojami techniniai indikatoriai ===")
            indicators_df = app.analyze_indicators()
            
            if indicators_df is not None:
                print(f"Indikatorių analizė baigta: {len(indicators_df)} eilutės.")
                
                # Vizualizuojame signalus
                app.visualize_signals()
        
        if args.signals or args.all:
            print(f"\n=== Generuojami prekybos signalai (metodas: {args.signal_method}) ===")
            signals_df = app.generate_trading_signals(method=args.signal_method)
            
            if signals_df is not None:
                print(f"Signalai sugeneruoti: {len(signals_df)} eilutės.")
        
        if args.backtest or args.all:
            print(f"\n=== Testuojama prekybos strategija ===")
            backtest_df = app.backtest_strategy(
                start_date=start_date,
                end_date=end_date,
                initial_capital=args.initial_capital
            )
            
            if backtest_df is not None:
                print(f"Strategijos testavimas baigtas: {len(backtest_df)} eilutės.")
        
        if args.test_simulator:
            test_simulator(args)
        
        # Analizuojame rezultatus
        if args.analyze or args.signals or args.backtest or args.all:
            print("\n=== Analizuojami rezultatai ===")
            returns_df = app.analyze_results()
            
            if returns_df is not None:
                print("Rezultatų analizė baigta.")
                
                # Rodome pagrindines metrikas
                if 'Buy_Hold_Cumulative' in returns_df.columns and 'Combined_Strategy_Cumulative' in returns_df.columns:
                    final_bh = returns_df['Buy_Hold_Cumulative'].iloc[-1]
                    final_strat = returns_df['Combined_Strategy_Cumulative'].iloc[-1]
                    print("\nVeiklos rezultatų metrikos:")
                    print(f"Buy & Hold galutinė vertė: {final_bh:.4f}")
                    print(f"Strategijos galutinė vertė: {final_strat:.4f}")
                    print(f"Skirtumas: {(final_strat - final_bh):.4f} ({((final_strat/final_bh)-1)*100:.2f}%)")
        
        # Išvalome aplikacijos resursus
        app.cleanup()
        
        print("\n=== Programa baigė darbą ===")
        
    except Exception as e:
        print(f"Klaida: {e}")
        app.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()