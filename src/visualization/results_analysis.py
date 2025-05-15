# SUKURTI FAILĄ: d:\CA_BTC\src\analysis\results_analysis.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def calculate_returns(df):
    """
    Apskaičiuoja grąžas pagal signalus
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su techniniais indikatoriais ir signalais
        
    Returns:
        pandas.DataFrame: Duomenų rinkinys su grąžomis
    """
    print("Skaičiuojamos grąžos pagal signalus...")
    
    # Kopijuojame duomenis
    data = df.copy()
    
    # Apskaičiuojame dienos grąžą
    data['Daily_Return'] = data['Close'].pct_change()
    
    # Patikriname, ar yra signalų stulpeliai
    signal_cols = ['SMA_Signal', 'RSI_Signal', 'MACD_Signal', 'Bollinger_Signal', 'Combined_Signal']
    missing_cols = [col for col in signal_cols if col not in data.columns]
    
    if missing_cols:
        print(f"Trūksta reikalingų signalų stulpelių: {', '.join(missing_cols)}")
        # Sukuriame trūkstamus stulpelius su 0 reikšmėmis
        for col in missing_cols:
            data[col] = 0
    
    # Bendra strategija
    data['Combined_Strategy_Return'] = data['Combined_Signal'].shift(1) * data['Daily_Return']
    
    # Apskaičiuojame kumuliacinę grąžą
    # Buy and Hold strategija
    data['Buy_Hold_Cumulative'] = (1 + data['Daily_Return']).cumprod()
    
    # Bendra strategija
    data['Combined_Strategy_Cumulative'] = (1 + data['Combined_Strategy_Return']).cumprod()
    
    return data

def run_results_analysis():
    """
    Paleidžia analizės rezultatų analizę
    
    Returns:
        tuple: (grąžų DataFrame, veiklos rezultatų metrikos DataFrame)
    """
    print("Pradedama analizės rezultatų analizė...")
    
    # Įkeliame duomenis
    signals_path = "data/analysis/signals.csv"
    if not os.path.exists(signals_path):
        print(f"Klaida: Nerastas signalų failas {signals_path}")
        print("Pirma paleiskite signalų analizę.")
        return None, None
    
    signals_df = pd.read_csv(signals_path, index_col=0, parse_dates=True)
    
    # Apskaičiuojame grąžas
    returns_df = calculate_returns(signals_df)
    
    # Išsaugome grąžų duomenis
    returns_path = "data/analysis/returns.csv"
    os.makedirs(os.path.dirname(returns_path), exist_ok=True)
    returns_df.to_csv(returns_path)
    print(f"Grąžų duomenys išsaugoti: {returns_path}")
    
    print("Analizės rezultatų analizė baigta.")
    
    return returns_df, None

if __name__ == "__main__":
    # Paleidžiame analizę
    returns_df, _ = run_results_analysis()
    if returns_df is not None:
        print(f"Analizės rezultatai: {len(returns_df)} eilutės")