# src/visualization/plots.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def plot_price_history(df, save_path="data/processed/btc_price_history.png"):
    """
    Nubraižo BTC kainos istorijos grafiką
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su BTC kainomis
        save_path (str): Kelias, kur išsaugoti grafiką
    """
    print("Braižomas BTC kainos istorijos grafikas...")
    
    # Sukuriame grafiką
    plt.figure(figsize=(14, 7))
    
    # Nubraižome kainų grafiką
    plt.plot(df.index, df['Close'], label='Uždarymo kaina', color='blue')
    
    # Pridedame slankųjį vidurkį
    if 'SMA_30' in df.columns:
        plt.plot(df.index, df['SMA_30'], label='30 dienų SMA', color='red', linestyle='--')
    
    # Pridedame tūrio grafiką apačioje
    ax2 = plt.twinx()
    ax2.fill_between(df.index, 0, df['Volume'], label='Tūris', alpha=0.3, color='gray')
    ax2.set_ylabel('Tūris')
    
    # Nustatome grafiko parametrus
    plt.title('Bitcoin (BTC) kainos istorija')
    plt.xlabel('Data')
    plt.ylabel('Kaina (USD)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Išsaugome grafiką
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path)
        print(f"Kainos istorijos grafikas išsaugotas: {save_path}")
    
    plt.close()

def plot_with_indicators(df, save_path="data/processed/btc_with_indicators.png"):
    """
    Nubraižo BTC kainos grafiką su techniniais indikatoriais
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su techniniais indikatoriais
        save_path (str): Kelias, kur išsaugoti grafiką
    """
    print("Braižomas BTC kainos grafikas su techniniais indikatoriais...")
    
    # Sukuriame grafiką su 3 subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 14), gridspec_kw={'height_ratios': [3, 1, 1]})
    
    # 1. Kainų ir slankiųjų vidurkių grafikas
    ax1.plot(df.index, df['Close'], label='Uždarymo kaina', color='black', linewidth=1.5)
    
    # Pridedame slankiuosius vidurkius
    if 'SMA_7' in df.columns:
        ax1.plot(df.index, df['SMA_7'], label='SMA 7', color='blue', alpha=0.7)
    if 'SMA_25' in df.columns:
        ax1.plot(df.index, df['SMA_25'], label='SMA 25', color='orange', alpha=0.7)
    if 'SMA_99' in df.columns:
        ax1.plot(df.index, df['SMA_99'], label='SMA 99', color='red', alpha=0.7)
    
    # Pridedame Bollinger juostas
    if all(col in df.columns for col in ['Bollinger_upper', 'Bollinger_lower']):
        ax1.plot(df.index, df['Bollinger_upper'], 'r--', alpha=0.3)
        ax1.plot(df.index, df['Bollinger_lower'], 'r--', alpha=0.3)
        ax1.fill_between(df.index, df['Bollinger_upper'], df['Bollinger_lower'], 
                         alpha=0.1, color='red')
    
    ax1.set_title('Bitcoin (BTC) kaina ir techniniai indikatoriai')
    ax1.set_ylabel('Kaina (USD)')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # 2. RSI grafikas
    if 'RSI_14' in df.columns:
        ax2.plot(df.index, df['RSI_14'], label='RSI 14', color='purple')
        ax2.axhline(y=70, color='red', linestyle='--', alpha=0.5)  # Perpirktumo linija
        ax2.axhline(y=30, color='green', linestyle='--', alpha=0.5)  # Perparduotumo linija
        ax2.fill_between(df.index, 70, df['RSI_14'], where=(df['RSI_14'] >= 70), 
                         color='red', alpha=0.3)
        ax2.fill_between(df.index, 30, df['RSI_14'], where=(df['RSI_14'] <= 30), 
                         color='green', alpha=0.3)
        ax2.set_ylabel('RSI')
        ax2.set_ylim(0, 100)
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)
    
    # 3. MACD grafikas
    if all(col in df.columns for col in ['MACD', 'MACD_signal']):
        ax3.plot(df.index, df['MACD'], label='MACD', color='blue')
        ax3.plot(df.index, df['MACD_signal'], label='Signal', color='red')
        
        # MACD histogramas
        if 'MACD_hist' in df.columns:
            positive = df['MACD_hist'] > 0
            negative = df['MACD_hist'] < 0
            ax3.bar(df.index[positive], df['MACD_hist'][positive], color='green', alpha=0.5, width=1)
            ax3.bar(df.index[negative], df['MACD_hist'][negative], color='red', alpha=0.5, width=1)
        
        ax3.set_ylabel('MACD')
        ax3.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        ax3.legend(loc='upper left')
        ax3.grid(True, alpha=0.3)
    
    ax3.set_xlabel('Data')
    
    plt.tight_layout()
    
    # Išsaugome grafiką
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path)
        print(f"Grafikas su indikatoriais išsaugotas: {save_path}")
    
    plt.close()

def plot_correlation_matrix(df, save_path="data/processed/correlation_matrix.png"):
    """
    Nubraižo koreliacijos matricą tarp BTC kainos ir indikatorių
    
    Args:
        df (pandas.DataFrame): Duomenų rinkinys su techniniais indikatoriais
        save_path (str): Kelias, kur išsaugoti grafiką
    """
    print("Braižoma koreliacijos matrica...")
    
    # Pasirenkame tik skaitinius stulpelius
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Pasirenkame pagrindinius stulpelius analizei
    important_cols = ['Close']
    
    # Pridedame techniniius indikatorius
    for col in numeric_cols:
        if any(x in col for x in ['SMA', 'EMA', 'RSI', 'MACD', 'Bollinger', 'ATR', 'OBV']):
            important_cols.append(col)
    
    # Atfiltruojame stulpelius, kurie yra DataFrame
    important_cols = [col for col in important_cols if col in df.columns]
    
    # Skaičiuojame koreliaciją
    corr = df[important_cols].corr()
    
    # Braižome šilumos žemėlapį
    plt.figure(figsize=(12, 10))
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5)
    plt.title('BTC kainos ir techninių indikatorių koreliacijos matrica')
    
    # Išsaugome grafiką
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path)
        print(f"Koreliacijos matrica išsaugota: {save_path}")
    
    plt.close()

if __name__ == "__main__":
    # Testuojame grafikus
    try:
        # Įkeliame duomenis
        csv_path = "data/processed/btc_features.csv"
        if os.path.exists(csv_path):
            data = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            
            # Braižome grafikus
            plot_price_history(data)
            plot_with_indicators(data)
            plot_correlation_matrix(data)
        else:
            print(f"Klaida: Nerastas duomenų failas {csv_path}")
    except Exception as e:
        print(f"Klaida braižant grafikus: {e}")