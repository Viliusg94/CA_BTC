# main.py
import os
import argparse
import pandas as pd
from datetime import datetime
from src.data.collector import collect_btc_data
from src.data.processor import process_btc_data
from src.visualization.plots import plot_price_history, plot_with_indicators
from src.analysis.indicators_analysis import run_indicators_analysis
from src.visualization.signal_plots import create_all_signal_visualizations
from src.analysis.results_analysis import run_results_analysis
from database.models import init_db, BtcPriceData
from database.repository import BtcPriceRepository
from database.db_init import create_database
from sqlalchemy import text

def create_all_visualizations(df):
    """
    Sukuria visas vizualizacijas
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su techniniais indikatoriais
    """
    print("Kuriamos vizualizacijos...")
    
    # Kainos istorijos grafikas
    plot_price_history(df)
    
    # Grafikas su techniniais indikatoriais
    plot_with_indicators(df)
    
    print("Pagrindinės vizualizacijos sukurtos.")

def main():
    """
    Pagrindinė programos funkcija antrajam checkpointui
    """
    parser = argparse.ArgumentParser(description='BTC kainų analizės įrankis')
    parser.add_argument('--collect', action='store_true', help='Rinkti duomenis')
    parser.add_argument('--process', action='store_true', help='Apdoroti duomenis')
    parser.add_argument('--visualize', action='store_true', help='Vizualizuoti duomenis')
    parser.add_argument('--analyze', action='store_true', help='Analizuoti signalus')
    parser.add_argument('--all', action='store_true', help='Vykdyti visas operacijas')
    parser.add_argument('--start-date', type=str, default='2023-01-01', 
                        help='Duomenų pradžios data (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    # Jei nurodyta --all, atliekame visas operacijas
    if args.all:
        args.collect = args.process = args.visualize = args.analyze = True
    
    # Jei nenurodyta jokių argumentų, taip pat atliekame visas operacijas
    if not any([args.collect, args.process, args.visualize, args.analyze]):
        args.collect = args.process = args.visualize = args.analyze = True
    
    # Sukuriame duomenų bazę, jei jos dar nėra
    create_database()
    
    # Inicializuojame duomenų bazės prisijungimą
    engine, session = init_db()
    btc_repo = BtcPriceRepository(session)
    
    # 1. Renkame duomenis, jei nurodyta
    if args.collect:
        print("\n--- [1/4] Duomenų rinkimas ---")
        btc_data = collect_btc_data(start_date=args.start_date)
        if btc_data is None:
            print("Nepavyko surinkti duomenų. Programa nutraukiama.")
            session.close()
            return
        
        # Patikriname, kiek įrašų yra duomenų bazėje
        # Naudojame text() funkciją
        result = session.execute(text("SELECT COUNT(*) FROM btc_price_data")).fetchone()
        db_count = result[0] if result else 0
        print(f"Duomenų bazėje yra {db_count} BTC kainos įrašai")
    
    # 2. Apdorojame duomenis, jei nurodyta
    if args.process:
        print("\n--- [2/4] Duomenų apdorojimas ---")
        processed_data = process_btc_data()
        if processed_data is None:
            print("Nepavyko apdoroti duomenų. Programa nutraukiama.")
            session.close()
            return
    
    # 3. Vizualizuojame duomenis, jei nurodyta
    if args.visualize:
        print("\n--- [3/4] Duomenų vizualizacija ---")
        # Patikriname, ar yra apdorotų duomenų failas
        processed_data_path = "data/processed/btc_features.csv"
        
        if not os.path.exists(processed_data_path):
            print(f"Klaida: Nerastas apdorotų duomenų failas {processed_data_path}")
            print("Pirma paleiskite programą su --process vėliavėle")
            session.close()
            return
        
        # Nuskaitome apdorotus duomenis iš CSV
        processed_data = pd.read_csv(processed_data_path, index_col=0, parse_dates=True)
        
        # Sukuriame visas vizualizacijas
        os.makedirs('data/processed', exist_ok=True)
        create_all_visualizations(processed_data)
        print("Vizualizacijos išsaugotos data/processed/ direktorijoje")
    
    # 4. Analizuojame signalus, jei nurodyta
    if args.analyze:
        print("\n--- [4/4] Signalų analizė ---")
        
        # Analizuojame signalus
        signals_data = run_indicators_analysis()
        if signals_data is None:
            print("Nepavyko analizuoti signalų. Programa nutraukiama.")
            session.close()
            return
        
        # Vizualizuojame signalus
        create_all_signal_visualizations(signals_data)
        print("Signalų vizualizacijos išsaugotos data/analysis/ direktorijoje")
        
        # Analizuojame rezultatus
        returns_df, performance_metrics = run_results_analysis()
        if returns_df is not None and performance_metrics is not None:
            print("Rezultatų analizė baigta.")
            print("\nVeiklos rezultatų metrikos:")
            print(performance_metrics)
    
    # Uždarome sesija
    session.close()
    print("\nProgramos vykdymas baigtas!")

if __name__ == "__main__":
    main()