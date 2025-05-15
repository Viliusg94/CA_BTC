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

def plot_cumulative_returns(df, save_path="data/analysis/cumulative_returns.png"):
    """
    Nubraižo kumuliacines grąžas
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su grąžomis
        save_path (str): Kelias, kur išsaugoti grafiką
    """
    # Sukuriame grafiką
    plt.figure(figsize=(14, 7))
    
    # Nubraižome kumuliacines grąžas
    plt.plot(df.index, df['Buy_Hold_Cumulative'], label='Buy & Hold strategija', color='blue')
    plt.plot(df.index, df['Combined_Strategy_Cumulative'], label='Techninių indikatorių strategija', color='green')
    
    plt.title('Kumuliacinės grąžos')
    plt.xlabel('Data')
    plt.ylabel('Kumuliacinė grąža')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Išsaugome grafiką
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path)
        print(f"Kumuliacinių grąžų grafikas išsaugotas: {save_path}")
    
    plt.close()

def calculate_performance_metrics(df):
    """
    Apskaičiuoja veiklos rezultatų metrikas
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su grąžomis
        
    Returns:
        pandas.DataFrame: Veiklos rezultatų metrikos
    """
    if df is None or df.empty:
        return None
    
    # Skaičiuojame metrikas
    metrics = {}
    
    # Bendros metrikos
    metrics['Total_Days'] = len(df)
    metrics['First_Date'] = df.index[0].strftime('%Y-%m-%d')
    metrics['Last_Date'] = df.index[-1].strftime('%Y-%m-%d')
    
    # Buy & Hold strategijos metrikos
    if 'Buy_Hold_Cumulative' in df.columns:
        metrics['Buy_Hold_Final'] = df['Buy_Hold_Cumulative'].iloc[-1]
        metrics['Buy_Hold_Return'] = (metrics['Buy_Hold_Final'] - 1) * 100
    
    # Strategijos metrikos
    if 'Combined_Strategy_Cumulative' in df.columns:
        metrics['Strategy_Final'] = df['Combined_Strategy_Cumulative'].iloc[-1]
        metrics['Strategy_Return'] = (metrics['Strategy_Final'] - 1) * 100
    
    # Palyginimo metrikos
    if 'Buy_Hold_Final' in metrics and 'Strategy_Final' in metrics:
        metrics['Outperformance'] = metrics['Strategy_Return'] - metrics['Buy_Hold_Return']
    
    # Konvertuojame į DataFrame
    metrics_df = pd.DataFrame({'Metric': list(metrics.keys()), 'Value': list(metrics.values())})
    
    return metrics_df

def run_results_analysis():
    """
    Paleidžia analizės rezultatų analizę
    
    Returns:
        tuple: Grąžų DataFrame ir veiklos rezultatų metrikos
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
    
    # Nubraižome kumuliacines grąžas
    plot_cumulative_returns(returns_df)
    
    # Apskaičiuojame veiklos metrikos
    performance_metrics = calculate_performance_metrics(returns_df)
    
    print("Analizės rezultatų analizė baigta.")
    
    return returns_df, performance_metrics

if __name__ == "__main__":
    # Paleidžiame analizę
    returns_df, performance_metrics = run_results_analysis()
    if returns_df is not None:
        print(f"Analizės rezultatai: {len(returns_df)} eilutės")
    if performance_metrics is not None:
        print("Veiklos rezultatų metrikos:")
        print(performance_metrics)